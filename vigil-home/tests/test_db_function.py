import sys
sys.path.insert(0, '/app')

from app.models import get_db, Device

# Test the get_db function
db_gen = get_db()
db = next(db_gen)

try:
    count = db.query(Device).count()
    print(f"Device count via get_db: {count}")
    
    devices = db.query(Device).limit(3).all()
    for d in devices:
        print(f"  - {d.hostname} ({d.mac})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
