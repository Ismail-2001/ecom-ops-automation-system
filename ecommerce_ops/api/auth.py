from fastapi import Request, HTTPException, Depends
from ecommerce_ops.config import settings, Environment


async def verify_auth(request: Request) -> str:
    if settings.ENV != Environment.PRODUCTION:
        return "development-operator"

    api_key_setting = settings.API_KEY
    if not api_key_setting:
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")

    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Use: Bearer <api-key>",
        )

    if token != api_key_setting.get_secret_value():
        raise HTTPException(status_code=403, detail="Invalid API key")

    operator = request.headers.get("X-Operator-Id", "api-operator")
    return operator
