# Testing the Agent Advisory Feature (Phase 1B)

## Test Property Created

**Property ID:** `c32f2d80-bab2-4aea-b3b6-cd37712f24fd`

**Details:**
- **Name:** Marina Bay Executive Tower
- **Address:** 1 Marina Boulevard
- **Postal Code:** 018989
- **Type:** Office
- **Status:** Existing
- **Location:** Downtown Core, Marina Centre
- **GFA:** 45,000 sqm
- **Land Area:** 8,000 sqm
- **Floors:** 40 above ground, 3 below
- **Units:** 200
- **Year Built:** 2018

## Test URLs

### Advisory UI
```
http://localhost:4400/#/agents/advisory?propertyId=c32f2d80-bab2-4aea-b3b6-cd37712f24fd
```

### API Endpoint
```bash
curl -H "X-Role: admin" \
  "http://localhost:9400/api/v1/agents/commercial-property/properties/c32f2d80-bab2-4aea-b3b6-cd37712f24fd/advisory"
```

## What to Test

### 1. Advisory Data Display
- [ ] Asset mix strategy section renders
- [ ] Mix recommendations table shows office/flex/amenities breakdown
- [ ] Total programmable GFA displays (45,000 sqm)
- [ ] Market positioning section shows tier and pricing
- [ ] Absorption forecast displays timeline and milestones
- [ ] All sections render without errors

### 2. Feedback Submission
- [ ] Feedback form is visible
- [ ] Can select sentiment (positive/neutral/negative)
- [ ] Can enter notes in textarea
- [ ] Submit button is initially disabled (no notes)
- [ ] Submit button enables when notes are entered
- [ ] Clicking submit creates feedback record
- [ ] Feedback appears in "Recent feedback" list after submission
- [ ] Can submit multiple feedback items

### 3. Data Accuracy
- [ ] Property ID matches in all sections
- [ ] Office property type triggers correct asset mix profile (70% office, 20% flex, 10% amenities)
- [ ] Market tier is appropriate for Downtown Core location
- [ ] Absorption forecast shows reasonable timeline (6+ months)

## API Testing

### Get Advisory Summary
```bash
curl -s -H "X-Role: admin" \
  "http://localhost:9400/api/v1/agents/commercial-property/properties/c32f2d80-bab2-4aea-b3b6-cd37712f24fd/advisory" \
  | python3 -m json.tool
```

### Submit Feedback
```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d '{
    "sentiment": "positive",
    "notes": "Strong investor interest from institutional buyers",
    "channel": "call"
  }' \
  "http://localhost:9400/api/v1/agents/commercial-property/properties/c32f2d80-bab2-4aea-b3b6-cd37712f24fd/advisory/feedback" \
  | python3 -m json.tool
```

### List Feedback
```bash
curl -s -H "X-Role: admin" \
  "http://localhost:9400/api/v1/agents/commercial-property/properties/c32f2d80-bab2-4aea-b3b6-cd37712f24fd/advisory/feedback" \
  | python3 -m json.tool
```

## Expected Behavior

### Asset Mix (Office Property)
```json
{
  "property_id": "c32f2d80-bab2-4aea-b3b6-cd37712f24fd",
  "total_programmable_gfa_sqm": 40000,
  "mix_recommendations": [
    {
      "use": "office",
      "allocation_pct": 70,
      "target_gfa_sqm": 28000,
      "rationale": "Preserve premium office positioning."
    },
    {
      "use": "flex workspace",
      "allocation_pct": 20,
      "target_gfa_sqm": 8000,
      "rationale": "Capture hybrid demand."
    },
    {
      "use": "amenities",
      "allocation_pct": 10,
      "target_gfa_sqm": 4000,
      "rationale": "Support tenant experience."
    }
  ]
}
```

### Market Positioning
- Tier: "Prime CBD" (for Downtown Core)
- Pricing guidance with PSF ranges
- Target segments (e.g., Regional HQ, Financial Services)

### Absorption Forecast
- Expected months to stabilize: 6-12 months
- Monthly velocity target: based on unit count
- Confidence level
- Timeline milestones with absorption percentages

## Troubleshooting

If the API returns 500 error:
1. Check backend is running: `curl http://localhost:9400/health`
2. Check database connection
3. Verify property exists: `docker exec optimal_build-postgres-1 psql -U postgres -d building_compliance -c "SELECT id, name FROM properties WHERE id = 'c32f2d80-bab2-4aea-b3b6-cd37712f24fd';"`
4. Check backend logs for errors

If UI shows "Provide a propertyId query parameter":
1. Verify URL includes `?propertyId=c32f2d80-bab2-4aea-b3b6-cd37712f24fd`
2. Check browser console for errors
3. Verify frontend is running: `http://localhost:4400/`

## Success Criteria

✅ Phase 1B is complete when:
1. Advisory UI loads without errors
2. All four sections display data (asset mix, positioning, absorption, feedback)
3. Feedback can be submitted and appears in the list
4. Backend tests pass (2/2) ✓ Already confirmed
5. No console errors in browser
6. Data makes sense for the property type and location
