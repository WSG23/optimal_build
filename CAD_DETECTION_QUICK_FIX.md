# 🔧 CAD Detection - Quick Fix Guide

## 🚨 **Problem: All Buttons Appear Broken/Disabled**

**Root Cause:** Project 5821 has **ZERO overlay suggestions** and **no CAD geometry**.

Without data, all the interactive features are intentionally disabled:
- ❌ Export button (disabled when nothing to export)
- ❌ Approve/Reject buttons (disabled when no pending items)
- ❌ Preview canvas (empty when no units to display)

---

## ✅ **Solution: Use a Different Project OR Upload CAD Data**

### **Option 1: Change Project ID (Quick Test)**

1. Go to **CAD Pipelines** page: http://localhost:4400/#/cad/pipelines
2. Change project ID from 5821 to a different number
3. Wait for the page to load suggestions

OR manually check which projects have data:

```bash
# Check if any projects have overlay data
for ID in 1 2 3 4 5 401 5821; do
  COUNT=$(curl -s "http://localhost:9400/api/v1/overlay/$ID" -H "X-Role: admin" | python3 -c "import json, sys; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")
  if [ "$COUNT" -gt "0" ]; then
    echo "✅ Project $ID has $COUNT overlays"
  fi
done
```

---

### **Option 2: Upload CAD File First (Proper Workflow)**

The correct workflow is:

1. **Upload** → Go to `/cad/upload` and upload a DXF/IFC file
2. **Wait** → Let it parse (should detect floors/units)
3. **Pipelines** → Go to `/cad/pipelines` to run overlay detection
4. **Detection** → Go to `/cad/detection` to review overlays
5. **Export** → Once reviewed, export to PDF/DXF/etc.

**Try this:**

```bash
# 1. Upload your flat_two_bed.dxf file via UI or API
curl -X POST "http://localhost:9400/api/v1/import" \
  -H "X-Role: admin" \
  -F "file=@/path/to/flat_two_bed.dxf" \
  -F "project_id=5821"

# 2. Wait for parsing to complete, then run overlay pipeline
curl -X POST "http://localhost:9400/api/v1/overlay/5821/run" \
  -H "X-Role: admin"

# 3. Check if overlays were generated
curl -s "http://localhost:9400/api/v1/overlay/5821" -H "X-Role: admin"
```

---

## 🎯 **What Each Button SHOULD Do (When Data Exists)**

### **1. Layer Toggle Buttons** (Source/Pending/Approved/Rejected)
**Expected Behavior:**
- Click to show/hide that layer on the preview
- Multiple can be active at once
- Visual feedback: button changes appearance when active

**How to Test:**
1. Click "Pending" button
2. It should toggle between highlighted/unhighlighted
3. Preview should update to show/hide pending overlays

---

### **2. Approve All / Reject All Buttons**
**Expected Behavior:**
- Approves/rejects ALL pending suggestions
- Makes API call: `POST /api/v1/overlay/{project_id}/decision`
- Page refreshes to show updated counts
- Audit timeline panel updates with new events

**How to Test:**
1. Click "Approve All"
2. Watch browser Network tab for POST request
3. Pending count should drop to 0
4. Units should move from "Pending" to "Approved" layer
5. Audit timeline should show new approval events

---

### **3. Lock/Unlock Button**
**Expected Behavior:**
- Just a safety toggle (doesn't call API)
- When locked: Approve/Reject buttons become disabled
- Prevents accidental bulk operations

**How to Test:**
1. Click lock icon
2. Approve/Reject buttons should become disabled
3. Click unlock
4. Buttons should re-enable

---

### **4. Export Review Pack Button**
**Expected Behavior:**
1. Click "Export Review Pack"
2. Dropdown shows: DXF, DWG, IFC, PDF
3. Click PDF
4. API call: `POST /api/v1/export/project/5821`
5. Browser downloads file

**Requirements to Work:**
- ✅ Pending count must be 0 (all items approved/rejected)
- ✅ Not currently exporting
- ✅ No bulk operation in progress

**How to Test:**
```bash
# Test export via API directly
curl -X POST "http://localhost:9400/api/v1/export/project/5821" \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d '{
    "format": "pdf",
    "include_source": true,
    "include_approved_overlays": true
  }' \
  --output test_export.pdf

# Check if file was created
ls -lh test_export.pdf
```

---

## 🧪 **Create Mock Data for Testing**

Since project 5821 has no data, let's create some:

```bash
cd backend

# Run this Python script to create test overlay suggestions
../.venv/bin/python << 'EOF'
import asyncio
from app.core import database
from app.models.overlay import OverlaySuggestion
from sqlalchemy import select

async def create_test_overlays():
    async with database.AsyncSessionLocal() as session:
        # Check if overlays already exist
        result = await session.execute(
            select(OverlaySuggestion).where(OverlaySuggestion.project_id == 5821)
        )
        existing = result.scalars().all()

        if len(existing) > 0:
            print(f"✅ Found {len(existing)} existing overlays")
            return

        # Create test suggestions
        suggestions = [
            OverlaySuggestion(
                project_id=5821,
                code="SETBACK_VIOLATION",
                title="Facade Setback Issue",
                status="pending",
                score=0.95,
                rationale="Building exceeds required setback",
                engine_payload={"area_sqm": 120}
            ),
            OverlaySuggestion(
                project_id=5821,
                code="HEIGHT_COMPLIANCE",
                title="Height Limit Check",
                status="pending",
                score=0.88,
                rationale="Building height within limits",
                engine_payload={"area_sqm": 450}
            ),
        ]

        session.add_all(suggestions)
        await session.commit()
        print(f"✅ Created {len(suggestions)} test overlays")

asyncio.run(create_test_overlays())
EOF
```

Then refresh the Detection page!

---

## 📊 **Visual Testing Checklist**

Once you have data, you should see:

### **Before Any Actions:**
- [ ] Preview canvas shows colored rectangles (units)
- [ ] Pending count shows number > 0
- [ ] Layer buttons are clickable
- [ ] Approve/Reject buttons are enabled (if unlocked)
- [ ] Export button is disabled (pending items exist)

### **After Clicking "Approve All":**
- [ ] Network tab shows POST to `/api/v1/overlay/{id}/decision`
- [ ] Pending count drops to 0
- [ ] Units change color/layer
- [ ] Audit timeline updates
- [ ] Export button becomes enabled

### **After Clicking "Export" → "PDF":**
- [ ] Network tab shows POST to `/api/v1/export/project/{id}`
- [ ] Download starts in browser
- [ ] File appears in Downloads folder
- [ ] File can be opened (is valid PDF)

---

## 🔍 **Debugging Steps**

1. **Open Browser DevTools** (F12)
2. **Go to Console tab**
3. **Refresh page**
4. **Look for error messages** (red text)

Common errors and fixes:

| Error Message | Cause | Fix |
|--------------|-------|-----|
| `404 Not Found` | API endpoint missing | Check backend is running |
| `Failed to fetch` | Backend not responding | Restart backend |
| `items: [], count: 0` | No data for project | Upload CAD file or use different project |
| Button disabled | Intentional | Follow workflow (upload → pipeline → detection) |

---

## 🎬 **Complete Demo Workflow**

```bash
#!/bin/bash

echo "=== Complete CAD Detection Demo ==="
echo ""

# 1. Upload CAD file
echo "1. Uploading DXF file..."
IMPORT_RESPONSE=$(curl -s -X POST "http://localhost:9400/api/v1/import" \
  -H "X-Role: admin" \
  -F "file=@flat_two_bed.dxf" \
  -F "project_id=5821")

IMPORT_ID=$(echo $IMPORT_RESPONSE | python3 -c "import json, sys; print(json.load(sys.stdin).get('import_id', ''))")
echo "   Import ID: $IMPORT_ID"

# 2. Trigger parse
echo ""
echo "2. Parsing CAD file..."
curl -s -X POST "http://localhost:9400/api/v1/parse/$IMPORT_ID" \
  -H "X-Role: admin" > /dev/null
sleep 3

# 3. Run overlay detection
echo ""
echo "3. Running overlay pipeline..."
curl -s -X POST "http://localhost:9400/api/v1/overlay/5821/run" \
  -H "X-Role: admin" > /dev/null
sleep 2

# 4. Check results
echo ""
echo "4. Checking results..."
OVERLAY_COUNT=$(curl -s "http://localhost:9400/api/v1/overlay/5821" \
  -H "X-Role: admin" | python3 -c "import json, sys; print(json.load(sys.stdin).get('count', 0))")

if [ "$OVERLAY_COUNT" -gt "0" ]; then
    echo "   ✅ Found $OVERLAY_COUNT overlays!"
    echo ""
    echo "NOW GO TO: http://localhost:4400/#/cad/detection"
    echo "All buttons should work!"
else
    echo "   ⚠️  No overlays generated"
    echo "   Project may not have compatible geometry"
fi
```

---

## ✅ **Summary**

**The buttons aren't broken** - they're correctly disabled because there's no data!

**To fix:**
1. Upload a CAD file first (`/cad/upload`)
2. Run the overlay pipeline (`/cad/pipelines`)
3. Then go to Detection page (`/cad/detection`)
4. Now all buttons will work as expected

**Or** use the mock data script above to create test overlays immediately.

---

**Need help?** Check `/tmp/backend.log` for API errors or browser console for frontend errors.
