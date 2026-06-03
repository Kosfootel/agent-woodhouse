from fastapi import FastAPI
from discovery import router as discovery_router

app = FastAPI(title="Vigil Home API", version="1.0.0")

# Include the discovery router
app.include_router(discovery_router)

@app.get("/")
async def root():
    return {"message": "Vigil Home API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)