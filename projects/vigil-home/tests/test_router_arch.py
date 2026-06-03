#!/usr/bin/env python3
import sys
sys.path.insert(0, 'app')
from routers.factory import RouterFactory
from routers.discovery import RouterDiscovery

print("Imports successful!")
print("Supported vendors:", [v.value for v in RouterFactory.get_supported_vendors()])

# Test discovery
discovery = RouterDiscovery()
result = discovery.discover("192.168.50.1")
print(f"Detected vendor: {result.vendor.value} (confidence: {result.confidence:.2f})")
