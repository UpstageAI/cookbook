# ========================= services/db.py =========================
"""DynamoDB wrapper – assumes tables already exist."""
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional

from housing_alert.config import settings

dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)

# ★ no DescribeTable / CreateTable – just reference existing tables
user_table = dynamodb.Table(settings.USER_TABLE)
notice_table = dynamodb.Table(settings.NOTICE_TABLE)
notification_table = dynamodb.Table(settings.NOTIFICATION_TABLE)


# ---------- User ----------
def save_user(user: Dict[str, Any]) -> None:
    user_table.put_item(Item=user)


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = user_table.get_item(Key={"user_id": user_id})
        print(resp)
        return resp.get("Item")
    except ClientError as e:
        print("DynamoDB get_user error", e)
        return None


# ---------- Notice ----------
def get_notice(id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = notice_table.get_item(Key={"id": id})
        return resp.get("Item")
    except ClientError as e:
        print("DynamoDB get_notice error", e)
        return None
