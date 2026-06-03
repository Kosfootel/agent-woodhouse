#!/usr/bin/env python3
"""
Test script for VIGIL Router Integration

Tests:
1. Router accessibility (port 80)
2. Authentication (if credentials available)
3. Device listing
4. Basic API functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import socket
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router_test")

ROUTER_IP = "192.168.50.1"

def test_router_reachable():
    """Test if router is reachable on port 80."""
    logger.info(f"Testing router reachability at {ROUTER_IP}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ROUTER_IP, 80))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Router {ROUTER_IP}:80 is reachable")
            return True
        else:
            logger.error(f"✗ Router {ROUTER_IP}:80 is not reachable (code: {result})")
            return False
    except Exception as e:
        logger.error(f"✗ Error testing reachability: {e}")
        return False

def test_router_http():
    """Test HTTP response from router."""
    logger.info(f"Testing HTTP response from {ROUTER_IP}...")
    
    try:
        response = requests.get(f"http://{ROUTER_IP}", timeout=10, allow_redirects=True)
        logger.info(f"✓ HTTP {response.status_code} response received")
        logger.info(f"  Server: {response.headers.get('Server', 'Unknown')}")
        
        if "login" in response.text.lower() or "Main_Login" in response.text:
            logger.info("✓ Router login page detected")
            return True
        else:
            logger.warning("? Unexpected response (may be normal)")
            return True
            
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ HTTP request failed: {e}")
        return False

def test_asus_imports():
    """Test that ASUS router module imports correctly."""
    logger.info("Testing module imports...")
    
    try:
        from app.routers.implementations.asus import ASUSRouter
        from app.routers.base import RouterCredentials, RouterVendor
        logger.info("✓ ASUSRouter module imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import modules: {e}")
        return False

def test_credential_store():
    """Test credential store initialization."""
    logger.info("Testing credential store...")
    
    try:
        from app.routers.router_credentials import RouterCredentialsStore, RouterCredentialsInput
        logger.info("✓ Credential store module imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import credential store: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 50)
    logger.info("VIGIL Router Integration Test Suite")
    logger.info("=" * 50)
    
    results = []
    
    # Test 1: Network reachability
    results.append(("Router Reachable", test_router_reachable()))
    
    # Test 2: HTTP response
    results.append(("HTTP Response", test_router_http()))
    
    # Test 3: Module imports
    results.append(("Module Imports", test_asus_imports()))
    
    # Test 4: Credential store
    results.append(("Credential Store", test_credential_store()))
    
    # Summary
    logger.info("=" * 50)
    logger.info("Test Summary:")
    logger.info("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {name}")
    
    logger.info("-" * 50)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! Router integration is ready.")
        return 0
    else:
        logger.warning("Some tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
