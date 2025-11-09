"""Test database connection and basic operations."""

import asyncio

import structlog

from app.core.config import settings
from app.models.rkp import RefRule, RefSource
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

logger = structlog.get_logger(__name__)


async def test_database():
    """Test database connection and basic CRUD operations."""
    logger.info("db_test.start")

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
                landing_url="https://www.scdf.gov.sg/docs/default-source/scdf-library/fire-code/fire-code-2018.pdf",
            )
            session.add(source)
            await session.commit()
            await session.refresh(source)
            logger.info(
                "db_test.source_created", source_id=source.id, title=source.doc_title
            )

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
                review_status="approved",
            )
            session.add(rule)
            await session.commit()
            await session.refresh(rule)
            logger.info(
                "db_test.rule_created",
                rule_id=rule.id,
                parameter_key=rule.parameter_key,
                operator=rule.operator,
                value=rule.value,
                unit=rule.unit,
            )

            # Test 3: Query rules
            from sqlalchemy import select

            result = await session.execute(
                select(RefRule).where(RefRule.jurisdiction == "SG")
            )
            rules = result.scalars().all()
            logger.info("db_test.rules_found", count=len(rules))

            logger.info("db_test.success")

        except Exception as exc:
            logger.exception("db_test.failed", error=str(exc))
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_database())
