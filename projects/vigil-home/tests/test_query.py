import sys
sys.path.insert(0, '/home/erik-ross/projects/vigil-home/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Device

engine = create_engine('sqlite:///backend/data/vigil.db')
Session = sessionmaker(bind=engine)
db = Session()

try:
    count = db.query(Device).count()
    print(f"Device count: {count}")
    
    devices = db.query(Device).all()
    print(f"Devices returned: {len(devices)}")
    
    for d in devices[:2]:
        print(f"  - {d.hostname} ({d.mac})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
