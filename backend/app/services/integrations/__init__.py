"""Integration service exports."""

from __future__ import annotations

from importlib import import_module
from typing import Final

_EXPORTS: Final[dict[str, str]] = {
    "ListingIntegrationAccountService": ".accounts",
    "PropertyGuruClient": ".propertyguru",
    "EdgePropClient": ".edgeprop",
    "ZohoClient": ".zoho",
    "ZillowClient": ".zillow",
    "LoopNetClient": ".loopnet",
    "SalesforceClient": ".salesforce",
    "HubSpotClient": ".hubspot",
}


def __getattr__(name: str) -> object:
    """Lazy-load integration helpers on first access."""

    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)
