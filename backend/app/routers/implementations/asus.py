"""
ASUS Router Implementation for Vigil

Supports ASUS GT6 and other ASUS routers with aiMesh support.
Uses HTTP API with session-based authentication.

Router Models Tested:
- ASUS GT6 (ZenWiFi Pro ET12)
- ASUS RT-AX86U
- ASUS RT-AX88U
"""

import re
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter

from ..base import (
    BaseHTTPRouter,
    RouterVendor,
    RouterCredentials,
    RouterDevice,
    RouterInfo,
    RouterAuthError,
    RouterConnectionError,
)


logger = logging.getLogger(__name__)


class ASUSRouter(BaseHTTPRouter):
    """
    ASUS Router implementation using HTTP API.
    
    This implementation supports ASUS routers running ASUSWRT firmware,
    including aiMesh nodes. It uses the router's web interface API
    which is accessible via HTTP/HTTPS.
    
    Note: Some newer firmware versions may require specific authentication
    flows. This implementation attempts multiple methods.
    """
    
    # ASUS-specific endpoints
    ENDPOINT_LOGIN = "/login.cgi"
    ENDPOINT_CLIENT_LIST = "/appGet.cgi"
    ENDPOINT_SYS_INFO = "/ajax_status.asp"
    
    def __init__(self, credentials: RouterCredentials):
        super().__init__(credentials)
        self._token: Optional[str] = None
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
    
    @property
    def vendor(self) -> RouterVendor:
        return RouterVendor.ASUS
    
    @property
    def vendor_name(self) -> str:
        return "ASUS"
    
    def _encode_credentials(self) -> str:
        """Encode credentials for ASUS login."""
        import base64
        creds = f"{self.credentials.username}:{self.credentials.password}"
        return base64.b64encode(creds.encode()).decode()
    
    def connect(self) -> bool:
        """
        Authenticate with ASUS router.
        
        ASUS routers use a session-based authentication where we POST
        to /login.cgi with base64-encoded credentials.
        """
        try:
            # Clear any existing session
            self._session.cookies.clear()
            
            # Prepare login data
            login_data = {
                "login_authorization": self._encode_credentials(),
            }
            
            logger.debug(f"Attempting login to {self.base_url}")
            
            response = self._session.post(
                f"{self.base_url}{self.ENDPOINT_LOGIN}",
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check if login was successful
            if response.status_code != 200:
                raise RouterConnectionError(f"HTTP {response.status_code}")
            
            # Check for redirect to login page (indicates failure)
            if "Main_Login.asp" in response.text and "location.href" in response.text:
                raise RouterAuthError("Invalid credentials")
            
            # Try to extract auth token from response or cookies
            self._token = self._extract_token(response)
            
            # Verify connection by fetching sys info
            info = self.get_router_info()
            if info.is_reachable:
                self._connected = True
                logger.info(f"Successfully connected to ASUS router at {self.credentials.ip_address}")
                return True
            
            raise RouterConnectionError("Router not responding after login")
            
        except (RouterAuthError, RouterConnectionError):
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise RouterConnectionError(f"Login failed: {e}")
    
    def disconnect(self) -> None:
        """Logout from router."""
        try:
            self._session.get(
                f"{self.base_url}/Logout.asp",
                timeout=5
            )
        except Exception:
            pass
        finally:
            self._connected = False
            self._token = None
    
    def _extract_token(self, response: requests.Response) -> Optional[str]:
        """Extract authentication token from response."""
        # Check for asus_token in response text
        patterns = [
            r'asus_token\s*=\s*["\']?([^"\'\s;]+)',
            r'asus_token\s*:\s*["\']?([^"\'\s,}]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                token = match.group(1)
                # Also set as cookie for subsequent requests
                self._session.cookies.set("asus_token", token)
                return token
        
        # Check cookies
        token = self._session.cookies.get("asus_token")
        if token:
            return token
        
        return None
    
    def _make_authenticated_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        method: str = "GET"
    ) -> requests.Response:
        """Make an authenticated request."""
        self._ensure_connected()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = self._session.post(url, data=params, timeout=self.timeout)
            else:
                response = self._session.get(url, params=params, timeout=self.timeout)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RouterConnectionError(f"Request to {endpoint} failed: {e}")
    
    def get_connected_devices(self) -> List[RouterDevice]:
        """
        Get list of devices connected to the router.
        
        Uses the appGet.cgi endpoint with nvram_get hook to fetch
        the client list from router memory.
        """
        devices = []
        
        try:
            # Try multiple methods to get device list
            
            # Method 1: custom_clientlist
            response = self._make_authenticated_request(
                self.ENDPOINT_CLIENT_LIST,
                params={"hook": "nvram_get(custom_clientlist)"}
            )
            devices = self._parse_clientlist_response(response.text)
            
            if devices:
                logger.debug(f"Found {len(devices)} devices via custom_clientlist")
                return devices
            
            # Method 2: networkmap
            response = self._make_authenticated_request(
                self.ENDPOINT_CLIENT_LIST,
                params={"hook": "get_networkmap_fullmesh()"}
            )
            devices = self._parse_networkmap_response(response.text)
            
            if devices:
                logger.debug(f"Found {len(devices)} devices via networkmap")
                return devices
            
            logger.warning("No devices found from ASUS router")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []
    
    def _parse_clientlist_response(self, data: str) -> List[RouterDevice]:
        """Parse ASUS custom_clientlist format."""
        devices = []
        
        try:
            # Decode HTML entities
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            
            # Format: mac>name>ip>connection>rssi<nextdevice...
            entries = data.split("<")
            
            for entry in entries:
                if not entry or ">" not in entry:
                    continue
                
                parts = entry.split(">")
                if len(parts) >= 4:
                    device = RouterDevice(
                        mac_address=self._normalize_mac(parts[0]),
                        hostname=parts[1] if len(parts) > 1 else "Unknown",
                        ip_address=parts[2] if len(parts) > 2 else "0.0.0.0",
                        connection_type=self._map_connection_type(parts[3]) if len(parts) > 3 else "unknown",
                        rssi=int(parts[4]) if len(parts) > 4 and parts[4].lstrip('-').isdigit() else None,
                        vendor=self.vendor_name,
                        is_online=True,
                        last_seen=datetime.now()
                    )
                    devices.append(device)
                    
        except Exception as e:
            logger.debug(f"Failed to parse clientlist: {e}")
        
        return devices
    
    def _parse_networkmap_response(self, data: str) -> List[RouterDevice]:
        """Parse networkmap_fullmesh response."""
        devices = []
        
        try:
            # Similar format to clientlist
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            
            entries = data.split("<")
            for entry in entries:
                if ">" in entry:
                    parts = entry.split(">")
                    if len(parts) >= 3:
                        device = RouterDevice(
                            mac_address=self._normalize_mac(parts[0]),
                            hostname=parts[1] if len(parts) > 1 else "Unknown",
                            ip_address=parts[2] if len(parts) > 2 else "0.0.0.0",
                            connection_type=self._map_connection_type(parts[3]) if len(parts) > 3 else "unknown",
                            vendor=self.vendor_name,
                            is_online=True,
                            last_seen=datetime.now()
                        )
                        devices.append(device)
                        
        except Exception as e:
            logger.debug(f"Failed to parse networkmap: {e}")
        
        return devices
    
    def get_router_info(self) -> RouterInfo:
        """Get router information."""
        info = RouterInfo(
            vendor=self.vendor,
            ip_address=self.credentials.ip_address,
            is_reachable=False
        )
        
        try:
            response = self._session.get(
                f"{self.base_url}{self.ENDPOINT_SYS_INFO}",
                timeout=5
            )
            
            if response.status_code == 200:
                info.is_reachable = True
                
                # Try to extract model info from response
                if "ASUS" in response.text:
                    info.model = self._extract_model(response.text)
                    info.supports_api = True
            
        except Exception as e:
            logger.debug(f"Could not get router info: {e}")
        
        return info
    
    def _extract_model(self, text: str) -> Optional[str]:
        """Extract router model from response."""
        # Look for model patterns like "RT-AX86U" or "GT6"
        patterns = [
            r'(RT-[A-Z]+\d+[A-Z]*)',
            r'(GT\d+)',
            r'(ZenWiFi [A-Za-z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to standard format."""
        mac = mac.lower().replace(":", "").replace("-", "").replace(".", "")
        return ":".join(mac[i:i+2] for i in range(0, 12, 2))
    
    def _map_connection_type(self, conn_type: str) -> str:
        """Map router connection type to standard format."""
        conn_lower = conn_type.lower()
        
        if any(x in conn_lower for x in ["wire", "eth", "lan"]):
            return "wired"
        elif "2.4" in conn_lower:
            return "2.4GHz"
        elif "5" in conn_lower and "6" not in conn_lower:
            return "5GHz"
        elif "6" in conn_lower:
            return "6GHz"
        elif "wifi" in conn_lower or "wlan" in conn_lower:
            return "wireless"
        
        return "unknown"
