"""
Router Integration Module for vigil-home

Provides router discovery, API communication, and device synchronization.
"""

from .router_integration import (
    # Data models
    RouterDevice,
    RouterInfo,
    
    # Core classes
    RouterDiscovery,
    SecureCredentialManager,
    DeviceSyncService,
    
    # API Clients
    RouterAPIClient,
    ASUSWRTClient,
)

__version__ = "1.0.0"
__all__ = [
    "RouterDevice",
    "RouterInfo",
    "RouterDiscovery",
    "SecureCredentialManager",
    "DeviceSyncService",
    "RouterAPIClient",
    "ASUSWRTClient",
]
