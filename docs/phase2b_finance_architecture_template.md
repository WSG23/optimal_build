# Phase 2B Finance Architecture Template

Capture the financing assumptions that should accompany each feasibility/financial scenario. Use this as a checklist or copy into your financial model spreadsheet.

## 1. Capital Structure Targets

| Scenario | Equity % | Debt % | Preferred Equity % | Target LTV | Target LTC | Target DSCR | Comments |
|----------|----------|--------|---------------------|------------|------------|-------------|----------|
| Base Case | 35 | 60 | 5 | 60 | 65 | 1.35 | Aligns with core Singapore development deals; assumes SORA + 250 bps spread. |
| Upside | 30 | 65 | 5 | 58 | 63 | 1.40 | Strong pre-leasing allows higher leverage and tighter DSCR covenants. |
| Downside | 45 | 50 | 5 | 55 | 60 | 1.25 | De-risked structure with more sponsor equity and lower leverage headroom. |

## 2. Debt Terms

| Facility Type | Amount (SGD) | Interest Rate | Tenor (years) | Amortisation | Drawdown Schedule Notes | Covenants / Triggers |
|---------------|--------------|---------------|---------------|--------------|--------------------------|----------------------|
| Construction Loan | 0.60 x total_dev_cost | 4.8% (SORA 3M + 240 bps) | 4 | Interest-only during build; convert to 20-yr schedule at PC | 15%/30%/30%/25% by construction quarter | DSCR ≥ 1.20 once income begins; cost-to-complete tests quarterly. |
| Bridge/Mezzanine | 0.10 x total_dev_cost | 8.5% fixed | 2 | Bullet | Tranche draws alongside equity for land/top-up costs | LTV hard cap 72%; cash sweep if DSCR < 1.15. |
| Permanent Debt | 0.55 x stabilised_value | 4.2% (SORA 3M + 180 bps) | 7 | 20-yr amort with 30% balloon | Funds post-PC upon 70% stabilised occupancy | DSCR ≥ 1.35; LTV maintain ≤ 60%; cash sweep above 1.45 DSCR. |

## 3. Equity Waterfall Assumptions

- Promote structure / IRR hurdles:
  - Tier 1: 12% IRR – promote 10%
  - Tier 2: 18% IRR – promote 20%
- Preferred return (if any): 9% annual pref to equity investors paid current if cash available.
- Catch-up rules / clawback: 50/50 catch-up after pref; clawback if promote paid but project IRR falls below 12% on exit.

## 4. Cash Flow Timing

| Item | Start Month | Duration (months) | Notes |
|------|-------------|-------------------|-------|
| Land Acquisition | 0 | 3 | DD, option exercise, completion, and stamping. |
| Construction | 3 | 30 | Includes enabling works and 6-month interior fit-out. |
| Leasing / Sales | 24 | 18 | Starts during final year of construction with phased TOP. |
| Stabilisation | 42 | 12 | Target 90% leased and NOI run-rate achieved. |
| Exit / Refinance | 48 | 3 | Refinance or partial asset sale once DSCR covenant achieved. |

## 5. Exit Assumptions

- Exit cap rate(s): Base 4.0% (prime office/hospitality), Upside 3.6%, Downside 4.5%.
- Sale costs (% of value): 1.75% broker + 0.25% legal + 0.25% stamp/fees (total 2.25%).
- Refinance terms (if applicable): 65% LTV senior loan at SORA + 170 bps, 5-year tenor, 25-yr amort.

## 6. Sensitivity Bands

| Parameter | Low | Base | High | Comments |
|-----------|-----|------|------|----------|
| Rent | -8% | 0% | +6% | Reflects URA QOQ ranges for CBD office and prime retail. |
| Exit Cap Rate | +40 bps | 0 bps | -30 bps | Stress and upside relative to base 4.0% cap. |
| Construction Cost | +10% | 0% | -5% | Based on 2024 BCA tender price index volatility. |
| Interest Rate | +150 bps | 0 bps | -75 bps | Captures SORA swings during tightening/easing cycles. |

Once populated, this sheet allows us to align finance feasibility runs (Phase 2C) with the optimisation output from Phase 2B. Provide the completed data or drop a link to the working model when ready.
