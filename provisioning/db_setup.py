import os
import psycopg2

RDS_HOST     = os.getenv("RDS_HOST")
RDS_PORT     = int(os.getenv("RDS_PORT", "5432"))
RDS_MASTER_USER = os.getenv("RDS_MASTER_USER")
RDS_MASTER_PASSWORD = os.getenv("RDS_MASTER_PASSWORD")


def create_database(db_name: str, db_password: str) -> None:
    """Create a Postgres database and dedicated user on the shared RDS instance."""
    conn = psycopg2.connect(
        host=RDS_HOST, port=RDS_PORT,
        user=RDS_MASTER_USER, password=RDS_MASTER_PASSWORD,
        dbname="postgres",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{db_name}"')
        cur.execute(f'CREATE USER "{db_name}" WITH PASSWORD %s', (db_password,))
        cur.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{db_name}"')
    conn.close()


def drop_database(db_name: str) -> None:
    """Drop a customer's database and user (used on cancellation)."""
    conn = psycopg2.connect(
        host=RDS_HOST, port=RDS_PORT,
        user=RDS_MASTER_USER, password=RDS_MASTER_PASSWORD,
        dbname="postgres",
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        cur.execute(f'DROP USER IF EXISTS "{db_name}"')
    conn.close()
