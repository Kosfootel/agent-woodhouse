"""Vigil Credential Vault - Test Suite

Tests for encryption, service layer, and API endpoints.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from typing import Generator

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test master key before importing vault modules
os.environ["VIGIL_VAULT_MASTER_KEY"] = "test-master-key-" + "x" * 48

from app.vault.vault_encryption import (
    VaultEncryptionService,
    VaultEncryptionError,
    get_encryption_service,
    reset_encryption_service,
)
from app.models import CredentialVault, CredentialAccessLog, Base
from app.vault.vault_service import VaultService, reset_vault_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a test database session with in-memory SQLite."""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def encryption_service() -> Generator[VaultEncryptionService, None, None]:
    """Provide a fresh encryption service for each test."""
    reset_encryption_service()
    service = VaultEncryptionService(master_key="test-master-key-" + "x" * 48)
    yield service
    reset_encryption_service()


@pytest.fixture
def vault_service(encryption_service) -> Generator[VaultService, None, None]:
    """Provide a fresh vault service for each test."""
    reset_vault_service()
    service = VaultService(encryption_service=encryption_service)
    yield service
    reset_vault_service()


# ============================================================================
# Encryption Service Tests
# ============================================================================

class TestVaultEncryption:
    """Tests for the VaultEncryptionService."""
    
    def test_encryption_roundtrip(self, encryption_service):
        """Test that encryption and decryption work correctly."""
        plaintext = "my-secret-api-key-12345"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encryption_produces_different_ciphertexts(self, encryption_service):
        """Test that encrypting same plaintext twice produces different ciphertexts."""
        plaintext = "my-secret"
        
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        
        # Different nonces should produce different ciphertexts
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext
    
    def test_decrypt_invalid_data(self, encryption_service):
        """Test that decryption fails appropriately with invalid data."""
        invalid_data = b"invalid-data"
        
        with pytest.raises(VaultEncryptionError):
            encryption_service.decrypt(invalid_data)
    
    def test_decrypt_tampered_data(self, encryption_service):
        """Test that decryption detects tampering."""
        plaintext = "secret"
        encrypted = encryption_service.encrypt(plaintext)
        
        # Tamper with the ciphertext
        tampered = encrypted[:-1] + bytes([encrypted[-1] ^ 0xFF])
        
        with pytest.raises(VaultEncryptionError):
            encryption_service.decrypt(tampered)
    
    def test_generate_master_key(self):
        """Test master key generation."""
        key = VaultEncryptionService.generate_master_key()
        
        assert len(key) >= 32  # Should be reasonably long
        
        # Should be URL-safe base64
        assert "=" not in key  # No padding
        assert "/" not in key  # URL-safe
        assert "+" not in key  # URL-safe
    
    def test_missing_master_key(self):
        """Test that missing master key raises appropriate error."""
        # Clear any existing env var
        if "VIGIL_VAULT_MASTER_KEY" in os.environ:
            del os.environ["VIGIL_VAULT_MASTER_KEY"]
        
        reset_encryption_service()
        
        with pytest.raises(VaultEncryptionError) as exc_info:
            VaultEncryptionService()
        
        assert "VIGIL_VAULT_MASTER_KEY" in str(exc_info.value)


# ============================================================================
# Vault Service Tests
# ============================================================================

class TestVaultService:
    """Tests for the VaultService business logic."""
    
    def test_create_credential(self, vault_service, db_session):
        """Test credential creation."""
        credential, success = vault_service.create_credential(
            db=db_session,
            name="Test Hue Bridge",
            service_type="hue",
            credential_type="api_key",
            credential_value="hue-api-key-12345",
            agent_id="test-agent",
            agent_scope=["agent-1", "agent-2"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        assert success is True
        assert credential.name == "Test Hue Bridge"
        assert credential.service_type == "hue"
        assert credential.credential_type == "api_key"
        assert credential.agent_scope == "agent-1,agent-2"
        assert credential.access_count == 0
        
        # Verify it's in the database
        db_cred = db_session.query(CredentialVault).filter_by(id=credential.id).first()
        assert db_cred is not None
        assert db_cred.name == "Test Hue Bridge"
    
    def test_create_credential_no_scope(self, vault_service, db_session):
        """Test credential creation without agent scope (open access)."""
        credential, success = vault_service.create_credential(
            db=db_session,
            name="Public Credential",
            service_type="test",
            credential_type="api_key",
            credential_value="public-key",
            agent_id="test-agent",
            agent_scope=None,
        )
        
        assert success is True
        assert credential.agent_scope is None
    
    def test_get_credential_metadata(self, vault_service, db_session):
        """Test retrieving credential metadata."""
        # First create a credential
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Test",
            service_type="nest",
            credential_type="oauth_token",
            credential_value="nest-token-123",
            agent_id="creator-agent",
            agent_scope=["reader-agent"],
        )
        
        # Get metadata (no decryption)
        retrieved, decrypted = vault_service.get_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="reader-agent",
            decrypt=False,
        )
        
        assert retrieved.name == "Test"
        assert retrieved.service_type == "nest"
        assert decrypted is None  # Not decrypted
    
    def test_get_credential_with_decryption(self, vault_service, db_session):
        """Test retrieving credential with decryption."""
        original_value = "my-secret-token-xyz789"
        
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Test",
            service_type="ring",
            credential_type="api_key",
            credential_value=original_value,
            agent_id="creator-agent",
            agent_scope=["reader-agent"],
        )
        
        # Get with decryption
        retrieved, decrypted = vault_service.get_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="reader-agent",
            decrypt=True,
        )
        
        assert decrypted == original_value
        assert retrieved.access_count == 1
        assert retrieved.last_accessed is not None
    
    def test_get_credential_access_denied(self, vault_service, db_session):
        """Test that unauthorized agents cannot access credentials."""
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Secret",
            service_type="myhomeid",
            credential_type="api_key",
            credential_value="restricted-key",
            agent_id="owner-agent",
            agent_scope=["allowed-agent"],  # Only allowed-agent can access
        )
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            vault_service.get_credential(
                db=db_session,
                credential_id=credential.id,
                agent_id="unauthorized-agent",
                decrypt=True,
            )
        
        assert exc_info.value.status_code == 403
    
    def test_get_credential_not_found(self, vault_service, db_session):
        """Test handling of non-existent credential."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            vault_service.get_credential(
                db=db_session,
                credential_id="non-existent-id",
                agent_id="any-agent",
            )
        
        assert exc_info.value.status_code == 404
    
    def test_update_credential(self, vault_service, db_session):
        """Test updating credential metadata."""
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Original Name",
            service_type="hue",
            credential_type="api_key",
            credential_value="original-key",
            agent_id="creator-agent",
        )
        
        updated = vault_service.update_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="creator-agent",
            name="Updated Name",
        )
        
        assert updated.name == "Updated Name"
    
    def test_rotate_credential(self, vault_service, db_session):
        """Test credential rotation."""
        original_value = "old-key"
        new_value = "new-rotated-key-12345"
        
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Test",
            service_type="nest",
            credential_type="api_key",
            credential_value=original_value,
            agent_id="creator-agent",
            agent_scope=["rotator-agent"],
        )
        
        original_rotated = credential.last_rotated
        
        rotated = vault_service.rotate_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="rotator-agent",
            new_credential_value=new_value,
            reason="Quarterly rotation",
        )
        
        assert rotated.last_rotated > original_rotated
        
        # Verify new value
        _, decrypted = vault_service.get_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="rotator-agent",
            decrypt=True,
        )
        assert decrypted == new_value
    
    def test_delete_credential(self, vault_service, db_session):
        """Test credential deletion."""
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="To Delete",
            service_type="test",
            credential_type="api_key",
            credential_value="delete-me",
            agent_id="creator-agent",
        )
        
        success = vault_service.delete_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="creator-agent",
        )
        
        assert success is True
        
        # Verify it's gone
        deleted = db_session.query(CredentialVault).filter_by(id=credential.id).first()
        assert deleted is None
    
    def test_list_credentials_by_agent_scope(self, vault_service, db_session):
        """Test that credentials are filtered by agent scope."""
        # Create credential for specific agent
        vault_service.create_credential(
            db=db_session,
            name="Private Credential",
            service_type="hue",
            credential_type="api_key",
            credential_value="private",
            agent_id="creator",
            agent_scope=["agent-a"],
        )
        
        # Create open credential
        vault_service.create_credential(
            db=db_session,
            name="Public Credential",
            service_type="nest",
            credential_type="api_key",
            credential_value="public",
            agent_id="creator",
            agent_scope=None,
        )
        
        # List as agent-a should see both
        results = vault_service.list_credentials(
            db=db_session,
            agent_id="agent-a",
        )
        assert len(results) == 2
        
        # List as agent-b should only see open credential
        results = vault_service.list_credentials(
            db=db_session,
            agent_id="agent-b",
        )
        assert len(results) == 1
        assert results[0].name == "Public Credential"
    
    def test_get_audit_log(self, vault_service, db_session):
        """Test audit log retrieval."""
        # Create and access a credential
        credential, _ = vault_service.create_credential(
            db=db_session,
            name="Audit Test",
            service_type="hue",
            credential_type="api_key",
            credential_value="audit-key",
            agent_id="creator",
        )
        
        vault_service.get_credential(
            db=db_session,
            credential_id=credential.id,
            agent_id="reader",
            decrypt=True,
        )
        
        # Get audit log
        logs, total = vault_service.get_audit_log(
            db=db_session,
            credential_id=credential.id,
        )
        
        assert total >= 2  # Create + read
        
        # Check log entries
        actions = [log.action for log in logs]
        assert "write" in actions  # Create
        assert "decrypt" in actions  # Read with decrypt
    
    def test_health_summary(self, vault_service, db_session):
        """Test health summary generation."""
        # Create credentials in various states
        vault_service.create_credential(
            db=db_session,
            name="Healthy",
            service_type="hue",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        
        vault_service.create_credential(
            db=db_session,
            name="Expiring Soon",
            service_type="nest",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        
        vault_service.create_credential(
            db=db_session,
            name="Expired",
            service_type="ring",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        
        summary = vault_service.get_health_summary(db_session)
        
        assert summary["total_credentials"] == 3
        assert summary["expiring_soon"] == 1
        assert summary["expired"] == 1
    
    def test_is_expired(self, vault_service, db_session):
        """Test credential expiration checking."""
        # Not expired
        cred1, _ = vault_service.create_credential(
            db=db_session,
            name="Future",
            service_type="test",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert cred1.is_expired() is False
        
        # Expired
        cred2, _ = vault_service.create_credential(
            db=db_session,
            name="Past",
            service_type="test",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert cred2.is_expired() is True
        
        # No expiration
        cred3, _ = vault_service.create_credential(
            db=db_session,
            name="Never",
            service_type="test",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=None,
        )
        assert cred3.is_expired() is False
    
    def test_is_expiring_soon(self, vault_service, db_session):
        """Test credential expiring soon checking."""
        # Expiring in 3 days (should trigger)
        cred1, _ = vault_service.create_credential(
            db=db_session,
            name="Soon",
            service_type="test",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        assert cred1.is_expiring_soon() is True
        
        # Expiring in 30 days (should not trigger)
        cred2, _ = vault_service.create_credential(
            db=db_session,
            name="Later",
            service_type="test",
            credential_type="api_key",
            credential_value="key",
            agent_id="creator",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        assert cred2.is_expiring_soon() is False


# ============================================================================
# Integration Tests (would require FastAPI app)
# ============================================================================

@pytest.mark.skip(reason="Requires full FastAPI app setup - run as part of integration tests")
class TestVaultEndpoints:
    """Integration tests for API endpoints."""
    pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestVaultPerformance:
    """Basic performance sanity checks."""
    
    def test_encryption_performance(self, encryption_service):
        """Test that encryption/decryption is fast (< 50ms)."""
        import time
        
        plaintext = "x" * 1000  # 1KB credential
        
        start = time.perf_counter()
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.05  # Should be under 50ms
        assert decrypted == plaintext
    
    def test_multiple_credential_operations(self, vault_service, db_session):
        """Test that multiple operations complete quickly."""
        import time
        
        start = time.perf_counter()
        
        # Create 100 credentials
        for i in range(100):
            vault_service.create_credential(
                db=db_session,
                name=f"Credential {i}",
                service_type="test",
                credential_type="api_key",
                credential_value=f"key-{i}",
                agent_id="test",
            )
        
        elapsed = time.perf_counter() - start
        
        # Should complete in reasonable time (100 credentials in < 5 seconds)
        assert elapsed < 5.0
        
        # Memory check - count should be correct
        count = db_session.query(CredentialVault).count()
        assert count == 100


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
