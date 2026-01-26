# Agent Catalog

This catalog documents the 11 production agent services implemented in
`backend/app/services/agents/` and referenced in architecture docs.

## Core Agent Services

| Agent | Module | Purpose | Primary Outputs |
| --- | --- | --- | --- |
| Market Intelligence Analytics | `market_intelligence_analytics.py` | Market analytics across yields, absorption, comparables, and trends. | Analytics payloads for market intelligence API responses. |
| Market Data Service | `market_data_service.py` | Ingests/syncs transactions, rentals, and market indices from providers. | Persisted market transactions, rental listings, indices. |
| Development Potential Scanner | `development_potential_scanner.py` | Evaluates development scenarios, constraints, and ROI for a property. | Development analysis records + scenario summaries. |
| GPS Property Logger | `gps_property_logger.py` | Captures GPS site visits and quick analysis context. | Property records, geocoded context, checklist linkage. |
| Investment Memorandum | `investment_memorandum.py` | Generates institutional-grade investment memo PDFs. | PDF buffers + storage artifacts. |
| Marketing Materials | `marketing_materials.py` | Generates marketing collateral and listing packs. | PDF collateral + QR assets. |
| Universal Site Pack | `universal_site_pack.py` | Builds a comprehensive site analysis PDF pack. | PDF pack + supporting snapshots. |
| Scenario Builder 3D | `scenario_builder_3d.py` | Produces quick 3D massing scenarios. | GLTF/preview-ready scenario data. |
| Photo Documentation | `photo_documentation.py` | Captures site photos and metadata for documentation. | Stored photos + metadata records. |
| PDF Generator | `pdf_generator.py` | Shared PDF generation utilities used by other agents. | Base PDF helpers, header/footer utilities. |
| URA Integration | `ura_integration.py` | URA zoning/regulatory data integration for Singapore. | Zoning/parcel data consumed by scanners/loggers. |

## Supporting Utilities

These modules support the agent flows but are not counted in the 11 core agents.

| Utility | Module | Purpose |
| --- | --- | --- |
| Advisory Helpers | `advisory.py` | Advisory analytics and feedback helpers for agent workflows. |
| Image Watermarking | `image_watermark.py` | Applies watermarks to marketing photos. |
| Voice Notes | `voice_note_service.py` | Stores and retrieves audio notes tied to properties. |

## Primary API Surfaces

- `backend/app/api/v1/agents.py` exposes the commercial property agent endpoints.
- `backend/app/api/v1/market_intelligence.py` serves market analytics workflows.

## Related Docs

- `docs/agents/marketing_pack_quickstart.md` for end-to-end agent workflow.
- `docs/architecture.md` for service placement and system context.
