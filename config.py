import os
import json
import boto3
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AWS_REGION: str = "ap-south-1"
    DB_SECRET_NAME: str = "trial-balance-db-secret"
    JWT_SECRET_NAME: str = "trial-balance-jwt-secret"

    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    def get_jwt_secret_value(self) -> str:
        if self.JWT_SECRET:
            return self.JWT_SECRET

        is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

        if is_lambda:
            secret_name = self.JWT_SECRET_NAME
            region_name = self.AWS_REGION

            session = boto3.session.Session()  # type: ignore
            client = session.client(
                service_name="secretsmanager",
                region_name=region_name,
            )

            secret_value = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(secret_value["SecretString"])

            jwt_secret = secret.get("JWT_SECRET") or secret.get("jwt_secret")
            if not jwt_secret:
                raise RuntimeError("JWT_SECRET not found in Secrets Manager")

            self.JWT_SECRET = jwt_secret
            return jwt_secret

        # local dev
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise RuntimeError("JWT_SECRET missing in environment")
        self.JWT_SECRET = jwt_secret
        return jwt_secret

    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None else None,
        extra="ignore",
    )

settings = Settings()
