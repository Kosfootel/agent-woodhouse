"""
Router Vendor Implementations

Available implementations:
- ASUSRouter: ASUSWRT-based routers (GT6, RT-AX series, ZenWiFi)

Usage:
    from app.routers.implementations.asus import ASUSRouter
    from app.routers.base import RouterCredentials
    
    creds = RouterCredentials(username="admin", password="secret")
    router = ASUSRouter("192.168.50.1", creds)
"""

from .asus import ASUSRouter

__all__ = ["ASUSRouter"]
