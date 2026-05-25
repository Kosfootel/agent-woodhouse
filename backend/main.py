from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.discovery import router as discovery_router
from app.routers.events import router as events_router
from app.routers.alerts import router as alerts_router
from app.routers.devices import router as devices_router
from app.routers.discovery_scan import router as discovery_scan_router
from app.routers.admin import router as admin_router
from app.routers.agents import router as agents_router

app = FastAPI(title="Vigil Home API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(discovery_router)
app.include_router(events_router)
app.include_router(alerts_router)
app.include_router(devices_router)
app.include_router(discovery_scan_router)
app.include_router(admin_router)
app.include_router(agents_router)

@app.get("/")
async def root():
    return {
        "message": "Vigil Home API",
        "version": "1.0.0",
        "endpoints": [
            "/api/devices",
            "/api/alerts", 
            "/api/events",
            "/api/agents",
            "/api/discovery/scan",
            "/api/reset",
            "/api/health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
