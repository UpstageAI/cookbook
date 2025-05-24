"""공통 설정 및 환경 변수 로딩."""

import os
from functools import lru_cache


class Settings:
    @property
    @lru_cache(maxsize=1)
    def aws_region(self) -> str:
        return os.getenv("AWS_REGION", "us-east-1")

    # DynamoDB
    USER_TABLE: str = os.getenv("DYNAMO_USER_TABLE", "minerva-1-user-info-table")
    NOTICE_TABLE: str = os.getenv("DYNAMO_NOTICE_TABLE", "minerva-1-pdf-info-table")
    NOTIFICATION_TABLE: str = os.getenv(
        "DYNAMO_NOTIFICATION_TABLE", "minerva-1-notification-table"
    )

    # S3
    S3_BUCKET: str = os.getenv("S3_BUCKET", "housing-alert-notices")

    # Bedrock / Upstage
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-7-sonnet-20250219-v1:0"
    )
    UPSTAGE_API_KEY: str = os.getenv("UPSTAGE_API_KEY", "")


settings = Settings()
