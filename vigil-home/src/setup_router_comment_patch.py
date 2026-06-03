#!/usr/bin/env python3
"""
Patch to comment out router integration in setup.py
This removes the router credential flow and focuses on ARP-based discovery
"""

import re

# Read the current setup.py
with open('/home/erik-ross/projects/vigil-home/backend/app/routers/setup.py', 'r') as f:
    content = f.read()

# Comment out the router imports section
content = content.replace(
    '# New router architecture imports\nfrom app.routers.factory import RouterFactory, get_connected_devices\nfrom app.routers.discovery import RouterDiscovery\nfrom app.routers.base import RouterException, RouterAuthError, RouterConnectionError',
    '''# Router integration commented out - future enhancement when Vigil is embedded in router
# See docs/ASUS_RESEARCH.md for details
# from app.routers.factory import RouterFactory, get_connected_devices
# from app.routers.discovery import RouterDiscovery
# from app.routers.base import RouterException, RouterAuthError, RouterConnectionError
from app.routers.implementations.generic import GenericRouter'''
)

# Comment out the router credential saving (not needed for ARP)
content = content.replace(
    '''def save_router_credentials(ip: str, username: str, password: str, db: Session):
    """Save encrypted router credentials to database."""
    # Check if we already have credentials for this router
    existing = db.query(RouterConfig).filter(RouterConfig.router_ip == ip).first()
    
    if existing:
        existing.username = username
        existing.password = password  # In production, encrypt this
        existing.updated_at = datetime.utcnow()
    else:
        config = RouterConfig(
            router_ip=ip,
            username=username,
            password=password,  # In production, encrypt this
            is_active=True
        )
        db.add(config)
    
    db.commit()''',
    '''# Router credential saving commented out - future enhancement
# def save_router_credentials(ip: str, username: str, password: str, db: Session):
#     """Save encrypted router credentials to database."""
#     pass'''
)

# Replace the connect endpoint to use ARP only
connect_replacement = '''@router.post("/setup/connect", response_model=ConnectResponse)
def connect_router(credentials: RouterCredentials, db: Session = Depends(get_db)):
    """
    Connect to network and discover devices via ARP scanning.
    
    Router API integration is a future enhancement - see docs/ASUS_RESEARCH.md
    For now, uses ARP table scanning which doesn't require router credentials.
    """
    try:
        logger.info(f"Starting device discovery via ARP scanning")
        
        # Use ARP-based discovery (no router credentials needed)
        from app.routers.implementations.generic import GenericRouter
        router_impl = GenericRouter(credentials.ip, credentials.username, credentials.password)
        devices_data = router_impl.get_devices()
        
        if not devices_data:
            return ConnectResponse(
                success=False,
                devices_found=0,
                message="No devices found on network"
            )
        
        # Import devices into database
        imported_count = import_devices_from_router(devices_data, db)
        
        logger.info(f"Successfully imported {imported_count} devices via ARP")
        
        return ConnectResponse(
            success=True,
            devices_found=imported_count,
            message=f"Discovered and imported {imported_count} devices"
        )
        
    except Exception as e:
        logger.error(f"Error during device discovery: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return ConnectResponse(
            success=False,
            devices_found=0,
            message=f"Error: {str(e)}"
        )'''

# Find and replace the connect_router function
pattern = r'@router\.post\("/setup/connect".*?\n\n\n@router\.get\("/setup/status"'
content = re.sub(pattern, connect_replacement + '\n\n\n@router.get("/setup/status"', content, flags=re.DOTALL)

# Write the modified file
with open('/home/erik-ross/projects/vigil-home/backend/app/routers/setup.py', 'w') as f:
    f.write(content)

print("Patched setup.py to comment out router integration")
print("- Router imports commented out")
print("- Connect endpoint now uses ARP only")
print("- Router credential saving disabled")
