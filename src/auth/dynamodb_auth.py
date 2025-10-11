import os
import time
from typing import Optional, Dict

import boto3
import bcrypt


class DynamoDBAuthService:
    """
    Simple auth service using DynamoDB and bcrypt.

    Table schema (users table):
    - PK: email (string)
    - password_hash: string
    - created_at: number (epoch seconds)
    """

    def __init__(self, table_name: Optional[str] = None, region: Optional[str] = None):
        self.table_name = table_name or os.getenv("DDB_USERS_TABLE", "stockbot_users")
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.dynamo = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamo.Table(self.table_name)

    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _check_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    def signup(self, email: str, password: str) -> bool:
        # Fail if user exists
        existing = self.get_user(email)
        if existing is not None:
            return False

        password_hash = self._hash_password(password)
        self.table.put_item(
            Item={
                "email": email,
                "password_hash": password_hash,
                "created_at": int(time.time()),
            },
            ConditionExpression="attribute_not_exists(email)",
        )
        return True

    def login(self, email: str, password: str) -> bool:
        user = self.get_user(email)
        if not user:
            return False
        return self._check_password(password, user.get("password_hash", ""))

    def get_user(self, email: str) -> Optional[Dict]:
        resp = self.table.get_item(Key={"email": email})
        return resp.get("Item")


