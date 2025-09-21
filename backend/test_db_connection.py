"""Test database connection and basic operations."""

import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.models.rkp import RefSource, RefRule

async def test_database():
    """Test database connection and basic CRUD operations."""
    print("Testing database connection...")
    
    # Create engine and session
    engine = create_async_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Test 1: Create a source
            source = RefSource(
                jurisdiction="SG",
                authority="SCDF", 
                topic="fire",
                doc_title="Fire Code 2018",
                landing_url="https://www.scdf.gov.sg/docs/default-source/scdf-library/fire-code/fire-code-2018.pdf"
            )
            session.add(source)
            await session.commit()
            await session.refresh(source)
            print(f"✅ Created source: {source.id} - {source.doc_title}")
            
            # Test 2: Create a rule
            rule = RefRule(
                source_id=source.id,
                jurisdiction="SG",
                authority="SCDF",
                topic="fire", 
                parameter_key="egress.corridor.min_width_mm",
                operator=">=",
                value="1200",
                unit="mm",
                clause_ref="4.2.1",
                review_status="approved"
            )
            session.add(rule)
            await session.commit()
            await session.refresh(rule)
            print(f"✅ Created rule: {rule.id} - {rule.parameter_key} {rule.operator} {rule.value}{rule.unit}")
            
            # Test 3: Query rules
            from sqlalchemy import select
            result = await session.execute(
                select(RefRule).where(RefRule.jurisdiction == "SG")
            )
            rules = result.scalars().all()
            print(f"✅ Found {len(rules)} Singapore rules in database")
            
            print("🎉 Database integration successful!")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database())
