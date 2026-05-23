"""
ASUS Router Device Monitor for Vigil

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
        use_https: bool = False,
        timeout: int = 10
    ):
        """
        Initialize the ASUS router client.
        
        Args:
            router_ip: Router IP address (default: 192.168.50.1)
            username: Router admin username
            password: Router admin password
            use_https: Whether to use HTTPS (default: HTTP)
            timeout: Request timeout in seconds
        """
        self.router_ip = router_ip
        self.username = username
        self.password = password
        self.use_https = use_https
        self.timeout = timeout
        
        # Build base URL
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{router_ip}"
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ASUSWRT-Client/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
        })
        
        # Authentication state
        self._token: Optional[str] = None
        self._last_auth: Optional[datetime] = None
        self._auth_lifetime = 300  # Re-auth after 5 minutes
        
    def _encode_credentials(self) -> str:
        """
        Encode credentials in ASUS format.
        
        The ASUS router expects base64 encoded username:password
        with some routers using a specific format.
        """
        import base64
        creds = f"{self.username}:{self.password}"
        return base64.b64encode(creds.encode()).decode()
    
    def login(self) -> bool:
        """
        Authenticate with the router and establish a session.
        
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            RouterAuthError: If authentication fails
            RouterConnectionError: If router is unreachable
        """
        try:
            # Clear any existing session
            self.session.cookies.clear()
            
            # Prepare login payload
            # ASUS login uses specific form data
            login_data = {
                "login_authorization": self._encode_credentials(),
            }
            
            logger.debug(f"Attempting login to {self.base_url}{self.ENDPOINT_LOGIN}")
            
            response = self.session.post(
                f"{self.base_url}{self.ENDPOINT_LOGIN}",
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check for successful login
            if response.status_code == 200:
                # ASUS returns success in various ways
                # Check for common success indicators
                if "error" in response.text.lower() and "login" in response.text.lower():
                    logger.error("Login failed: Invalid credentials")
                    raise RouterAuthError("Invalid username or password")
                
                # Extract token from response if present
                self._token = self._extract_token(response.text)
                self._last_auth = datetime.now()
                
                logger.info(f"Successfully authenticated to ASUS router at {self.router_ip}")
                return True
            
            elif response.status_code == 401:
                logger.error("Login failed: Unauthorized (401)")
                raise RouterAuthError("Authentication failed - check credentials")
            
            else:
                logger.error(f"Login failed: HTTP {response.status_code}")
                raise RouterConnectionError(f"Unexpected response: HTTP {response.status_code}")
                
        except RouterAuthError:
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Login timeout - router at {self.router_ip} not responding")
            raise RouterConnectionError(f"Connection timeout to {self.router_ip}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to router: {e}")
            raise RouterConnectionError(f"Cannot connect to router at {self.router_ip}")
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise RouterConnectionError(f"Login error: {e}")
    
    def _extract_token(self, response_text: str) -> Optional[str]:
        """Extract authentication token from response."""
        # ASUS may return tokens in various formats
        # Try common patterns
        patterns = [
            r'asus_token\s*=\s*["\']?([^"\'\s;]+)',
            r'token\s*:\s*["\']?([^"\'\s,}]+)',
            r'cookie\s*:\s*["\']?([^"\'\s,}]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _ensure_authenticated(self):
        """Ensure we have a valid authentication session."""
        needs_auth = (
            self._last_auth is None or
            self._token is None or
            (datetime.now() - self._last_auth).seconds > self._auth_lifetime
        )
        
        if needs_auth:
            self.login()
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> requests.Response:
        """Make an authenticated request to the router."""
        self._ensure_authenticated()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=data, timeout=self.timeout)
            else:
                response = self.session.get(url, params=params, timeout=self.timeout)
            
            # Check for session expiration
            if response.status_code == 401 or "not authenticated" in response.text.lower():
                logger.warning("Session expired, re-authenticating...")
                self.login()
                # Retry the request
                if method.upper() == "POST":
                    response = self.session.post(url, data=data, timeout=self.timeout)
                else:
                    response = self.session.get(url, params=params, timeout=self.timeout)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RouterConnectionError(f"Request to {endpoint} failed: {e}")
    
    def get_device_list(self) -> List[RouterDevice]:
        """
        Get list of connected devices from the router.
        
        Returns:
            List of RouterDevice objects with connection information
            
        Raises:
            RouterConnectionError: If unable to fetch device list
        """
        devices = []
        
        try:
            # ASUS stores device info in nvram and exposes via custom endpoints
            # Try multiple approaches for compatibility
            
            # Approach 1: Use the custom client list API
            devices = self._get_devices_clientlist()
            if devices:
                logger.debug(f"Found {len(devices)} devices via clientlist API")
                return devices
            
            # Approach 2: Parse from status page
            devices = self._get_devices_from_status()
            if devices:
                logger.debug(f"Found {len(devices)} devices via status page")
                return devices
            
            # Approach 3: Use networkmap endpoint
            devices = self._get_devices_networkmap()
            if devices:
                logger.debug(f"Found {len(devices)} devices via networkmap")
                return devices
            
        except Exception as e:
            logger.error(f"Failed to get device list: {e}")
            raise RouterConnectionError(f"Device list extraction failed: {e}")
        
        return devices
    
    def _get_devices_clientlist(self) -> List[RouterDevice]:
        """
        Get devices using ASUS clientlist API.
        
        This is the primary method for ASUSWRT firmware.
        """
        devices = []
        
        try:
            # ASUS routers store client info in nvram
            # We need to extract it from specific endpoints
            
            # Get the custom client list from nvram
            response = self._make_request("/appGet.cgi", params={
                "hook": "nvram_get(custom_clientlist);nvram_get(networkmap_fullmesh)"
            })
            
            if response.status_code == 200:
                data = response.text
                devices = self._parse_clientlist_data(data)
                
        except Exception as e:
            logger.debug(f"Clientlist API failed: {e}")
        
        return devices
    
    def _get_devices_from_status(self) -> List[RouterDevice]:
        """
        Extract devices from status pages.
        
        Fallback method that parses HTML/JS from status pages.
        """
        devices = []
        
        try:
            # Get network clients status
            response = self._make_request("/ajax_status.asp")
            
            if response.status_code == 200:
                # Parse the JavaScript data structures
                text = response.text
                devices = self._parse_status_page(text)
                
        except Exception as e:
            logger.debug(f"Status page parsing failed: {e}")
        
        return devices
    
    def _get_devices_networkmap(self) -> List[RouterDevice]:
        """Get devices from networkmap endpoint."""
        devices = []
        
        try:
            response = self._make_request("/appGet.cgi", params={
                "hook": "get_networkmap_fullmesh()"
            })
            
            if response.status_code == 200:
                data = response.text
                devices = self._parse_networkmap_data(data)
                
        except Exception as e:
            logger.debug(f"Networkmap API failed: {e}")
        
        return devices
    
    def _parse_clientlist_data(self, data: str) -> List[RouterDevice]:
        """Parse ASUS custom_clientlist format."""
        devices = []
        
        try:
            # ASUS custom_clientlist format:
            # mac1>deviceName1>ip1>connectionType1>rssi1...mac2>...
            # Uses HTML entities like &gt; for >
            
            # Decode HTML entities
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            
            # Split by device entries
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
    
    def _parse_status_page(self, text: str) -> List[RouterDevice]:
        """Parse device data from AJAX status page JavaScript."""
        devices = []
        
        try:
            # Look for JavaScript arrays containing device info
            # Common patterns in ASUS firmware:
            # var clients = [...]
            # var client_list = {...}
            
            # Try to find client list objects
            patterns = [
                r'networkmap_fullmesh\s*=\s*"([^"]+)"',
                r'fromNetworkmap\s*=\s*\{([^}]+)\}',
                r'client_list\s*=\s*\{([^}]+)\}',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    # Parse the matched data
                    data = match.group(1)
                    # Further parsing depends on the format found
                    logger.debug(f"Found pattern match: {pattern[:30]}...")
                    break
                    
        except Exception as e:
            logger.debug(f"Status page parse error: {e}")
        
        return devices
    
    def _parse_networkmap_data(self, data: str) -> List[RouterDevice]:
        """Parse networkmap_fullmesh data."""
        devices = []
        
        try:
            # Similar to clientlist format
            # mac&gt;name&gt;ip&gt;connection&gt;...&lt;nextdevice...
            data = data.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
            
            entries = data.split("<")
            for entry in entries:
                if ">" in entry:
                    parts = entry.split(">")
                    if len(parts) >= 3:
                        device = RouterDevice(
                            mac=self._normalize_mac(parts[0]),
                            hostname=parts[1] if parts[1] else "Unknown",
                            ip=parts[2] if len(parts) > 2 else "0.0.0.0",
                            connection_type=self._map_connection_type(parts[3]) if len(parts) > 3 else "unknown",
                            last_seen=datetime.now()
                        )
                        devices.append(device)
                        
        except Exception as e:
            logger.debug(f"Networkmap parse error: {e}")
        
        return devices
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to standard format (aa:bb:cc:dd:ee:ff)."""
        # Remove any separators and convert to lowercase
        mac_clean = re.sub(r'[^a-fA-F0-9]', '', mac).lower()
        
        # Ensure 12 characters
        if len(mac_clean) != 12:
            return mac  # Return original if invalid
        
        # Format with colons
        return ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))
    
    def _map_connection_type(self, conn_type: str) -> str:
        """Map ASUS connection type codes to readable strings."""
        mapping = {
            "0": "wired",
            "1": "2.4GHz",
            "2": "5GHz", 
            "3": "5GHz-2",
            "4": "6GHz",
            "wired": "wired",
            "lan": "wired",
            "eth": "wired",
            "2.4": "2.4GHz",
            "5": "5GHz",
            "6": "6GHz",
        }
        
        return mapping.get(conn_type.lower(), conn_type) if conn_type else "unknown"
    
    def get_router_info(self) -> Dict[str, Any]:
        """
        Get basic router information.
        
        Returns:
            Dictionary with router model, firmware version, uptime, etc.
        """
        info = {
            "model": "Unknown",
            "firmware": "Unknown",
            "uptime": None,
            "ip": self.router_ip,
        }
        
        try:
            self._ensure_authenticated()
            
            # Get sysinfo
            response = self._make_request("/appGet.cgi", params={
                "hook": "nvram_get(productid);nvram_get(firmver);nvram_get(buildno);nvram_get(extendno);nvram_get(uptime)"
            })
            
            if response.status_code == 200:
                text = response.text
                # Parse nvram values from response
                info["raw_response"] = text[:500]  # Debug info
                
        except Exception as e:
            logger.error(f"Failed to get router info: {e}")
        
        return info
    
    def logout(self):
        """Logout and clear session."""
        try:
            self._make_request("/Logout.asp")
        except:
            pass
        finally:
            self.session.cookies.clear()
            self._token = None
            self._last_auth = None


class RouterAuthError(Exception):
    """Raised when router authentication fails."""
    pass


class RouterConnectionError(Exception):
    """Raised when router connection fails."""
    pass


# Convenience function for direct use
def get_connected_devices(
    router_ip: str = "192.168.50.1",
    username: str = "admin",
    password: str = "",
    use_https: bool = False
) -> List[Dict[str, Any]]:
    """
    Convenience function to get connected devices.
    
    Args:
        router_ip: Router IP address
        username: Admin username
        password: Admin password
        use_https: Use HTTPS instead of HTTP
        
    Returns:
        List of device dictionaries
    """
    client = ASUSRouterClient(router_ip, username, password, use_https)
    
    try:
        devices = client.get_device_list()
        return [d.to_dict() for d in devices]
    finally:
        client.logout()


if __name__ == "__main__":
    # Example usage
    import sys
    
    print("ASUS Router Monitor for Vigil")
    print("=" * 40)
    
    # Check for config import
    try:
        from config import ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWORD
    except ImportError:
        print("\nNote: Create config.py from config_template.py with your credentials")
        print("Using defaults for testing...")
        ROUTER_IP = "192.168.50.1"
        ROUTER_USERNAME = "admin"
        ROUTER_PASSWORD = ""
    
    if not ROUTER_PASSWORD:
        print("\nError: No password configured. Please set ROUTER_PASSWORD in config.py")
        sys.exit(1)
    
    # Create client and fetch devices
    client = ASUSRouterClient(ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWORD)
    
    try:
        print(f"\nConnecting to router at {ROUTER_IP}...")
        
        # Get router info
        info = client.get_router_info()
        print(f"Router Info: {info}")
        
        # Get device list
        devices = client.get_device_list()
        
        print(f"\nFound {len(devices)} connected devices:\n")
        
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device.hostname}")
            print(f"   MAC: {device.mac}")
            print(f"   IP: {device.ip}")
            print(f"   Connection: {device.connection_type}", end="")
            if device.rssi is not None:
                print(f" (RSSI: {device.rssi} dBm)")
            else:
                print()
            print()
            
    except RouterAuthError as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)
    except RouterConnectionError as e:
        print(f"\nConnection failed: {e}")
        sys.exit(1)
    finally:
        client.logout()
