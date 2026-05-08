from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import build, settings, poses

app = FastAPI(title="Block Robot IDE", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API routers
app.include_router(build.router, prefix="/api", tags=["build"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(poses.router, prefix="/api", tags=["poses"])

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    """Serve the main IDE page"""
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Block Robot IDE is running"}
