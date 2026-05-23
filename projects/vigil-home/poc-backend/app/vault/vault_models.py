"""Vigil Credential Vault - Database Models and Pydantic Schemas

SQLAlchemy models for credential_vault and credential_access_log tables.
Pydantic models for API request/response validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, validator

# Note: SQLAlchemy models use the shared Base from app.models
# The actual table definitions are in app/models.py to avoid circular imports
# This file contains Pydantic schemas for API validation
# ============================================================================

class CredentialCreateRequest(BaseModel):
    """Request model for creating a new credential."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable label")
    service_type: str = Field(..., min_length=1, max_length=64, description="Service type (hue, nest, ring, etc.)")
    credential_type: str = Field(..., pattern="^(api_key|oauth_token|password|certificate|other)$")
    credential_value: str = Field(..., min_length=1, description="The credential to encrypt (will not be stored plaintext)")
    agent_scope: Optional[List[str]] = Field(None, description="List of agent IDs allowed to access this credential")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp for rotation alerts")

    @validator("expires_at")
    def expires_at_must_be_future(cls, v):
        if v and v < datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return v


class CredentialUpdateRequest(BaseModel):
    """Request model for updating a credential."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    credential_value: Optional[str] = Field(None, min_length=1)
    agent_scope: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class CredentialRotateRequest(BaseModel):
    """Request model for rotating a credential."""
    new_credential_value: str = Field(..., min_length=1, description="New credential value")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for rotation")


class CredentialResponse(BaseModel):
    """Response model for credential data (never includes decrypted value)."""
    id: str
    name: str
    service_type: str
    credential_type: str
    agent_scope: Optional[List[str]] = None
    created_at: str
    expires_at: Optional[str] = None
    last_rotated: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int
    is_expired: bool
    is_expiring_soon: bool

    class Config:
        from_attributes = True


class CredentialDecryptedResponse(BaseModel):
    """Response model including decrypted credential (logged access)."""
    id: str
    name: str
    service_type: str
    credential_type: str
    credential_value: str  # Decrypted value
    agent_scope: Optional[List[str]] = None
    expires_at: Optional[str] = None


class AccessLogEntry(BaseModel):
    """Single access log entry."""
    id: str
    credential_id: str
    credential_name: Optional[str] = None
    service_type: Optional[str] = None
    agent_id: str
    action: str
    timestamp: str
    success: bool
    reason: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Response model for audit log queries."""
    count: int
    logs: List[AccessLogEntry]
    skip: int
    limit: int


class CredentialHealthSummary(BaseModel):
    """Health summary for dashboard display."""
    total_credentials: int
    expiring_soon: int
    expired: int
    needs_rotation: int
    max_access_count: int
    avg_access_count: float


class VaultOperationResponse(BaseModel):
    """Standard response for vault operations."""
    success: bool
    message: str
    credential_id: Optional[str] = None
    credential: Optional[CredentialResponse] = None


class VaultListResponse(BaseModel):
    """Response for listing credentials."""
    count: int
    credentials: List[CredentialResponse]


class ServiceTypeSummary(BaseModel):
    """Summary of credentials by service type."""
    service_type: str
    count: int
    expiring_soon: int
    expired: int
