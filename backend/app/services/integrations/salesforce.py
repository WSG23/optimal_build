"""Salesforce CRM integration client (mock)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from backend._compat.datetime import utcnow

logger = structlog.get_logger()


_DATACLASS_KWARGS = {"slots": True} if sys.version_info >= (3, 10) else {}


@dataclass(**_DATACLASS_KWARGS)
class SalesforceOAuthBundle:
    access_token: str
    refresh_token: str
    instance_url: str
    expires_at: datetime


@dataclass
class SalesforceLead:
    """Salesforce Lead object."""

    id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: str = "Open"  # Open, Working, Closed - Converted, Closed - Not Converted
    lead_source: Optional[str] = None
    rating: Optional[str] = None  # Hot, Warm, Cold
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    description: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    # Custom fields for real estate
    property_interest: Optional[str] = None
    budget_range: Optional[str] = None
    preferred_location: Optional[str] = None


@dataclass
class SalesforceOpportunity:
    """Salesforce Opportunity object."""

    id: Optional[str] = None
    name: str = ""
    account_id: Optional[str] = None
    stage_name: str = "Prospecting"  # Prospecting, Qualification, Needs Analysis, etc.
    amount: Optional[float] = None
    close_date: Optional[datetime] = None
    probability: Optional[float] = None
    type: Optional[str] = None  # New Business, Existing Business
    lead_source: Optional[str] = None
    description: Optional[str] = None
    created_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    # Custom fields for real estate
    property_id: Optional[str] = None
    unit_type: Optional[str] = None
    expected_closing: Optional[datetime] = None


@dataclass
class SalesforceAccount:
    """Salesforce Account object."""

    id: Optional[str] = None
    name: str = ""
    account_type: Optional[str] = None  # Prospect, Customer, Partner
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    created_date: Optional[datetime] = None


class SalesforceClient:
    """Mock client for Salesforce CRM interactions.

    Salesforce requires Connected App setup and OAuth 2.0 authentication.
    This stub provides the expected interface for future implementation.
    """

    AUTH_BASE_URL = "https://login.salesforce.com/services/oauth2"
    API_VERSION = "v59.0"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        instance_url: str | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.instance_url = instance_url or "https://na1.salesforce.com"

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> SalesforceOAuthBundle:
        """Exchange an authorization code for access/refresh tokens."""
        logger.info("salesforce.exchange_code", redirect_uri=redirect_uri)
        now = utcnow()
        return SalesforceOAuthBundle(
            access_token=f"sf-access-{code}",
            refresh_token=f"sf-refresh-{code}",
            instance_url=self.instance_url,
            expires_at=now + timedelta(hours=2),
        )

    async def refresh_tokens(self, refresh_token: str) -> SalesforceOAuthBundle:
        """Refresh the OAuth tokens."""
        logger.info("salesforce.refresh_token")
        now = utcnow()
        return SalesforceOAuthBundle(
            access_token=f"sf-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            instance_url=self.instance_url,
            expires_at=now + timedelta(hours=2),
        )

    # Lead operations
    async def create_lead(self, lead: SalesforceLead) -> SalesforceLead:
        """Create a new lead in Salesforce."""
        logger.info("salesforce.create_lead", email=lead.email)
        now = utcnow()
        lead.id = f"00Q{now.timestamp():.0f}"
        lead.created_date = now
        lead.last_modified_date = now
        return lead

    async def update_lead(
        self, lead_id: str, updates: Dict[str, Any]
    ) -> SalesforceLead:
        """Update an existing lead."""
        logger.info(
            "salesforce.update_lead", lead_id=lead_id, fields=list(updates.keys())
        )
        lead = SalesforceLead(id=lead_id, **updates)
        lead.last_modified_date = utcnow()
        return lead

    async def get_lead(self, lead_id: str) -> Optional[SalesforceLead]:
        """Get a lead by ID."""
        logger.info("salesforce.get_lead", lead_id=lead_id)
        return SalesforceLead(
            id=lead_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            company="Acme Corp",
            status="Working",
            rating="Warm",
            property_interest="Residential Condo",
            budget_range="$500k-$750k",
            created_date=utcnow() - timedelta(days=7),
        )

    async def search_leads(
        self,
        status: Optional[str] = None,
        rating: Optional[str] = None,
        lead_source: Optional[str] = None,
        limit: int = 100,
    ) -> List[SalesforceLead]:
        """Search leads with filters."""
        logger.info("salesforce.search_leads", status=status, rating=rating)
        now = utcnow()
        return [
            SalesforceLead(
                id="00Q001",
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                company="Smith Holdings",
                status=status or "Open",
                rating=rating or "Hot",
                lead_source=lead_source or "Web",
                property_interest="Office Space",
                budget_range="$1M-$2M",
                created_date=now - timedelta(days=3),
            ),
            SalesforceLead(
                id="00Q002",
                first_name="Bob",
                last_name="Johnson",
                email="bob.j@example.com",
                company="Johnson Dev",
                status=status or "Working",
                rating=rating or "Warm",
                lead_source=lead_source or "Referral",
                property_interest="Mixed-Use",
                budget_range="$5M+",
                created_date=now - timedelta(days=14),
            ),
        ]

    # Opportunity operations
    async def create_opportunity(
        self, opportunity: SalesforceOpportunity
    ) -> SalesforceOpportunity:
        """Create a new opportunity in Salesforce."""
        logger.info("salesforce.create_opportunity", name=opportunity.name)
        now = utcnow()
        opportunity.id = f"006{now.timestamp():.0f}"
        opportunity.created_date = now
        opportunity.last_modified_date = now
        return opportunity

    async def update_opportunity(
        self, opp_id: str, updates: Dict[str, Any]
    ) -> SalesforceOpportunity:
        """Update an existing opportunity."""
        logger.info(
            "salesforce.update_opportunity", opp_id=opp_id, fields=list(updates.keys())
        )
        opp = SalesforceOpportunity(id=opp_id, **updates)
        opp.last_modified_date = utcnow()
        return opp

    async def get_opportunity(self, opp_id: str) -> Optional[SalesforceOpportunity]:
        """Get an opportunity by ID."""
        logger.info("salesforce.get_opportunity", opp_id=opp_id)
        return SalesforceOpportunity(
            id=opp_id,
            name="123 Main St - Unit 501",
            stage_name="Negotiation",
            amount=875000,
            probability=0.6,
            close_date=utcnow() + timedelta(days=30),
            property_id="prop-123",
            unit_type="2BR Condo",
            created_date=utcnow() - timedelta(days=21),
        )

    async def get_pipeline(
        self, stage_name: Optional[str] = None, min_amount: Optional[float] = None
    ) -> List[SalesforceOpportunity]:
        """Get sales pipeline opportunities."""
        logger.info("salesforce.get_pipeline", stage=stage_name, min_amount=min_amount)
        now = utcnow()
        return [
            SalesforceOpportunity(
                id="006001",
                name="456 Oak Ave - Penthouse",
                stage_name="Qualification",
                amount=2500000,
                probability=0.25,
                close_date=now + timedelta(days=60),
                property_id="prop-456",
                created_date=now - timedelta(days=7),
            ),
            SalesforceOpportunity(
                id="006002",
                name="789 Pine St - Commercial",
                stage_name="Proposal",
                amount=5000000,
                probability=0.5,
                close_date=now + timedelta(days=45),
                property_id="prop-789",
                created_date=now - timedelta(days=30),
            ),
        ]

    # Account operations
    async def create_account(self, account: SalesforceAccount) -> SalesforceAccount:
        """Create a new account in Salesforce."""
        logger.info("salesforce.create_account", name=account.name)
        account.id = f"001{utcnow().timestamp():.0f}"
        account.created_date = utcnow()
        return account

    async def get_account(self, account_id: str) -> Optional[SalesforceAccount]:
        """Get an account by ID."""
        logger.info("salesforce.get_account", account_id=account_id)
        return SalesforceAccount(
            id=account_id,
            name="Premium Buyers LLC",
            account_type="Customer",
            industry="Real Estate",
            annual_revenue=10000000,
            created_date=utcnow() - timedelta(days=90),
        )

    # SOQL queries
    async def query(self, soql: str) -> List[Dict[str, Any]]:
        """Execute a SOQL query (mock)."""
        logger.info("salesforce.query", soql=soql[:100])
        return [
            {"Id": "mock001", "Name": "Mock Record 1"},
            {"Id": "mock002", "Name": "Mock Record 2"},
        ]

    # Bulk operations
    async def bulk_create_leads(
        self, leads: List[SalesforceLead]
    ) -> List[SalesforceLead]:
        """Bulk create leads."""
        logger.info("salesforce.bulk_create_leads", count=len(leads))
        now = utcnow()
        for i, lead in enumerate(leads):
            lead.id = f"00Q{now.timestamp():.0f}{i:03d}"
            lead.created_date = now
        return leads

    async def sync_property_to_salesforce(
        self, property_id: str, property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync a property to Salesforce as a custom object (mock)."""
        logger.info("salesforce.sync_property", property_id=property_id)
        return {
            "success": True,
            "salesforce_id": f"a00{utcnow().timestamp():.0f}",
            "property_id": property_id,
            "synced_at": utcnow().isoformat(),
        }
