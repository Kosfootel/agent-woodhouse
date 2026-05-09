"""Vigil Home - Authentication module.

Implements JWT-based authentication for the FastAPI backend:
- Argon2id password hashing (with bcrypt fallback)
- JWT access tokens (HS256, short-lived)
- Opaque refresh tokens with rotation
- FastAPI dependency injection for route protection
- Optional auth bypass via VIGIL_AUTH_DISABLED env var (dev only)

Designed per SECURITY-HARDENING-PLAN.md Phase 0.
"""

import hashlib
import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
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
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Combined auth dependency: accepts JWT (Bearer), API key (X-API-Key),
    or token in query param (?token=).

    Checks in order:
    1. Authorization: Bearer <JWT> (standard header)
    2. X-API-Key header
    3. Query parameter ?token=<JWT>

    Returns the auth payload dict on success.
    Raises HTTPException 401 if all methods fail.
    """
    if AUTH_DISABLED:
        return {"sub": "0", "role": "admin", "auth_disabled": True}

    # 1. Try Bearer token (JWT)
    if credentials and credentials.credentials:
        payload = verify_access_token(credentials.credentials)
        if payload:
            return payload
        # Bearer token present but invalid — don't fall through
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Try X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        payload = validate_api_key(api_key, db)
        if payload:
            return payload
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key",
        )

    # 3. Try query parameter token (for SSE)
    query_token = request.query_params.get("token")
    if query_token:
        payload = verify_access_token(query_token)
        if payload:
            return payload
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — provide Bearer token, X-API-Key header, or ?token= query param",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def optional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """FastAPI dependency: optional auth — returns payload or None.

    Checks Bearer header first, then X-API-Key, then ?token= query param.
    Returns None if none are present (no 401).
    """
    if AUTH_DISABLED:
        return {"sub": "0", "role": "admin", "auth_disabled": True}

    # 1. Try Bearer token
    if credentials and credentials.credentials:
        payload = verify_access_token(credentials.credentials)
        if payload:
            return payload

    # 2. Try X-API-Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        payload = validate_api_key(api_key, db)
        if payload:
            return payload

    # 3. Try query param token
    query_token = request.query_params.get("token")
    if query_token:
        return verify_access_token(query_token)

    return None


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


# ── API Key authentication ──────────────────────────────────────────


API_KEY_PREFIX = "vh_"  # vigil-home prefix


def generate_api_key() -> str:
    """Generate a new API key with the vigil-home prefix."""
    random_part = secrets.token_urlsafe(32)
    return f"{API_KEY_PREFIX}{random_part}"


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256 (consistent with refresh token pattern)."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_api_key_prefix(key: str) -> str:
    """Extract the first 8 chars after prefix for identification."""
    if key.startswith(API_KEY_PREFIX):
        return key[len(API_KEY_PREFIX):len(API_KEY_PREFIX) + 8]
    return key[:8]


def create_api_key(db: Session, label: str, role: str = "admin") -> dict:
    """Create a new API key and store its hash in the database.

    Returns the plaintext key (only shown once) and the stored record.
    """
    from app.models import ApiKey

    plaintext = generate_api_key()
    key_hash = hash_api_key(plaintext)
    key_prefix = get_api_key_prefix(plaintext)

    api_key = ApiKey(
        key_prefix=key_prefix,
        key_hash=key_hash,
        label=label,
        role=role,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "plaintext_key": plaintext,
        "record": api_key,
    }


def validate_api_key(key: str, db: Session) -> Optional[dict]:
    """Validate an API key against stored hashes.

    Returns a payload dict compatible with require_auth if valid,
    or None if invalid/revoked.
    """
    from app.models import ApiKey

    if not key.startswith(API_KEY_PREFIX):
        return None

    key_hash = hash_api_key(key)
    stored = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == 1,
    ).first()

    if not stored:
        return None

    # Update last_used_at
    stored.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "sub": f"apikey:{stored.id}",
        "role": stored.role,
        "auth_method": "apikey",
        "label": stored.label,
    }


# ── Combined auth middleware ────────────────────────────────────────


def _extract_bearer_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    """Extract token from Authorization header."""
    if credentials:
        return credentials.credentials
    return None


def _extract_query_token(request: Request) -> Optional[str]:
    """Extract token from query parameter 'token'.

    Used for SSE connections where EventSource cannot set custom headers.
    Token in query string is short-lived (handled by caller) and should
    be stripped from proxy logs.
    """
    return request.query_params.get("token")


def _extract_header_token(request: Request) -> Optional[str]:
    """Extract API key from X-API-Key header."""
    return request.headers.get("X-API-Key")


async def require_auth_any(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Combined auth dependency: accepts JWT (Bearer), API key (X-API-Key),
    or token in query param (?token=).

    Checks in order:
    1. Authorization: Bearer <JWT> (standard header)
    2. X-API-Key header
    3. Query parameter ?token=<JWT>

    Designed for SSE streams and programmatic access where Bearer headers
    are not always available.
    """
    if AUTH_DISABLED:
        return {"sub": "0", "role": "admin", "auth_disabled": True}

    token = None

    # 1. Try Bearer token (JWT)
    bearer_token = _extract_bearer_token(credentials)
    if bearer_token:
        payload = verify_access_token(bearer_token)
        if payload:
            return payload
        # Bearer token present but invalid — don't fall through to other methods
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Try X-API-Key header
    api_key = _extract_header_token(request)
    if api_key:
        payload = validate_api_key(api_key, db)
        if payload:
            return payload
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key",
        )

    # 3. Try query parameter token (for SSE)
    query_token = _extract_query_token(request)
    if query_token:
        payload = verify_access_token(query_token)
        if payload:
            return payload
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — provide Bearer token, X-API-Key header, or ?token= query param",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """Auth dependency that requires an API key (X-API-Key header).

    Used for endpoints that should only be accessed via API key,
    such as event ingestion from Suricata/sensors.
    """
    if AUTH_DISABLED:
        return {"sub": "0", "role": "admin", "auth_disabled": True}

    # API key can come from Authorization: Bearer <key> or X-API-Key header
    api_key = None
    if credentials:
        api_key = credentials.credentials

    if not api_key:
        # FastAPI Request object isn't available as a default Depends,
        # so we only check Bearer. X-API-Key users should use require_auth_any.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required in Authorization header",
        )

    payload = validate_api_key(api_key, db)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or deactivated API key",
        )

    return payload
