"""
Test suite for router integration module.
Run with: pytest test_router_integration.py -v
"""

import asyncio
import json
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest

from router_integration import (
    RouterDevice,
    RouterInfo,
    RouterDiscovery,
    SecureCredentialManager,
    ASUSWRTClient,
    DeviceSyncService,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


@pytest.fixture
def sample_router_device():
    """Create a sample router device for testing."""
    return RouterDevice(
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.100",
        name="TestDevice",
        device_type="laptop",
        is_connected=True,
        metadata={"rssi": -45, "vendor": "TestVendor"}
    )


@pytest.fixture
def sample_router_info():
    """Create a sample router info for testing."""
    return RouterInfo(
        ip_address="192.168.1.1",
        mac_address="04:D4:C4:00:00:01",
        brand="ASUSTek",
        model="GT6",
        discovery_method="gateway"
    )


# =============================================================================
# RouterDevice Tests
# =============================================================================

class TestRouterDevice:
    """Tests for the RouterDevice dataclass."""
    
    def test_device_creation(self, sample_router_device):
        """Test basic device creation."""
        assert sample_router_device.mac_address == "AA:BB:CC:DD:EE:FF"
        assert sample_router_device.ip_address == "192.168.1.100"
        assert sample_router_device.name == "TestDevice"
        assert sample_router_device.device_type == "laptop"
        assert sample_router_device.is_connected is True
        assert isinstance(sample_router_device.first_seen, datetime)
    
    def test_device_defaults(self):
        """Test device creation with default values."""
        device = RouterDevice(
            mac_address="11:22:33:44:55:66",
            ip_address="192.168.1.50"
        )
        assert device.name == ""
        assert device.device_type == "unknown"
        assert device.is_connected is True
        assert device.metadata == {}


# =============================================================================
# SecureCredentialManager Tests
# =============================================================================

class TestSecureCredentialManager:
    """Tests for the SecureCredentialManager class."""
    
    def test_init_creates_database(self, temp_db_path):
        """Test that initialization creates the database tables."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            
            assert "credentials" in tables
            assert "encryption_key" in tables
    
    def test_key_generation(self, temp_db_path):
        """Test that a key is generated on first run."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute("SELECT key_value FROM encryption_key")
            row = cursor.fetchone()
            assert row is not None
            assert len(row[0]) > 0
    
    def test_store_and_retrieve_credentials(self, temp_db_path):
        """Test storing and retrieving encrypted credentials."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        manager.store_credentials(
            router_id="router_192_168_1_1",
            username="admin",
            password="secret123",
            api_key="apikey456"
        )
        
        creds = manager.get_credentials("router_192_168_1_1")
        
        assert creds is not None
        assert creds["username"] == "admin"
        assert creds["password"] == "secret123"
        assert creds["api_key"] == "apikey456"
    
    def test_retrieve_nonexistent_credentials(self, temp_db_path):
        """Test retrieving credentials that don't exist."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        creds = manager.get_credentials("nonexistent_router")
        assert creds is None
    
    def test_delete_credentials(self, temp_db_path):
        """Test deleting credentials."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        manager.store_credentials("router_to_delete", "user", "pass")
        assert manager.get_credentials("router_to_delete") is not None
        
        manager.delete_credentials("router_to_delete")
        assert manager.get_credentials("router_to_delete") is None
    
    def test_encryption_is_secure(self, temp_db_path):
        """Test that credentials are actually encrypted in database."""
        manager = SecureCredentialManager(db_path=temp_db_path)
        
        manager.store_credentials("router_test", "admin", "password123")
        
        # Verify raw database contents are not plaintext
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute(
                "SELECT username_encrypted FROM credentials WHERE router_id = ?",
                ("router_test",)
            )
            row = cursor.fetchone()
            encrypted = row[0]
            
            assert b"admin" not in encrypted
            assert b"password123" not in encrypted


# =============================================================================
# RouterDiscovery Tests
# =============================================================================

class TestRouterDiscovery:
    """Tests for the RouterDiscovery class."""
    
    @pytest.fixture
    def discovery(self):
        return RouterDiscovery()
    
    def test_oui_vendor_lookup_asus(self, discovery):
        """Test ASUS OUI lookup."""
        vendor = discovery.identify_vendor_from_oui("04:D4:C4:00:00:00")
        assert vendor == "ASUSTek"
    
    def test_oui_vendor_lookup_netgear(self, discovery):
        """Test Netgear OUI lookup."""
        vendor = discovery.identify_vendor_from_oui("28:C6:8E:00:00:00")
        assert vendor == "Netgear"
    
    def test_oui_vendor_lookup_unknown(self, discovery):
        """Test unknown OUI returns None."""
        vendor = discovery.identify_vendor_from_oui("00:00:00:00:00:00")
        assert vendor is None
    
    @patch("subprocess.run")
    def test_get_default_gateway(self, mock_run, discovery):
        """Test default gateway detection."""
        mock_run.return_value = Mock(
            stdout="default via 192.168.1.1 dev eth0\n",
            returncode=0
        )
        
        gateway = discovery.get_default_gateway()
        assert gateway == "192.168.1.1"
    
    @patch("subprocess.run")
    def test_get_mac_from_ip(self, mock_run, discovery):
        """Test MAC address lookup from IP."""
        mock_run.return_value = Mock(
            stdout="192.168.1.1 dev eth0 lladdr 04:d4:c4:00:00:01 REACHABLE\n",
            returncode=0
        )
        
        mac = discovery.get_mac_from_ip("192.168.1.1")
        assert mac == "04:D4:C4:00:00:01"
    
    @pytest.mark.asyncio
    async def test_discover_returns_list(self, discovery):
        """Test discover method returns a list."""
        with patch.object(discovery, 'get_default_gateway', return_value="192.168.1.1"):
            with patch.object(discovery, 'get_mac_from_ip', return_value="04:D4:C4:00:00:01"):
                routers = await discovery.discover()
                assert isinstance(routers, list)
                assert len(routers) >= 1


# =============================================================================
# DeviceSyncService Tests
# =============================================================================

class TestDeviceSyncService:
    """Tests for the DeviceSyncService class."""
    
    @pytest.fixture
    def sync_service(self, temp_db_path):
        return DeviceSyncService(db_path=temp_db_path)
    
    @pytest.fixture
    def sample_devices(self):
        return [
            RouterDevice(
                mac_address="AA:BB:CC:DD:EE:01",
                ip_address="192.168.1.101",
                name="Phone",
                device_type="mobile",
                is_connected=True
            ),
            RouterDevice(
                mac_address="AA:BB:CC:DD:EE:02",
                ip_address="192.168.1.102",
                name="Laptop",
                device_type="computer",
                is_connected=True
            ),
        ]
    
    def test_init_creates_tables(self, sync_service, temp_db_path):
        """Test that database tables are created on init."""
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
            assert "devices" in tables
    
    def test_sync_devices(self, sync_service, sample_devices):
        """Test syncing devices to database."""
        sync_service.sync_devices(sample_devices, "192.168.1.1")
        
        devices = sync_service.get_devices()
        assert len(devices) == 2
        
        mac_addresses = {d["mac_address"] for d in devices}
        assert "AA:BB:CC:DD:EE:01" in mac_addresses
        assert "AA:BB:CC:DD:EE:02" in mac_addresses
    
    def test_sync_updates_existing_devices(self, sync_service, sample_devices):
        """Test that syncing updates existing devices."""
        # First sync
        sync_service.sync_devices(sample_devices, "192.168.1.1")
        
        # Modify a device
        sample_devices[0].name = "UpdatedPhone"
        sample_devices[0].is_connected = False
        
        # Sync again
        sync_service.sync_devices(sample_devices, "192.168.1.1")
        
        devices = sync_service.get_devices()
        phone = next(d for d in devices if d["mac_address"] == "AA:BB:CC:DD:EE:01")
        assert phone["name"] == "UpdatedPhone"
    
    def test_get_devices_connected_only(self, sync_service, sample_devices):
        """Test filtering by connected status."""
        sample_devices[0].is_connected = False
        sync_service.sync_devices(sample_devices, "192.168.1.1")
        
        all_devices = sync_service.get_devices(connected_only=False)
        assert len(all_devices) == 2
        
        connected = sync_service.get_devices(connected_only=True)
        assert len(connected) == 1
        assert connected[0]["mac_address"] == "AA:BB:CC:DD:EE:02"
    
    def test_get_device_by_mac(self, sync_service, sample_devices):
        """Test getting a specific device by MAC."""
        sync_service.sync_devices(sample_devices, "192.168.1.1")
        
        device = sync_service.get_device_by_mac("AA:BB:CC:DD:EE:01")
        assert device is not None
        assert device["name"] == "Phone"
        
        not_found = sync_service.get_device_by_mac("00:00:00:00:00:00")
        assert not_found is None


# =============================================================================
# ASUSWRTClient Tests (Mock-based)
# =============================================================================

class TestASUSWRTClient:
    """Tests for the ASUSWRTClient class using mocks."""
    
    @pytest.fixture
    def credentials(self):
        return {"username": "admin", "password": "password123"}
    
    @pytest.fixture
    def client(self, credentials):
        return ASUSWRTClient("192.168.1.1", credentials)
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, client):
        """Test async context manager."""
        async with client:
            assert client.session is not None
        assert client.session is None
    
    def test_base_url_construction(self, client):
        """Test URL construction."""
        assert client._get_base_url() == "http://192.168.1.1"
    
    def test_https_base_url(self, credentials):
        """Test HTTPS URL when enabled."""
        client = ASUSWRTClient("192.168.1.1", credentials, use_https=True)
        assert client._get_base_url() == "https://192.168.1.1"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full flow."""
    
    @pytest.mark.asyncio
    async def test_full_discovery_and_sync_flow(self, temp_db_path):
        """Test the complete flow from discovery to sync."""
        # This is a simplified integration test
        discovery = RouterDiscovery()
        sync_service = DeviceSyncService(db_path=temp_db_path)
        cred_manager = SecureCredentialManager(db_path=f"{temp_db_path}.creds")
        
        # Mock discovery
        with patch.object(discovery, 'get_default_gateway', return_value="192.168.1.1"):
            with patch.object(discovery, 'get_mac_from_ip', return_value="04:D4:C4:00:00:01"):
                routers = await discovery.discover()
        
        assert len(routers) >= 1
        
        # Store credentials
        router_id = f"router_{routers[0].ip_address.replace('.', '_')}"
        cred_manager.store_credentials(router_id, "admin", "password")
        
        retrieved = cred_manager.get_credentials(router_id)
        assert retrieved is not None
        assert retrieved["username"] == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
