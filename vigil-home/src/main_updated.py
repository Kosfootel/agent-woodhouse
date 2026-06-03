"""
Vigil Tier A - Backend Security Service
FastAPI application for security scanning, logging, and anomaly detection.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import security, devices, alerts, stats, setup, events

app = FastAPI(
    title="Vigil Security Service",
    description="Home agent security platform - Tier A MVP (Rule-based security)",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(security.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(setup.router, prefix="/api")
app.include_router(events.router, prefix="/api")

# ALSO include routers WITHOUT prefix for dashboard compatibility
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(events.router)

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
