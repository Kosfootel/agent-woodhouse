# Patch main.py to use PORT env var
import os

port = int(os.getenv("PORT", "8000"))

# Read current main.py
with open("/home/erik-ross/vigil/backend/app/main.py", "r") as f:
    content = f.read()

# Replace hardcoded port with env var
content = content.replace(
    'uvicorn.run(app, host="0.0.0.0", port=8000)',
    'port = int(os.getenv("PORT", "8000"))\n    uvicorn.run(app, host="0.0.0.0", port=port)'
)

# Also need to import os if not already there
if "import os" not in content:
    content = "import os\n" + content

with open("/home/erik-ross/vigil/backend/app/main.py", "w") as f:
    f.write(content)

print("Patched main.py")
