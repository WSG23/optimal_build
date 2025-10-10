"""Projects API with CRUD operations."""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.jwt_auth import TokenData, get_current_user
from app.utils.db import session_dependency
from pydantic import BaseModel, Field

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./projects.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

router = APIRouter(prefix="/projects", tags=["Projects"])


# Database Model
class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(
        String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:8]}"
    )
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    project_type = Column(String, nullable=True)
    status = Column(String, default="planning")
    budget = Column(Float, nullable=True)
    owner_email = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
get_db = session_dependency(SessionLocal)


# Pydantic models
class ProjectCreate(BaseModel):
    """Project creation model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    project_type: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="planning")
    budget: Optional[float] = Field(None, gt=0)


class ProjectUpdate(BaseModel):
    """Project update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    project_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    budget: Optional[float] = Field(None, gt=0)


class ProjectResponse(BaseModel):
    """Project response model."""

    id: str
    name: str
    description: Optional[str]
    location: Optional[str]
    project_type: Optional[str]
    status: str
    budget: Optional[float]
    owner_email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# API Endpoints
@router.post("/create", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated user."""

    # Create new project with user's email
    db_project = ProjectDB(
        name=project_data.name,
        description=project_data.description,
        location=project_data.location,
        project_type=project_data.project_type,
        status=project_data.status,
        budget=project_data.budget,
        owner_email=current_user.email,  # Use authenticated user's email
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return ProjectResponse.model_validate(db_project)


@router.get("/list", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """List all active projects (no auth required for viewing)."""
    projects = (
        db.query(ProjectDB).filter(ProjectDB.is_active).offset(skip).limit(limit).all()
    )

    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific project by ID."""
    project = (
        db.query(ProjectDB)
        .filter(ProjectDB.id == project_id, ProjectDB.owner_email == current_user.email)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a project (must be owner)."""
    project = (
        db.query(ProjectDB)
        .filter(ProjectDB.id == project_id, ProjectDB.owner_email == current_user.email)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(project)

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete a project (marks as inactive) - must be owner."""
    project = (
        db.query(ProjectDB)
        .filter(ProjectDB.id == project_id, ProjectDB.owner_email == current_user.email)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_active = False
    project.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Project deleted successfully", "project_id": project_id}


@router.get("/stats/summary")
async def get_project_stats(db: Session = Depends(get_db)):
    """Get project statistics (temporarily without auth for testing)."""
    # Temporarily disabled authentication for testing
    # current_user: TokenData = Depends(get_current_user)
    # ProjectDB.owner_email == current_user.email,
    projects = db.query(ProjectDB).filter(ProjectDB.is_active).all()

    total_budget = sum(p.budget for p in projects if p.budget)
    status_counts = {}
    type_counts = {}

    for project in projects:
        status_counts[project.status] = status_counts.get(project.status, 0) + 1
        if project.project_type:
            type_counts[project.project_type] = (
                type_counts.get(project.project_type, 0) + 1
            )

    active_count = (
        status_counts.get("planning", 0)
        + status_counts.get("approval", 0)
        + status_counts.get("construction", 0)
    )

    return {
        "total_projects": len(projects),
        "total_budget": total_budget,
        "active_projects": active_count,
        "completed_projects": status_counts.get("completed", 0),
        "status_breakdown": status_counts,
        "type_breakdown": type_counts,
        "recent_projects": [
            {"id": p.id, "name": p.name, "created_at": p.created_at}
            for p in sorted(projects, key=lambda x: x.created_at, reverse=True)[:5]
        ],
    }
