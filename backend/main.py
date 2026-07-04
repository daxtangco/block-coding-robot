import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import build, settings, poses, detect, teach, programs, train, camera

# Fix Windows asyncio subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
app.include_router(programs.router, prefix="/api", tags=["programs"])
app.include_router(detect.router, prefix="/api", tags=["detect"])
app.include_router(teach.router, prefix="/api", tags=["teach"])
app.include_router(train.router, prefix="/api", tags=["train"])
app.include_router(camera.router, prefix="/api", tags=["camera"])

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    """Serve the main IDE page"""
    return FileResponse("frontend/index.html")

@app.on_event("startup")
async def warmup_detector():
    """Pre-load the detection model in a background thread so the first
    Vision-tab frame isn't hit with a ~3.5s cold start."""
    import threading
    from backend.services import detection, teachable
    threading.Thread(target=detection.warmup, daemon=True).start()
    threading.Thread(target=teachable.warmup, daemon=True).start()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Block Robot IDE is running"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Block Robot IDE server...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="127.0.0.1", port=8000)
