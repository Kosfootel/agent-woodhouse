import sys

# Read current main.py
with open('/home/erik-ross/vigil/backend/app/main.py', 'r') as f:
    content = f.read()

if 'def mark_as_trusted_baseline' in content:
    print('baseline endpoint already exists in main.py')
    sys.exit(0)

# Add imports and endpoint after the existing imports
endpoint_code = '''

# Additional imports for baseline endpoint
from fastapi import Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import get_db, Device

class BaselineRequest(BaseModel):
    mac: str
    ip: Optional[str] = None
    hostname: Optional[str] = None
    device_type: Optional[str] = None

@app.post("/baseline")
def mark_as_trusted_baseline(
    request: BaselineRequest,
    db: Session = Depends(get_db)
):
    """Mark a device as trusted. Sets trust_score to 1.0."""
    device = db.query(Device).filter(Device.mac == request.mac).first()
    
    if not device:
        device = Device(
            mac=request.mac,
            ip=request.ip,
            hostname=request.hostname,
            device_type=request.device_type,
            trust_score=1.0,
            containment_status="trusted",
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            online=True,
            is_known=True
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    else:
        device.trust_score = 1.0
        device.containment_status = "trusted"
        device.is_known = True
        if request.ip:
            device.ip = request.ip
        if request.hostname:
            device.hostname = request.hostname
        if request.device_type:
            device.device_type = request.device_type
        db.commit()
        db.refresh(device)
    
    return {
        "id": device.id,
        "mac": device.mac,
        "ip": device.ip,
        "hostname": device.hostname,
        "nickname": device.nickname,
        "trust_score": device.trust_score,
        "containment_status": device.containment_status,
        "message": "Device marked as trusted"
    }

'''

# Find where to insert (before @app.get("/"))
insert_point = content.find('@app.get("/")')
if insert_point == -1:
    print('Could not find insertion point')
    sys.exit(1)

content = content[:insert_point] + endpoint_code + content[insert_point:]

with open('/home/erik-ross/vigil/backend/app/main.py', 'w') as f:
    f.write(content)

print('Added /baseline endpoint to main.py')
