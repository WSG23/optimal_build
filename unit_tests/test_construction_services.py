"""Unit tests for Phase 2G Construction services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal
from datetime import date

from app.services.construction.project_manager import ConstructionProjectManager
from app.services.construction.construction_finance import ConstructionFinanceService
from app.schemas.construction import ContractorCreate, DrawdownRequestCreate
from app.models.construction import ContractorType

@pytest.mark.asyncio
async def test_create_contractor():
    session = AsyncMock()
    service = ConstructionProjectManager(session)

    payload = ContractorCreate(
        project_id=uuid4(),
        company_name="Test Builder",
        contractor_type=ContractorType.GENERAL_CONTRACTOR,
        contract_value=Decimal("100000.00")
    )

    contractor = await service.create_contractor(payload)

    assert contractor.company_name == "Test Builder"
    assert session.add.called
    assert session.commit.called
    assert session.refresh.called

@pytest.mark.asyncio
async def test_create_drawdown():
    session = AsyncMock()
    service = ConstructionFinanceService(session)

    payload = DrawdownRequestCreate(
        project_id=uuid4(),
        request_name="Drawdown 1",
        request_date=date.today(),
        amount_requested=Decimal("50000.00")
    )

    request = await service.create_drawdown_request(payload)

    assert request.request_name == "Drawdown 1"
    assert session.add.called
    assert session.commit.called
