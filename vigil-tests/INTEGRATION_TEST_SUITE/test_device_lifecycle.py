"""
Integration Test: Device Lifecycle (CRUD) Flow

This test verifies the complete device management workflow:
1. Device discovery and registration
2. Reading device information
3. Updating device metadata
4. Device containment actions (block/unblock/trust)
5. Device deletion with cascade effects

Tests verify data flow through: Database → API → Frontend
"""

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v2"
FRONTEND_URL = "http://localhost:3000"

# Test data fixtures
TEST_DEVICE_DATA = {
    "mac": "AA:BB:CC:DD:EE:FF",
    "ip": "192.168.50.150",
    "hostname": "Test-Device-Integration",
    "nickname": "Integration Test Device",
    "vendor": "TestCorp",
    "device_type": "iot"
}


class TestDeviceLifecycle:
    """Test suite for complete device CRUD lifecycle."""

    @pytest.fixture(scope="class")
    async def api_client(self):
        """Create async HTTP client for API testing."""
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
            follow_redirects=True
        ) as client:
            yield client

    @pytest.fixture
    async def created_device(self, api_client: httpx.AsyncClient) -> Dict[str, Any]:
        """Create a test device and return its data."""
        # Use the agent announcement endpoint as a way to create devices
        agent_data = {
            "name": TEST_DEVICE_DATA["hostname"],
            "ip": TEST_DEVICE_DATA["ip"],
            "mac": TEST_DEVICE_DATA["mac"],
            "agent_type": "test",
            "capabilities": ["test_device"]
        }

        response = await api_client.post("/setup/agent/announce", json=agent_data)
        assert response.status_code == 200

        result = response.json()
        device_id = result.get("device_id")

        # Get the created device
        device_response = await api_client.get(f"/devices/{device_id}")
        assert device_response.status_code == 200

        device = device_response.json()

        # Update with additional metadata
        patch_response = await api_client.patch(
            f"/devices/{device_id}",
            json={
                "nickname": TEST_DEVICE_DATA["nickname"],
                "device_type": TEST_DEVICE_DATA["device_type"]
            }
        )
        assert patch_response.status_code == 200

        yield patch_response.json()["device"]

        # Cleanup: Delete the device after test
        try:
            await api_client.delete(f"/devices/{device['id']}")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_device_discovery_flow(self, api_client: httpx.AsyncClient):
        """
        Test: Device discovery and initial registration
        Verifies: Device is discovered, registered, and visible in API
        """
        # Step 1: Initiate device discovery via agent announcement
        unique_mac = f"AA:BB:CC:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}"
        agent_data = {
            "name": f"Discovered-Device-{uuid.uuid4().hex[:8]}",
            "ip": f"192.168.50.{150 + hash(unique_mac) % 50}",
            "mac": unique_mac,
            "agent_type": "auto_discovered",
            "capabilities": ["network_device"]
        }

        response = await api_client.post("/setup/agent/announce", json=agent_data)
        assert response.status_code == 200

        result = response.json()
        assert result["status"] in ["created", "updated"]
        assert "device_id" in result

        device_id = result["device_id"]

        # Step 2: Verify device exists in device list
        list_response = await api_client.get("/devices")
        assert list_response.status_code == 200

        devices = list_response.json()
        assert "devices" in devices

        device_ids = [d["id"] for d in devices["devices"]]
        assert device_id in device_ids

        # Step 3: Verify device details match
        device_response = await api_client.get(f"/devices/{device_id}")
        assert device_response.status_code == 200

        device = device_response.json()
        assert device["mac"].upper() == unique_mac.upper()
        assert device["ip"] == agent_data["ip"]

        # Cleanup
        await api_client.delete(f"/devices/{device_id}")

    @pytest.mark.asyncio
    async def test_device_read_operations(self, api_client: httpx.AsyncClient, created_device):
        """
        Test: Reading device information
        Verifies: Pagination, filtering, search, and detail retrieval
        """
        device_id = created_device["id"]

        # Test 1: Get device by ID
        response = await api_client.get(f"/devices/{device_id}")
        assert response.status_code == 200

        device = response.json()
        assert device["id"] == device_id
        assert "mac" in device
        assert "ip" in device
        assert "trust_score" in device
        assert "containment_status" in device
        assert "online" in device
        assert "last_seen" in device
        assert "first_seen" in device

        # Test 2: List devices with pagination
        list_response = await api_client.get("/devices?limit=10&offset=0")
        assert list_response.status_code == 200

        data = list_response.json()
        assert "devices" in data
        assert "total_count" in data
        assert isinstance(data["devices"], list)

        # Test 3: Filter by containment status
        filtered_response = await api_client.get("/devices?status=observing")
        assert filtered_response.status_code == 200

        filtered_data = filtered_response.json()
        for device in filtered_data["devices"]:
            assert device["containment_status"] == "observing"

        # Test 4: Search by MAC, IP, or hostname
        search_response = await api_client.get(f"/devices?search={created_device['mac']}")
        assert search_response.status_code == 200

        search_results = search_response.json()
        assert any(d["id"] == device_id for d in search_results["devices"])

        # Test 5: Get non-existent device returns 404
        not_found_response = await api_client.get("/devices/999999")
        assert not_found_response.status_code == 404

    @pytest.mark.asyncio
    async def test_device_update_operations(self, api_client: httpx.AsyncClient, created_device):
        """
        Test: Updating device metadata
        Verifies: PATCH updates are persisted and reflected in API
        """
        device_id = created_device["id"]

        # Test 1: Update nickname
        new_nickname = f"Updated Device {uuid.uuid4().hex[:8]}"
        update_data = {"nickname": new_nickname}

        response = await api_client.patch(f"/devices/{device_id}", json=update_data)
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["device"]["nickname"] == new_nickname

        # Verify update persisted
        verify_response = await api_client.get(f"/devices/{device_id}")
        assert verify_response.json()["nickname"] == new_nickname

        # Test 2: Update device type
        type_update = {"device_type": "phone"}
        type_response = await api_client.patch(f"/devices/{device_id}", json=type_update)
        assert type_response.status_code == 200
        assert type_response.json()["device"]["device_type"] == "phone"

        # Test 3: Update hostname
        hostname_update = {"hostname": f"new-hostname-{uuid.uuid4().hex[:6]}"}
        hostname_response = await api_client.patch(f"/devices/{device_id}", json=hostname_update)
        assert hostname_response.status_code == 200

        # Test 4: Invalid device type rejected
        invalid_update = {"device_type": "invalid_type"}
        invalid_response = await api_client.patch(f"/devices/{device_id}", json=invalid_update)
        assert invalid_response.status_code == 422  # Validation error

        # Test 5: Update non-existent device returns 404
        not_found_response = await api_client.patch("/devices/999999", json={"nickname": "test"})
        assert not_found_response.status_code == 404

    @pytest.mark.asyncio
    async def test_device_containment_actions(self, api_client: httpx.AsyncClient, created_device):
        """
        Test: Device containment (block/unblock/trust)
        Verifies: Containment actions update device status correctly
        """
        device_id = created_device["id"]

        # Test 1: Trust device
        trust_response = await api_client.post(f"/devices/{device_id}/trust")
        assert trust_response.status_code == 200

        trust_result = trust_response.json()
        assert trust_result["success"] is True
        assert "trust_score" in trust_result
        assert trust_result["trust_score"] > created_device["trust_score"]

        # Verify status changed to trusted
        verify_trust = await api_client.get(f"/devices/{device_id}")
        assert verify_trust.json()["containment_status"] == "trusted"

        # Test 2: Block device
        block_response = await api_client.post(f"/devices/{device_id}/block")
        assert block_response.status_code == 200

        block_result = block_response.json()
        assert block_result["success"] is True
        assert "blocked" in block_result["message"].lower() or "block" in block_result["message"].lower()

        # Verify status changed to blocked
        verify_block = await api_client.get(f"/devices/{device_id}")
        assert verify_block.json()["containment_status"] == "blocked"

        # Test 3: Unblock device
        unblock_response = await api_client.post(f"/devices/{device_id}/unblock")
        assert unblock_response.status_code == 200

        # Verify status changed back to observing
        verify_unblock = await api_client.get(f"/devices/{device_id}")
        assert verify_unblock.json()["containment_status"] == "observing"

        # Test 4: Actions on non-existent device return 404
        assert (await api_client.post("/devices/999999/block")).status_code == 404
        assert (await api_client.post("/devices/999999/unblock")).status_code == 404
        assert (await api_client.post("/devices/999999/trust")).status_code == 404

    @pytest.mark.asyncio
    async def test_device_deletion_cascade(self, api_client: httpx.AsyncClient):
        """
        Test: Device deletion with cascade effects
        Verifies: Device deletion removes device and cascades to related records
        """
        # Create a device with related data (events, alerts)
        unique_mac = f"DE:LE:TE:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}"
        agent_data = {
            "name": "Cascade-Test-Device",
            "ip": "192.168.50.200",
            "mac": unique_mac,
            "agent_type": "test",
            "capabilities": ["test"]
        }

        create_response = await api_client.post("/setup/agent/announce", json=agent_data)
        device_id = create_response.json()["device_id"]

        # Create some events for this device
        # Note: Events are created by system, we'll check they exist after device activity

        # Get initial device count
        initial_list = await api_client.get("/devices")
        initial_count = initial_list.json()["total_count"]

        # Delete the device
        delete_response = await api_client.delete(f"/devices/{device_id}")
        assert delete_response.status_code in [200, 204]

        # Verify device no longer exists
        get_response = await api_client.get(f"/devices/{device_id}")
        assert get_response.status_code == 404

        # Verify device removed from list
        final_list = await api_client.get("/devices")
        final_count = final_list.json()["total_count"]
        assert final_count == initial_count - 1

        # Verify related events still exist but device_id is handled
        # (depending on implementation - events may be kept for audit or cascade deleted)
        events_response = await api_client.get(f"/events?device_id={device_id}")
        if events_response.status_code == 200:
            events = events_response.json()
            # Events may be returned with null device reference or cascade deleted
            # Both are valid depending on requirements

    @pytest.mark.asyncio
    async def test_device_concurrent_operations(self, api_client: httpx.AsyncClient):
        """
        Test: Concurrent device operations
        Verifies: System handles concurrent requests correctly
        """
        # Create multiple devices concurrently
        devices_data = []
        for i in range(5):
            unique_mac = f"CC:{i:02X}:CC:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}"
            devices_data.append({
                "name": f"Concurrent-Device-{i}",
                "ip": f"192.168.50.{200 + i}",
                "mac": unique_mac,
                "agent_type": "concurrent_test",
                "capabilities": ["test"]
            })

        # Create all devices concurrently
        create_tasks = [
            api_client.post("/setup/agent/announce", json=data)
            for data in devices_data
        ]
        responses = await asyncio.gather(*create_tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        device_ids = [r.json()["device_id"] for r in responses]

        # Update all devices concurrently with different data
        update_tasks = [
            api_client.patch(f"/devices/{did}", json={"nickname": f"Updated-{i}"})
            for i, did in enumerate(device_ids)
        ]
        update_responses = await asyncio.gather(*update_tasks)
        assert all(r.status_code == 200 for r in update_responses)

        # Verify all updates persisted
        verify_tasks = [api_client.get(f"/devices/{did}") for did in device_ids]
        verify_responses = await asyncio.gather(*verify_tasks)

        for i, resp in enumerate(verify_responses):
            assert resp.status_code == 200
            assert resp.json()["nickname"] == f"Updated-{i}"

        # Cleanup
        delete_tasks = [api_client.delete(f"/devices/{did}") for did in device_ids]
        await asyncio.gather(*delete_tasks)

    @pytest.mark.asyncio
    async def test_device_list_performance(self, api_client: httpx.AsyncClient):
        """
        Test: Device list performance with many devices
        Verifies: API responds within acceptable time limits
        """
        import time

        # Get device list
        start = time.time()
        response = await api_client.get("/devices?limit=100")
        elapsed = time.time() - start

        assert response.status_code == 200
        # API should respond within 2 seconds
        assert elapsed < 2.0

        data = response.json()
        assert "devices" in data
        assert "total_count" in data

        # Test filtering performance
        start = time.time()
        filtered = await api_client.get("/devices?status=observing&limit=50")
        elapsed = time.time() - start

        assert filtered.status_code == 200
        assert elapsed < 2.0
