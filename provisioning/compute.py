import os
import boto3

AWS_REGION          = os.getenv("AWS_REGION", "us-east-1")
ECS_CLUSTER         = os.getenv("ECS_CLUSTER")
ECR_IMAGE           = os.getenv("ECR_IMAGE")
VPC_SUBNETS         = os.getenv("VPC_SUBNETS", "").split(",")
SECURITY_GROUP      = os.getenv("SECURITY_GROUP")
ALB_LISTENER_ARN    = os.getenv("ALB_LISTENER_ARN")
VPC_ID              = os.getenv("VPC_ID")
TASK_EXECUTION_ROLE = os.getenv("TASK_EXECUTION_ROLE_ARN")
RDS_HOST            = os.getenv("RDS_HOST")
RDS_PORT            = os.getenv("RDS_PORT", "5432")

ecs    = boto3.client("ecs",    region_name=AWS_REGION)
elbv2  = boto3.client("elbv2",  region_name=AWS_REGION)
logs   = boto3.client("logs",   region_name=AWS_REGION)

LOG_GROUP = "/crimata/customers"


def create_service(slug: str, db_name: str, db_password: str, secret_key: str, passphrase: str) -> str:
    """Spin up a Fargate service for a customer. Returns the target group ARN."""
    _ensure_log_group()
    target_group_arn = _create_target_group(slug)
    task_def_arn     = _register_task_definition(slug, db_name, db_password, secret_key, passphrase)
    _create_ecs_service(slug, task_def_arn, target_group_arn)
    _add_alb_listener_rule(slug, target_group_arn)
    return target_group_arn


def delete_service(slug: str, target_group_arn: str) -> None:
    """Tear down a customer's ECS service and ALB resources (used on cancellation)."""
    # Scale down and delete ECS service
    try:
        ecs.update_service(cluster=ECS_CLUSTER, service=f"crimata-{slug}", desiredCount=0)
        ecs.delete_service(cluster=ECS_CLUSTER, service=f"crimata-{slug}")
    except ecs.exceptions.ServiceNotFoundException:
        pass

    # Remove ALB listener rules pointing to this target group
    rules = elbv2.describe_rules(ListenerArn=ALB_LISTENER_ARN)["Rules"]
    for rule in rules:
        for action in rule.get("Actions", []):
            if action.get("TargetGroupArn") == target_group_arn:
                elbv2.delete_rule(RuleArn=rule["RuleArn"])

    # Delete target group
    try:
        elbv2.delete_target_group(TargetGroupArn=target_group_arn)
    except Exception:
        pass


# --- helpers ---

def _ensure_log_group() -> None:
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass


def _create_target_group(slug: str) -> str:
    resp = elbv2.create_target_group(
        Name=f"crimata-{slug}"[:32],
        Protocol="HTTP",
        Port=8000,
        VpcId=VPC_ID,
        TargetType="ip",
        HealthCheckPath="/api/health",
        HealthCheckIntervalSeconds=30,
        HealthyThresholdCount=2,
    )
    return resp["TargetGroups"][0]["TargetGroupArn"]


def _register_task_definition(slug: str, db_name: str, db_password: str, secret_key: str, passphrase: str) -> str:
    database_url = f"postgresql://{db_name}:{db_password}@{RDS_HOST}:{RDS_PORT}/{db_name}"
    resp = ecs.register_task_definition(
        family=f"crimata-{slug}",
        networkMode="awsvpc",
        requiresCompatibilities=["FARGATE"],
        cpu="256",
        memory="512",
        executionRoleArn=TASK_EXECUTION_ROLE,
        containerDefinitions=[{
            "name": "crimata",
            "image": ECR_IMAGE,
            "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
            "environment": [
                {"name": "DATABASE_URL",  "value": database_url},
                {"name": "SECRET_KEY",    "value": secret_key},
                {"name": "PASSPHRASE",    "value": passphrase},
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group":         LOG_GROUP,
                    "awslogs-region":        AWS_REGION,
                    "awslogs-stream-prefix": slug,
                },
            },
        }],
    )
    return resp["taskDefinition"]["taskDefinitionArn"]


def _create_ecs_service(slug: str, task_def_arn: str, target_group_arn: str) -> None:
    ecs.create_service(
        cluster=ECS_CLUSTER,
        serviceName=f"crimata-{slug}",
        taskDefinition=task_def_arn,
        desiredCount=1,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets":        VPC_SUBNETS,
                "securityGroups": [SECURITY_GROUP],
                "assignPublicIp": "ENABLED",
            },
        },
        loadBalancers=[{
            "targetGroupArn": target_group_arn,
            "containerName":  "crimata",
            "containerPort":  8000,
        }],
    )


def _add_alb_listener_rule(slug: str, target_group_arn: str) -> None:
    # Use existing rule count to pick a priority (offset from 100 to leave room below)
    existing = elbv2.describe_rules(ListenerArn=ALB_LISTENER_ARN)["Rules"]
    priorities = [int(r["Priority"]) for r in existing if r["Priority"] != "default"]
    priority = max(priorities, default=99) + 1

    elbv2.create_rule(
        ListenerArn=ALB_LISTENER_ARN,
        Priority=priority,
        Conditions=[{"Field": "host-header", "Values": [f"{slug}.crimata.com"]}],
        Actions=[{"Type": "forward", "TargetGroupArn": target_group_arn}],
    )
