"""Vigil Tier A - Backend Security Service
FastAPI application for security scanning, logging, and anomaly detection.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import security, devices, alerts, stats, setup, agents

app = FastAPI(
    title="Vigil Security Service",
    description="Home agent security platform - Tier A MVP (Rule-based security)",
    version="0.1.0"
)

# Configure CORS - allow dashboard origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://192.168.50.30:8085", "http://localhost:3000"],
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
app.include_router(agents.router, prefix="/api")

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
