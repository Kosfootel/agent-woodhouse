#!/usr/bin/env python3
"""
Test script for the new device discovery endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_discover_device():
    """Test the device discovery endpoint."""
    print("Testing device discovery...")
    
    # Test data
    device_id = "test-device-001"
    payload = {
        "ip_address": "192.168.1.1",
        "mac_address": "00:11:22:33:44:55"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/devices/{device_id}/discover", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_discovery_history():
    """Test getting discovery history."""
    print("\nTesting discovery history...")
    
    device_id = "test-device-001"
    
    try:
        response = requests.get(f"{BASE_URL}/api/devices/{device_id}/discovery-history")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_set_nickname():
    """Test setting device nickname."""
    print("\nTesting setting nickname...")
    
    device_id = "test-device-001"
    payload = {
        "nickname": "My Test Device"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/devices/{device_id}/nickname", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_set_device_type():
    """Test setting device type."""
    print("\nTesting setting device type...")
    
    device_id = "test-device-001"
    payload = {
        "device_type": "smartphone"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/devices/{device_id}/type", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing device discovery endpoints...")
    
    # Note: These tests require the FastAPI server to be running
    # You would typically run this after starting the server with:
    # uvicorn main:app --reload
    
    print("Please ensure your FastAPI server is running before testing.")
    print("Example: uvicorn main:app --reload")