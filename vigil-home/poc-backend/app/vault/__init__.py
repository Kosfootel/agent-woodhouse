"""Vigil Credential Vault - Secure credential storage for home automation."""

from app.vault.vault_encryption import (
    VaultEncryptionService,
    VaultEncryptionError,
    get_encryption_service,
)
from app.vault.vault_service import (
    VaultService,
    get_vault_service,
)
from app.vault.vault_endpoints import (
    vault_router,
    include_vault_routes,
)
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

__all__ = [
    # Encryption
    VaultEncryptionService,
    VaultEncryptionError,
    get_encryption_service,
    # Service
    VaultService,
    get_vault_service,
    # Pydantic schemas
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
    # Endpoints
    vault_router,
    include_vault_routes,
]
