"""URA (Urban Redevelopment Authority) integration service for Singapore property data."""

from datetime import date, datetime, timedelta
from functools import lru_cache
import json
import re
from typing import Any, Dict, Iterable, List, Optional

import structlog
from pydantic import BaseModel

import httpx
from app.core.config import settings
from app.schemas.external_sources import ExternalSourceMetadata, ExternalSourceState
from app.services.base import AsyncClientService

logger = structlog.get_logger()

URA_REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "OptimalBuildCapture/1.0",
}


class URAZoningInfo(BaseModel):
    """URA zoning information."""

    zone_code: str
    zone_description: str
    plot_ratio: float
    building_height_limit: Optional[float] = None
    site_coverage: Optional[float] = None
    use_groups: List[str] = []
    special_conditions: Optional[str] = None


class URAPropertyInfo(BaseModel):
    """URA property information."""

    property_name: Optional[str] = None
    tenure: Optional[str] = None
    site_area_sqm: Optional[float] = None
    gfa_approved: Optional[float] = None
    current_gfa_source: Optional[str] = None
    current_gfa_source_kind: Optional[str] = None
    building_height: Optional[float] = None
    completion_year: Optional[int] = None
    last_transaction_date: Optional[date] = None
    last_transaction_price: Optional[float] = None


class URAIntegrationService(AsyncClientService):
    """Service for integrating with URA APIs for property and zoning data."""

    def __init__(self) -> None:
        self.token_url = "https://eservice.ura.gov.sg/uraDataService/insertNewToken/v1"
        self.data_url = "https://eservice.ura.gov.sg/uraDataService/invokeUraDS/v1"
        self.access_key = getattr(settings, "URA_ACCESS_KEY", None)
        self.token: str | None = None
        self.token_expiry: datetime | None = None
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
        except (
            RuntimeError
        ):  # pragma: no cover - falls back when httpx stub unavailable
            logger.warning("httpx AsyncClient unavailable; URA integration disabled")
            self.client = None

    def source_metadata(self) -> ExternalSourceMetadata:
        """Describe the current URA integration mode."""

        if not self.access_key:
            return ExternalSourceMetadata(
                provider="ura",
                state=ExternalSourceState.UNAVAILABLE,
                configured=False,
                synthetic=False,
                reason="URA_ACCESS_KEY not configured",
            )
        if self.client is None:
            return ExternalSourceMetadata(
                provider="ura",
                state=ExternalSourceState.UNAVAILABLE,
                configured=True,
                synthetic=False,
                reason="HTTP client unavailable",
            )
        return ExternalSourceMetadata(
            provider="ura",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        )

    async def _get_token(self) -> Optional[str]:
        """Get or refresh URA API token."""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token

        if not self.access_key or self.client is None:
            logger.warning("URA access key not configured")
            return None

        try:
            response = await self.client.get(
                self.token_url,
                headers={**URA_REQUEST_HEADERS, "AccessKey": self.access_key},
            )

            if response.status_code == 200:
                data = self._decode_json_response(response)
                if data is None:
                    logger.error(
                        "URA token endpoint returned non-JSON response",
                        content_type=response.headers.get("content-type"),
                    )
                    return None
                self.token = data.get("Result")
                # Token valid for 24 hours
                self.token_expiry = datetime.now().replace(
                    hour=23, minute=59, second=59
                )
                return self.token
            else:
                logger.error(f"Failed to get URA token: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting URA token: {str(e)}")
            return None

    async def get_zoning_info(self, address: str) -> Optional[URAZoningInfo]:
        """Get zoning information for a property address."""
        logger.info(
            "URA zoning lookup is unavailable; use imported jurisdiction zoning layers",
            address=address,
        )
        return None

    async def get_existing_use(self, address: str) -> Optional[str]:
        """Get existing use of a property."""

        params = self._approved_residential_use_params(address)
        if params is None:
            logger.info(
                "Cannot query URA approved residential use without block/street"
            )
            return None

        payload = await self._get_ura_data("EAU_Appr_Resi_Use", params)
        if payload is None:
            return None

        resi_use = self._extract_first(payload, ("isResiUse", "is_resi_use", "isResi"))
        if isinstance(resi_use, str) and resi_use.strip().upper() == "Y":
            return "Residential"
        return None

    async def get_property_info(self, address: str) -> Optional[URAPropertyInfo]:
        """Get detailed property information from URA."""

        transactions = await self._fetch_residential_transactions()
        matched = self._find_matching_project(address, transactions)
        if matched is None:
            return None

        transaction_date = self._parse_contract_date(matched.get("contractDate"))
        return URAPropertyInfo(
            property_name=self._clean_string(matched.get("project")),
            tenure=self._clean_string(matched.get("tenure")),
            last_transaction_date=transaction_date,
            last_transaction_price=self._coerce_float(matched.get("price")),
        )

    async def get_development_plans(
        self, latitude: float, longitude: float, radius_km: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Get nearby development plans and proposals."""

        payload = await self._get_ura_data("PMI_Resi_Pipeline")
        if payload is None:
            return []

        plans = []
        for record in self._records_from_payload(payload):
            plans.append(
                {
                    "project_name": self._clean_string(record.get("project")),
                    "developer": self._clean_string(
                        record.get("developer") or record.get("developerName")
                    ),
                    "status": "Pipeline",
                    "gfa": self._coerce_float(record.get("gfa")),
                    "use": self._pipeline_use(record),
                    "expected_completion": self._clean_string(
                        record.get("expectedTOPYear")
                    ),
                    "district": self._clean_string(record.get("district")),
                    "total_units": self._coerce_int(record.get("totalUnits")),
                    "source": "ura_data_service",
                }
            )
        return plans

    async def get_transaction_data(
        self, property_type: str, district: Optional[str] = None, months_back: int = 12
    ) -> List[Dict[str, Any]]:
        """Get recent transaction data from URA REALIS."""

        if not self._is_private_residential_type(property_type):
            logger.info(
                "URA transaction adapter currently supports private residential data",
                property_type=property_type,
            )
            return []

        transactions = await self._fetch_residential_transactions()
        cutoff = date.today() - timedelta(days=max(months_back, 0) * 31)
        results = []
        for record in transactions:
            transaction = self._transaction_to_payload(record)
            transaction_date = self._parse_iso_date(transaction.get("transaction_date"))
            if transaction_date is None or transaction_date < cutoff:
                continue
            if district and self._normalise_district(
                district
            ) != self._normalise_district(transaction.get("district")):
                continue
            results.append(transaction)

        return sorted(
            results,
            key=lambda item: str(item.get("transaction_date") or ""),
            reverse=True,
        )

    async def get_rental_data(
        self, property_type: str, district: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get rental transaction data."""

        if not self._is_private_residential_type(property_type):
            logger.info(
                "URA rental adapter currently supports private residential data",
                property_type=property_type,
            )
            return []

        payload = None
        for ref_period in self._recent_ura_ref_quarters():
            payload = await self._get_ura_data(
                "PMI_Resi_Rental", {"refPeriod": ref_period}
            )
            if payload is not None and self._records_from_payload(payload):
                break
        if payload is None:
            return []

        rentals = []
        for record in self._rental_records_from_payload(payload):
            if district and self._normalise_district(
                district
            ) != self._normalise_district(record.get("district")):
                continue
            rentals.append(
                {
                    "property_name": self._clean_string(record.get("project")),
                    "property_type": property_type,
                    "district": self._normalise_district(record.get("district")),
                    "floor_area_sqm": self._coerce_float(
                        record.get("area") or record.get("floorArea")
                    ),
                    "floor_area_sqft_range": self._clean_string(record.get("areaSqft")),
                    "monthly_rent": self._coerce_float(
                        record.get("rent") or record.get("monthlyRent")
                    ),
                    "psf_monthly": self._coerce_float(
                        record.get("rentPsf") or record.get("psfMonthly")
                    ),
                    "lease_commencement": self._clean_string(
                        record.get("leaseDate") or record.get("contractDate")
                    ),
                    "bedrooms": self._clean_string(record.get("noOfBedRoom")),
                    "source": "ura_data_service",
                }
            )
        return rentals

    async def _get_ura_data(
        self, service: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Call a URA Data Service endpoint and return its JSON payload."""

        token = await self._get_token()
        if not token or not self.access_key or self.client is None:
            return None

        query = {"service": service}
        if params:
            query.update({key: value for key, value in params.items() if value})

        try:
            response = await self.client.get(
                self.data_url,
                params=query,
                headers={
                    **URA_REQUEST_HEADERS,
                    "AccessKey": self.access_key,
                    "Token": token,
                },
            )
            if response.status_code != 200:
                logger.warning(
                    "URA data service request failed",
                    service=service,
                    status_code=response.status_code,
                )
                return None
            payload = self._decode_json_response(response)
            if payload is None:
                logger.warning(
                    "URA data service returned non-JSON response",
                    service=service,
                    content_type=response.headers.get("content-type"),
                )
                return None
            status = str(payload.get("Status") or payload.get("status") or "").lower()
            if status and status != "success":
                logger.warning(
                    "URA data service returned non-success status",
                    service=service,
                    status=status,
                    message=payload.get("Message"),
                )
                return None
            return payload
        except Exception as exc:
            logger.warning(
                "URA data service request errored",
                service=service,
                error=str(exc),
            )
            return None

    @staticmethod
    def _decode_json_response(response: httpx.Response) -> Optional[Dict[str, Any]]:
        try:
            payload = response.json()
        except ValueError:
            encoding = response.encoding or "utf-8"
            try:
                text = response.content.decode(encoding, errors="replace")
                payload = json.loads(text)
            except (LookupError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
                return None
        return payload if isinstance(payload, dict) else None

    async def _fetch_residential_transactions(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for batch in range(1, 5):
            payload = await self._get_ura_data(
                "PMI_Resi_Transaction", {"batch": str(batch)}
            )
            if payload is None:
                continue
            records.extend(self._residential_transactions_from_payload(payload))
        return records

    def _residential_transactions_from_payload(
        self, payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        transactions: List[Dict[str, Any]] = []
        for project in self._records_from_payload(payload):
            project_context = {
                "project": project.get("project"),
                "street": project.get("street"),
                "marketSegment": project.get("marketSegment"),
                "x": project.get("x"),
                "y": project.get("y"),
            }
            nested_transactions = project.get("transaction")
            if not isinstance(nested_transactions, list):
                continue
            for transaction in nested_transactions:
                if isinstance(transaction, dict):
                    merged = dict(project_context)
                    merged.update(transaction)
                    transactions.append(merged)
        return transactions

    def _rental_records_from_payload(
        self, payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        rentals: List[Dict[str, Any]] = []
        for project in self._records_from_payload(payload):
            project_context = {
                "project": project.get("project"),
                "street": project.get("street"),
                "x": project.get("x"),
                "y": project.get("y"),
            }
            nested_rentals = project.get("rental")
            if not isinstance(nested_rentals, list):
                continue
            for rental in nested_rentals:
                if isinstance(rental, dict):
                    merged = dict(project_context)
                    merged.update(rental)
                    rentals.append(merged)
        return rentals

    @staticmethod
    def _records_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = payload.get("Result") or payload.get("result") or []
        if isinstance(result, dict):
            return [result]
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        return []

    def _transaction_to_payload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        floor_area = self._coerce_float(record.get("area"))
        price = self._coerce_float(record.get("price"))
        psf_price = price / floor_area if price is not None and floor_area else None
        transaction_date = self._parse_contract_date(record.get("contractDate"))
        return {
            "transaction_date": (
                transaction_date.isoformat() if transaction_date else None
            ),
            "property_type": self._clean_string(record.get("propertyType")),
            "district": self._normalise_district(record.get("district")),
            "project_name": self._clean_string(record.get("project")),
            "street": self._clean_string(record.get("street")),
            "floor_area_sqm": floor_area,
            "price": price,
            "psf_price": psf_price,
            "buyer_type": self._type_of_sale(record.get("typeOfSale")),
            "tenure": self._clean_string(record.get("tenure")),
            "source": "ura_data_service",
        }

    def _find_matching_project(
        self, address: str, transactions: Iterable[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        address_tokens = self._address_tokens(address)
        if not address_tokens:
            return None

        best_match: Optional[Dict[str, Any]] = None
        best_date: Optional[date] = None
        for transaction in transactions:
            project_tokens = self._address_tokens(
                " ".join(
                    str(value or "")
                    for value in (
                        transaction.get("project"),
                        transaction.get("street"),
                    )
                )
            )
            if not project_tokens:
                continue
            overlap = address_tokens.intersection(project_tokens)
            if not project_tokens.issubset(address_tokens) and len(overlap) < 2:
                continue
            transaction_date = self._parse_contract_date(
                transaction.get("contractDate")
            )
            if best_match is None or (
                transaction_date is not None
                and (best_date is None or transaction_date > best_date)
            ):
                best_match = transaction
                best_date = transaction_date
        return best_match

    @staticmethod
    def _address_tokens(value: str) -> set[str]:
        ignored = {
            "singapore",
            "sg",
            "road",
            "rd",
            "street",
            "st",
            "avenue",
            "ave",
            "drive",
            "dr",
            "way",
            "north",
            "south",
            "east",
            "west",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", value.lower())
            if len(token) > 1 and token not in ignored and not token.isdigit()
        }

    @staticmethod
    def _approved_residential_use_params(
        address: str,
    ) -> Optional[Dict[str, str]]:
        unit_match = re.search(r"#\s*(\d{1,3})\s*[-/]\s*(\d{1,5})", address)
        cleaned = re.sub(r"#\s*\d{1,3}\s*[-/]\s*\d{1,5}", "", address)
        first_segment = cleaned.split(",", 1)[0].strip()
        block_match = re.match(
            r"(?P<block>\d+[A-Za-z]?)\s+(?P<street>.+)", first_segment
        )
        if block_match is None:
            return None
        params = {
            "blkHouseNo": block_match.group("block"),
            "street": block_match.group("street").strip(),
        }
        if unit_match:
            params["storeyNo"] = unit_match.group(1)
            params["unitNo"] = unit_match.group(2)
        return params

    @staticmethod
    def _extract_first(source: Any, keys: Iterable[str]) -> Optional[Any]:
        if isinstance(source, dict):
            normalised = {key.lower(): value for key, value in source.items()}
            for key in keys:
                if key.lower() in normalised:
                    return normalised[key.lower()]
        return None

    @staticmethod
    def _clean_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    def _coerce_int(self, value: Any) -> Optional[int]:
        coerced = self._coerce_float(value)
        if coerced is None:
            return None
        return int(round(coerced))

    @staticmethod
    def _parse_contract_date(value: Any) -> Optional[date]:
        if value is None:
            return None
        text = str(value).strip()
        if re.fullmatch(r"\d{4}", text):
            month = int(text[:2])
            year = 2000 + int(text[2:])
            if 1 <= month <= 12:
                return date(year, month, 1)
        if re.fullmatch(r"\d{6}", text):
            year = 2000 + int(text[4:])
            month = int(text[2:4])
            day = int(text[:2])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return date(year, month, day)
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None

    @staticmethod
    def _parse_iso_date(value: Any) -> Optional[date]:
        if value is None:
            return None
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _normalise_district(value: Any) -> Optional[str]:
        if value is None:
            return None
        match = re.search(r"\d+", str(value))
        if match is None:
            return None
        return f"D{int(match.group()):02d}"

    @staticmethod
    def _is_private_residential_type(property_type: str) -> bool:
        value = str(property_type or "").lower()
        return any(
            token in value
            for token in ("residential", "apartment", "condominium", "condo")
        )

    @staticmethod
    def _recent_ura_ref_quarters(lookback: int = 8) -> List[str]:
        today = date.today()
        quarter = ((today.month - 1) // 3) + 1
        year = today.year
        periods = []
        for _ in range(max(lookback, 1)):
            periods.append(f"{str(year)[2:]}q{quarter}")
            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1
        return periods

    @staticmethod
    def _pipeline_use(record: Dict[str, Any]) -> Optional[str]:
        unit_keys = {
            "Condo": "noOfCondo",
            "Apartment": "noOfApartment",
            "Detached": "noOfDetachedHouse",
            "Semi-detached": "noOfSemiDetached",
            "Terrace": "noOfTerrace",
        }
        uses = [
            label
            for label, key in unit_keys.items()
            if URAIntegrationService._coerce_float(record.get(key))
        ]
        return "/".join(uses) if uses else "Residential"

    @staticmethod
    def _type_of_sale(value: Any) -> Optional[str]:
        sale_type = str(value or "").strip()
        return {"1": "New Sale", "2": "Sub Sale", "3": "Resale"}.get(
            sale_type, sale_type or None
        )


# Singleton instance


@lru_cache(maxsize=1)
def get_ura_service() -> URAIntegrationService:
    """Return the shared URA integration client on first use."""

    return URAIntegrationService()


def __getattr__(name: str) -> object:
    """Provide lazy backward-compatible access to the shared URA client."""

    if name == "ura_service":
        return get_ura_service()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
