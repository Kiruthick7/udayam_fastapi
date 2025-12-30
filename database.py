import mysql.connector
from mysql.connector import pooling
# import boto3  # PRODUCTION: Uncomment for AWS
# import json  # PRODUCTION: Uncomment for AWS
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()


# PRODUCTION CODE (AWS Secrets Manager) - Commented for dev
# def get_db_credentials():
#     """Load credentials from AWS Secrets Manager"""
#     try:
#         from config import settings
#         client = boto3.client('secretsmanager', region_name=settings.AWS_REGION)
#         secret = client.get_secret_value(SecretId=settings.DB_SECRET_NAME)
#         return json.loads(secret['SecretString'])
#     except Exception as e:
#         # Fallback to environment variables
#         return {
#             'host': os.getenv('DB_HOST'),
#             'database': os.getenv('DB_NAME'),
#             'username': os.getenv('DB_USER'),
#             'password': os.getenv('DB_PASSWORD')
#         }

# DEV CODE: Direct environment variables
def get_db_credentials():
    """Load credentials from environment variables for local development"""
    return {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }


creds = get_db_credentials()

db_pool = pooling.MySQLConnectionPool(
    pool_name="trial_balance_pool",
    pool_size=10,
    host=creds['host'],
    database=creds['database'],
    user=creds['username'],
    password=creds['password'],
    # ssl_ca='/path/to/rds-ca-cert.pem',  # Uncomment for AWS RDS SSL
    # ssl_verify_cert=True
)


def get_db():
    """Get database connection from pool"""
    return db_pool.get_connection()
