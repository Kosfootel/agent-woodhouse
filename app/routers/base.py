"""
Router Interface Base Classes

Abstract base classes defining the router interface that all vendor implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import logging

import requests

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    """Standardized connection types."""
    WIRED = "wired"
    WIFI_2_4GHZ = "2.4GHz"
    WIFI_5GHZ = "5GHz"
    WIFI_6GHZ = "6GHz"
    WIFI_UNKNOWN = "wifi_unknown"
    UNKNOWN = "unknown"


class RouterVendor(str, Enum):
    """Supported router vendors."""
    ASUS = "asus"
    TP_LINK = "tp-link"
    NETGEAR = "netgear"
    UBIQUITI = "ubiquiti"
    LINKSYS = "linksys"
    D_LINK = "d-link"
    GENERIC = "generic"
    UNKNOWN = "unknown"


@dataclass
class RouterCredentials:
    """Router authentication credentials."""
    username: str
    password: str
    # Optional API key for some routers
    api_key: Optional[str] = None
    # For routers that use token-based auth
    token: Optional[str] = None
    # SNMP community string (for SNMP fallback)
    snmp_community: str = "public"
    
    def mask_password(self) -> str:
        """Return masked representation for logging."""
        return "*" * len(self.password) if self.password else ""


@dataclass
class RouterInfo:
    """Router system information."""
    vendor: RouterVendor
    model: str
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: str = ""
    hostname: Optional[str] = None
    uptime_seconds: Optional[int] = None
    serial_number: Optional[str] = None
    features: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vendor": self.vendor.value,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "uptime_seconds": self.uptime_seconds,
            "serial_number": self.serial_number,
            "features": self.features,
        }


@dataclass
class RouterDevice:
    """Represents a device connected to the router."""
    mac: str
    ip: str
    hostname: str
    connection_type: str = ConnectionType.UNKNOWN
    rssi: Optional[int] = None  # Signal strength in dBm
    upload_speed: Optional[float] = None  # Mbps
    download_speed: Optional[float] = None  # Mbps
    is_online: bool = True
    device_type: Optional[str] = None  # Router's classification
    vendor: Optional[str] = None  # Detected vendor from MAC OUI
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    dhcp_lease_time: Optional[int] = None  # seconds
    port: Optional[str] = None  # For wired: port number
    ssid: Optional[str] = None  # For wireless: connected SSID
    
    def __post_init__(self):
        """Normalize MAC address format."""
        if self.mac:
            self.mac = self._normalize_mac(self.mac)
    
    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to standard format (aa:bb:cc:dd:ee:ff)."""
        # Remove any separators and non-hex characters
        clean = ''.join(c.lower() for c in mac if c.isalnum())
        # Take last 12 characters (in case of padding)
        clean = clean[-12:]
        # Insert colons
        return ':'.join(clean[i:i+2] for i in range(0, 12, 2))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "mac": self.mac,
            "ip": self.ip,
            "hostname": self.hostname,
            "connection_type": self.connection_type,
            "rssi": self.rssi,
            "upload_speed": self.upload_speed,
            "download_speed": self.download_speed,
            "is_online": self.is_online,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "dhcp_lease_time": self.dhcp_lease_time,
            "port": self.port,
            "ssid": self.ssid,
        }
        return {k: v for k, v in result.items() if v is not None}


# Exception Classes

class RouterError(Exception):
    """Base exception for router operations."""
    pass


class RouterAuthError(RouterError):
    """Raised when router authentication fails."""
    pass


class RouterConnectionError(RouterError):
    """Raised when connection to router fails."""
    pass


class RouterTimeoutError(RouterConnectionError):
    """Raised when router request times out."""
    pass


class RouterNotSupportedError(RouterError):
    """Raised when router type is not supported."""
    pass


class RouterAPIError(RouterError):
    """Raised when router API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# Abstract Base Class

class RouterInterface(ABC):
    """
    Abstract base class for router implementations.
    
    All vendor-specific router classes must inherit from this and implement
    all abstract methods. This provides a unified interface for Vigil to
    interact with different router types.
    """
    
    # Vendor identifier (must be set by subclasses)
    VENDOR: RouterVendor = RouterVendor.UNKNOWN
    
    # Common model identifiers for auto-detection
    MODEL_KEYWORDS: List[str] = []
    
    def __init__(
        self,
        ip_address: str,
        credentials: RouterCredentials,
        use_https: bool = False,
        timeout: int = 30
    ):
        """
        Initialize router interface.
        
        Args:
            ip_address: Router's IP address
            credentials: Authentication credentials
            use_https: Whether to use HTTPS (default: HTTP)
            timeout: Request timeout in seconds
        """
        self.ip_address = ip_address
        self.credentials = credentials
        self.use_https = use_https
        self.timeout = timeout
        self._is_connected = False
        self._router_info: Optional[RouterInfo] = None
        self._last_error: Optional[str] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Authenticate and establish connection to the router.
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            RouterAuthError: If authentication fails
            RouterConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection and logout from router.
        Safe to call even if not connected.
        """
        pass
    
    @abstractmethod
    def get_connected_devices(self) -> List[RouterDevice]:
        """
        Get list of devices currently connected to the router.
        
        Returns:
            List of RouterDevice objects
            
        Raises:
            RouterConnectionError: If not connected or connection lost
            RouterAPIError: If API request fails
        """
        pass
    
    @abstractmethod
    def get_router_info(self) -> RouterInfo:
        """
        Get router system information.
        
        Returns:
            RouterInfo object with system details
            
        Raises:
            RouterConnectionError: If not connected
            RouterAPIError: If API request fails
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if router is reachable on the network.
        
        This should be a lightweight check (e.g., ping or simple HTTP request)
        that doesn't require authentication.
        
        Returns:
            True if router appears to be online
        """
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.ip_address, 80 if not self.use_https else 443))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """
        Check if currently authenticated/connected to router.
        
        Returns:
            True if authenticated session is active
        """
        return self._is_connected
    
    @classmethod
    def get_vendor(cls) -> RouterVendor:
        """
        Get the vendor type for this router implementation.
        
        Returns:
            RouterVendor enum value
        """
        return cls.VENDOR
    
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error message, if any.
        
        Returns:
            Error message string or None
        """
        return self._last_error
    
    def _set_error(self, message: str) -> None:
        """Set error message and log it."""
        self._last_error = message
        logger.error(f"[{self.VENDOR.value}] {message}")
    
    def _ensure_connected(self) -> None:
        """
        Ensure router is connected, raise exception if not.
        
        Raises:
            RouterConnectionError: If not connected
        """
        if not self._is_connected:
            raise RouterConnectionError("Not connected to router. Call connect() first.")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures disconnect."""
        self.disconnect()
        return False


class BaseHTTPRouter(RouterInterface):
    """
    Base class for HTTP-based router implementations.
    
    Provides common HTTP session management and utilities for
    routers that use HTTP/HTTPS web interfaces.
    """
    
    def __init__(
        self,
        ip_address: str,
        credentials: RouterCredentials,
        use_https: bool = False,
        timeout: int = 30
    ):
        super().__init__(ip_address, credentials, use_https, timeout)
        self._session = requests.Session()
        self.base_url = f"{'https' if use_https else 'http'}://{ip_address}"
        
        # Configure session
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
    
    def _ensure_connected(self) -> None:
        """Ensure router is connected, raise exception if not."""
        if not self._is_connected:
            raise RouterConnectionError("Not connected to router. Call connect() first.")
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        method: str = "GET",
        timeout: Optional[int] = None
    ) -> requests.Response:
        """Make an HTTP request to the router."""
        url = f"{self.base_url}{endpoint}"
        req_timeout = timeout or self.timeout
        
        try:
            if method.upper() == "POST":
                response = self._session.post(url, data=data, timeout=req_timeout)
            else:
                response = self._session.get(url, params=params, timeout=req_timeout)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            raise RouterTimeoutError(f"Request to {endpoint} timed out")
        except requests.exceptions.ConnectionError as e:
            raise RouterConnectionError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise RouterAPIError(f"Request failed: {e}")
    
    def _make_authenticated_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        method: str = "GET"
    ) -> requests.Response:
        """Make an authenticated request (requires active session)."""
        self._ensure_connected()
        return self._make_request(endpoint, params, data, method)
    
    def disconnect(self) -> None:
        """Close HTTP session and logout."""
        try:
            self._session.close()
        except Exception:
            pass
        finally:
            self._is_connected = False


class RouterCapabilityChecker:
    """
    Utility class to check router capabilities.
    
    Used for feature detection and capability reporting.
    """
    
    CAPABILITIES = [
        "device_list",
        "device_history",
        "traffic_stats",
        "bandwidth_limits",
        "port_forwarding",
        "dhcp_settings",
        "guest_network",
        "parental_controls",
        "qos",
        "vpn",
        "firmware_update",
    ]
    
    def __init__(self, router: RouterInterface):
        self.router = router
    
    def check_capability(self, capability: str) -> bool:
        """
        Check if router supports a specific capability.
        
        Args:
            capability: Capability name to check
            
        Returns:
            True if capability is supported
        """
        # Base class implementations should override this
        # or provide specific capability detection
        checker = getattr(self.router, f"_check_{capability}", None)
        if callable(checker):
            try:
                return checker()
            except Exception:
                return False
        return False
    
    def get_all_capabilities(self) -> Dict[str, bool]:
        """Get status of all known capabilities."""
        return {cap: self.check_capability(cap) for cap in self.CAPABILITIES}


# Utility Functions

def normalize_mac_address(mac: str) -> str:
    """
    Normalize any MAC address format to standard aa:bb:cc:dd:ee:ff format.
    
    Args:
        mac: MAC address in any format
        
    Returns:
        Normalized MAC address or empty string if invalid
    """
    if not mac:
        return ""
    
    # Remove all non-alphanumeric characters
    clean = ''.join(c.lower() for c in mac if c.isalnum())
    
    # Must be 12 hex characters
    if len(clean) != 12:
        return ""
    
    # Format with colons
    return ':'.join(clean[i:i+2] for i in range(0, 12, 2))


def get_vendor_from_mac(mac: str) -> Optional[str]:
    """
    Get vendor name from MAC address OUI.
    
    Args:
        mac: MAC address (any format)
        
    Returns:
        Vendor name or None if not recognized
    """
    normalized = normalize_mac_address(mac)
    if not normalized:
        return None
    
    # OUI database (first 3 octets)
    oui_db = {
        "00:1b:fc": "ASUSTeK",
        "00:26:18": "ASUSTeK",
        "04:d9:f5": "ASUSTeK",
        "08:60:6e": "ASUSTeK",
        "0c:9d:92": "ASUSTeK",
        "10:7b:44": "ASUSTeK",
        "10:c3:7b": "ASUSTeK",
        "14:dd:a9": "ASUSTeK",
        "1c:b7:2c": "ASUSTeK",
        "24:4b:fe": "ASUSTeK",
        "2c:4d:54": "ASUSTeK",
        "30:5a:3a": "ASUSTeK",
        "38:2c:4a": "ASUSTeK",
        "3c:06:30": "ASUSTeK",
        "40:16:7e": "ASUSTeK",
        "50:46:5d": "ASUSTeK",
        "54:a0:50": "ASUSTeK",
        "60:45:cb": "ASUSTeK",
        "70:4d:7b": "ASUSTeK",
        "78:24:af": "ASUSTeK",
        "88:d7:f6": "ASUSTeK",
        "90:e6:ba": "ASUSTeK",
        "9c:5c:8e": "ASUSTeK",
        "a8:5e:45": "ASUSTeK",
        "ac:22:0b": "ASUSTeK",
        "b0:be:76": "ASUSTeK",
        "b4:2e:99": "ASUSTeK",
        "bc:ee:7b": "ASUSTeK",
        "c0:56:27": "ASUSTeK",
        "c8:60:00": "ASUSTeK",
        "d4:5d:64": "ASUSTeK",
        "d8:50:e6": "ASUSTeK",
        "e0:3f:49": "ASUSTeK",
        "e0:db:10": "ASUSTeK",
        "f0:79:59": "ASUSTeK",
        "f4:6d:04": "ASUSTeK",
        "fc:34:97": "ASUSTeK",
        # TP-Link
        "00:14:78": "TP-Link",
        "00:27:19": "TP-Link",
        "00:5f:67": "TP-Link",
        "0c:80:63": "TP-Link",
        "10:27:be": "TP-Link",
        "14:cc:20": "TP-Link",
        "18:d6:c7": "TP-Link",
        "1c:3b:f3": "TP-Link",
        "20:dc:e6": "TP-Link",
        "24:65:11": "TP-Link",
        "28:ee:2c": "TP-Link",
        "30:de:4b": "TP-Link",
        "3c:84:6a": "TP-Link",
        "40:16:9f": "TP-Link",
        "44:4e:6d": "TP-Link",
        "50:c7:bf": "TP-Link",
        "58:d9:c3": "TP-Link",
        "5c:62:8b": "TP-Link",
        "60:3a:7c": "TP-Link",
        "68:ff:7b": "TP-Link",
        "78:44:76": "TP-Link",
        "88:25:93": "TP-Link",
        "8c:ab:8e": "TP-Link",
        "90:9a:4a": "TP-Link",
        "98:de:d0": "TP-Link",
        "a4:11:94": "TP-Link",
        "ac:15:a2": "TP-Link",
        "b0:48:7a": "TP-Link",
        "b0:95:75": "TP-Link",
        "bc:32:b2": "TP-Link",
        "c4:36:6c": "TP-Link",
        "c4:e9:84": "TP-Link",
        "cc:08:fb": "TP-Link",
        "d8:0d:17": "TP-Link",
        "d8:5d:4c": "TP-Link",
        "e4:c3:2a": "TP-Link",
        "ec:08:6b": "TP-Link",
        "ec:26:ca": "TP-Link",
        "f4:f2:6d": "TP-Link",
        # Netgear
        "00:09:5b": "Netgear",
        "00:0f:b5": "Netgear",
        "00:1b:2f": "Netgear",
        "00:1e:2a": "Netgear",
        "00:24:b2": "Netgear",
        "00:26:f2": "Netgear",
        "00:8e:f2": "Netgear",
        "08:02:8e": "Netgear",
        "08:36:c9": "Netgear",
        "08:bd:43": "Netgear",
        "10:0d:7f": "Netgear",
        "10:7b:44": "Netgear",
        "20:4e:7f": "Netgear",
        "20:e5:2a": "Netgear",
        "28:c6:8e": "Netgear",
        "2c:b0:5d": "Netgear",
        "2c:30:a1": "Netgear",
        "30:46:9a": "Netgear",
        "34:98:b5": "Netgear",
        "38:94:ed": "Netgear",
        "40:5b:df": "Netgear",
        "44:a5:6e": "Netgear",
        "4c:01:43": "Netgear",
        "4c:60:de": "Netgear",
        "50:6a:03": "Netgear",
        "60:a4:b7": "Netgear",
        "6c:b0:ce": "Netgear",
        "74:44:01": "Netgear",
        "80:37:73": "Netgear",
        "90:9a:4a": "Netgear",
        "94:18:82": "Netgear",
        "a0:04:60": "Netgear",
        "a4:11:62": "Netgear",
        "b0:39:56": "Netgear",
        "b0:7f:b3": "Netgear",
        "b4:82:c5": "Netgear",
        "c0:ff:d4": "Netgear",
        "c4:3d:c7": "Netgear",
        "c8:9e:43": "Netgear",
        "cc:40:d0": "Netgear",
        "d4:6d:6d": "Netgear",
        "dc:ef:ca": "Netgear",
        "e0:46:9a": "Netgear",
        "e0:91:f5": "Netgear",
        "e8:fc:af": "Netgear",
        "f0:3e:95": "Netgear",
        "fc:03:9f": "Netgear",
        # Ubiquiti
        "04:18:d6": "Ubiquiti",
        "18:e8:29": "Ubiquiti",
        "24:a4:3c": "Ubiquiti",
        "44:d9:e7": "Ubiquiti",
        "68:d7:9a": "Ubiquiti",
        "74:83:c2": "Ubiquiti",
        "78:45:58": "Ubiquiti",
        "9c:05:d6": "Ubiquiti",
        "ac:8b:a9": "Ubiquiti",
        "e0:63:da": "Ubiquiti",
        "f0:9f:c2": "Ubiquiti",
        "f4:92:bf": "Ubiquiti",
        "f9:2f:fb": "Ubiquiti",
        "fc:ec:da": "Ubiquiti",
    }
    
    oui = ':'.join(normalized.split(':')[:3])
    return oui_db.get(oui)
