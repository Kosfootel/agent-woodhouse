"""
Vigil Router Abstraction Layer

Provides a unified interface for multiple router vendors and models.
Supports ASUS, TP-Link, Netgear, Ubiquiti, and generic fallback implementations.

Usage:
    from app.routers.implementations.asus import ASUSRouter
    from app.routers.base import RouterCredentials
    
    credentials = RouterCredentials(username="admin", password="secret")
    router = ASUSRouter("192.168.50.1", credentials)
    
    if router.connect():
        devices = router.get_connected_devices()
        info = router.get_router_info()
"""

from app.routers.base import (
    RouterInterface,
    RouterCredentials,
    RouterInfo,
    RouterDevice,
    RouterAuthError,
    RouterConnectionError,
    RouterNotSupportedError,
)

from app.routers.implementations.asus import ASUSRouter

__all__ = [
    "RouterInterface",
    "RouterCredentials", 
    "RouterInfo",
    "RouterDevice",
    "RouterAuthError",
    "RouterConnectionError",
    "RouterNotSupportedError",
    "ASUSRouter",
]