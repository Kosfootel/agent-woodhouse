"""
Router Abstraction Base Classes for Vigil

Provides abstract base classes for router implementations, enabling
support for multiple router vendors (ASUS, TP-Link, Netgear, Ubiquiti, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class RouterVendor(Enum):
    """Supported router vendors."""
    ASUS = "asus"
    TP_LINK = "tp-link"
    NETGEAR = "netgear"
    UBIQUITI = "ubiquiti"
    LINKSYS = "linksys"
    GENERIC = "generic"  # Fallback for unsupported vendors


@dataclass
class RouterCredentials:
    """Router authentication credentials."""
    username: str
    password: str
    ip_address: str
    use_https: bool = False
    port: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "ip_address": self.ip_address,
            "use_https": self.use_https,
            "port": self.port,
        }


@dataclass
class RouterDevice:
    """Represents a device connected to the router."""
    mac_address: str
    ip_address: str
    hostname: str
    connection_type: str = "unknown"  # 'wired', '2.4GHz', '5GHz', '6GHz'
    vendor: Optional[str] = None
    rssi: Optional[int] = None  # Signal strength for wireless
    upload_speed: Optional[float] = None  # Mbps
    download_speed: Optional[float] = None  # Mbps
    is_online: bool = True
    device_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now()
        if self.last_seen is None:
            self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "connection_type": self.connection_type,
            "vendor": self.vendor,
            "rssi": self.rssi,
            "upload_speed": self.upload_speed,
            "download_speed": self.download_speed,
            "is_online": self.is_online,
            "device_type": self.device_type,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "metadata": self.metadata,
        }


@dataclass
class RouterInfo:
    """Router information and status."""
    vendor: RouterVendor
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    wan_ip: Optional[str] = None
    uptime_seconds: Optional[int] = None
    is_reachable: bool = False
    supports_api: bool = False
    discovery_method: str = "unknown"  # How the router was detected


class RouterException(Exception):
    """Base exception for router operations."""
    pass


class RouterAuthError(RouterException):
    """Raised when router authentication fails."""
    pass


class RouterConnectionError(RouterException):
    """Raised when connection to router fails."""
    pass


class RouterNotSupportedError(RouterException):
    """Raised when router vendor is not supported."""
    pass


class BaseRouter(ABC):
    """
    Abstract base class for router implementations.
    
    All router implementations must inherit from this class and implement
    the abstract methods. This provides a consistent interface regardless
    of the underlying router vendor.
    """
    
    def __init__(self, credentials: RouterCredentials):
        self.credentials = credentials
        self._connected = False
        self._router_info: Optional[RouterInfo] = None
        self._session: Optional[Any] = None
    
    @property
    @abstractmethod
    def vendor(self) -> RouterVendor:
        """Return the router vendor."""
        pass
    
    @property
    @abstractmethod
    def vendor_name(self) -> str:
        """Return human-readable vendor name."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the router is reachable and available.
        
        Returns:
            True if router responds to ping/HTTP, False otherwise
        """
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Authenticate with the router.
        
        Returns:
            True if authentication successful
            
        Raises:
            RouterAuthError: If authentication fails
            RouterConnectionError: If router is unreachable
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """End the session with the router."""
        pass
    
    @abstractmethod
    def get_connected_devices(self) -> List[RouterDevice]:
        """
        Get list of devices connected to the router.
        
        Returns:
            List of RouterDevice objects
            
        Raises:
            RouterAuthError: If not authenticated
            RouterConnectionError: If request fails
        """
        pass
    
    @abstractmethod
    def get_router_info(self) -> RouterInfo:
        """
        Get router information and status.
        
        Returns:
            RouterInfo object with router details
        """
        pass
    
    def is_connected(self) -> bool:
        """Check if currently connected to router."""
        return self._connected
    
    def _ensure_connected(self) -> None:
        """Ensure we have an active connection, connect if not."""
        if not self._connected:
            self.connect()


class BaseHTTPRouter(BaseRouter):
    """
    Base class for routers that use HTTP/HTTPS APIs.
    
    Provides common HTTP functionality like session management,
    request retry logic, and response parsing.
    """
    
    def __init__(self, credentials: RouterCredentials):
        super().__init__(credentials)
        self.base_url = self._build_base_url()
        self.timeout = 10
    
    def _build_base_url(self) -> str:
        """Build the base URL for API requests."""
        protocol = "https" if self.credentials.use_https else "http"
        port = self.credentials.port
        if port:
            return f"{protocol}://{self.credentials.ip_address}:{port}"
        return f"{protocol}://{self.credentials.ip_address}"
    
    def is_available(self) -> bool:
        """Check if router HTTP interface is reachable."""
        import requests
        try:
            response = requests.get(
                f"{self.base_url}/",
                timeout=5,
                allow_redirects=True
            )
            return response.status_code < 500
        except Exception:
            return False


class BaseSNMPRouter(BaseRouter):
    """
    Base class for routers that support SNMP.
    
    Provides SNMP functionality for routers that support it.
    """
    
    def __init__(self, credentials: RouterCredentials, snmp_community: str = "public"):
        super().__init__(credentials)
        self.snmp_community = snmp_community
    
    def is_available(self) -> bool:
        """Check if router SNMP is reachable."""
        # Would use pysnmp here
        return False  # Placeholder


class RouterCapability(Enum):
    """Router capabilities that implementations may support."""
    DEVICE_LIST = "device_list"
    BANDWIDTH_STATS = "bandwidth_stats"
    PORT_FORWARDING = "port_forwarding"
    VPN = "vpn"
    PARENTAL_CONTROLS = "parental_controls"
    GUEST_NETWORK = "guest_network"
    QOS = "qos"
    TRAFFIC_MONITORING = "traffic_monitoring"
    WPS = "wps"
