# 🧪 Complete Feature Testing Guide

## Overview
This guide covers testing all interactive features in the Optimal Build application.

**Base URLs:**
- Frontend: http://localhost:4400
- Backend API: http://localhost:9400
- Admin Panel: http://localhost:4401

---

## ✅ Navigation Menu Items

### 1. Home Page (`/`)
**Test:** Click on "Home" in the sidebar

**Expected:**
- Shows 5 feature cards: Upload, Detection, Pipelines, Feasibility, Finance
- Each card has a title, description, and CTA button
- Clicking any CTA navigates to that feature

**API Test:**
```bash
curl -s http://localhost:4400/ | grep -o '<h3>[^<]*</h3>' | head -5
```

---

### 2. CAD Upload (`/cad/upload`)
**Test:** Click on "Upload" in the sidebar

**Features to Test:**
- ✅ **File Drag & Drop**
  - Drag a DXF/IFC/JSON file into the dropzone
  - Dropzone should highlight when dragging over it
  - File uploads automatically on drop

- ✅ **Browse Button**
  - Click "Browse" button
  - File picker opens
  - Select a file (.dxf, .ifc, .json, .pdf, .svg, .jpg, .jpeg, .png)
  - File uploads automatically

- ✅ **Upload Progress**
  - Shows "Latest status" panel
  - Displays filename
  - Shows parsing status (parsing → completed/failed)
  - Shows detected floors (comma-separated list)
  - Shows detected units (count)

- ✅ **Rule Pack Explanation Panel**
  - Shows below uploader
  - Lists compliance rules loaded from backend

**Test Files:**
```bash
# Test with your DXF file
# Expected: 2 floors (LEVEL_01, LEVEL_02), 2 units
```

**API Test:**
```bash
# Upload via API
curl -X POST "http://localhost:9400/api/v1/import" \
  -H "X-Role: admin" \
  -F "file=@/path/to/flat_two_bed.dxf" \
  -F "project_id=1"
```

---

### 3. CAD Detection (`/cad/detection`)
**Test:** Click on "Detection" in the sidebar

**Features to Test:**
- ✅ **Detection Preview**
  - Shows parsed CAD geometry
  - Displays detected floors and units
  - Visual representation of boundaries

**Expected:**
- Detection visualization interface
- List of detected entities
- Geometry preview (if implemented)

---

### 4. CAD Pipelines (`/cad/pipelines`)
**Test:** Click on "Pipelines" in the sidebar

**Features to Test:**
- ✅ **Pipeline Management**
  - View parsing pipelines
  - Pipeline status tracking
  - Job queue visualization

**Expected:**
- Pipeline dashboard
- Processing queue status
- Historical pipeline runs

---

### 5. Feasibility Calculator (`/feasibility`)
**Test:** Click on "Feasibility" in the sidebar

**Features to Test:**
- ✅ **Buildable Screening**
  - Input property parameters
  - Calculate buildable metrics
  - View zoning constraints

**API Test:**
```bash
curl -X POST "http://localhost:9400/api/v1/screen/buildable" \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d '{
    "zone_code": "Residential",
    "land_area_sqm": "1000",
    "defaults": {}
  }'
```

---

### 6. Finance Scenarios (`/finance`)
**Test:** Click on "Finance" in the sidebar

**Features to Test:**
- ✅ **Scenario Table**
  - Lists finance scenarios for project 401
  - Shows NPV, IRR, escalated cost
  - Sortable columns

- ✅ **Capital Stack Visualization**
  - Chart showing equity vs debt breakdown
  - Weighted average debt rate
  - Loan-to-cost ratio

- ✅ **Drawdown Schedule**
  - Timeline of equity/debt draws
  - Cumulative balances chart
  - Outstanding debt over time

- ✅ **Refresh Button**
  - Click "Refresh" in header
  - Re-fetches scenarios from API
  - Shows "Refreshing..." state

**API Test:**
```bash
# List scenarios
curl -s "http://localhost:9400/api/v1/finance/scenarios?project_id=401" \
  -H "X-Role: admin" | python3 -m json.tool
```

---

### 7. Agent Site Capture (`/agents/site-capture`)
**Test:** Click on "Agent Capture" in the sidebar

**Features to Test:**
- ✅ **GPS Property Logger**
  - Input address or coordinates
  - Fetch property intelligence
  - View quick analysis scenarios

**API Test:**
```bash
curl -X POST "http://localhost:9400/api/v1/agents/gps/log" \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d '{
    "address": "1 Marina Boulevard, Singapore",
    "notes": "Test property"
  }'
```

---

### 8. Advanced Intelligence (`/visualizations/intelligence`)
**Test:** Click on "Intelligence" in the sidebar

**Features to Test:**
- ✅ **Graph Intelligence**
  - Network graph visualization
  - Node and edge relationships
  - Interactive zoom/pan

- ✅ **Predictive Intelligence**
  - Adoption trends
  - Segment analysis
  - Predicted outcomes

- ✅ **Cross-Correlation**
  - Factor relationships
  - Correlation matrix
  - Significance scores

**API Test:**
```bash
# Graph intelligence
curl -s "http://localhost:9400/api/v1/analytics/intelligence/graph?workspaceId=default-investigation" \
  -H "X-Role: admin"

# Predictive intelligence
curl -s "http://localhost:9400/api/v1/analytics/intelligence/predictive?workspaceId=default-investigation" \
  -H "X-Role: admin"

# Cross-correlation
curl -s "http://localhost:9400/api/v1/analytics/intelligence/cross-correlation?workspaceId=default-investigation" \
  -H "X-Role: admin"
```

---

### 9. Locale Switcher
**Test:** Click language dropdown in top-right corner

**Features to Test:**
- ✅ **Language Toggle**
  - Click dropdown
  - Select different language (en/es/fr/zh)
  - UI text updates immediately
  - Preference persists on refresh

**Expected Languages:**
- English (en)
- Spanish (es) - if implemented
- French (fr) - if implemented
- Chinese (zh) - if implemented

---

## 🔧 Backend API Endpoints

### Health Checks
```bash
# Application health
curl -s http://localhost:9400/health

# Prometheus metrics
curl -s http://localhost:9400/health/metrics
```

### OpenAPI Documentation
```bash
# Interactive API docs
open http://localhost:9400/docs

# ReDoc
open http://localhost:9400/redoc

# OpenAPI JSON
curl -s http://localhost:9400/openapi.json | python3 -m json.tool
```

---

## 🎨 UI Component Tests

### Buttons
- ✅ Browse (CAD Upload)
- ✅ Refresh (Finance page)
- ✅ Submit (various forms)
- ✅ Navigation links (sidebar)
- ✅ CTA buttons (home cards)

### Forms
- ✅ File upload input
- ✅ Property search (if exists)
- ✅ Filter controls (if exists)

### Data Display
- ✅ Tables (Finance scenarios)
- ✅ Charts (Capital stack, drawdown)
- ✅ Cards (Home page, detection results)
- ✅ Status indicators (parsing status)

### Interactive Elements
- ✅ Drag and drop zones
- ✅ Dropdown menus (locale switcher)
- ✅ Tabs (if exists)
- ✅ Modals/dialogs (if exists)

---

## 🚀 Quick Test Script

Run all tests at once:

```bash
#!/bin/bash
echo "🧪 Testing All Features"
echo ""

echo "1. Health Check..."
curl -s http://localhost:9400/health && echo "✅" || echo "❌"

echo "2. Frontend Accessible..."
curl -s http://localhost:4400 > /dev/null && echo "✅" || echo "❌"

echo "3. Finance API..."
curl -s "http://localhost:9400/api/v1/finance/scenarios?project_id=401" \
  -H "X-Role: admin" > /dev/null && echo "✅" || echo "❌"

echo "4. Intelligence API..."
curl -s "http://localhost:9400/api/v1/analytics/intelligence/graph?workspaceId=default" \
  -H "X-Role: admin" > /dev/null && echo "✅" || echo "❌"

echo "5. Import Status..."
curl -s "http://localhost:9400/api/v1/parse/33d3b246-36e2-44b7-948c-b30107252458" \
  -H "X-Role: admin" > /dev/null && echo "✅" || echo "❌"

echo ""
echo "✅ All API tests complete!"
```

---

## 📊 Testing Checklist

- [ ] All navigation links work
- [ ] File upload accepts all formats
- [ ] Drag and drop works
- [ ] Finance scenarios load and display
- [ ] Charts render correctly
- [ ] Language switcher changes UI text
- [ ] API endpoints return valid JSON
- [ ] Error states display properly
- [ ] Loading states show during async operations
- [ ] Responsive design works on different screen sizes

---

## 🐛 Known Issues to Check

1. Console logs in development mode (expected)
2. Missing data shows fallback values ("—")
3. Empty states display helpful messages
4. Error boundaries catch crashes

---

## 📝 Notes

- Use Chrome DevTools to monitor network requests
- Check browser console for errors
- Use React DevTools to inspect component state
- Monitor backend logs: `tail -f /tmp/backend.log`

**Happy Testing! 🎉**
