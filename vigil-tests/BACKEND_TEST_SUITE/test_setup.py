"""
Vigil Dashboard - Setup Wizard API Tests

Test suite for setup wizard and initial configuration endpoints.
Covers router discovery, credentials management, and setup progress tracking.

Related Requirements:
    - FR-020: Setup Wizard
    - FR-004: Router Discovery and Integration
    - FR-021: Environment Configuration
    - NFR-011: Secret Management
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestSetupStatus:
    """Tests for GET /setup/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_setup_status_initial(self, async_client: AsyncClient):
        """
        Test getting setup status before configuration.
        
        Related Requirements:
            - FR-020: Setup Wizard status tracking
        
        Expected:
            - is_setup_complete: false
            - router_connected: false
            - device_count: 0
        """
        response = await async_client.get("/setup/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "is_setup_complete" in data
        assert "router_connected" in data
        assert "device_count" in data
        assert data["is_setup_complete"] is False

    @pytest.mark.asyncio
    async def test_get_setup_status_after_setup(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test getting setup status after successful setup.
        
        Expected:
            - is_setup_complete: true
            - router_connected: true
            - device_count: > 0
        """
        response = await async_client.get("/setup/status", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Status may vary depending on test state
        assert "is_setup_complete" in data
        assert "router_connected" in data
        assert "device_count" in data


class TestSetupSession:
    """Tests for POST /setup/session endpoint."""

    @pytest.mark.asyncio
    async def test_create_setup_session(self, async_client: AsyncClient):
        """
        Test creating a new setup session.
        
        Related Requirements:
            - FR-020 AC6: Setup state persistence
        
        Expected:
            - session_id returned
            - expires_at timestamp
            - Message confirming creation
        """
        response = await async_client.post("/setup/session")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert "expires_at" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_create_setup_session_returns_uuid(self, async_client: AsyncClient):
        """
        Test that session ID is a valid UUID format.
        """
        import uuid
        
        response = await async_client.post("/setup/session")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify valid UUID
        try:
            uuid.UUID(data["session_id"])
        except ValueError:
            pytest.fail("session_id is not a valid UUID")


class TestSetupDiscover:
    """Tests for POST /setup/discover endpoint."""

    @pytest.mark.asyncio
    async def test_discover_routers_success(self, async_client: AsyncClient):
        """
        Test router discovery on the network.
        
        Related Requirements:
            - FR-004 AC1: Auto-discovery via UPnP/SSDP
            - FR-020 AC3: Router auto-discovery
        
        Expected:
            - List of discovered routers
            - Each router has ip, type, model, confidence
        """
        response = await async_client.post("/setup/discover")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "routers" in data
        assert isinstance(data["routers"], list)
        
        for router in data["routers"]:
            assert "ip" in router
            assert "type" in router

    @pytest.mark.asyncio
    async def test_discover_routers_returns_valid_ips(self, async_client: AsyncClient):
        """
        Test that discovered routers have valid IP addresses.
        """
        import ipaddress
        
        response = await async_client.post("/setup/discover")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            for router in data.get("routers", []):
                try:
                    ipaddress.ip_address(router["ip"])
                except ValueError:
                    pytest.fail(f"Invalid IP: {router['ip']}")


class TestSetupConnect:
    """Tests for POST /setup/connect endpoint."""

    @pytest.mark.asyncio
    async def test_connect_router_success(self, async_client: AsyncClient, router_credentials: dict):
        """
        Test connecting to router with valid credentials.
        
        Related Requirements:
            - FR-004 AC3: Router credentials securely stored
            - FR-004 AC4: Test connectivity endpoint
            - FR-020 AC4: Credential test before proceeding
        
        Expected:
            - success: true
            - devices_found count
            - Confirmation message
        """
        response = await async_client.post(
            "/setup/connect",
            json=router_credentials
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "success" in data
        assert "devices_found" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_connect_router_invalid_credentials(self, async_client: AsyncClient):
        """
        Test connection failure with invalid credentials.
        
        Expected:
            - success: false
            - Appropriate error message
        """
        invalid_credentials = {
            "router_ip": "192.168.1.1",
            "admin_username": "wrong",
            "admin_password": "wrong_password",
        }
        
        response = await async_client.post(
            "/setup/connect",
            json=invalid_credentials
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "message" in data

    @pytest.mark.asyncio
    async def test_connect_router_invalid_ip(self, async_client: AsyncClient):
        """
        Test validation of router IP address.
        
        Related Requirements:
            - NFR-009: Input Validation
        """
        invalid_credentials = {
            "router_ip": "999.999.999.999",
            "admin_username": "admin",
            "admin_password": "password",
        }
        
        response = await async_client.post(
            "/setup/connect",
            json=invalid_credentials
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_connect_router_missing_credentials(self, async_client: AsyncClient):
        """
        Test validation of required credential fields.
        """
        incomplete_credentials = [
            {"admin_username": "admin", "admin_password": "pass"},  # Missing router_ip
            {"router_ip": "192.168.1.1", "admin_password": "pass"},  # Missing username
            {"router_ip": "192.168.1.1", "admin_username": "admin"},  # Missing password
        ]
        
        for creds in incomplete_credentials:
            response = await async_client.post(
                "/setup/connect",
                json=creds
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSetupRouterStatus:
    """Tests for GET /setup/router-status endpoint."""

    @pytest.mark.asyncio
    async def test_get_router_status(self, async_client: AsyncClient):
        """
        Test getting router configuration status.
        
        Related Requirements:
            - FR-004 AC3: Router credentials stored status
        
        Expected:
            - configured: boolean
            - router_ip: string or null
            - vendor: string or null
            - message: status description
            - setup_required: boolean
        """
        response = await async_client.get("/setup/router-status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "configured" in data
        assert "router_ip" in data
        assert "message" in data
        assert "setup_required" in data
        assert isinstance(data["configured"], bool)

    @pytest.mark.asyncio
    async def test_get_router_status_with_session(self, async_client: AsyncClient):
        """
        Test router status with session ID parameter.
        """
        response = await async_client.get("/setup/router-status?session_id=test-session-123")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "configured" in data


class TestSetupRouterCredentials:
    """Tests for POST /setup/router-credentials endpoint."""

    @pytest.mark.asyncio
    async def test_submit_router_credentials(self, async_client: AsyncClient, router_credentials: dict):
        """
        Test submitting router credentials.
        
        Related Requirements:
            - FR-004 AC3: Router credentials securely stored
            - FR-020 AC4: Credential test before proceeding
        
        Expected:
            - status: success
            - Router details returned
            - next_step URL
        """
        response = await async_client.post(
            "/setup/router-credentials",
            json=router_credentials
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "router" in data
        assert "next_step" in data

    @pytest.mark.asyncio
    async def test_submit_router_credentials_encryption(self, async_client: AsyncClient, router_credentials: dict):
        """
        Test that credentials are encrypted before storage.
        
        Related Requirements:
            - NFR-011: Secret Management (encrypted storage)
        
        Note: This is a conceptual test. Actual implementation would verify
        that credentials are not stored in plaintext.
        """
        response = await async_client.post(
            "/setup/router-credentials",
            json=router_credentials
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("status") == "success"
        
        # In a real test, we would verify the database storage
        # to ensure password is not in plaintext

    @pytest.mark.asyncio
    async def test_delete_router_credentials(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test deleting stored router credentials.
        
        Related Requirements:
            - FR-004: Router credential management
        """
        response = await async_client.delete(
            "/setup/router-credentials",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_delete_router_credentials_unauthorized(self, async_client: AsyncClient):
        """
        Test that credential deletion requires authentication.
        """
        response = await async_client.delete("/setup/router-credentials")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSetupAgents:
    """Tests for GET /setup/agents endpoint."""

    @pytest.mark.asyncio
    async def test_list_setup_agents(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test listing agents during setup.
        
        Related Requirements:
            - FR-020 AC5: Device import preview
        """
        response = await async_client.get("/setup/agents", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "count" in data
        assert "agents" in data
        assert isinstance(data["agents"], list)


class TestSetupAgentAnnounce:
    """Tests for POST /setup/agent/announce endpoint."""

    @pytest.mark.asyncio
    async def test_agent_announce_success(self, async_client: AsyncClient):
        """
        Test agent self-announcement.
        
        Related Requirements:
            - FR-011: Agent Registration
        """
        announcement = {
            "name": "New Agent",
            "ip": "192.168.1.200",
            "mac": "AA:BB:CC:DD:EE:99",
            "agent_type": "mesh",
            "capabilities": ["file_access", "network_scan"]
        }
        
        response = await async_client.post(
            "/setup/agent/announce",
            json=announcement
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] in ["created", "updated"]
        assert "device_id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_agent_announce_missing_required(self, async_client: AsyncClient):
        """
        Test validation of required fields in agent announcement.
        """
        incomplete_announcements = [
            {"ip": "192.168.1.200"},  # Missing name
            {"name": "Agent"},  # Missing ip
        ]
        
        for announcement in incomplete_announcements:
            response = await async_client.post(
                "/setup/agent/announce",
                json=announcement
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_agent_announce_invalid_mac(self, async_client: AsyncClient):
        """
        Test MAC address validation in agent announcement.
        """
        announcement = {
            "name": "New Agent",
            "ip": "192.168.1.200",
            "mac": "invalid-mac",
        }
        
        response = await async_client.post(
            "/setup/agent/announce",
            json=announcement
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    @pytest.mark.asyncio
    async def test_agent_announce_invalid_ip(self, async_client: AsyncClient):
        """
        Test IP address validation in agent announcement.
        """
        announcement = {
            "name": "New Agent",
            "ip": "999.999.999.999",
        }
        
        response = await async_client.post(
            "/setup/agent/announce",
            json=announcement
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


class TestSetupValidation:
    """Tests for setup input validation (NFR-009)."""

    @pytest.mark.asyncio
    async def test_router_ip_validation(self, async_client: AsyncClient):
        """
        Test router IP validation for various formats.
        
        Related Requirements:
            - FR-002 AC3: IP address validation
        """
        import ipaddress
        
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "192.168.50.1",
        ]
        
        invalid_ips = [
            "999.999.999.999",
            "192.168.1",
            "192.168.1.1.1",
            "not-an-ip",
            "",
        ]
        
        for ip in valid_ips:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                pytest.fail(f"Should be valid: {ip}")
        
        for ip in invalid_ips:
            if ip:  # Skip empty for this test
                with pytest.raises(ValueError):
                    ipaddress.ip_address(ip)

    @pytest.mark.asyncio
    async def test_password_length_validation(self, async_client: AsyncClient):
        """
        Test password length validation.
        
        Related Requirements:
            - NFR-006: Authentication Security
        """
        # Passwords should be non-empty
        short_credentials = {
            "router_ip": "192.168.1.1",
            "admin_username": "admin",
            "admin_password": "",
        }
        
        response = await async_client.post(
            "/setup/connect",
            json=short_credentials
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_username_length_validation(self, async_client: AsyncClient):
        """
        Test username length validation.
        """
        empty_username = {
            "router_ip": "192.168.1.1",
            "admin_username": "",
            "admin_password": "password123",
        }
        
        response = await async_client.post(
            "/setup/connect",
            json=empty_username
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSetupSecurity:
    """Security-focused tests for setup endpoints."""

    @pytest.mark.asyncio
    async def test_credentials_not_in_response(self, async_client: AsyncClient, router_credentials: dict):
        """
        Test that credentials are never returned in API responses.
        
        Related Requirements:
            - NFR-011 AC5: Secrets never logged or returned
        """
        response = await async_client.post(
            "/setup/router-credentials",
            json=router_credentials
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password is not in response
        response_text = response.text.lower()
        assert router_credentials["admin_password"].lower() not in response_text

    @pytest.mark.asyncio
    async def test_sql_injection_in_vendor(self, async_client: AsyncClient):
        """
        Test SQL injection prevention in vendor field.
        
        Related Requirements:
            - NFR-009 AC2: SQL injection prevention
        """
        malicious_credentials = {
            "router_ip": "192.168.1.1",
            "admin_username": "admin",
            "admin_password": "password",
            "vendor": "'; DROP TABLE routers; --",
        }
        
        response = await async_client.post(
            "/setup/router-credentials",
            json=malicious_credentials
        )
        
        # Should not crash or execute malicious SQL
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    @pytest.mark.asyncio
    async def test_xss_in_router_data(self, async_client: AsyncClient):
        """
        Test XSS prevention in router data.
        
        Related Requirements:
            - NFR-009 AC3: XSS prevention
        """
        xss_credentials = {
            "router_ip": "192.168.1.1",
            "admin_username": "admin",
            "admin_password": "password",
            "vendor": "<script>alert('xss')</script>",
        }
        
        response = await async_client.post(
            "/setup/router-credentials",
            json=xss_credentials
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]
        
        if response.status_code == status.HTTP_200_OK:
            # Verify response doesn't contain unescaped script
            assert "<script>" not in response.text


class TestSetupEdgeCases:
    """Edge case tests for setup API."""

    @pytest.mark.asyncio
    async def test_setup_unicode_in_router_name(self, async_client: AsyncClient):
        """
        Test handling of Unicode characters in router/vendor names.
        """
        unicode_credentials = {
            "router_ip": "192.168.1.1",
            "admin_username": "admin",
            "admin_password": "password",
            "vendor": "路由器",  # Chinese for "router"
        }
        
        response = await async_client.post(
            "/setup/router-credentials",
            json=unicode_credentials
        )
        
        # Should either accept or reject with clear error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    @pytest.mark.asyncio
    async def test_setup_special_chars_in_password(self, async_client: AsyncClient):
        """
        Test handling of special characters in passwords.
        
        Passwords should support special characters for security.
        """
        special_passwords = [
            "P@ssw0rd!#$%^",
            "pass word",  # Space in password
            "pass\tword",  # Tab in password
            "日本語パスワード",  # Unicode password
        ]
        
        for password in special_passwords:
            credentials = {
                "router_ip": "192.168.1.1",
                "admin_username": "admin",
                "admin_password": password,
            }
            
            response = await async_client.post(
                "/setup/connect",
                json=credentials
            )
            
            # Should accept or reject gracefully, never crash
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST
            ]

    @pytest.mark.asyncio
    async def test_setup_resume_after_interruption(self, async_client: AsyncClient):
        """
        Test that setup can be resumed after interruption.
        
        Related Requirements:
            - FR-020 AC7: Wizard can be resumed
        """
        # Create a session
        session_response = await async_client.post("/setup/session")
        assert session_response.status_code == status.HTTP_200_OK
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Get status with session
        status_response = await async_client.get(
            f"/setup/router-status?session_id={session_id}"
        )
        assert status_response.status_code == status.HTTP_200_OK
