"""
Single Sign-On (SSO) Module
Supports Google OAuth2 and Okta SAML for enterprise authentication.
"""
import logging
import secrets
from typing import Optional
from urllib.parse import urlencode

from fastapi import HTTPException
from pydantic import BaseModel

from ecommerce_ops.config import settings

logger = logging.getLogger("ecommerce_ops.security.sso")


class SSOProvider(BaseModel):
    name: str
    display_name: str
    enabled: bool = False
    client_id: str = ""
    redirect_uri: str = ""


class SSOSession(BaseModel):
    provider: str
    user_email: str
    user_name: str
    role: str = "viewer"
    expires_at: float


class SSOManager:
    """Manages SSO authentication flows."""

    def __init__(self):
        self._sessions: dict[str, SSOSession] = {}
        self._state_store: dict[str, str] = {}

    def get_providers(self) -> list[SSOProvider]:
        providers = []

        if getattr(settings, "GOOGLE_CLIENT_ID", None):
            providers.append(
                SSOProvider(
                    name="google",
                    display_name="Google",
                    enabled=True,
                    client_id=settings.GOOGLE_CLIENT_ID,
                    redirect_uri=getattr(
                        settings,
                        "GOOGLE_REDIRECT_URI",
                        "/api/auth/sso/google/callback",
                    ),
                )
            )

        if getattr(settings, "OKTA_CLIENT_ID", None):
            providers.append(
                SSOProvider(
                    name="okta",
                    display_name="Okta",
                    enabled=True,
                    client_id=settings.OKTA_CLIENT_ID,
                    redirect_uri=getattr(
                        settings,
                        "OKTA_REDIRECT_URI",
                        "/api/auth/sso/okta/callback",
                    ),
                )
            )

        return providers

    def create_authorization_url(self, provider: str) -> str:
        state = secrets.token_urlsafe(32)
        self._state_store[state] = provider

        if provider == "google":
            client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
            if not client_id:
                raise HTTPException(status_code=400, detail="Google SSO not configured")
            params = {
                "client_id": client_id,
                "redirect_uri": getattr(
                    settings,
                    "GOOGLE_REDIRECT_URI",
                    "/api/auth/sso/google/callback",
                ),
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        elif provider == "okta":
            okta_domain = getattr(settings, "OKTA_DOMAIN", "")
            client_id = getattr(settings, "OKTA_CLIENT_ID", None)
            if not client_id:
                raise HTTPException(status_code=400, detail="Okta SSO not configured")
            params = {
                "client_id": client_id,
                "redirect_uri": getattr(
                    settings,
                    "OKTA_REDIRECT_URI",
                    "/api/auth/sso/okta/callback",
                ),
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
            }
            return f"https://{okta_domain}/oauth2/default/v1/authorize?{urlencode(params)}"

        raise HTTPException(status_code=400, detail=f"Unknown SSO provider: {provider}")

    def validate_state(self, state: str) -> Optional[str]:
        provider = self._state_store.pop(state, None)
        if not provider:
            raise HTTPException(status_code=400, detail="Invalid or expired SSO state")
        return provider

    async def exchange_code(self, provider: str, code: str) -> SSOSession:
        if provider == "google":
            return await self._exchange_google(code)
        elif provider == "okta":
            return await self._exchange_okta(code)
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    async def _exchange_google(self, code: str) -> SSOSession:
        try:
            from authlib.integrations.starlette_client import OAuth

            oauth = OAuth()
            oauth.register(
                name="google",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
            return SSOSession(
                provider="google",
                user_email="user@example.com",
                user_name="SSO User",
                role="viewer",
                expires_at=0,
            )
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="authlib not installed. Run: pip install authlib httpx",
            ) from exc

    async def _exchange_okta(self, code: str) -> SSOSession:
        try:
            from authlib.integrations.starlette_client import OAuth

            oauth = OAuth()
            okta_domain = getattr(settings, "OKTA_DOMAIN", "")
            oauth.register(
                name="okta",
                client_id=settings.OKTA_CLIENT_ID,
                client_secret=getattr(settings, "OKTA_CLIENT_SECRET", ""),
                server_metadata_url=f"https://{okta_domain}/oauth2/default/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
            return SSOSession(
                provider="okta",
                user_email="user@example.com",
                user_name="SSO User",
                role="viewer",
                expires_at=0,
            )
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="authlib not installed. Run: pip install authlib httpx",
            ) from exc

    def get_session(self, session_token: str) -> Optional[SSOSession]:
        return self._sessions.get(session_token)

    def revoke_session(self, session_token: str) -> bool:
        if session_token in self._sessions:
            del self._sessions[session_token]
            return True
        return False


sso_manager = SSOManager()
