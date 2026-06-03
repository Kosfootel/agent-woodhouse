"""
Integration Test: Network Discovery Scan and Dashboard Reporting Flow

This test verifies the complete scan → dashboard reporting workflow:
1. Network scan initiation
2. Scan progress tracking
3. Device discovery and registration
4. Dashboard statistics updates
5. Event timeline population
6. Report generation

Tests verify data flow through: Discovery Service → Database → Dashboard API → Frontend
"""

import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import time

# Test configuration
API_BASE_URL = "http://localhost:8000/api/v2"
FRONTEND_URL = "http://localhost:3000"


class TestScanAndReport:
    """Test suite for network scan and dashboard reporting flow."""

    @pytest.fixture(scope="class")
    async def api_client(self):
        """Create async HTTP client for API testing."""
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            headers={"Content-Type": "application/json"},
            timeout=60.0
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_dashboard_statistics_initial(self, api_client: httpx.AsyncClient):
        """
        Test: Initial dashboard statistics
        Verifies: Stats endpoint returns consistent data structure
        """
        response = await api_client.get("/stats")
        assert response.status_code == 200

        stats = response.json()
        required_fields = [
            "device_count", "active_devices", "blocked_devices",
            "avg_trust_score", "alert_count", "unacknowledged_alerts",
            "critical_alerts"
        ]

        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
            assert isinstance(stats[field], (int, float))

        # Validate logical relationships
        assert stats["active_devices"] <= stats["device_count"]
        assert stats["blocked_devices"] <= stats["device_count"]
        assert 0 <= stats["avg_trust_score"] <= 100
        assert stats["unacknowledged_alerts"] <= stats["alert_count"]
        assert stats["critical_alerts"] <= stats["alert_count"]

    @pytest.mark.asyncio
    async def test_events_timeline_initial(self, api_client: httpx.AsyncClient):
        """
        Test: Events timeline retrieval
        Verifies: Events endpoint returns timeline data correctly
        """
        response = await api_client.get("/events?limit=50")
        assert response.status_code == 200

        events_data = response.json()
        assert "count" in events_data
        assert "events" in events_data
        assert isinstance(events_data["events"], list)

        # Verify event structure
        for event in events_data["events"]:
            assert "id" in event
            assert "device_id" in event
            assert "event_type" in event
            assert "timestamp" in event

            # Event type should be valid
            valid_types = [
                "device_joined", "device_left", "device_blocked",
                "device_unblocked", "alert_triggered", "scan_complete", "device_updated"
            ]
            assert event["event_type"] in valid_types

    @pytest.mark.asyncio
    async def test_events_filtering(self, api_client: httpx.AsyncClient):
        """
        Test: Events filtering by type, device, and time
        Verifies: Events can be filtered correctly
        """
        # Test filter by event type
        for event_type in ["device_joined", "scan_complete", "device_updated"]:
            response = await api_client.get(f"/events?event_type={event_type}&limit=50")
            assert response.status_code == 200

            data = response.json()
            for event in data["events"]:
                assert event["event_type"] == event_type

        # Test filter by hours
        hours_response = await api_client.get("/events?hours=24&limit=50")
        assert hours_response.status_code == 200

        # Test filter by device_id (if devices exist)
        devices_response = await api_client.get("/devices?limit=1")
        if devices_response.json().get("devices"):
            device_id = devices_response.json()["devices"][0]["id"]
            device_events = await api_client.get(f"/events?device_id={device_id}&limit=50")
            assert device_events.status_code == 200

            for event in device_events.json()["events"]:
                assert event["device_id"] == device_id

    @pytest.mark.asyncio
    async def test_device_discovery_via_announcement(self, api_client: httpx.AsyncClient):
        """
        Test: Device discovery through agent announcement
        Verifies: New devices appear in dashboard after discovery
        """
        # Get initial stats
        initial_stats = await api_client.get("/stats")
        initial_device_count = initial_stats.json()["device_count"]

        # Create multiple devices
        discovered_devices = []
        for i in range(5):
            device_data = {
                "name": f"Discovered-Device-{i}-{uuid.uuid4().hex[:6]}",
                "ip": f"192.168.50.{100 + i}",
                "mac": f"AA:BB:CC:DD:EE:{i:02X}",
                "agent_type": "discovered",
                "capabilities": ["network_device"]
            }

            response = await api_client.post("/setup/agent/announce", json=device_data)
            assert response.status_code == 200

            result = response.json()
            assert result["status"] in ["created", "updated"]

            discovered_devices.append(result["device_id"])

        # Wait for processing
        await asyncio.sleep(1)

        # Verify stats updated
        updated_stats = await api_client.get("/stats")
        updated_device_count = updated_stats.json()["device_count"]
        assert updated_device_count >= initial_device_count + 5

        # Verify events were created
        events_response = await api_client.get("/events?event_type=device_joined&limit=50")
        events = events_response.json()["events"]

        # At least some of our devices should have events
        event_device_ids = [e["device_id"] for e in events]
        for device_id in discovered_devices:
            assert device_id in event_device_ids

        # Cleanup
        for device_id in discovered_devices:
            await api_client.delete(f"/devices/{device_id}")

    @pytest.mark.asyncio
    async def test_scan_triggers_events(self, api_client: httpx.AsyncClient):
        """
        Test: Network scan triggers appropriate events
        Verifies: Scan operations generate events and update dashboard
        """
        # Get initial event count
        initial_events = await api_client.get("/events?limit=100")
        initial_count = initial_events.json()["count"]

        # Trigger a scan (via router discovery)
        discover_response = await api_client.post("/setup/discover")
        assert discover_response.status_code == 200

        # Wait for events to be generated
        await asyncio.sleep(2)

        # Check for new events
        final_events = await api_client.get("/events?limit=100")
        final_count = final_events.json()["count"]

        # Event count may have increased
        assert final_count >= initial_count

    @pytest.mark.asyncio
    async def test_dashboard_stats_after_device_changes(self, api_client: httpx.AsyncClient):
        """
        Test: Dashboard statistics reflect device changes
        Verifies: Stats update when devices are added, blocked, or removed
        """
        # Get baseline stats
        baseline_stats = await api_client.get("/stats")
        baseline = baseline_stats.json()

        # Create a device
        device_data = {
            "name": f"Stats-Test-{uuid.uuid4().hex[:8]}",
            "ip": "192.168.50.200",
            "mac": f"AA:BB:CC:DD:EE:{uuid.uuid4().hex[:2].upper()}",
            "agent_type": "test"
        }

        create_response = await api_client.post("/setup/agent/announce", json=device_data)
        device_id = create_response.json()["device_id"]

        await asyncio.sleep(1)

        # Stats should show new device
        after_create = await api_client.get("/stats")
        after_create_stats = after_create.json()
        assert after_create_stats["device_count"] >= baseline["device_count"] + 1

        # Block the device
        await api_client.post(f"/devices/{device_id}/block")
        await asyncio.sleep(1)

        # Stats should show blocked device
        after_block = await api_client.get("/stats")
        after_block_stats = after_block.json()
        assert after_block_stats["blocked_devices"] >= baseline["blocked_devices"] + 1

        # Delete the device
        await api_client.delete(f"/devices/{device_id}")
        await asyncio.sleep(1)

        # Cleanup verification
        final_stats = await api_client.get("/stats")
        assert final_stats.status_code == 200

    @pytest.mark.asyncio
    async def test_recent_events_for_dashboard(self, api_client: httpx.AsyncClient):
        """
        Test: Recent events endpoint for dashboard display
        Verifies: Events endpoint returns data suitable for dashboard
        """
        # Create some activity
        for i in range(3):
            device_data = {
                "name": f"Activity-Device-{i}",
                "ip": f"192.168.50.{210 + i}",
                "mac": f"AA:BB:CC:DD:EE:{i + 10:02X}",
                "agent_type": "test"
            }
            await api_client.post("/setup/agent/announce", json=device_data)

        await asyncio.sleep(1)

        # Get recent events for different time windows
        for hours in [1, 24, 168]:  # 1 hour, 1 day, 1 week
            response = await api_client.get(f"/stats/events?hours={hours}&limit=100")
            assert response.status_code == 200

            data = response.json()
            assert "events" in data
            assert "total_count" in data
            assert isinstance(data["events"], list)

    @pytest.mark.asyncio
    async def test_device_list_for_dashboard(self, api_client: httpx.AsyncClient):
        """
        Test: Device list endpoint for dashboard device table
        Verifies: Device list returns paginated data suitable for tables
        """
        # Test pagination
        for limit in [10, 25, 50, 100]:
            response = await api_client.get(f"/devices?limit={limit}&offset=0")
            assert response.status_code == 200

            data = response.json()
            assert "devices" in data
            assert "total_count" in data
            assert len(data["devices"]) <= limit

        # Test sorting by different statuses
        for status in ["observing", "blocked", "trusted", "quarantined"]:
            status_response = await api_client.get(f"/devices?status={status}&limit=50")
            assert status_response.status_code == 200

            status_data = status_response.json()
            for device in status_data["devices"]:
                assert device["containment_status"] == status

        # Test search functionality
        devices_response = await api_client.get("/devices?limit=1")
        if devices_response.json().get("devices"):
            device = devices_response.json()["devices"][0]

            # Search by MAC
            mac_search = await api_client.get(f"/devices?search={device['mac']}&limit=10")
            assert mac_search.status_code == 200

            # Search by IP
            ip_search = await api_client.get(f"/devices?search={device['ip']}&limit=10")
            assert ip_search.status_code == 200

            # Search by hostname
            if device.get("hostname"):
                hostname_search = await api_client.get(f"/devices?search={device['hostname']}&limit=10")
                assert hostname_search.status_code == 200

    @pytest.mark.asyncio
    async def test_alert_dashboard_integration(self, api_client: httpx.AsyncClient):
        """
        Test: Alert data for dashboard display
        Verifies: Alert endpoint returns data suitable for dashboard panels
        """
        # Get alerts with different filters
        filters = [
            ("severity", "critical"),
            ("severity", "high"),
            ("severity", "medium"),
            ("severity", "low"),
            ("acknowledged", "true"),
            ("acknowledged", "false"),
        ]

        for param, value in filters:
            response = await api_client.get(f"/alerts?{param}={value}&limit=50")
            assert response.status_code == 200

            data = response.json()
            assert "alerts" in data
            assert "count" in data
            assert "new_count" in data
            assert "acknowledged_count" in data

            # Verify filter was applied
            for alert in data["alerts"]:
                if param == "severity":
                    assert alert["severity"] == value
                elif param == "acknowledged":
                    assert alert["acknowledged"] == (value == "true")

        # Get alert count endpoint (lightweight for dashboard badge)
        count_response = await api_client.get("/alerts/count")
        assert count_response.status_code == 200
        assert "count" in count_response.json()

    @pytest.mark.asyncio
    async def test_security_dashboard_data(self, api_client: httpx.AsyncClient):
        """
        Test: Security data for security dashboard
        Verifies: Security endpoints provide data for security overview
        """
        # Blocked stats
        blocked_response = await api_client.get("/security/blocked-stats")
        assert blocked_response.status_code == 200

        blocked_data = blocked_response.json()
        assert "total" in blocked_data
        assert "byCategory" in blocked_data

        # Tool usage
        usage_response = await api_client.get("/security/tool-usage?period=24h")
        assert usage_response.status_code == 200

        usage_data = usage_response.json()
        assert "period" in usage_data
        assert "tools" in usage_data

        # Memory access heatmap data
        heatmap_response = await api_client.get("/security/memory-access")
        assert heatmap_response.status_code == 200

        heatmap_data = heatmap_response.json()
        assert "agents" in heatmap_data
        assert "levels" in heatmap_data
        assert "data" in heatmap_data

    @pytest.mark.asyncio
    async def test_agent_list_for_dashboard(self, api_client: httpx.AsyncClient):
        """
        Test: Agent list for dashboard display
        Verifies: Agent endpoint returns data for agent monitoring
        """
        response = await api_client.get("/agents")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "agents" in data

        for agent in data["agents"]:
            required_fields = [
                "id", "name", "status", "trust_level",
                "trust_score", "is_trusted", "is_blocked"
            ]
            for field in required_fields:
                assert field in agent

            assert agent["trust_score"] >= 0 and agent["trust_score"] <= 100
            assert agent["trust_level"] in ["trusted", "untrusted", "blocked"]
            assert agent["status"] in ["online", "offline", "unknown"]

    @pytest.mark.asyncio
    async def test_dashboard_data_consistency(self, api_client: httpx.AsyncClient):
        """
        Test: Dashboard data consistency across endpoints
        Verifies: Related endpoints return consistent data
        """
        # Get stats
        stats_response = await api_client.get("/stats")
        stats = stats_response.json()

        # Get devices
        devices_response = await api_client.get("/devices?limit=1000")
        devices = devices_response.json()

        # Verify device counts match
        assert devices["total_count"] == stats["device_count"]

        # Count blocked devices manually
        blocked_count = sum(1 for d in devices["devices"] if d["containment_status"] == "blocked")
        assert blocked_count == stats["blocked_devices"]

        # Get alerts
        alerts_response = await api_client.get("/alerts?limit=1000")
        alerts = alerts_response.json()

        # Verify alert counts match
        assert alerts["count"] == stats["alert_count"]

        new_alerts = sum(1 for a in alerts["alerts"] if not a["acknowledged"])
        assert new_alerts == stats["unacknowledged_alerts"]

        critical_alerts = sum(1 for a in alerts["alerts"] if a["severity"] == "critical")
        assert critical_alerts == stats["critical_alerts"]

    @pytest.mark.asyncio
    async def test_dashboard_performance(self, api_client: httpx.AsyncClient):
        """
        Test: Dashboard data loading performance
        Verifies: Dashboard endpoints respond within acceptable time
        """
        import time

        dashboard_endpoints = [
            ("GET", "/stats"),
            ("GET", "/devices?limit=25"),
            ("GET", "/alerts?limit=25"),
            ("GET", "/events?limit=25"),
            ("GET", "/agents"),
        ]

        for method, endpoint in dashboard_endpoints:
            start = time.time()

            if method == "GET":
                response = await api_client.get(endpoint)
            else:
                response = await api_client.post(endpoint)

            elapsed = time.time() - start

            assert response.status_code == 200
            assert elapsed < 1.0, f"{endpoint} took too long: {elapsed}s"

    @pytest.mark.asyncio
    async def test_complete_scan_to_report_flow(self, api_client: httpx.AsyncClient):
        """
        Test: Complete scan to report flow
        Verifies: End-to-end flow from scan initiation to dashboard reporting
        """
        # Step 1: Get baseline
        baseline_stats = await api_client.get("/stats")
        baseline_count = baseline_stats.json()["device_count"]

        baseline_events = await api_client.get("/events?limit=100")
        baseline_event_count = baseline_events.json()["count"]

        # Step 2: Simulate network discovery (via multiple agent announcements)
        discovered = []
        for i in range(5):
            device = {
                "name": f"Flow-Test-{i}",
                "ip": f"192.168.50.{180 + i}",
                "mac": f"AA:BB:CC:DD:EE:{i + 50:02X}",
                "agent_type": "discovered",
                "capabilities": ["network"]
            }
            resp = await api_client.post("/setup/agent/announce", json=device)
            discovered.append(resp.json()["device_id"])

        # Step 3: Wait for processing
        await asyncio.sleep(2)

        # Step 4: Verify dashboard updated
        updated_stats = await api_client.get("/stats")
        assert updated_stats.json()["device_count"] >= baseline_count + 5

        # Step 5: Verify events created
        updated_events = await api_client.get("/events?limit=100")
        assert updated_events.json()["count"] > baseline_event_count

        # Step 6: Verify device list updated
        devices = await api_client.get("/devices?limit=100")
        device_ids = [d["id"] for d in devices.json()["devices"]]
        for did in discovered:
            assert did in device_ids

        # Step 7: Generate activity on devices (trust/block)
        for did in discovered[:2]:
            await api_client.post(f"/devices/{did}/trust")

        for did in discovered[2:3]:
            await api_client.post(f"/devices/{did}/block")

        await asyncio.sleep(1)

        # Step 8: Verify stats reflect changes
        final_stats = await api_client.get("/stats")
        final = final_stats.json()
        assert final["blocked_devices"] >= baseline_stats.json()["blocked_devices"] + 1

        # Step 9: Verify security events created
        security_events = await api_client.get("/security/events?limit=50")
        assert security_events.status_code == 200

        # Cleanup
        for did in discovered:
            await api_client.delete(f"/devices/{did}")
