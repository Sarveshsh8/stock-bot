import os
import time
from typing import List, Dict, Optional

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

    def add_message(self, email: str, role: str, content: str, session_id: Optional[str] = None) -> None:
        ts = int(time.time())
        self.table.put_item(
            Item={
                "email": email,
                "ts": ts,
                "role": role,
                "content": content,
                "session_id": session_id or "",
            }
        )

    def get_last_messages(self, email: str, session_id: Optional[str] = None) -> List[Dict]:
        resp = self.table.query(
            KeyConditionExpression="#e = :e",
            ExpressionAttributeNames={"#e": "email"},
            ExpressionAttributeValues={":e": email},
            ScanIndexForward=False,
            Limit=self.max_messages,
        )
        items = resp.get("Items", [])
        if session_id is not None:
            items = [it for it in items if it.get("session_id", "") == session_id]
        # Return ascending by time
        return sorted(items, key=lambda x: x["ts"]) if items else []


