"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_session, engine
from app.models.rkp import RefRule

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting Building Compliance Platform")
    logger.info(f"📊 Database URL: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
    
    yield
    
    # Shutdown
    await engine.dispose()
    logger.info("⬇️ Shutting down Building Compliance Platform")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
    return {
        "message": "Building Compliance Platform API", 
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint with database connectivity."""
    try:
        # Test database connection
        result = await session.execute(select(RefRule).limit(1))
        rule_count_result = await session.execute(select(RefRule))
        rule_count = len(list(rule_count_result.scalars().all()))
        
        return {
            "status": "healthy",
            "service": "building-compliance-platform",
            "database": "connected",
            "rules_count": rule_count
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "degraded",
            "service": "building-compliance-platform", 
            "database": "disconnected",
            "error": str(e)
        }


@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint."""
    return {"message": "API is working", "version": settings.VERSION}


@app.get("/api/v1/rules/test")
async def test_rules():
    """Test rules endpoint."""
    return {"message": "Rules API working"}


@app.get("/api/v1/rules/count")
async def rules_count(session: AsyncSession = Depends(get_session)):
    """Get count of rules in database."""
    try:
        result = await session.execute(select(RefRule))
        rules = list(result.scalars().all())
        
        # Group by authority
        by_authority = {}
        for rule in rules:
            auth = rule.authority
            if auth not in by_authority:
                by_authority[auth] = 0
            by_authority[auth] += 1
            
        return {
            "total_rules": len(rules),
            "by_authority": by_authority,
            "sample_rule": {
                "parameter_key": rules[0].parameter_key if rules else None,
                "value": rules[0].value if rules else None,
                "unit": rules[0].unit if rules else None
            } if rules else None
        }
    except Exception as e:
        logger.error(f"Failed to count rules: {e}")
        return {"error": str(e)}


@app.get("/api/v1/database/status")
async def database_status(session: AsyncSession = Depends(get_session)):
    """Get database status and table information."""
    try:
        from sqlalchemy import text
        
        # Get table list
        tables_result = await session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tables = [row[0] for row in tables_result.fetchall()]
        
        # Get rules count by topic
        rules_result = await session.execute(select(RefRule))
        rules = list(rules_result.scalars().all())
        
        by_topic = {}
        for rule in rules:
            topic = rule.topic
            if topic not in by_topic:
                by_topic[topic] = 0
            by_topic[topic] += 1
        
        return {
            "database_connected": True,
            "tables": sorted(tables),
            "rules_by_topic": by_topic,
            "total_rules": len(rules)
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
