import os
import boto3

AWS_REGION     = os.getenv("AWS_REGION", "us-east-1")
HOSTED_ZONE_ID = os.getenv("HOSTED_ZONE_ID")
ALB_DNS_NAME   = os.getenv("ALB_DNS_NAME")
ALB_ZONE_ID    = os.getenv("ALB_ZONE_ID")  # ALB's hosted zone ID (not your Route53 zone)

route53 = boto3.client("route53", region_name=AWS_REGION)


def create_record(slug: str) -> None:
    """Create a Route53 alias record: {slug}.crimata.com → ALB."""
    route53.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch={
            "Changes": [{
                "Action": "CREATE",
                "ResourceRecordSet": {
                    "Name": f"{slug}.crimata.com",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId":         ALB_ZONE_ID,
                        "DNSName":              ALB_DNS_NAME,
                        "EvaluateTargetHealth": True,
                    },
                },
            }],
        },
    )


def delete_record(slug: str) -> None:
    """Remove the Route53 record for a cancelled customer."""
    route53.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch={
            "Changes": [{
                "Action": "DELETE",
                "ResourceRecordSet": {
                    "Name": f"{slug}.crimata.com",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId":         ALB_ZONE_ID,
                        "DNSName":              ALB_DNS_NAME,
                        "EvaluateTargetHealth": True,
                    },
                },
            }],
        },
    )
