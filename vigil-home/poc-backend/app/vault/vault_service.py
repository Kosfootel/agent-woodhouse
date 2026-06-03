"""Vigil Credential Vault - Service Layer

Business logic for credential vault operations including:
- CRUD operations with encryption
- Access logging
- Scope enforcement
- Expiration tracking
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, Request

from app.vault.vault_encryption import VaultEncryptionService, VaultEncryptionError
from app.models import CredentialVault, CredentialAccessLog

logger = logging.getLogger("vigil.vault.service")


class VaultService:
    """Service layer for credential vault operations."""

    def __init__(self, encryption_service: Optional[VaultEncryptionService] = None):
        """Initialize the vault service.
        
        Args:
            encryption_service: Optional pre-configured encryption service.
        """
        self._encryption = encryption_service or VaultEncryptionService()

    def _log_access(
        self,
        db: Session,
        credential_id: str,
        agent_id: str,
        action: str,
        success: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log a credential access attempt."""
        log_entry = CredentialAccessLog(
            id=str(uuid.uuid4()),
            credential_id=credential_id,
            agent_id=agent_id,
            action=action,
            timestamp=datetime.now(timezone.utc),
            success=success,
            reason=reason,
            ip_address=ip_address,
        )
        db.add(log_entry)
        db.commit()

    def _check_agent_scope(
        self,
        credential: CredentialVault,
        agent_id: str,
        require_exact: bool = False,
    ) -> bool:
        """Check if an agent is authorized to access a credential.
        
        Args:
            credential: The credential to check.
            agent_id: The agent requesting access.
            require_exact: If True, requires exact match. If False, allows wildcard '*'.
        
        Returns:
            True if agent has access, False otherwise.
        """
        if not credential.agent_scope:
            # No scope restriction = accessible to all
            return True
        
        allowed_agents = credential._parse_agent_scope()
        if not allowed_agents:
            return True
        
        if require_exact:
            return agent_id in allowed_agents
        
        # Check for wildcard or explicit match
        return "*" in allowed_agents or agent_id in allowed_agents

    def create_credential(
        self,
        db: Session,
        name: str,
        service_type: str,
        credential_type: str,
        credential_value: str,
        agent_id: str,
        agent_scope: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[CredentialVault, bool]:
        """Create and store a new encrypted credential.
        
        Args:
            db: Database session.
            name: Human-readable label.
            service_type: Service type (hue, nest, etc.).
            credential_type: Type of credential (api_key, oauth_token, etc.).
            credential_value: The credential to encrypt.
            agent_id: Agent creating the credential.
            agent_scope: List of agent IDs allowed to access.
            expires_at: Optional expiration timestamp.
            ip_address: Source IP for logging.
        
        Returns:
            Tuple of (created_credential, success).
        
        Raises:
            HTTPException: If encryption fails.
        """
        try:
            # Encrypt the credential
            encrypted_data = self._encryption.encrypt(credential_value)
            
            # Create the credential record
            credential = CredentialVault(
                id=str(uuid.uuid4()),
                name=name,
                service_type=service_type,
                credential_type=credential_type,
                encrypted_data=encrypted_data,
                agent_scope=",".join(agent_scope) if agent_scope else None,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                last_rotated=datetime.now(timezone.utc) if credential_value else None,
                access_count=0,
            )
            
            db.add(credential)
            db.commit()
            db.refresh(credential)
            
            # Log the creation
            self._log_access(
                db, credential.id, agent_id, "write", True,
                reason="Credential created", ip_address=ip_address
            )
            
            logger.info(f"Created credential {credential.id} for service {service_type}")
            return credential, True
            
        except VaultEncryptionError as e:
            logger.error(f"Failed to encrypt credential: {e}")
            raise HTTPException(status_code=500, detail=f"Encryption failed: {e}")
        except Exception as e:
            logger.error(f"Failed to create credential: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create credential: {e}")

    def get_credential(
        self,
        db: Session,
        credential_id: str,
        agent_id: str,
        ip_address: Optional[str] = None,
        decrypt: bool = False,
    ) -> Tuple[CredentialVault, Optional[str]]:
        """Retrieve a credential by ID.
        
        Args:
            db: Database session.
            credential_id: The credential ID.
            agent_id: The agent requesting access.
            ip_address: Source IP for logging.
            decrypt: If True, decrypt and return the credential value.
        
        Returns:
            Tuple of (credential, decrypted_value_or_None).
        
        Raises:
            HTTPException: If credential not found or access denied.
        """
        credential = db.query(CredentialVault).filter(
            CredentialVault.id == credential_id
        ).first()
        
        if not credential:
            self._log_access(
                db, credential_id, agent_id, "read", False,
                reason="Credential not found", ip_address=ip_address
            )
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Check agent scope
        if not self._check_agent_scope(credential, agent_id):
            self._log_access(
                db, credential_id, agent_id, "read", False,
                reason="Agent not authorized for this credential", ip_address=ip_address
            )
            raise HTTPException(status_code=403, detail="Access denied: agent not authorized")
        
        decrypted_value = None
        
        if decrypt:
            try:
                decrypted_value = self._encryption.decrypt(credential.encrypted_data)
                
                # Update access tracking
                credential.last_accessed = datetime.now(timezone.utc)
                credential.access_count += 1
                db.commit()
                
                # Log successful decryption
                self._log_access(
                    db, credential_id, agent_id, "decrypt", True,
                    reason="Credential decrypted for retrieval", ip_address=ip_address
                )
                
            except VaultEncryptionError as e:
                self._log_access(
                    db, credential_id, agent_id, "decrypt", False,
                    reason=f"Decryption failed: {e}", ip_address=ip_address
                )
                raise HTTPException(status_code=500, detail="Failed to decrypt credential")
        else:
            # Log metadata access (no decryption)
            self._log_access(
                db, credential_id, agent_id, "read", True,
                reason="Metadata retrieval", ip_address=ip_address
            )
        
        return credential, decrypted_value

    def list_credentials(
        self,
        db: Session,
        agent_id: str,
        service_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[CredentialVault]:
        """List credentials accessible to an agent.
        
        Args:
            db: Database session.
            agent_id: The agent requesting the list.
            service_type: Optional filter by service type.
            skip: Pagination offset.
            limit: Pagination limit.
        
        Returns:
            List of credentials the agent can access.
        """
        query = db.query(CredentialVault)
        
        if service_type:
            query = query.filter(CredentialVault.service_type == service_type)
        
        # Filter by agent scope (credentials with no scope restriction or matching scope)
        # This is a simplified check; in production, you might want more complex logic
        query = query.filter(
            (CredentialVault.agent_scope.is_(None)) |
            (CredentialVault.agent_scope == "*") |
            (CredentialVault.agent_scope.contains(agent_id))
        )
        
        return query.order_by(CredentialVault.created_at.desc()).offset(skip).limit(limit).all()

    def update_credential(
        self,
        db: Session,
        credential_id: str,
        agent_id: str,
        name: Optional[str] = None,
        credential_value: Optional[str] = None,
        agent_scope: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        ip_address: Optional[str] = None,
    ) -> CredentialVault:
        """Update an existing credential.
        
        Args:
            db: Database session.
            credential_id: The credential ID.
            agent_id: The agent making the update.
            name: New name (optional).
            credential_value: New credential value (optional, triggers re-encryption).
            agent_scope: New agent scope (optional).
            expires_at: New expiration date (optional).
            ip_address: Source IP for logging.
        
        Returns:
            Updated credential.
        
        Raises:
            HTTPException: If credential not found or access denied.
        """
        credential = db.query(CredentialVault).filter(
            CredentialVault.id == credential_id
        ).first()
        
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Check agent scope for updates (require exact match or wildcard)
        if not self._check_agent_scope(credential, agent_id, require_exact=False):
            self._log_access(
                db, credential_id, agent_id, "write", False,
                reason="Agent not authorized to update", ip_address=ip_address
            )
            raise HTTPException(status_code=403, detail="Access denied: cannot modify credential")
        
        try:
            if name:
                credential.name = name
            
            if credential_value is not None:
                # Re-encrypt with new value
                credential.encrypted_data = self._encryption.encrypt(credential_value)
                credential.last_rotated = datetime.now(timezone.utc)
            
            if agent_scope is not None:
                credential.agent_scope = ",".join(agent_scope) if agent_scope else None
            
            if expires_at is not None:
                credential.expires_at = expires_at
            
            db.commit()
            db.refresh(credential)
            
            self._log_access(
                db, credential_id, agent_id, "write", True,
                reason="Credential updated", ip_address=ip_address
            )
            
            return credential
            
        except VaultEncryptionError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Encryption failed: {e}")

    def rotate_credential(
        self,
        db: Session,
        credential_id: str,
        agent_id: str,
        new_credential_value: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> CredentialVault:
        """Rotate a credential to a new value.
        
        Args:
            db: Database session.
            credential_id: The credential ID.
            agent_id: The agent performing rotation.
            new_credential_value: The new credential value.
            reason: Optional reason for rotation.
            ip_address: Source IP for logging.
        
        Returns:
            Updated credential.
        
        Raises:
            HTTPException: If credential not found or access denied.
        """
        credential = db.query(CredentialVault).filter(
            CredentialVault.id == credential_id
        ).first()
        
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Check agent scope
        if not self._check_agent_scope(credential, agent_id):
            self._log_access(
                db, credential_id, agent_id, "rotate", False,
                reason="Agent not authorized to rotate", ip_address=ip_address
            )
            raise HTTPException(status_code=403, detail="Access denied: cannot rotate credential")
        
        try:
            # Encrypt new value
            credential.encrypted_data = self._encryption.encrypt(new_credential_value)
            credential.last_rotated = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(credential)
            
            log_reason = f"Credential rotated: {reason}" if reason else "Credential rotated"
            self._log_access(
                db, credential_id, agent_id, "rotate", True,
                reason=log_reason, ip_address=ip_address
            )
            
            logger.info(f"Rotated credential {credential_id} by agent {agent_id}")
            return credential
            
        except VaultEncryptionError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Encryption failed: {e}")

    def delete_credential(
        self,
        db: Session,
        credential_id: str,
        agent_id: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Delete a credential.
        
        Args:
            db: Database session.
            credential_id: The credential ID.
            agent_id: The agent requesting deletion.
            ip_address: Source IP for logging.
        
        Returns:
            True if deleted successfully.
        
        Raises:
            HTTPException: If credential not found or access denied.
        """
        credential = db.query(CredentialVault).filter(
            CredentialVault.id == credential_id
        ).first()
        
        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        # Check agent scope
        if not self._check_agent_scope(credential, agent_id):
            self._log_access(
                db, credential_id, agent_id, "delete", False,
                reason="Agent not authorized to delete", ip_address=ip_address
            )
            raise HTTPException(status_code=403, detail="Access denied: cannot delete credential")
        
        # Log before deletion
        self._log_access(
            db, credential_id, agent_id, "delete", True,
            reason="Credential revoked/deleted", ip_address=ip_address
        )
        
        db.delete(credential)
        db.commit()
        
        logger.info(f"Deleted credential {credential_id} by agent {agent_id}")
        return True

    def get_audit_log(
        self,
        db: Session,
        credential_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[CredentialAccessLog], int]:
        """Query the credential access audit log.
        
        Args:
            db: Database session.
            credential_id: Optional filter by credential.
            agent_id: Optional filter by agent.
            action: Optional filter by action type.
            skip: Pagination offset.
            limit: Pagination limit.
        
        Returns:
            Tuple of (log_entries, total_count).
        """
        query = db.query(CredentialAccessLog)
        
        if credential_id:
            query = query.filter(CredentialAccessLog.credential_id == credential_id)
        if agent_id:
            query = query.filter(CredentialAccessLog.agent_id == agent_id)
        if action:
            query = query.filter(CredentialAccessLog.action == action)
        
        total = query.count()
        logs = query.order_by(CredentialAccessLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        return logs, total

    def get_health_summary(self, db: Session) -> dict:
        """Get credential vault health summary.
        
        Args:
            db: Database session.
        
        Returns:
            Dictionary with health metrics.
        """
        total = db.query(CredentialVault).count()
        
        if total == 0:
            return {
                "total_credentials": 0,
                "expiring_soon": 0,
                "expired": 0,
                "needs_rotation": 0,
                "max_access_count": 0,
                "avg_access_count": 0.0,
            }
        
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        soon = now + timedelta(days=7)
        
        expiring_soon = db.query(CredentialVault).filter(
            CredentialVault.expires_at.isnot(None),
            CredentialVault.expires_at <= soon,
            CredentialVault.expires_at > now
        ).count()
        
        expired = db.query(CredentialVault).filter(
            CredentialVault.expires_at.isnot(None),
            CredentialVault.expires_at <= now
        ).count()
        
        # Credentials not rotated in 90 days
        ninety_days_ago = now - timedelta(days=90)
        needs_rotation = db.query(CredentialVault).filter(
            (CredentialVault.last_rotated.is_(None)) |
            (CredentialVault.last_rotated <= ninety_days_ago)
        ).count()
        
        stats = db.query(
            func.max(CredentialVault.access_count).label("max_access"),
            func.avg(CredentialVault.access_count).label("avg_access")
        ).first()
        
        return {
            "total_credentials": total,
            "expiring_soon": expiring_soon,
            "expired": expired,
            "needs_rotation": needs_rotation,
            "max_access_count": stats.max_access or 0,
            "avg_access_count": round(stats.avg_access or 0.0, 2),
        }


# Singleton instance
_vault_service: Optional[VaultService] = None


def get_vault_service() -> VaultService:
    """Get or create the singleton vault service."""
    global _vault_service
    if _vault_service is None:
        _vault_service = VaultService()
    return _vault_service


def reset_vault_service() -> None:
    """Reset the singleton (for testing)."""
    global _vault_service
    _vault_service = None
