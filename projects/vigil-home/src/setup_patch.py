import re

with open('/home/erik-ross/vigil/backend/app/routers/setup.py', 'r') as f:
    content = f.read()

# Replace the old get_setup_status function
old_func = '''@router.get("/setup/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Get the current setup status.
    """
    # Check if router is configured
    router_config = db.query(Device).filter(Device.mac == "ROUTER_CONFIG").first()
    router_connected = router_config is not None
    
    # Count devices
    device_count = db.query(Device).filter(Device.mac != "ROUTER_CONFIG").count()
    
    return SetupStatus(
        is_setup_complete=router_connected and device_count > 0,
        router_connected=router_connected,
        device_count=device_count
    )'''

new_func = '''@router.get("/setup/status", response_model=SetupStatus)
def get_setup_status(db: Session = Depends(get_db)):
    """
    Get the current setup status.
    """
    # Count real devices (exclude config markers)
    device_count = db.query(Device).filter(Device.mac != "ROUTER_CONFIG").count()
    
    # Setup is complete if we have devices imported
    return SetupStatus(
        is_setup_complete=device_count > 0,
        router_connected=device_count > 0,
        device_count=device_count
    )'''

content = content.replace(old_func, new_func)

with open('/home/erik-ross/vigil/backend/app/routers/setup.py', 'w') as f:
    f.write(content)

print('Patched setup.py')
