"""Vigil Credential Vault - FastAPI Endpoints

These endpoints should be integrated into the main Vigil FastAPI application.
Copy these routes into app/main.py or import and include them.
"""

from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

# These imports assume vault modules are in app/vault/
from app.vault.vault_service import VaultService, get_vault_service
from app.vault.vault_models import (
    CredentialCreateRequest,
    CredentialUpdateRequest,
    CredentialRotateRequest,
    CredentialResponse,
    CredentialDecryptedResponse,
    AuditLogResponse,
    AccessLogEntry,
    VaultOperationResponse,
    VaultListResponse,
    CredentialHealthSummary,
    ServiceTypeSummary,
)
from app.database import get_db
from app.auth import require_auth, require_auth_any
from app.rate_limiter import limiter, GENERAL_LIMITS

# Create router
vault_router = APIRouter(prefix="/vault", tags=["credential-vault"])


# ============================================================================
# Helper to extract agent ID from auth payload
# ============================================================================

def get_agent_id(auth: dict) -> str:
    """Extract agent ID from auth payload.
    
    Falls back to user ID if agent ID not present.
    """
    # Try to get agent-specific ID first, then fall back to user sub
    return auth.get("agent_id") or auth.get("sub") or "unknown"


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request."""
    # Check for forwarded headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    if hasattr(request.client, "host"):
        return request.client.host
    
    return None


# ============================================================================
# Credential Management Endpoints
# ============================================================================

@vault_router.post("/credentials", response_model=VaultOperationResponse)
@limiter.limit(GENERAL_LIMITS)
def create_credential(
    req: CredentialCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Store a new encrypted credential in the vault.
    
    The credential_value will be encrypted using AES-256-GCM and never stored
    in plaintext. Access is logged for audit purposes.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    credential, success = vault.create_credential(
        db=db,
        name=req.name,
        service_type=req.service_type,
        credential_type=req.credential_type,
        credential_value=req.credential_value,
        agent_id=agent_id,
        agent_scope=req.agent_scope,
        expires_at=req.expires_at,
        ip_address=ip_address,
    )
    
    return VaultOperationResponse(
        success=success,
        message=f"Credential '{req.name}' created successfully",
        credential_id=credential.id,
        credential=CredentialResponse(
            id=credential.id,
            name=credential.name,
            service_type=credential.service_type,
            credential_type=credential.credential_type,
            agent_scope=credential._parse_agent_scope(),
            created_at=credential.created_at.isoformat() if credential.created_at else None,
            expires_at=credential.expires_at.isoformat() if credential.expires_at else None,
            last_rotated=credential.last_rotated.isoformat() if credential.last_rotated else None,
            last_accessed=credential.last_accessed.isoformat() if credential.last_accessed else None,
            access_count=credential.access_count,
            is_expired=credential.is_expired(),
            is_expiring_soon=credential.is_expiring_soon(),
        ),
    )


@vault_router.get("/credentials", response_model=VaultListResponse)
@limiter.limit(GENERAL_LIMITS)
def list_credentials(
    request: Request,
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """List credentials accessible to the requesting agent.
    
    Returns only metadata (never decrypted values). Results are filtered
    by agent scope.
    """
    agent_id = get_agent_id(auth)
    
    credentials = vault.list_credentials(
        db=db,
        agent_id=agent_id,
        service_type=service_type,
        skip=skip,
        limit=limit,
    )
    
    return VaultListResponse(
        count=len(credentials),
        credentials=[
            CredentialResponse(
                id=c.id,
                name=c.name,
                service_type=c.service_type,
                credential_type=c.credential_type,
                agent_scope=c._parse_agent_scope(),
                created_at=c.created_at.isoformat() if c.created_at else None,
                expires_at=c.expires_at.isoformat() if c.expires_at else None,
                last_rotated=c.last_rotated.isoformat() if c.last_rotated else None,
                last_accessed=c.last_accessed.isoformat() if c.last_accessed else None,
                access_count=c.access_count,
                is_expired=c.is_expired(),
                is_expiring_soon=c.is_expiring_soon(),
            )
            for c in credentials
        ],
    )


@vault_router.get("/credentials/{credential_id}", response_model=CredentialResponse)
@limiter.limit(GENERAL_LIMITS)
def get_credential(
    credential_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Get credential metadata by ID.
    
    Returns only metadata (name, service_type, etc.). Use POST to retrieve
    decrypted value. Access is logged.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    credential, _ = vault.get_credential(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        ip_address=ip_address,
        decrypt=False,
    )
    
    return CredentialResponse(
        id=credential.id,
        name=credential.name,
        service_type=credential.service_type,
        credential_type=credential.credential_type,
        agent_scope=credential._parse_agent_scope(),
        created_at=credential.created_at.isoformat() if credential.created_at else None,
        expires_at=credential.expires_at.isoformat() if credential.expires_at else None,
        last_rotated=credential.last_rotated.isoformat() if credential.last_rotated else None,
        last_accessed=credential.last_accessed.isoformat() if credential.last_accessed else None,
        access_count=credential.access_count,
        is_expired=credential.is_expired(),
        is_expiring_soon=credential.is_expiring_soon(),
    )


@vault_router.post("/credentials/{credential_id}/decrypt", response_model=CredentialDecryptedResponse)
@limiter.limit(GENERAL_LIMITS)
def decrypt_credential(
    credential_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Retrieve a credential with decrypted value.
    
    **WARNING:** This endpoint decrypts and returns the actual credential value.
    Every access is logged to the audit trail. Use with caution.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    credential, decrypted_value = vault.get_credential(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        ip_address=ip_address,
        decrypt=True,
    )
    
    return CredentialDecryptedResponse(
        id=credential.id,
        name=credential.name,
        service_type=credential.service_type,
        credential_type=credential.credential_type,
        credential_value=decrypted_value,
        agent_scope=credential._parse_agent_scope(),
        expires_at=credential.expires_at.isoformat() if credential.expires_at else None,
    )


@vault_router.patch("/credentials/{credential_id}", response_model=VaultOperationResponse)
@limiter.limit(GENERAL_LIMITS)
def update_credential(
    credential_id: str,
    req: CredentialUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Update credential metadata or value.
    
    If credential_value is provided, it will be encrypted and the
    last_rotated timestamp will be updated.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    credential = vault.update_credential(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        name=req.name,
        credential_value=req.credential_value,
        agent_scope=req.agent_scope,
        expires_at=req.expires_at,
        ip_address=ip_address,
    )
    
    return VaultOperationResponse(
        success=True,
        message=f"Credential '{credential.name}' updated successfully",
        credential_id=credential.id,
        credential=CredentialResponse(
            id=credential.id,
            name=credential.name,
            service_type=credential.service_type,
            credential_type=credential.credential_type,
            agent_scope=credential._parse_agent_scope(),
            created_at=credential.created_at.isoformat() if credential.created_at else None,
            expires_at=credential.expires_at.isoformat() if credential.expires_at else None,
            last_rotated=credential.last_rotated.isoformat() if credential.last_rotated else None,
            last_accessed=credential.last_accessed.isoformat() if credential.last_accessed else None,
            access_count=credential.access_count,
            is_expired=credential.is_expired(),
            is_expiring_soon=credential.is_expiring_soon(),
        ),
    )


@vault_router.post("/credentials/{credential_id}/rotate", response_model=VaultOperationResponse)
@limiter.limit(GENERAL_LIMITS)
def rotate_credential(
    credential_id: str,
    req: CredentialRotateRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Rotate a credential to a new value.
    
    Updates the encrypted credential value and sets last_rotated timestamp.
    The rotation is logged to the audit trail with optional reason.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    credential = vault.rotate_credential(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        new_credential_value=req.new_credential_value,
        reason=req.reason,
        ip_address=ip_address,
    )
    
    return VaultOperationResponse(
        success=True,
        message=f"Credential '{credential.name}' rotated successfully",
        credential_id=credential.id,
        credential=CredentialResponse(
            id=credential.id,
            name=credential.name,
            service_type=credential.service_type,
            credential_type=credential.credential_type,
            agent_scope=credential._parse_agent_scope(),
            created_at=credential.created_at.isoformat() if credential.created_at else None,
            expires_at=credential.expires_at.isoformat() if credential.expires_at else None,
            last_rotated=credential.last_rotated.isoformat() if credential.last_rotated else None,
            last_accessed=credential.last_accessed.isoformat() if credential.last_accessed else None,
            access_count=credential.access_count,
            is_expired=credential.is_expired(),
            is_expiring_soon=credential.is_expiring_soon(),
        ),
    )


@vault_router.delete("/credentials/{credential_id}")
@limiter.limit(GENERAL_LIMITS)
def delete_credential(
    credential_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Revoke and delete a credential.
    
    The credential is permanently deleted. This action is logged to the
    audit trail. Associated access logs are retained for compliance.
    """
    agent_id = get_agent_id(auth)
    ip_address = get_client_ip(request)
    
    vault.delete_credential(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        ip_address=ip_address,
    )
    
    return {"success": True, "message": f"Credential {credential_id} deleted"}


# ============================================================================
# Audit and Health Endpoints
# ============================================================================

@vault_router.get("/audit", response_model=AuditLogResponse)
@limiter.limit(GENERAL_LIMITS)
def get_audit_log(
    request: Request,
    credential_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None, pattern="^(read|write|rotate|delete|decrypt)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Query the credential access audit log.
    
    Returns all credential access events including reads, writes, rotations,
    deletions, and decryptions. Results include the agent ID and success status.
    """
    logs, total = vault.get_audit_log(
        db=db,
        credential_id=credential_id,
        agent_id=agent_id,
        action=action,
        skip=skip,
        limit=limit,
    )
    
    return AuditLogResponse(
        count=total,
        skip=skip,
        limit=limit,
        logs=[
            AccessLogEntry(
                id=log.id,
                credential_id=log.credential_id,
                credential_name=log.credential.name if log.credential else None,
                service_type=log.credential.service_type if log.credential else None,
                agent_id=log.agent_id,
                action=log.action,
                timestamp=log.timestamp.isoformat() if log.timestamp else None,
                success=log.success,
                reason=log.reason,
                ip_address=log.ip_address,
            )
            for log in logs
        ],
    )


@vault_router.get("/health", response_model=CredentialHealthSummary)
@limiter.limit(GENERAL_LIMITS)
def get_vault_health(
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
    vault: VaultService = Depends(get_vault_service),
):
    """Get credential vault health summary.
    
    Returns statistics on credential count, expiration status, and
    access patterns. Useful for dashboard monitoring.
    """
    summary = vault.get_health_summary(db)
    return CredentialHealthSummary(**summary)


@vault_router.get("/service-types", response_model=List[ServiceTypeSummary])
@limiter.limit(GENERAL_LIMITS)
def get_service_type_summary(
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth),
):
    """Get summary statistics grouped by service type.
    
    Returns credential counts and health metrics for each service type.
    """
    from sqlalchemy import func
    from app.vault.vault_models import CredentialVault
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=7)
    
    results = db.query(
        CredentialVault.service_type,
        func.count(CredentialVault.id).label("count"),
        func.sum(
            (CredentialVault.expires_at.isnot(None) & 
             (CredentialVault.expires_at <= soon) &
             (CredentialVault.expires_at > now)).cast(Integer)
        ).label("expiring_soon"),
        func.sum(
            (CredentialVault.expires_at.isnot(None) & 
             (CredentialVault.expires_at <= now)).cast(Integer)
        ).label("expired"),
    ).group_by(CredentialVault.service_type).all()
    
    return [
        ServiceTypeSummary(
            service_type=r.service_type,
            count=r.count,
            expiring_soon=r.expiring_soon or 0,
            expired=r.expired or 0,
        )
        for r in results
    ]


# ============================================================================
# Integration helper
# ============================================================================

def include_vault_routes(app):
    """Include vault routes in the main FastAPI app.
    
    Usage in main.py:
        from app.vault.vault_endpoints import include_vault_routes
        include_vault_routes(app)
    """
    app.include_router(vault_router)
