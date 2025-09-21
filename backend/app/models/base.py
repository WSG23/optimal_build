"""Base model class."""

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Base model class."""
    
    __abstract__ = True
