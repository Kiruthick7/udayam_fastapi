from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # PRODUCTION: Uncomment for AWS deployment
    # AWS_REGION: str = "us-east-1"
    # DB_SECRET_NAME: str = "trial-balance-db-secret"

    # JWT Settings (DEV: using default value)
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"  # Ignore extra fields like DB_HOST, DB_NAME, etc.
    ) # type: ignore


settings = Settings() # type: ignore
