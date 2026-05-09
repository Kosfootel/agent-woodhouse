"""Vigil Home - Authentication module.

Implements JWT-based authentication for the FastAPI backend:
- Argon2id password hashing (with bcrypt fallback)
- JWT access tokens (HS256, short-lived)
- Opaque refresh tokens with rotation
- FastAPI dependency injection for route protection
- Optional auth bypass via VIGIL_AUTH_DISABLED env var (dev only)

Designed per SECURITY-HARDENING-PLAN.md Phase 0.
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RefreshToken

logger = logging.getLogger("vigil.auth")

# ── Configuration ──────────────────────────────────────────────────

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("VIGIL_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("VIGIL_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
ALGORITHM = "HS256"

# Auth bypass for development
AUTH_DISABLED = os.environ.get("VIGIL_AUTH_DISABLED", "").lower() in ("true", "1", "yes")


def _get_jwt_secret() -> str:
    """Get or auto-generate the JWT signing secret.

    Precedence:
    1. VIGIL_JWT_SECRET env var
    2. VIGIL_JWT_SECRET_FILE (read secret from file path)
    3. Auto-generate and persist to /data/.jwt_secret
    """
    secret = os.environ.get("VIGIL_JWT_SECRET")
    if secret:
        return secret

    file_path = os.environ.get("VIGIL_JWT_SECRET_FILE")
    if file_path:
        try:
            with open(file_path) as f:
                return f.read().strip()
        except OSError:
            logger.warning(f"Could not read JWT secret from {file_path}")

    # Auto-generate and persist
    default_path = "/data/.jwt_secret"
    try:
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        if os.path.exists(default_path):
            with open(default_path) as f:
                return f.read().strip()
        secret = secrets.token_hex(32)
        with open(default_path, "w") as f:
            f.write(secret)
        os.chmod(default_path, 0o600)
        logger.info(f"Auto-generated JWT secret written to {default_path}")
        return secret
    except OSError:
        logger.warning("Could not persist JWT secret; generating ephemeral secret")
        return secrets.token_hex(32)


JWT_SECRET = _get_jwt_secret()

# Password hashing context
# Prefer Argon2id (modern, memory-hard), fall back to bcrypt
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    argon2__time_cost=2,        # light enough for consumer hardware
    argon2__memory_cost=1024 * 32,  # 32 MB
    argon2__parallelism=2,
    bcrypt__rounds=12,
)

# FastAPI security scheme
security = HTTPBearer(auto_error=False)


# ── Password hashing ───────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using the configured context."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT token management ──────────────────────────────────────────

def create_access_token(user_id: int, role: str = "admin") -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_access_token(token: str) -> Optional[dict]:
    """Verify a JWT access token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            logger.warning("Token type is not 'access'")
            return None
        return payload
    except JWTError as e:
        logger.debug(f"JWT verification failed: {e}")
        return None


def create_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token."""
    return secrets.token_urlsafe(48)


def create_refresh_token_expiry() -> datetime:
    """Return the expiry datetime for a new refresh token."""
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


# ── FastAPI dependency: require authentication ─────────────────────

async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """FastAPI dependency that validates JWT bearer token.

    Returns the JWT payload dict on success.
    Raises HTTPException 401 if missing, invalid, or expired.
    """
    if AUTH_DISABLED:
        return {"sub": "0", "role": "admin", "auth_disabled": True}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """FastAPI dependency: optional auth — returns payload or None.

    Use for endpoints that work both authenticated and unauthenticated
    (e.g., SSE streams where the token is in a query param as fallback).
    """
    if AUTH_DISABLED or not credentials:
        return None
    return verify_access_token(credentials.credentials)


# ── Admin user bootstrapping ───────────────────────────────────────

def bootstrap_admin(db: Session) -> User:
    """Ensure the admin user exists in the database.

    Reads credentials from environment:
      - VIGIL_ADMIN_USERNAME (default: "admin")
      - VIGIL_ADMIN_PASSWORD or VIGIL_ADMIN_PASSWORD_FILE

    If no password is configured, generates one and logs it.
    """
    username = os.environ.get("VIGIL_ADMIN_USERNAME", "admin")

    # Read password with _FILE fallback
    password = os.environ.get("VIGIL_ADMIN_PASSWORD")
    if not password:
        file_path = os.environ.get("VIGIL_ADMIN_PASSWORD_FILE")
        if file_path:
            try:
                with open(file_path) as f:
                    password = f.read().strip()
            except OSError:
                logger.warning(f"Could not read admin password from {file_path}")

    generated = False
    if not password:
        password = secrets.token_urlsafe(16)
        generated = True

    # Check if admin already exists
    admin = db.query(User).filter(User.username == username).first()
    if admin:
        # Update password if it changed
        if not verify_password(password, admin.password_hash):
            admin.password_hash = hash_password(password)
            db.commit()
            logger.info(f"Admin user '{username}' password updated")
        return admin

    # Create admin user
    admin = User(
        username=username,
        password_hash=hash_password(password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    if generated:
        logger.warning(
            f"No VIGIL_ADMIN_PASSWORD set. Generated password: {password}. "
            f"Set this in your environment and restart."
        )
        print(f"\n{'='*60}")
        print(f"⚠️  No admin password configured!")
        print(f"   Generated password: {password}")
        print(f"   Login with username: {username}")
        print(f"   Set VIGIL_ADMIN_PASSWORD in your environment and restart to secure.")
        print(f"{'='*60}\n")
    else:
        logger.info(f"Admin user '{username}' created")

    return admin
