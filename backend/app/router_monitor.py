#!/usr/bin/env python3
"""
ASUS Router Device Monitor for Vigil - Updated with fallback

This module provides integration with ASUS GT6 (ZenWiFi Pro ET12) routers
to extract device information for network monitoring.

Router Model: ASUS GT6 (ZenWiFi Pro ET12)
Firmware: 3.0.0.4.388_24734

Authentication: ASUS routers use a session-based auth system with specific
token generation. This implementation uses direct HTTP requests with
the ASUS custom API endpoints.

Security Note: Credentials should be stored securely (see config_template.py)
and not committed to version control.
"""

import re
import json
import time
import logging
import hashlib
import subprocess
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urlencode, urlparse


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RouterDevice:
    """Represents a device connected to the router."""
    mac: str
    ip: str
    hostname: str
    connection_type: str  # 'wired', '2.4GHz', '5GHz', '6GHz'
    rssi: Optional[int] = None  # Signal strength for wireless
    last_seen: Optional[datetime] = None
    upload_speed: Optional[float] = None  # Mbps
    download_speed: Optional[float] = None  # Mbps
    is_online: bool = True
    device_type: Optional[str] = None  # Router's classification
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.last_seen:
            result['last_seen'] = self.last_seen.isoformat()
        return result


class RouterAuthError(Exception):
    """Raised when router authentication fails."""
    pass


class RouterConnectionError(Exception):
    """Raised when connection to router fails."""
    pass


class ASUSRouterClient:
    """
    Client for ASUS GT6 router HTTP API.
    
    The ASUS router uses a custom HTTP API with specific endpoints:
    - Login: /login.cgi with encoded credentials
    - Device list: /appGet.cgi with specific app IDs
    - Status: /ajax_status.asp and similar endpoints
    
    This implementation handles the ASUS-specific authentication
    and data extraction.
    """
    
    # ASUS Router API endpoints
    ENDPOINT_LOGIN = "/login.cgi"
    ENDPOINT_APPGET = "/appGet.cgi"
    ENDPOINT_STATUS = "/ajax_status.asp"
    
    # Common app IDs for device information
    APP_ID_CLIENT_LIST = "get_clientlist"
    APP_ID_NETWORKMAP = "get_networkmapd_fullmesh"
    APP_ID_WL_STATUS = "get_wl_status"
    
    def __init__(
        self,
        router_ip: str = "192.168.50.1",
        username: str = "admin",
        password: str = "",
        use_https: bool = False
    ):
        self.router_ip = router_ip
        self.username = username
        self.password = password
        self.use_https = use_https
        self.base_url = f"{'https' if use_https else 'http'}://{router_ip}"
        
        # Session management
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=3))
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        
        # Authentication state
        self._token: Optional[str] = None
        self._last_auth: Optional[datetime] = None
        self._auth_lifetime = 300  # seconds
    
    def _encode_credentials(self) -> str:
        """Encode credentials in ASUS format."""
        import base64
        creds = f"{self.username}:{self.password}"
        return base64.b64encode(creds.encode()).decode()
    
    def login(self) -> bool:
        """Authenticate with the router."""
        try:
            self.session.cookies.clear()
            login_data = {"login_authorization": self._encode_credentials()}
            
            response = self.session.post(
                f"{self.base_url}{self.ENDPOINT_LOGIN}",
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                if "error" in response.text.lower() and "login" in response.text.lower():
                    raise RouterAuthError("Invalid username or password")
                
                self._token = self._extract_token(response.text)
                self._last_auth = datetime.now()
                return True
            else:
                raise RouterConnectionError(f"HTTP {response.status_code}")
                
        except Exception as e:
            raise RouterConnectionError(f"Login failed: {e}")
    
    def _extract_token(self, response_text: str) -> Optional[str]:
        """Extract authentication token from response."""
        patterns = [
            r'asus_token\s*=\s*["\']?([^"\'\s;]+)',
            r'token\s:\s*["\']?([^"\'\s,}]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def get_device_list(self) -> List[RouterDevice]:
        """Get list of connected devices from the router."""
        devices = []
        try:
            # Try ASUS API methods
            devices = self._get_devices_clientlist()
            if not devices:
                devices = self._get_devices_networkmap()
            return devices
        except Exception as e:
            logger.warning(f"Router API failed: {e}")
            return []
    
    def _get_devices_clientlist(self) -> List[RouterDevice]:
        """Get devices using ASUS clientlist API."""
        devices = []
        try:
            response = self._make_request("/appGet.cgi", params={
                "hook": "nvram_get(custom_clientlist)"
            })
            if response.status_code == 200:
                devices = self._parse_clientlist_data(response.text)
        except Exception as e:
            logger.debug(f"Clientlist API failed: {e}")
        return devices
    
    def _get_devices_networkmap(self) -> List[RouterDevice]:
        """Get devices from networkmap endpoint."""
        devices = []
        try:
            response = self._make_request("/appGet.cgi", params={
                "hook": "get_networkmap_fullmesh()"
            })
            if response.status_code == 200:
                devices = self._parse_networkmap_data(response.text)
        except Exception as e:
            logger.debug(f"Networkmap API failed: {e}")
        return devices
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> requests.Response:
        """Make an authenticated request to the router."""
        self.login()
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=data, timeout=10)
            else:
                response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise RouterConnectionError(f"Request to {endpoint} failed: {e}")
    
    def _parse_clientlist_data(self, data: str) -> List[RouterDevice]:
        """Parse ASUS custom_clientlist format."""
        devices = []
        try:
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            entries = data.split("<")
            for entry in entries:
                if not entry or ">" not in entry:
                    continue
                parts = entry.split(">")
                if len(parts) >= 4:
                    device = RouterDevice(
                        mac=self._normalize_mac(parts[0]),
                        hostname=parts[1] if len(parts) > 1 else "Unknown",
                        ip=parts[2] if len(parts) > 2 else "0.0.0.0",
                        connection_type=self._map_connection_type(parts[3]) if len(parts) > 3 else "unknown",
                        rssi=int(parts[4]) if len(parts) > 4 and parts[4].lstrip('-').isdigit() else None,
                        last_seen=datetime.now()
                    )
                    devices.append(device)
        except Exception as e:
            logger.debug(f"Failed to parse clientlist: {e}")
        return devices
    
    def _parse_networkmap_data(self, data: str) -> List[RouterDevice]:
        """Parse networkmap_fullmesh data."""
        devices = []
        try:
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            entries = data.split("<")
            for entry in entries:
                if ">" in entry:
                    parts = entry.split(">")
                    if len(parts) >= 3:
                        device = RouterDevice(
                            mac=self._normalize_mac(parts[0]),
                            hostname=parts[1] if len(parts) > 1 else "Unknown",
                            ip=parts[2] if len(parts) > 2 else "0.0.0.0",
                            connection_type=self._map_connection_type(parts[3]) if len(parts) > 3 else "unknown",
                            last_seen=datetime.now()
                        )
                        devices.append(device)
        except Exception as e:
            logger.debug(f"Failed to parse networkmap: {e}")
        return devices
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address format."""
        mac = mac.lower().replace(":", "-").replace(".", "-")
        parts = mac.split("-")
        return ":".join(p.zfill(2) for p in parts[-6:]) if len(parts) >= 6 else mac
    
    def _map_connection_type(self, conn_type: str) -> str:
        """Map router connection type to standard format."""
        conn_lower = conn_type.lower()
        if "wire" in conn_lower or "eth" in conn_lower:
            return "wired"
        elif "2.4" in conn_lower:
            return "2.4GHz"
        elif "5" in conn_lower:
            return "5GHz"
        elif "6" in conn_lower:
            return "6GHz"
        return "unknown"
    
    def logout(self):
        """End session with router."""
        try:
            self.session.get(f"{self.base_url}/Logout.asp", timeout=5)
        except:
            pass


def get_connected_devices(
    router_ip: str = "192.168.50.1",
    username: str = "admin",
    password: str = "",
    use_https: bool = False
) -> List[Dict[str, Any]]:
    """
    Get connected devices from router with fallback to ARP scanning.
    """
    # Try router API first
    try:
        client = ASUSRouterClient(router_ip, username, password, use_https)
        devices = client.get_device_list()
        if devices:
            logger.info(f"Found {len(devices)} devices via router API")
            return [d.to_dict() for d in devices]
    except Exception as e:
        logger.warning(f"Router API failed, falling back to ARP: {e}")
    
    # Fallback: Use ARP table scanning
    return _get_devices_from_arp(router_ip)


def _get_devices_from_arp(router_ip: str) -> List[Dict[str, Any]]:
    """
    Get devices from ARP table as fallback.
    """
    devices = []
    try:
        # Get ARP table entries
        result = subprocess.run(
            ["ip", "neigh", "show"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        arp_entries = result.stdout.strip().split("\n")
        router_network = ".".join(router_ip.split(".")[:3])  # e.g., 192.168.50
        
        for entry in arp_entries:
            # Parse: 192.168.50.24 dev enP7s7 lladdr 00:e0:4c:be:fa:cc REACHABLE
            match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+\w+\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)', entry)
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                # Only include devices on the same network as the router
                if ip.startswith(router_network) and ip != router_ip:
                    devices.append({
                        "mac": mac.lower().replace("-", ":"),
                        "ip": ip,
                        "hostname": f"Device-{mac.replace(':', '')[-6:]}",
                        "connection_type": "unknown",
                        "is_online": True,
                        "last_seen": datetime.now().isoformat()
                    })
        
        logger.info(f"Found {len(devices)} devices via ARP")
        
    except Exception as e:
        logger.error(f"ARP scan failed: {e}")
    
    return devices


if __name__ == "__main__":
    print("ASUS Router Monitor with ARP Fallback")
    print("=" * 40)
    
    # Test with default credentials
    devices = get_connected_devices("192.168.50.1", "admin", "LuckyToby1!")
    
    print(f"\nFound {len(devices)} devices:\n")
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.get('hostname', 'Unknown')}")
        print(f"   MAC: {device.get('mac', 'N/A')}")
        print(f"   IP: {device.get('ip', 'N/A')}")
        print(f"   Connection: {device.get('connection_type', 'unknown')}")
        print()
