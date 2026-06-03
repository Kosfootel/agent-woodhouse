import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True)
    mac = Column(String, unique=True)
    ip = Column(String)
    hostname = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    trust_score = Column(Float, default=50.0)
    containment_status = Column(String, default="observing")
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    online = Column(Boolean, default=True)

engine = create_engine('sqlite:///data/vigil.db')
Session = sessionmaker(bind=engine)
db = Session()

try:
    count = db.query(Device).count()
    print(f"Device count: {count}")
    
    devices = db.query(Device).all()
    print(f"Devices returned: {len(devices)}")
    
    for d in devices:
        print(f"  - {d.hostname} ({d.mac})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
