import os
import time
from typing import List, Dict

import boto3


class DynamoDBChatHistory:
    """
    Stores chat messages per user in DynamoDB.

    Table schema (chats table):
    - PK: email (string)
    - SK: ts (number epoch seconds) as sort key
    - role: "user" | "assistant"
    - content: string
    """

    def __init__(self, table_name: str = None, region: str = None, max_messages: int = 20):
        self.table_name = table_name or os.getenv("DDB_CHATS_TABLE", "stockbot_chats")
        self.region = region or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.max_messages = max_messages
        self.dynamo = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamo.Table(self.table_name)

    def add_message(self, email: str, role: str, content: str) -> None:
        ts = int(time.time())
        self.table.put_item(
            Item={
                "email": email,
                "ts": ts,
                "role": role,
                "content": content,
            }
        )

    def get_last_messages(self, email: str) -> List[Dict]:
        resp = self.table.query(
            KeyConditionExpression="#e = :e",
            ExpressionAttributeNames={"#e": "email"},
            ExpressionAttributeValues={":e": email},
            ScanIndexForward=False,
            Limit=self.max_messages,
        )
        items = resp.get("Items", [])
        # Return ascending by time
        return sorted(items, key=lambda x: x["ts"]) if items else []


