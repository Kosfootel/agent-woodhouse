import sys

# Read current main.py
with open('/home/erik-ross/vigil/backend/app/main.py', 'r') as f:
    content = f.read()

if 'def classify_device' in content:
    print('classify endpoint already exists in main.py')
    sys.exit(0)

# Add the classify endpoint before the root endpoint
endpoint_code = '''

from pydantic import BaseModel

class ClassificationResponse(BaseModel):
    mac: str
    device_type: str
    confidence: float
    method: str

@app.get("/classify/{mac}")
def classify_device(mac: str):
    """Classify a device by MAC address using OUI and heuristics."""
    oui = mac.replace(":", "")[:6].upper() if ":" in mac else mac[:6].upper()
    
    # OUI-based classification
    oui_map = {
        "30C599": ("server", 0.7),
        "A86E84": ("router", 0.8),
        "406C8F": ("server", 0.7),
        "C8A362": ("workstation", 0.6),
        "002381": ("computer", 0.5),
        "00E04C": ("iot", 0.5),
    }
    
    if oui in oui_map:
        device_type, confidence = oui_map[oui]
        return ClassificationResponse(
            mac=mac,
            device_type=device_type,
            confidence=confidence,
            method="heuristic"
        )
    
    return ClassificationResponse(
        mac=mac,
        device_type="unknown",
        confidence=0.0,
        method="unknown"
    )

'''

# Find where to insert (before @app.get("/"))
insert_point = content.find('@app.get("/")')
if insert_point == -1:
    print('Could not find insertion point')
    sys.exit(1)

content = content[:insert_point] + endpoint_code + content[insert_point:]

with open('/home/erik-ross/vigil/backend/app/main.py', 'w') as f:
    f.write(content)

print('Added /classify/{mac} endpoint to main.py')
