"""
Vigil Tier A - Backend Security Service
FastAPI application for security scanning, logging, and anomaly detection.
"""

from fastapi import FastAPI
from app.routers import security, devices, alerts, stats, setup, discovery
from app.routers.events import router as events_router
from app.routers.admin import router as admin_router
from app.models import init_db

# Initialize database on startup
init_db()

app = FastAPI(
    title="Vigil Security Service",
    description="Home agent security platform - Tier A MVP (Rule-based security)",
    version="0.1.0"
)

# Include routers with /api prefix
app.include_router(security.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(setup.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "service": "Vigil Security",
        "tier": "A (MVP)",
        "status": "operational"
    }


@app.get("/health")
def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "database": "connected",
            "policy": "loaded"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
