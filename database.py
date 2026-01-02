import os
import json
import boto3
from mysql.connector import pooling
from typing import Optional
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

_db_pool: Optional[pooling.MySQLConnectionPool] = None
_db_credentials_cache: Optional[dict] = None


def get_db_credentials():
    """Load credentials from AWS Secrets Manager with caching"""
    global _db_credentials_cache

    # Return cached credentials if available
    if _db_credentials_cache is not None:
        return _db_credentials_cache

    # Check if running in Lambda (production)
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    if is_lambda:
        # PRODUCTION: Load from AWS Secrets Manager
        secret_name = os.getenv("DB_SECRET_NAME", "trial-balance-db-secret")
        region_name = os.getenv("AWS_REGION", "ap-south-1")

        try:
            session = boto3.session.Session() # type: ignore
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            secret_value = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(secret_value['SecretString'])

            # Map secret keys to database config
            _db_credentials_cache = {
                "host": secret.get('host'),
                "database": secret.get('database') or secret.get('dbname'),
                "user": secret.get('user') or secret.get('username'),
                "password": secret.get('password'),
            }

            print(f"Loaded database credentials from Secrets Manager: {secret_name}")
            return _db_credentials_cache

        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"Error loading secret from Secrets Manager: {error_code}")
            raise RuntimeError(f"Failed to load database credentials: {error_code}")
    else:
        # LOCAL DEVELOPMENT: Load from environment variables
        _db_credentials_cache = {
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }
        print("Loaded database credentials from environment variables (local dev)")
        return _db_credentials_cache


def get_db_pool():
    global _db_pool

    if _db_pool is None:
        creds = get_db_credentials()

        if not all(creds.values()):
            raise RuntimeError("Database credentials are incomplete")

        _db_pool = pooling.MySQLConnectionPool(
            pool_name="trial_balance_pool",
            pool_size=5,
            **creds # type: ignore
        )

        print(f"Created database connection pool to {creds['host']}")

    return _db_pool


def get_db():
    return get_db_pool().get_connection()
