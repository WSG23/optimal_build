"""Smoke-check live URA Data Service connectivity.

The script never fabricates fallback records. If ``URA_ACCESS_KEY`` is missing,
it reports a skipped smoke check and exits successfully unless ``--require-live``
is supplied.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
for candidate in (str(BACKEND_DIR), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def _load_dotenv(path: Path, *, override: bool = False) -> None:
    """Load a minimal KEY=VALUE dotenv file without overriding the environment."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def _json_default(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _capability(name: str, ok: bool, **details: Any) -> dict[str, Any]:
    return {"name": name, "ok": ok, **details}


def _sample(
    items: list[dict[str, Any]], keys: tuple[str, ...]
) -> dict[str, Any] | None:
    if not items:
        return None
    first = items[0]
    return {key: first.get(key) for key in keys if key in first}


async def run_smoke(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    _load_dotenv(REPO_ROOT / ".env")
    _load_dotenv(REPO_ROOT / ".env.local", override=True)

    from app.services.agents.ura_integration import URAIntegrationService

    service = URAIntegrationService()
    try:
        source = service.source_metadata()
        payload: dict[str, Any] = {
            "provider": "ura",
            "source": source.model_dump(),
            "address": args.address,
            "district": args.district,
            "capabilities": [],
        }

        if not source.configured:
            payload["status"] = "skipped"
            payload["reason"] = source.reason or "URA_ACCESS_KEY not configured"
            return (2 if args.require_live else 0), payload

        token = await service._get_token()
        payload["capabilities"].append(
            _capability("token", bool(token), token_present=bool(token))
        )
        if not token:
            payload["status"] = "failed"
            payload["reason"] = "Could not obtain URA Data Service token"
            return 1, payload

        existing_use = await service.get_existing_use(args.address)
        payload["capabilities"].append(
            _capability(
                "approved_residential_use",
                existing_use is not None,
                value=existing_use,
            )
        )

        transactions = await service.get_transaction_data(
            args.property_type,
            args.district,
            months_back=args.months_back,
        )
        payload["capabilities"].append(
            _capability(
                "private_residential_transactions",
                bool(transactions),
                count=len(transactions),
                sample=_sample(
                    transactions,
                    (
                        "transaction_date",
                        "project_name",
                        "street",
                        "district",
                        "price",
                    ),
                ),
            )
        )

        property_info = await service.get_property_info(args.address)
        payload["capabilities"].append(
            _capability(
                "property_info_from_transactions",
                property_info is not None,
                value=property_info.model_dump() if property_info else None,
            )
        )

        plans = await service.get_development_plans(args.latitude, args.longitude)
        payload["capabilities"].append(
            _capability(
                "private_residential_pipeline",
                bool(plans),
                count=len(plans),
                sample=_sample(
                    plans,
                    ("project_name", "developer", "district", "expected_completion"),
                ),
            )
        )

        rentals = await service.get_rental_data(args.property_type, args.district)
        payload["capabilities"].append(
            _capability(
                "private_residential_rentals",
                bool(rentals),
                count=len(rentals),
                sample=_sample(
                    rentals,
                    (
                        "property_name",
                        "district",
                        "monthly_rent",
                        "psf_monthly",
                    ),
                ),
            )
        )

        failed = [
            capability["name"]
            for capability in payload["capabilities"]
            if not capability["ok"]
        ]
        payload["status"] = "failed" if args.require_all and failed else "ok"
        if failed:
            payload["failed_capabilities"] = failed
        return (1 if args.require_all and failed else 0), payload
    finally:
        await service.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-check live URA Data Service connectivity."
    )
    parser.add_argument(
        "--address",
        default="10 Jln Besar, #11-06 Sim Lim Tower, Singapore 208787",
        help="Singapore address to test approved-use and transaction matching.",
    )
    parser.add_argument(
        "--latitude",
        type=float,
        default=1.3007,
        help="Latitude used for pipeline smoke context.",
    )
    parser.add_argument(
        "--longitude",
        type=float,
        default=103.8556,
        help="Longitude used for pipeline smoke context.",
    )
    parser.add_argument(
        "--property-type",
        default="residential",
        help="Property type for URA transaction/rental adapters.",
    )
    parser.add_argument(
        "--district",
        default=None,
        help="Optional Singapore postal district filter, e.g. D08.",
    )
    parser.add_argument(
        "--months-back",
        type=int,
        default=60,
        help="Transaction recency window for the smoke check.",
    )
    parser.add_argument(
        "--require-live",
        action="store_true",
        help="Exit non-zero when URA_ACCESS_KEY is not configured.",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Exit non-zero when any checked live capability has no response/data.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    exit_code, payload = asyncio.run(run_smoke(args))
    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
