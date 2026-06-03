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
import base64
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests

from ..base import (
    RouterInterface,
    RouterCredentials,
    RouterInfo,
    RouterDevice,
    RouterVendor,
    RouterAuthError,
    RouterConnectionError,
    RouterTimeoutError,
    RouterAPIError,
)

logger = logging.getLogger(__name__)


class ASUSRouter(RouterInterface):
    """
    ASUS Router implementation using HTTP API.
    
    This implementation supports ASUS routers running ASUSWRT firmware,
    including aiMesh nodes. It uses the router's web interface API
    which is accessible via HTTP/HTTPS.
    
    Note: Some newer firmware versions may require specific authentication
    flows. This implementation attempts multiple methods.
    """
    
    VENDOR = RouterVendor.ASUS
    MODEL_KEYWORDS = ["asus", "gt6", "rt-ax", "zenwifi"]
    
    # ASUS-specific endpoints
    ENDPOINT_LOGIN = "/login.cgi"
    ENDPOINT_CLIENT_LIST = "/appGet.cgi"
    ENDPOINT_SYS_INFO = "/ajax_status.asp"
    ENDPOINT_LOGOUT = "/Logout.asp"
    
    def __init__(
        self,
        ip_address: str,
        credentials: RouterCredentials,
        use_https: bool = False,
        timeout: int = 30
    ):
        super().__init__(ip_address, credentials, use_https, timeout)
        self._session = requests.Session()
        self._token: Optional[str] = None
        self._base_url = f"{'https' if use_https else 'http'}://{ip_address}"
        
        # Configure session
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
    
    def _encode_credentials(self) -> str:
        """Encode credentials for ASUS login."""
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
            self._token = None
            
            # Prepare login data
            login_data = {
                "login_authorization": self._encode_credentials(),
            }
            
            logger.debug(f"Attempting login to {self._base_url}")
            
            response = self._session.post(
                f"{self._base_url}{self.ENDPOINT_LOGIN}",
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
                self._is_connected = True
                logger.info(f"Successfully connected to ASUS router at {self.ip_address}")
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
                f"{self._base_url}{self.ENDPOINT_LOGOUT}",
                timeout=5
            )
        except Exception:
            pass
        finally:
            self._is_connected = False
            self._token = None
            try:
                self._session.close()
            except Exception:
                pass
    
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
    
    def _ensure_connected(self) -> None:
        """Ensure router is connected, raise exception if not."""
        if not self._is_connected:
            raise RouterConnectionError("Not connected to router. Call connect() first.")
    
    def _make_authenticated_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        method: str = "GET"
    ) -> requests.Response:
        """Make an authenticated request."""
        self._ensure_connected()
        
        url = f"{self._base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = self._session.post(url, data=data, timeout=self.timeout)
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
                        mac=parts[0],
                        ip=parts[2] if len(parts) > 2 else "0.0.0.0",
                        hostname=parts[1] if len(parts) > 1 else "Unknown",
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
                            mac=parts[0],
                            ip=parts[2] if len(parts) > 2 else "0.0.0.0",
                            hostname=parts[1] if len(parts) > 1 else "Unknown",
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
        """Get router system information."""
        info = RouterInfo(
            vendor=self.VENDOR,
            model="Unknown",
            ip_address=self.ip_address,
            is_reachable=False
        )
        
        try:
            response = self._session.get(
                f"{self._base_url}{self.ENDPOINT_SYS_INFO}",
                timeout=5
            )
            
            if response.status_code == 200:
                info.is_reachable = True
                
                # Try to extract model info from response
                if "ASUS" in response.text:
                    info.model = self._extract_model(response.text) or "ASUS Router"
                    info.features = ["device_list", "traffic_stats", "parental_controls"]
            
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
    
    def block_device(self, mac_address: str) -> bool:
        """
        Block a device by MAC address using Parental Controls.
        
        Note: This requires the router to have parental controls enabled
        and may require additional configuration.
        """
        try:
            self._ensure_connected()
            
            # ASUS uses parental controls for blocking
            block_data = {
                "action": "parental_control",
                "mac": mac_address,
                "enable": "1"
            }
            
            response = self._session.post(
                f"{self._base_url}/apply.cgi",
                data=block_data,
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                logger.info(f"Blocked device {mac_address}")
            else:
                logger.error(f"Failed to block {mac_address}: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error blocking device: {e}")
            return False
    
    def unblock_device(self, mac_address: str) -> bool:
        """Unblock a device previously blocked."""
        try:
            self._ensure_connected()
            
            unblock_data = {
                "action": "parental_control",
                "mac": mac_address,
                "enable": "0"
            }
            
            response = self._session.post(
                f"{self._base_url}/apply.cgi",
                data=unblock_data,
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                logger.info(f"Unblocked device {mac_address}")
            else:
                logger.error(f"Failed to unblock {mac_address}: {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error unblocking device: {e}")
            return False
    
    def check_firmware_version(self) -> Dict[str, Any]:
        """Check current firmware version."""
        try:
            response = self._make_authenticated_request(
                self.ENDPOINT_CLIENT_LIST,
                params={"hook": "nvram_get(firmver)"}
            )
            
            version = response.text.strip()
            
            return {
                "current_version": version,
                "model": self._extract_model(version) or "ASUS Router",
                "update_available": False,  # Would check against ASUS servers
                "ip_address": self.ip_address
            }
        except Exception as e:
            logger.error(f"Error checking firmware: {e}")
            return {
                "error": "Unable to retrieve firmware info",
                "ip_address": self.ip_address
            }
