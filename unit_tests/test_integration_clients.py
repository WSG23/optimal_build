import pytest

from app.services.integrations.edgeprop import EdgePropClient
from app.services.integrations.propertyguru import PropertyGuruClient
from app.services.integrations.zoho import ZohoClient


@pytest.mark.anyio
async def test_edgeprop_client_end_to_end():
    client = EdgePropClient(client_id="id", client_secret="secret")
    bundle = await client.exchange_authorization_code("abc", "https://redirect")
    assert bundle.access_token == "edgeprop-access-abc"
    assert bundle.refresh_token == "edgeprop-refresh-abc"

    refreshed = await client.refresh_tokens(bundle.refresh_token)
    assert refreshed.access_token.startswith("edgeprop-access-")

    listing_id, echoed = await client.publish_listing({"external_id": "edge-1", "price": 100})
    assert listing_id == "edge-1"
    assert echoed["echo"]["price"] == 100
    assert await client.remove_listing(listing_id) is True


@pytest.mark.anyio
async def test_propertyguru_client_end_to_end():
    client = PropertyGuruClient(client_id="id", client_secret="secret")
    bundle = await client.exchange_authorization_code("xyz", "https://redirect")
    assert bundle.access_token == "mock-access-xyz"
    assert bundle.refresh_token == "mock-refresh-xyz"

    refreshed = await client.refresh_tokens(bundle.refresh_token)
    assert refreshed.access_token.startswith("mock-access-")

    listing_id, echoed = await client.publish_listing({"external_id": "guru-1", "title": "Sample"})
    assert listing_id == "guru-1"
    assert echoed["echo"]["title"] == "Sample"
    assert await client.remove_listing(listing_id) is True


@pytest.mark.anyio
async def test_zoho_client_end_to_end():
    client = ZohoClient(client_id="id", client_secret="secret")
    bundle = await client.exchange_authorization_code("def", "https://redirect")
    assert bundle.access_token == "zoho-access-def"
    assert bundle.refresh_token == "zoho-refresh-def"

    refreshed = await client.refresh_tokens(bundle.refresh_token)
    assert refreshed.access_token.startswith("zoho-access-")

    lead_id, echoed = await client.publish_listing({"external_id": "lead-1", "name": "Lead"})
    assert lead_id == "lead-1"
    assert echoed["echo"]["name"] == "Lead"
    assert await client.remove_listing(lead_id) is True
