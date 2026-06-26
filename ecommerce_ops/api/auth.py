from fastapi import Request, HTTPException
from ecommerce_ops.config import settings, Environment


async def verify_auth(request: Request) -> str:
    api_key_setting = settings.API_KEY
    if api_key_setting:
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or token != api_key_setting.get_secret_value():
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid API key. Use: Bearer <api-key>",
            )
        operator = request.headers.get("X-Operator-Id", "api-operator")
        return operator

    if settings.ENV != Environment.PRODUCTION:
        return "development-operator"

    raise HTTPException(status_code=500, detail="API_KEY not configured on server")


async def verify_auth_optional(request: Request) -> str:
    try:
        return await verify_auth(request)
    except HTTPException:
        return "anonymous"
