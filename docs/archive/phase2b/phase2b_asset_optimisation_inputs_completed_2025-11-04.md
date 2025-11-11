# Phase 2B Asset Optimisation Inputs – Data Template

Use this sheet (or export to CSV/Excel) to capture the modelling assumptions that drive the asset-mix engine and finance summaries. Fill in the highlighted columns for each asset type. If a value is not known, leave it blank for now and add a note in the “Comments” column.

| Asset Type | Rent (SGD/psm/month) | Stabilised Vacancy % | OPEX % of Rent | NIA Efficiency % | Absorption (months) | Fit-out CAPEX (SGD/psm) | Heritage Premium % | Parking Ratio (lots/1,000 sqm) | Typical Floor Height (m) | Notes / Comments |
|------------|----------------------|-----------------------|----------------|------------------|----------------------|-------------------------|--------------------|-------------------------------|------------------------|------------------|
| Office – Grade A | 128 | 6 | 18 | 82 | 12 | 1500 | 5 | 0.8 | 4.2 | CBD core; reflects 2024 average asking rents converted from $12 psf/mth. |
| Retail – Prime Podium | 360 | 4 | 22 | 75 | 9 | 2200 | 8 | 2.5 | 5.0 | Orchard/Marina prime podium benchmark; assumes escalator voids reduce efficiency. |
| Residential – Condo | 65 | 7 | 25 | 78 | 18 | 1100 | 5 | 1.0 | 3.2 | Core Central Region rental equivalent at $6 psf/mth; sales absorption ~1.5 years. |
| Serviced Apartments | 110 | 10 | 35 | 74 | 12 | 1400 | 7 | 0.6 | 3.4 | ADR $310, 72% occ converted to psqm; higher opex for hospitality operations. |
| Hospitality – Hotel | 205 | 25 | 45 | 62 | 15 | 3800 | 12 | 0.7 | 4.0 | Tier-1 CBD hotel RevPAR assumption (ADR $320, 75% occ) with heritage uplift. |
| Industrial – High Spec Logistics | 26 | 6 | 15 | 88 | 8 | 850 | 0 | 1.3 | 12.0 | Jurong/Changi high-spec rents (~$2.4 psf/mth) with MEZZ loading. |
| Industrial – Production | 19 | 9 | 18 | 86 | 10 | 950 | 0 | 1.8 | 8.0 | Light manufacturing estates (JTC) using $1.8 psf/mth baseline. |
| Mixed Use – Retail Podium | 320 | 5 | 22 | 72 | 12 | 2100 | 8 | 2.0 | 4.8 | Podium tied to integrated scheme; rent slightly below standalone prime. |
| Mixed Use – Office Tower | 118 | 6 | 19 | 80 | 14 | 1400 | 6 | 1.0 | 4.1 | Fringe CBD Grade B+/New Downtown blend with moderate heritage surcharge. |
| Mixed Use – Hospitality Stack | 190 | 28 | 43 | 60 | 15 | 3600 | 15 | 0.8 | 4.2 | Serviced hotel floors within mixed-use scheme; uses blended RevPAR. |
| Amenities / Community | 25 | 12 | 30 | 85 | 16 | 900 | 10 | 1.2 | 3.5 | Community/childcare/medical centre average including conservation fit-out. |

### Data Dictionary

- **Rent (SGD/psm/month):** Stabilised gross rent. If you prefer annual rent, note that in “Comments”.
- **Stabilised Vacancy %:** Long-term vacancy assumption once the building is stabilised.
- **OPEX % of Rent:** Operating expenses as a fraction of rental income.
- **NIA Efficiency %:** Net internal area as a fraction of GFA for this use.
- **Absorption (months):** How many months it typically takes to lease/sell the new product.
- **Fit-out CAPEX (SGD/psm):** All-in capex needed per sqm for this use.
- **Heritage Premium %:** Additional cost uplift if the building is conserved/heritage. Leave blank if not applicable.
- **Parking Ratio (lots/1,000 sqm):** Minimum requirement for this use.
- **Typical Floor Height (m):** Used by the 3D preview stub.

Populate the table with the best available numbers (even if they are ranges). Once filled, the data can be exported to CSV for ingestion by the optimisation engine.
