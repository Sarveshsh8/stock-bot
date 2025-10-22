import os
import base64
import json
import time
import urllib.parse
import requests
from typing import Optional, Dict, Any
from jose import jwt


class CognitoOAuth:
    """
    Minimal helper for AWS Cognito Hosted UI OAuth (Authorization Code Flow with PKCE optional).
    Assumes the following env vars:
      - COGNITO_DOMAIN: e.g., https://your-domain.auth.us-east-1.amazoncognito.com
      - COGNITO_CLIENT_ID
      - COGNITO_REDIRECT_URI: e.g., http://localhost:8501
      - COGNITO_REGION
      - COGNITO_USERPOOL_ID (for JWKS)
      - Optional: COGNITO_CLIENT_SECRET (if app client uses secret)
    """

    def __init__(self) -> None:
        self.domain = os.getenv("COGNITO_DOMAIN", "").rstrip("/")
        self.client_id = os.getenv("COGNITO_CLIENT_ID", "")
        self.client_secret = os.getenv("COGNITO_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("COGNITO_REDIRECT_URI", "")
        self.region = os.getenv("COGNITO_REGION", "us-east-1")
        self.userpool_id = os.getenv("COGNITO_USERPOOL_ID", "")
        self.scopes = os.getenv("COGNITO_SCOPES", "openid email profile").split()
        if not self.domain or not self.client_id or not self.redirect_uri:
            raise ValueError("Cognito OAuth env variables missing (COGNITO_DOMAIN, COGNITO_CLIENT_ID, COGNITO_REDIRECT_URI)")

    def get_authorize_url(self, state: str = "state") -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        return f"{self.domain}/oauth2/authorize?{urllib.parse.urlencode(params)}"

    def _basic_auth(self) -> Optional[str]:
        if not self.client_secret:
            return None
        token = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        return f"Basic {token}"

    def exchange_code(self, code: str) -> Dict[str, Any]:
        token_url = f"{self.domain}/oauth2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth = self._basic_auth()
        if auth:
            headers["Authorization"] = auth
        resp = requests.post(token_url, data=data, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_jwks(self) -> Dict[str, Any]:
        jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.userpool_id}/.well-known/jwks.json"
        resp = requests.get(jwks_url, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        jwks = self.get_jwks()
        unverified_headers = jwt.get_unverified_header(id_token)
        kid = unverified_headers.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise ValueError("Matching JWK not found for token")
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=self.client_id,
            issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.userpool_id}",
        )
        return claims


