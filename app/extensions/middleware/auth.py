"""
Authentication Middleware
Customize this for your authentication needs
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer(auto_error=False)


async def verify_token(credentials: HTTPAuthorizationCredentials | None) -> dict:
    """
    Verify JWT token and return user data
    Customize this for your authentication logic
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    token = credentials.credentials

    # Add your token validation logic here
    # Example: decode JWT, verify signature, check expiration

    # For now, just return a placeholder
    return {"user_id": "placeholder", "token": token}


async def auth_middleware(request: Request, call_next):
    """
    Authentication middleware
    Add this to your FastAPI app to require authentication on all routes
    """
    # Skip authentication for public routes
    public_paths = ["/health", "/_docs", "/_redoc", "/openapi.json"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    # Get and verify token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    # Add token verification here
    # token = auth_header.split(" ")[1]
    # user = await verify_token(token)
    # request.state.user = user

    return await call_next(request)
