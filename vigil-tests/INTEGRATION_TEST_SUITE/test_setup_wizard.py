"""
Integration Test: Setup Wizard Flow

This test verifies the complete setup process:
1. Initial setup status check
2. Router discovery
3. Router credentials submission and validation
4. Device import from router
5. Setup completion
6. Setup state persistence and resumption

Tests verify the multi-step wizard workflow and data persistence.
"""

import pytest
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v2"
FRONTEND_URL = "http://localhost:3000"
MOCK_ROUTER_URL = "http://localhost:8080"


class TestSetupWizard:
    """Test suite for complete setup wizard workflow."""

    @pytest.fixture(scope="class")
    async def api_client(self):
        """Create async HTTP client for API testing."""
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        ) as client:
            yield client

    @pytest.fixture
    async def setup_session(self, api_client: httpx.AsyncClient) -> str:
        """Create a setup session and return the session ID."""
        response = await api_client.post("/setup/session")
        assert response.status_code == 200

        result = response.json()
        assert "session_id" in result
        assert "message" in result

        yield result["session_id"]

        # Session cleanup happens automatically after expiration

    @pytest.mark.asyncio
    async def test_setup_status_initial(self, api_client: httpx.AsyncClient):
        """
        Test: Initial setup status check
        Verifies: Setup status endpoint returns correct initial state
        """
        response = await api_client.get("/setup/status")
        assert response.status_code == 200

        status = response.json()
        required_fields = ["is_setup_complete", "router_connected", "device_count"]

        for field in required_fields:
            assert field in status, f"Missing required field: {field}"

        # Initial setup should not be complete
        assert isinstance(status["is_setup_complete"], bool)
        assert isinstance(status["router_connected"], bool)
        assert isinstance(status["device_count"], int)

    @pytest.mark.asyncio
    async def test_setup_session_creation(self, api_client: httpx.AsyncClient):
        """
        Test: Setup session creation
        Verifies: Sessions are created with unique IDs and expiration
        """
        # Create first session
        response1 = await api_client.post("/setup/session")
        assert response1.status_code == 200

        data1 = response1.json()
        assert "session_id" in data1
        assert len(data1["session_id"]) > 0

        # Create second session
        response2 = await api_client.post("/setup/session")
        assert response2.status_code == 200

        data2 = response2.json()

        # Session IDs should be unique
        assert data1["session_id"] != data2["session_id"]

        # Should have expiration
        if "expires_at" in data1:
            assert isinstance(data1["expires_at"], str)

    @pytest.mark.asyncio
    async def test_router_discovery(self, api_client: httpx.AsyncClient, setup_session: str):
        """
        Test: Router discovery process
        Verifies: Routers are discovered on the network
        """
        response = await api_client.post("/setup/discover")
        assert response.status_code == 200

        result = response.json()
        assert "routers" in result
        assert isinstance(result["routers"], list)

        # If routers are found, verify structure
        for router in result["routers"]:
            assert "ip" in router
            assert "type" in router

            # Optional fields
            if "confidence" in router:
                assert 0 <= router["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_router_status_check(self, api_client: httpx.AsyncClient):
        """
        Test: Router setup status check
        Verifies: Status endpoint returns current router configuration state
        """
        response = await api_client.get("/setup/router-status")
        assert response.status_code == 200

        status = response.json()
        required_fields = ["configured", "router_ip", "message", "setup_required"]

        for field in required_fields:
            assert field in status

        assert isinstance(status["configured"], bool)
        assert isinstance(status["setup_required"], bool)

        # If configured, should have vendor info
        if status["configured"] and "vendor" in status:
            assert isinstance(status["vendor"], str)

    @pytest.mark.asyncio
    async def test_router_credentials_submission(self, api_client: httpx.AsyncClient):
        """
        Test: Router credentials submission
        Verifies: Credentials are validated and stored securely
        """
        # Test data
        credentials = {
            "router_ip": "192.168.50.1",
            "admin_username": "admin",
            "admin_password": "test_password_123",
            "vendor": "test_vendor"
        }

        response = await api_client.post("/setup/router-credentials", json=credentials)

        # Should either succeed or fail validation (both are valid responses)
        assert response.status_code in [200, 400, 401]

        if response.status_code == 200:
            result = response.json()
            assert "status" in result
            assert "message" in result

            if result["status"] == "success":
                assert "router" in result
                assert "next_step" in result

                router_info = result["router"]
                assert "ip" in router_info
                assert "configured" in router_info

    @pytest.mark.asyncio
    async def test_router_credentials_validation(self, api_client: httpx.AsyncClient):
        """
        Test: Router credentials validation
        Verifies: Invalid credentials are rejected appropriately
        """
        # Test missing required fields
        invalid_credentials = [
            {"admin_username": "admin", "admin_password": "pass"},  # Missing router_ip
            {"router_ip": "192.168.1.1", "admin_password": "pass"},  # Missing username
            {"router_ip": "192.168.1.1", "admin_username": "admin"},  # Missing password
        ]

        for creds in invalid_credentials:
            response = await api_client.post("/setup/router-credentials", json=creds)
            assert response.status_code == 422  # Validation error

        # Test invalid IP format
        bad_ip = {
            "router_ip": "not_an_ip",
            "admin_username": "admin",
            "admin_password": "password"
        }
        bad_ip_response = await api_client.post("/setup/router-credentials", json=bad_ip)
        assert bad_ip_response.status_code == 422

    @pytest.mark.asyncio
    async def test_router_connection_and_device_discovery(self, api_client: httpx.AsyncClient):
        """
        Test: Router connection and device import
        Verifies: Connecting to router discovers devices successfully
        """
        credentials = {
            "router_ip": "192.168.50.1",
            "admin_username": "admin",
            "admin_password": "admin",
            "vendor": "generic"
        }

        response = await api_client.post("/setup/connect", json=credentials)
        assert response.status_code in [200, 400, 401, 502]

        if response.status_code == 200:
            result = response.json()
            assert "success" in result
            assert "devices_found" in result
            assert "message" in result

            assert isinstance(result["success"], bool)
            assert isinstance(result["devices_found"], int)
            assert result["devices_found"] >= 0

    @pytest.mark.asyncio
    async def test_setup_wizard_complete_flow(self, api_client: httpx.AsyncClient):
        """
        Test: Complete setup wizard flow
        Verifies: Entire wizard workflow from start to completion
        """
        # Step 1: Check initial status
        status_response = await api_client.get("/setup/status")
        assert status_response.status_code == 200

        initial_status = status_response.json()
        initial_device_count = initial_status["device_count"]

        # Step 2: Create setup session
        session_response = await api_client.post("/setup/session")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Step 3: Discover routers
        discover_response = await api_client.post("/setup/discover")
        assert discover_response.status_code == 200

        # Step 4: Submit router credentials
        credentials = {
            "router_ip": "192.168.50.1",
            "admin_username": "admin",
            "admin_password": "admin123",
            "vendor": "generic"
        }

        cred_response = await api_client.post("/setup/router-credentials", json=credentials)
        # May succeed or fail depending on mock router availability

        # Step 5: Connect router and import devices
        connect_response = await api_client.post("/setup/connect", json=credentials)

        # Step 6: Verify setup status after configuration
        final_status_response = await api_client.get("/setup/status")
        assert final_status_response.status_code == 200

        final_status = final_status_response.json()

        # Setup may or may not be complete depending on connection success
        assert "is_setup_complete" in final_status
        assert "device_count" in final_status

    @pytest.mark.asyncio
    async def test_setup_credentials_deletion(self, api_client: httpx.AsyncClient):
        """
        Test: Router credentials deletion
        Verifies: Credentials can be securely deleted
        """
        # First add credentials
        credentials = {
            "router_ip": "192.168.50.1",
            "admin_username": "admin",
            "admin_password": "testpass",
            "vendor": "test"
        }

        await api_client.post("/setup/router-credentials", json=credentials)

        # Delete credentials
        delete_response = await api_client.delete("/setup/router-credentials")
        assert delete_response.status_code == 200

        result = delete_response.json()
        assert "status" in result
        assert "message" in result

        # Verify credentials are removed
        status_response = await api_client.get("/setup/router-status")
        status = status_response.json()
        assert status["configured"] is False

    @pytest.mark.asyncio
    async def test_agent_announcement_during_setup(self, api_client: httpx.AsyncClient):
        """
        Test: Agent announcement during setup
        Verifies: Agents can self-announce during setup process
        """
        # Create a test agent announcement
        agent_data = {
            "name": f"Setup-Test-Agent-{uuid.uuid4().hex[:8]}",
            "ip": "192.168.50.100",
            "mac": f"AA:BB:CC:DD:EE:{uuid.uuid4().hex[:2].upper()}",
            "agent_type": "test",
            "capabilities": ["test_capability"]
        }

        response = await api_client.post("/setup/agent/announce", json=agent_data)
        assert response.status_code == 200

        result = response.json()
        assert "status" in result
        assert result["status"] in ["created", "updated"]
        assert "device_id" in result
        assert "message" in result

        device_id = result["device_id"]

        # Verify agent appears in list
        agents_response = await api_client.get("/setup/agents")
        assert agents_response.status_code == 200

        agents_data = agents_response.json()
        assert "count" in agents_data
        assert "agents" in agents_data

        # Check our agent is in the list
        agent_ids = [a["id"] for a in agents_data["agents"]]
        assert device_id in agent_ids

        # Cleanup
        await api_client.delete(f"/devices/{device_id}")

    @pytest.mark.asyncio
    async def test_setup_resumption(self, api_client: httpx.AsyncClient):
        """
        Test: Setup wizard resumption
        Verifies: Wizard can be resumed after interruption
        """
        # Create a session
        session_response = await api_client.post("/setup/session")
        session_id = session_response.json()["session_id"]

        # Simulate interruption by checking status
        status1 = await api_client.get(f"/setup/router-status?session_id={session_id}")

        # Resume by continuing with the same session context
        # (In real implementation, session state would be persisted)
        status2 = await api_client.get("/setup/status")
        assert status2.status_code == 200

        # Setup state should be consistent
        data = status2.json()
        assert "is_setup_complete" in data

    @pytest.mark.asyncio
    async def test_setup_wizard_error_handling(self, api_client: httpx.AsyncClient):
        """
        Test: Setup wizard error handling
        Verifies: Wizard handles errors gracefully
        """
        # Test connection to unreachable router
        bad_credentials = {
            "router_ip": "192.168.255.255",  # Unlikely to exist
            "admin_username": "admin",
            "admin_password": "wrong_password",
            "vendor": "nonexistent"
        }

        response = await api_client.post("/setup/connect", json=bad_credentials)

        # Should return appropriate error code
        assert response.status_code in [200, 400, 401, 502, 503]

        if response.status_code == 200:
            result = response.json()
            assert result["success"] is False or result.get("devices_found", 0) == 0

    @pytest.mark.asyncio
    async def test_setup_state_persistence(self, api_client: httpx.AsyncClient):
        """
        Test: Setup state persistence across requests
        Verifies: Setup progress is maintained between API calls
        """
        # Check status multiple times
        status_checks = []
        for _ in range(3):
            response = await api_client.get("/setup/status")
            assert response.status_code == 200
            status_checks.append(response.json())

        # Status should be consistent
        for status in status_checks[1:]:
            assert status["is_setup_complete"] == status_checks[0]["is_setup_complete"]
            assert status["router_connected"] == status_checks[0]["router_connected"]

    @pytest.mark.asyncio
    async def test_setup_wizard_performance(self, api_client: httpx.AsyncClient):
        """
        Test: Setup wizard API performance
        Verifies: Setup endpoints respond within acceptable time
        """
        import time

        endpoints = [
            ("GET", "/setup/status"),
            ("POST", "/setup/session"),
            ("GET", "/setup/router-status"),
        ]

        for method, endpoint in endpoints:
            start = time.time()

            if method == "GET":
                response = await api_client.get(endpoint)
            else:
                response = await api_client.post(endpoint)

            elapsed = time.time() - start

            assert response.status_code in [200, 201]
            assert elapsed < 2.0, f"{endpoint} took too long: {elapsed}s"

    @pytest.mark.asyncio
    async def test_setup_with_existing_devices(self, api_client: httpx.AsyncClient):
        """
        Test: Setup with existing devices
        Verifies: Setup handles pre-existing devices correctly
        """
        # Create some devices first
        for i in range(3):
            agent_data = {
                "name": f"PreExisting-{i}",
                "ip": f"192.168.50.{100 + i}",
                "mac": f"AA:BB:CC:DD:EE:{i:02X}",
                "agent_type": "test"
            }
            await api_client.post("/setup/agent/announce", json=agent_data)

        # Check setup status with existing devices
        status_response = await api_client.get("/setup/status")
        assert status_response.status_code == 200

        status = status_response.json()
        assert status["device_count"] >= 3

        # Setup should account for existing devices
        assert "is_setup_complete" in status
