"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Building Compliance Platform API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "building-compliance-platform"}

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint."""
    return {"message": "API is working", "version": settings.VERSION}

# Include API routes
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/rules/test")
async def test_rules():
    """Test rules endpoint."""
    return {"message": "Rules API working"}

@api_router.get("/buildable/test")
async def test_buildable():
    """Test buildable endpoint."""
    return {"message": "Buildable API working"}

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
