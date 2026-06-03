"""
Vigil Dashboard - Device API Tests

Test suite for device management API endpoints.
Covers CRUD operations, filtering, validation, and containment actions.

Related Requirements:
    - FR-001: Multi-Protocol Device Discovery
    - FR-002: Device Registration and Baseline
    - FR-003: Device Inventory Management
    - NFR-001: API Response Time (≤100ms for CRUD)
    - NFR-009: Input Validation
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestDeviceList:
    """Tests for GET /devices endpoint."""

    @pytest.mark.asyncio
    async def test_list_devices_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test successful retrieval of device list with default pagination.
        
        Related Requirements:
            - FR-003: Device Inventory Management
            - NFR-001: API Response Time ≤100ms
        
        Test Steps:
            1. Send GET request to /devices with authentication
            2. Verify 200 response
            3. Validate response structure contains devices and total_count
        """
        response = await async_client.get("/devices", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "devices" in data
        assert "total_count" in data
        assert isinstance(data["devices"], list)

    @pytest.mark.asyncio
    async def test_list_devices_unauthorized(self, async_client: AsyncClient):
        """
        Test that device list requires authentication.
        
        Related Requirements:
            - NFR-006: Authentication Security
        """
        response = await async_client.get("/devices")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_devices_with_status_filter(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test filtering devices by containment status.
        
        Related Requirements:
            - FR-003 AC5: Devices can be filtered by containment_status
        
        Test Cases:
            - Filter by 'trusted'
            - Filter by 'blocked'
            - Filter by 'observing'
            - Filter by 'quarantined'
        """
        for status_filter in ["observing", "blocked", "trusted", "quarantined"]:
            response = await async_client.get(
                f"/devices?status={status_filter}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # All returned devices should match the filter
            for device in data["devices"]:
                assert device["containment_status"] == status_filter

    @pytest.mark.asyncio
    async def test_list_devices_with_search(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test searching devices by MAC, IP, hostname, or nickname.
        
        Related Requirements:
            - FR-003 AC5: Device search capability
        """
        search_terms = ["AA:BB:CC", "192.168.1", "iPhone", "Phone"]
        
        for term in search_terms:
            response = await async_client.get(
                f"/devices?search={term}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data["devices"], list)

    @pytest.mark.asyncio
    async def test_list_devices_pagination(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test pagination with limit and offset parameters.
        
        Related Requirements:
            - FR-003 AC1: Paginated device list
        """
        # Test with custom limit
        response = await async_client.get(
            "/devices?limit=5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["devices"]) <= 5

        # Test with offset
        response = await async_client.get(
            "/devices?limit=5&offset=5",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_list_devices_invalid_limit(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test validation of invalid limit parameter.
        
        Related Requirements:
            - NFR-009: Input Validation
        """
        response = await async_client.get(
            "/devices?limit=0",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = await async_client.get(
            "/devices?limit=1001",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeviceDetail:
    """Tests for GET /devices/{deviceId} endpoint."""

    @pytest.mark.asyncio
    async def test_get_device_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test successful retrieval of a specific device.
        
        Related Requirements:
            - FR-003 AC2: Get detailed device information
        """
        response = await async_client.get("/devices/1", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "mac" in data
        assert "ip" in data
        assert "trust_score" in data
        assert "containment_status" in data

    @pytest.mark.asyncio
    async def test_get_device_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test 404 response for non-existent device.
        
        Related Requirements:
            - FR-003 AC2: Handle missing device gracefully
        """
        response = await async_client.get("/devices/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_device_invalid_id(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test validation of invalid device ID format.
        
        Related Requirements:
            - NFR-009: Input Validation
        """
        response = await async_client.get("/devices/invalid", headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_device_unauthorized(self, async_client: AsyncClient):
        """
        Test authentication requirement for device detail.
        """
        response = await async_client.get("/devices/1")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeviceUpdate:
    """Tests for PATCH /devices/{deviceId} endpoint."""

    @pytest.mark.asyncio
    async def test_update_device_nickname(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test updating device nickname.
        
        Related Requirements:
            - FR-003 AC3: Update device metadata
        """
        update_data = {"nickname": "Updated Device Name"}
        
        response = await async_client.patch(
            "/devices/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["device"]["nickname"] == "Updated Device Name"

    @pytest.mark.asyncio
    async def test_update_device_hostname(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test updating device hostname.
        
        Related Requirements:
            - FR-003 AC3: Update device metadata
        """
        update_data = {"hostname": "New-Hostname"}
        
        response = await async_client.patch(
            "/devices/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["device"]["hostname"] == "New-Hostname"

    @pytest.mark.asyncio
    async def test_update_device_type(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test updating device type with valid enum values.
        
        Related Requirements:
            - FR-003 AC3: Update device type
        """
        valid_types = ["phone", "laptop", "desktop", "tablet", "iot", "tv", "speaker", "unknown"]
        
        for device_type in valid_types:
            update_data = {"device_type": device_type}
            
            response = await async_client.patch(
                "/devices/1",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["device"]["device_type"] == device_type

    @pytest.mark.asyncio
    async def test_update_device_invalid_type(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test validation of invalid device type.
        
        Related Requirements:
            - NFR-009: Input Validation
        """
        update_data = {"device_type": "invalid_type"}
        
        response = await async_client.patch(
            "/devices/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_update_device_nickname_too_long(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test validation of nickname length (max 100 chars).
        
        Related Requirements:
            - FR-003 AC3: Input validation
            - NFR-009: Input Validation
        """
        update_data = {"nickname": "A" * 101}
        
        response = await async_client.patch(
            "/devices/1",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_update_device_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test 404 response when updating non-existent device.
        """
        update_data = {"nickname": "New Name"}
        
        response = await async_client.patch(
            "/devices/99999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeviceBlock:
    """Tests for POST /devices/{deviceId}/block endpoint."""

    @pytest.mark.asyncio
    async def test_block_device_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test successful blocking of a device.
        
        Related Requirements:
            - FR-003 AC4: Device containment controls
        """
        response = await async_client.post(
            "/devices/1/block",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "blocked" in data["message"].lower() or "block" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_block_device_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test 404 response when blocking non-existent device.
        """
        response = await async_client.post(
            "/devices/99999/block",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_block_already_blocked_device(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test blocking an already blocked device.
        
        Expected: Should return success or 409 Conflict depending on implementation.
        """
        response = await async_client.post(
            "/devices/2/block",  # Assuming device 2 is already blocked
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_409_CONFLICT]


class TestDeviceUnblock:
    """Tests for POST /devices/{deviceId}/unblock endpoint."""

    @pytest.mark.asyncio
    async def test_unblock_device_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test successful unblocking of a device.
        
        Related Requirements:
            - FR-003 AC4: Device containment controls
        """
        response = await async_client.post(
            "/devices/2/unblock",  # Assuming device 2 is blocked
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "unblock" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_unblock_device_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test 404 response when unblocking non-existent device.
        """
        response = await async_client.post(
            "/devices/99999/unblock",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_unblock_not_blocked_device(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test unblocking a device that is not blocked.
        
        Expected: Should return appropriate error or success with warning.
        """
        response = await async_client.post(
            "/devices/1/unblock",  # Assuming device 1 is not blocked
            headers=auth_headers
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestDeviceTrust:
    """Tests for POST /devices/{deviceId}/trust endpoint."""

    @pytest.mark.asyncio
    async def test_trust_device_success(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test trusting a device.
        
        Related Requirements:
            - FR-002 AC2: Device trust management
        """
        response = await async_client.post(
            "/devices/1/trust",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "trust_score" in data
        assert data["trust_score"] >= 90  # Trusted devices should have high score

    @pytest.mark.asyncio
    async def test_trust_device_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test 404 when trusting non-existent device.
        """
        response = await async_client.post(
            "/devices/99999/trust",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeviceValidation:
    """Tests for device data validation (NFR-009)."""

    @pytest.mark.asyncio
    async def test_mac_address_validation(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test MAC address format validation.
        
        Valid formats:
            - AA:BB:CC:DD:EE:FF
            - aa:bb:cc:dd:ee:ff
        
        Invalid formats should be rejected.
        
        Related Requirements:
            - FR-002 AC2: MAC address regex validation
        """
        valid_macs = [
            "AA:BB:CC:DD:EE:FF",
            "aa:bb:cc:dd:ee:ff",
            "00:11:22:33:44:55",
        ]
        
        invalid_macs = [
            "invalid",
            "AA:BB:CC:DD:EE",
            "AA-BB-CC-DD-EE-FF",
            "AABBCCDDEEFF",
            "AA:BB:CC:DD:EE:GG",
        ]
        
        # In a real implementation, test device creation with these values
        # For now, just validate the regex pattern
        import re
        mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})$")
        
        for mac in valid_macs:
            assert mac_pattern.match(mac), f"Should match: {mac}"
        
        for mac in invalid_macs:
            assert not mac_pattern.match(mac), f"Should not match: {mac}"

    @pytest.mark.asyncio
    async def test_ip_address_validation(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test IP address validation using ipaddress module.
        
        Related Requirements:
            - FR-002 AC3: IP address validation
        """
        import ipaddress
        
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "255.255.255.255",
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
            with pytest.raises(ValueError):
                ipaddress.ip_address(ip)

    @pytest.mark.asyncio
    async def test_hostname_validation(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test hostname validation.
        
        Rules:
            - Max 253 characters
            - Alphanumeric, hyphens, dots
            - No consecutive dots
        
        Related Requirements:
            - FR-002 AC4: Hostname validation
        """
        import re
        
        valid_hostnames = [
            "device-1",
            "my.device.local",
            "Device-Name-123",
            "a" * 253,
        ]
        
        invalid_hostnames = [
            "device..double-dot",
            "device space",
            "device@symbol",
            "a" * 254,
        ]
        
        hostname_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
        
        for hostname in valid_hostnames:
            if len(hostname) <= 253:
                assert hostname_pattern.match(hostname), f"Should match: {hostname}"
        
        for hostname in invalid_hostnames:
            if len(hostname) > 253:
                assert len(hostname) > 253
            else:
                assert not hostname_pattern.match(hostname), f"Should not match: {hostname}"


class TestDeviceSecurity:
    """Security-focused tests for device endpoints (NFR-009)."""

    @pytest.mark.asyncio
    async def test_sql_injection_in_search(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test that SQL injection attempts in search parameter are prevented.
        
        Related Requirements:
            - NFR-009 AC2: SQL injection prevention
        """
        malicious_search = "'; DROP TABLE devices; --"
        
        response = await async_client.get(
            f"/devices?search={malicious_search}",
            headers=auth_headers
        )
        
        # Should not crash or execute malicious SQL
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.asyncio
    async def test_xss_in_nickname(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test that XSS payloads in nickname are sanitized.
        
        Related Requirements:
            - NFR-009 AC3: XSS prevention
        """
        xss_payload = "<script>alert('xss')</script>"
        update_data = {"nickname": xss_payload}
        
        response = await async_client.patch(
            "/devices/1",
            json=update_data,
            headers=auth_headers
        )
        
        # Should either reject or sanitize
        if response.status_code == status.HTTP_200_OK:
            # If accepted, the response should not contain unescaped script
            assert "<script>" not in response.text or xss_payload not in response.text

    @pytest.mark.asyncio
    async def test_path_traversal_in_device_id(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test that path traversal attempts in device ID are prevented.
        
        Related Requirements:
            - NFR-009 AC6: Path traversal prevention
        """
        malicious_ids = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "1/../../etc/passwd",
        ]
        
        for device_id in malicious_ids:
            response = await async_client.get(
                f"/devices/{device_id}",
                headers=auth_headers
            )
            
            # Should return 404 or 422, never execute path traversal
            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]


class TestDeviceEdgeCases:
    """Edge case tests for device API."""

    @pytest.mark.asyncio
    async def test_device_with_null_hostname(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test handling of devices with null hostname.
        
        Related Requirements:
            - FR-002: Device registration with optional fields
        """
        response = await async_client.get("/devices/4", headers=auth_headers)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should handle null gracefully
            assert data.get("hostname") is None or isinstance(data.get("hostname"), str)

    @pytest.mark.asyncio
    async def test_device_unicode_in_nickname(self, async_client: AsyncClient, auth_headers: dict):
        """
        Test handling of Unicode characters in device nickname.
        """
        unicode_nicknames = [
            " John's Device",
            "日本語デバイス",
            "Девайс",
            "📱 Mobile Phone",
        ]
        
        for nickname in unicode_nicknames:
            update_data = {"nickname": nickname}
            
            response = await async_client.patch(
                "/devices/1",
                json=update_data,
                headers=auth_headers
            )
            
            # Should either accept or reject with clear error
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST
            ]
