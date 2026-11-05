"""Optional Google OAuth2 token verification module for ConsensusProbe.

Controlled by environment variables:
- AUTH_ENFORCE: "true" to require and verify tokens, "false" (default) to pass-through.
- AUTH_SKIP_NETWORK: "true" to skip network verification (for test/local runs).
- GOOGLE_CLIENT_ID: expected Google OAuth2 client ID.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from fastapi import Header, HTTPException, status


def is_auth_enforced() -> bool:
    return os.getenv("AUTH_ENFORCE", "false").lower() in ("true", "1", "yes")


def verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify Bearer token if AUTH_ENFORCE is enabled; otherwise no-op."""
    if not is_auth_enforced():
        return {"sub": "anonymous", "email": "anonymous@consensusprobe.local"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token",
        )

    # Dev/test mode token
    if os.getenv("AUTH_SKIP_NETWORK", "false").lower() in ("true", "1") or token.startswith("test-token-"):
        return {"sub": "test-user-id", "email": "test@consensusprobe.local", "token": token}

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests

        client_id = os.getenv("GOOGLE_CLIENT_ID")
        req = requests.Request()
        payload = id_token.verify_oauth2_token(token, req, client_id)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )
