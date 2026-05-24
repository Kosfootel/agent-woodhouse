# Helper to get value from dict or dataclass
from dataclasses import is_dataclass

def get_attr(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict):
        return obj.get(key, default)
    return default

# Update import_devices_from_router to use get_attr
def import_devices_from_router(devices_data: list, db: Session) -> int:
    from dataclasses import is_dataclass
    
    count = 0
    
    for device_data in devices_data:
        mac = get_attr(device_data, 'mac_address', '').upper()
        if not mac:
            continue
        
        existing = db.query(Device).filter(Device.mac == mac).first()
        
        if existing:
            existing.ip = get_attr(device_data, 'ip_address', existing.ip)
            existing.hostname = get_attr(device_data, 'hostname') or existing.hostname
            existing.last_seen = datetime.utcnow()
            existing.containment_status = 'observing'
        else:
            hostname = get_attr(device_data, 'hostname', '').lower()
            device_type = 'unknown'
            
            if any(kw in hostname for kw in ['phone', 'iphone', 'pixel', 'samsung']):
                device_type = 'phone'
            elif any(kw in hostname for kw in ['macbook', 'laptop', 'desktop', 'pc']):
                device_type = 'laptop'
            elif any(kw in hostname for kw in ['tv', 'speaker', 'homepod', 'echo', 'nest']):
                device_type = 'iot'
            elif any(kw in hostname for kw in ['router', 'gateway']):
                device_type = 'router'
            
            new_device = Device(
                mac=mac,
                ip=get_attr(device_data, 'ip_address', '0.0.0.0'),
                hostname=get_attr(device_data, 'hostname', 'Unknown Device'),
                device_type=device_type,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                status='online',
                trust_score=0.5,
                containment_status='observing'
            )
            db.add(new_device)
            count += 1
    
    db.commit()
    return count
