"""
Router Credential Setup - Simplified for Commercial Deployment

This module provides secure router credential submission during Vigil setup.
Credentials are encrypted and stored securely without attempting router auth
at setup time - authentication happens later when the router client is used.
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db, Device
from app.utils.crypto import encrypt_password

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"])

# Temporary setup session storage
_setup_sessions: Dict[str, Dict] = {}


class RouterCredentialsInput(BaseModel):
    """Secure input model for router credentials"""
    router_ip: str = Field(default="192.168.50.1", description="Router IP address")
    admin_username: str = Field(..., description="Router admin username")
    admin_password: str = Field(..., description="Router admin password", min_length=1)
    vendor: Optional[str] = Field(default=None, description="Router vendor")


def create_setup_session() -> str:
    """Create a secure setup session"""
    session_id = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    _setup_sessions[session_id] = {
        "session_id": session_id,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "step": "discover",
        "data": {}
    }
    return session_id


@router.post("/setup/session")
async def create_new_setup_session():
    """Create a new setup session"""
    session_id = create_setup_session()
    return {
        "session_id": session_id,
        "expires_at": _setup_sessions[session_id]["expires_at"]
    }


@router.get("/setup/router-status")
async def check_router_setup_status(
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Check if router credentials are configured"""
    router_config = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    
    # Get vendor from hostname if exists
    vendor = "unknown"
    if router_config and router_config.hostname and router_config.hostname.startswith("ROUTER:"):
        vendor = router_config.hostname.split(":", 1)[1]
    
    return {
        "configured": router_config is not None,
        "router_ip": router_config.ip if router_config else "192.168.50.1",
        "vendor": vendor if router_config else None,
        "message": "Router credentials configured" if router_config else "Router credentials required",
        "setup_required": router_config is None
    }


@router.post("/setup/router-credentials")
async def submit_router_credentials(
    credentials: RouterCredentialsInput,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Secure endpoint for router credential submission during setup
    
    - Validates input
    - Encrypts and stores credentials securely
    - Returns success/failure without exposing credentials
    """
    logger.info(f"Received router credentials for {credentials.router_ip}")
    
    # Validate session if provided
    if session_id and session_id not in _setup_sessions:
        raise HTTPException(status_code=400, detail="Invalid or expired setup session")
    
    try:
        # Validate IP address format
        import ipaddress
        try:
            ipaddress.ip_address(credentials.router_ip)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid IP address format")
        
        # Validate credentials are provided
        if not credentials.admin_username or not credentials.admin_password:
            raise HTTPException(status_code=400, detail="Username and password are required")
        
        # Encrypt password for storage
        encrypted_password = encrypt_password(credentials.admin_password)
        
        # Determine vendor
        vendor = credentials.vendor or "unknown"
        
        # Check if router config already exists
        existing = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
        if existing:
            db.delete(existing)
        
        # Store router configuration in database
        router_config = Device(
            mac="ROUTER_CONFIG",
            ip=credentials.router_ip,
            hostname=f"ROUTER:{vendor}",
            nickname=credentials.admin_username,  # Store username in nickname
            vendor=vendor,
            device_type="router",
            containment_status="trusted",
            trust_score=100.0,
            discovery_method="manual_setup",
            metadata=f"encrypted_password:{encrypted_password}"
        )
        
        db.add(router_config)
        db.commit()
        
        # Update setup session
        if session_id:
            _setup_sessions[session_id]["step"] = "router_auth"
            _setup_sessions[session_id]["data"]["router_configured"] = True
            _setup_sessions[session_id]["data"]["router_vendor"] = vendor
            _setup_sessions[session_id]["data"]["router_ip"] = credentials.router_ip
        
        logger.info(f"Router credentials stored securely for {credentials.router_ip}")
        
        return {
            "status": "success",
            "message": "Router credentials stored securely",
            "router": {
                "ip": credentials.router_ip,
                "vendor": vendor,
                "model": "Configured",
                "configured": True
            },
            "next_step": "/setup/complete"
        }
           
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing router credentials: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to process router credentials")


@router.delete("/setup/router-credentials")
async def delete_router_credentials(
    db: Session = Depends(get_db)
):
    """Delete stored router credentials"""
    router_config = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    if router_config:
        db.delete(router_config)
        db.commit()
        return {"status": "deleted", "message": "Router credentials removed"}
    return {"status": "not_found", "message": "No router credentials found"}
