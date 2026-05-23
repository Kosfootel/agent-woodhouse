"""
Router Factory for Vigil

Creates appropriate router instances based on vendor detection.
"""

import logging
from typing import Optional, Type

from .base import (
    BaseRouter,
    RouterVendor,
    RouterCredentials,
    RouterException,
)
from .discovery import RouterDiscovery

# Import implementations (will be added as they're created)
try:
    from .implementations.asus import ASUSRouter
    ASUS_AVAILABLE = True
except ImportError:
    ASUS_AVAILABLE = False

try:
    from .implementations.generic import GenericRouter
    GENERIC_AVAILABLE = True
except ImportError:
    GENERIC_AVAILABLE = False


logger = logging.getLogger(__name__)


class RouterFactory:
    """
    Factory for creating router instances.
    
    Automatically detects router vendor and returns appropriate
    implementation. Falls back to generic implementation for
    unsupported vendors.
    """
    
    # Mapping of vendors to their implementations
    _implementations: dict[RouterVendor, Type[BaseRouter]] = {}
    
    @classmethod
    def _register_implementations(cls):
        """Register available router implementations."""
        if ASUS_AVAILABLE:
            cls._implementations[RouterVendor.ASUS] = ASUSRouter
        
        # Generic fallback is always available
        if GENERIC_AVAILABLE:
            cls._implementations[RouterVendor.GENERIC] = GenericRouter
    
    @classmethod
    def create(
        cls,
        credentials: RouterCredentials,
        vendor: Optional[RouterVendor] = None,
        auto_detect: bool = True
    ) -> BaseRouter:
        """
        Create router instance for given credentials.
        
        Args:
            credentials: Router authentication credentials
            vendor: Specific vendor (optional, will auto-detect if None)
            auto_detect: Whether to auto-detect vendor if not specified
            
        Returns:
            BaseRouter instance for detected/specified vendor
            
        Raises:
            RouterException: If router cannot be created
        """
        cls._register_implementations()
        
        # Auto-detect vendor if not specified
        if vendor is None and auto_detect:
            discovery = RouterDiscovery()
            result = discovery.discover(credentials.ip_address)
            vendor = result.vendor
            logger.info(
                f"Auto-detected router vendor: {vendor.value} "
                f"(confidence: {result.confidence:.2f}, method: {result.method})"
            )
        
        # Default to generic if still not determined
        if vendor is None:
            vendor = RouterVendor.GENERIC
            logger.warning("Could not detect router vendor, using generic implementation")
        
        # Get implementation class
        impl_class = cls._implementations.get(vendor)
        
        if impl_class is None:
            logger.warning(
                f"No implementation for {vendor.value}, falling back to generic"
            )
            impl_class = cls._implementations.get(RouterVendor.GENERIC)
        
        if impl_class is None:
            raise RouterException(
                f"No router implementation available for vendor: {vendor.value}"
            )
        
        logger.info(f"Creating {impl_class.__name__} for {credentials.ip_address}")
        return impl_class(credentials)
    
    @classmethod
    def create_from_ip(
        cls,
        ip_address: str,
        username: str,
        password: str,
        **kwargs
    ) -> BaseRouter:
        """
        Convenience method to create router from IP and credentials.
        
        Args:
            ip_address: Router IP address
            username: Router admin username
            password: Router admin password
            **kwargs: Additional credential options (use_https, port)
            
        Returns:
            BaseRouter instance
        """
        credentials = RouterCredentials(
            username=username,
            password=password,
            ip_address=ip_address,
            **kwargs
        )
        return cls.create(credentials)
    
    @classmethod
    def get_supported_vendors(cls) -> list[RouterVendor]:
        """Get list of supported router vendors."""
        cls._register_implementations()
        return list(cls._implementations.keys())
    
    @classmethod
    def is_vendor_supported(cls, vendor: RouterVendor) -> bool:
        """Check if a vendor has an implementation."""
        cls._register_implementations()
        return vendor in cls._implementations


def get_connected_devices(
    router_ip: str,
    username: str,
    password: str,
    use_https: bool = False,
    **kwargs
) -> list[dict]:
    """
    Convenience function to get devices from router.
    
    This is the main entry point for device discovery.
    
    Args:
        router_ip: Router IP address
        username: Router admin username
        password: Router admin password
        use_https: Whether to use HTTPS
        **kwargs: Additional options
        
    Returns:
        List of device dictionaries
    """
    logger.info(f"Getting devices from router at {router_ip}")
    
    try:
        # Create router instance
        router = RouterFactory.create_from_ip(
            router_ip,
            username,
            password,
            use_https=use_https,
            **kwargs
        )
        
        # Check if router is available
        if not router.is_available():
            logger.warning(f"Router at {router_ip} is not reachable")
            return []
        
        # Connect and get devices
        router.connect()
        devices = router.get_connected_devices()
        router.disconnect()
        
        logger.info(f"Found {len(devices)} devices from {router.vendor_name}")
        return [d.to_dict() for d in devices]
        
    except Exception as e:
        logger.error(f"Failed to get devices: {e}")
        # Fall back to generic ARP scanning
        logger.info("Falling back to ARP scanning")
        return _get_devices_from_arp_fallback(router_ip)


def _get_devices_from_arp_fallback(router_ip: str) -> list[dict]:
    """Fallback to ARP scanning if router API fails."""
    import subprocess
    import re
    from datetime import datetime
    
    devices = []
    try:
        result = subprocess.run(
            ["ip", "neigh", "show"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Get network prefix from router IP
        parts = router_ip.split(".")
        router_network = ".".join(parts[:3])
        
        for line in result.stdout.strip().split("\n"):
            # Parse: 192.168.50.24 dev enP7s7 lladdr 00:e0:4c:be:fa:cc REACHABLE
            match = re.match(
                r'(\d+\.\d+\.\d+\.\d+)\s+\w+\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)',
                line
            )
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                # Only include devices on same network, exclude router itself
                if ip.startswith(router_network) and ip != router_ip:
                    devices.append({
                        "mac_address": mac.lower().replace("-", ":"),
                        "ip_address": ip,
                        "hostname": f"Device-{mac.replace(':', '')[-6:].upper()}",
                        "connection_type": "unknown",
                        "is_online": True,
                        "last_seen": datetime.now().isoformat(),
                        "vendor": None,
                    })
        
        logger.info(f"ARP fallback found {len(devices)} devices")
        
    except Exception as e:
        logger.error(f"ARP fallback failed: {e}")
    
    return devices
