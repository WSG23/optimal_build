# 🔍 CAD Detection Page - Feature Testing & Debugging Guide

## 📍 Location
**URL:** http://localhost:4400/#/cad/detection
**Page:** CAD Detection
**Purpose:** Review and approve/reject detected building overlays

---

## 🎯 What This Page Does

This page loads **overlay suggestions** for Project ID 5821 and allows you to:
1. **View detected units** on a preview canvas
2. **Toggle layers** (source, pending, approved, rejected)
3. **Bulk approve/reject** pending overlays
4. **Lock/unlock zone editing**
5. **Export** approved overlays to DXF/DWG/IFC/PDF

---

## 🐛 Why Buttons Appear Disabled/Broken

### **"Export Review Pack" Button**
**Status:** ❌ Disabled when there are pending items
**Reason:** Line 287 in CadDetectionPage.tsx
```typescript
disabled={pendingCount > 0 || exporting || mutationPending}
```

**How to Fix:**
You need to either:
1. **Approve all pending items** first, OR
2. **Wait for data to load** (project 5821 needs overlay suggestions)

---

## 🧪 Step-by-Step Testing Guide

### **Step 1: Check if Data Exists**

```bash
# Check if project 5821 has overlay suggestions
curl -s "http://localhost:9400/api/v1/overlay/suggestions/5821" \
  -H "X-Role: admin" | python3 -m json.tool
```

**Expected:** Should return an array of suggestions
**If empty:** You need to seed data first (see "Seeding Data" below)

---

### **Step 2: Check Audit Trail**

```bash
# Check project audit events
curl -s "http://localhost:9400/api/v1/audit/trail/5821?event_type=overlay_decision" \
  -H "X-Role: admin" | python3 -m json.tool
```

**Expected:** Shows approval/rejection history

---

### **Step 3: Open Browser Console**

1. Open the page: http://localhost:4400/#/cad/detection
2. Open DevTools (F12 or Cmd+Option+I)
3. Go to **Console** tab
4. Look for errors (red text)

**Common Errors:**
- `404 Not Found` → Endpoint doesn't exist or project has no data
- `Failed to fetch` → Backend not running
- `Network Error` → CORS or connection issue

---

### **Step 4: Check Network Tab**

1. Open DevTools → **Network** tab
2. Refresh the page
3. Look for these requests:

| Request | URL | Expected Status |
|---------|-----|----------------|
| List Suggestions | `/api/v1/overlay/suggestions/5821` | 200 OK |
| Audit Trail | `/api/v1/audit/trail/5821` | 200 OK |

**If 404:** The endpoints don't exist or project ID 5821 has no data

---

## 🔧 What Each Button Does

### **1. Layer Toggle Panel**
**Location:** Left side of page
**Buttons:** Source / Pending / Approved / Rejected

**Function:**
- Toggle visibility of each layer type on the preview
- Click to show/hide that layer
- Multiple layers can be active at once

**Test:**
```javascript
// In browser console
console.log("Active layers:", document.querySelectorAll('.layer-toggle-panel button[aria-pressed="true"]'))
```

---

### **2. Bulk Review Controls**
**Location:** Middle section
**Buttons:** "Approve All" / "Reject All"

**Function:**
- Approves/rejects ALL pending suggestions at once
- Disabled when: locked, mutation in progress, or no pending items
- Makes API calls to `/api/v1/overlay/decide`

**Why Disabled:**
```javascript
disabled={locked || mutationPending}
```

**Test:**
1. Click "Approve All"
2. Watch Network tab for POST requests to `/api/v1/overlay/decide`
3. Check Console for errors

---

### **3. Zone Lock Controls**
**Location:** Right side
**Button:** Lock/Unlock toggle

**Function:**
- Prevents accidental modifications
- When locked, Approve/Reject buttons are disabled
- Just a UI safety feature (doesn't call API)

**Test:**
1. Click lock button
2. Try clicking "Approve All" → should be disabled
3. Unlock → buttons should re-enable

---

### **4. Export Dialog**
**Location:** Bottom right
**Button:** "Export Review Pack"
**Options:** DXF, DWG, IFC, PDF

**Function:**
- Exports approved overlays to selected format
- Downloads file to your computer
- Calls `/api/v1/export/project/5821`

**Why Not Working:**
```javascript
// From line 287
disabled={pendingCount > 0 || exporting || mutationPending}
```

**Conditions to enable:**
1. ✅ `pendingCount === 0` (no pending items)
2. ✅ `exporting === false` (not currently exporting)
3. ✅ `mutationPending === false` (no bulk operation in progress)

**Test:**
```bash
# Try export via API directly
curl -X POST "http://localhost:9400/api/v1/export/project/5821" \
  -H "Content-Type: application/json" \
  -H "X-Role: admin" \
  -d '{
    "format": "pdf",
    "include_source": true,
    "include_approved_overlays": true,
    "include_pending_overlays": false,
    "include_rejected_overlays": false
  }' \
  --output test_export.pdf
```

**Expected:** Downloads a PDF file
**If 404:** Export endpoint not implemented yet
**If 500:** Backend error (check logs)

---

## 🌱 Seeding Test Data

If project 5821 has no data, you need to seed it:

```bash
cd backend

# Option 1: Run overlay seeding script (if exists)
../.venv/bin/python scripts/seed_overlays.py

# Option 2: Create test project manually via API
curl -X POST "http://localhost:9400/api/v1/overlay/run/5821" \
  -H "X-Role: admin"
```

---

## 🔍 Debugging Checklist

### **When Export Button is Disabled:**

- [ ] Open browser console
- [ ] Check `pendingCount` value:
  ```javascript
  // In console
  document.querySelector('.bulk-review-controls').textContent
  ```
- [ ] If it says "X pending", you need to approve/reject them first
- [ ] If it says "0 pending", check if `exporting` or `mutationPending` is true

### **When Approve/Reject Buttons Do Nothing:**

- [ ] Check if zone is locked (unlock button should be unchecked)
- [ ] Open Network tab
- [ ] Click "Approve All"
- [ ] Look for POST request to `/api/v1/overlay/decide`
- [ ] Check response status (200 = success, 4xx/5xx = error)
- [ ] Check Console for JavaScript errors

### **When Nothing Loads:**

- [ ] Check Network tab for failed requests
- [ ] Verify backend is running: `curl http://localhost:9400/health`
- [ ] Check if project 5821 exists:
  ```bash
  curl -s "http://localhost:9400/api/v1/overlay/suggestions/5821" -H "X-Role: admin"
  ```
- [ ] Look for errors in `/tmp/backend.log`

---

## 📊 Expected API Responses

### **List Suggestions**
```json
[
  {
    "id": 1,
    "code": "FACADE_SETBACK",
    "title": "Facade Setback Violation",
    "status": "pending",
    "score": 0.95,
    "rationale": "Building exceeds setback limit",
    "enginePayload": {"area_sqm": 120}
  }
]
```

### **Decide Overlay**
```json
{
  "suggestionId": 1,
  "decision": "approved",
  "decidedBy": "Planner"
}
```

### **Export Project**
Binary file download (DXF/DWG/IFC/PDF)

---

## 🚀 Quick Test Script

```bash
#!/bin/bash
PROJECT_ID=5821

echo "Testing CAD Detection Features..."
echo ""

echo "1. Check overlay suggestions..."
curl -s "http://localhost:9400/api/v1/overlay/suggestions/$PROJECT_ID" \
  -H "X-Role: admin" > /tmp/suggestions.json

SUGGESTION_COUNT=$(cat /tmp/suggestions.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "   Found $SUGGESTION_COUNT suggestions"

if [ "$SUGGESTION_COUNT" -eq "0" ]; then
    echo "   ⚠️  No suggestions found - need to run overlay pipeline"
    echo ""
    echo "2. Running overlay pipeline..."
    curl -X POST "http://localhost:9400/api/v1/overlay/run/$PROJECT_ID" \
      -H "X-Role: admin"
else
    echo "   ✅ Data exists"
fi

echo ""
echo "3. Check audit trail..."
curl -s "http://localhost:9400/api/v1/audit/trail/$PROJECT_ID?event_type=overlay_decision" \
  -H "X-Role: admin" > /tmp/audit.json

AUDIT_COUNT=$(cat /tmp/audit.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "   Found $AUDIT_COUNT audit events"

echo ""
echo "Done! Now open: http://localhost:4400/#/cad/detection"
```

---

## 💡 Tips

1. **Always check browser console first** - Most issues show error messages there
2. **Use Network tab** to see API calls and responses
3. **Check `/tmp/backend.log`** for server-side errors
4. **Pending count must be 0** before export works
5. **Lock must be off** before approve/reject works

---

## ❓ Common Questions

### Q: Why doesn't clicking Export do anything?
**A:** Export is disabled when `pendingCount > 0`. Approve/reject all pending items first.

### Q: How do I approve a single item (not bulk)?
**A:** Currently only bulk operations are implemented. Individual item review requires enhancement.

### Q: Where does the exported file go?
**A:** Downloads folder (browser downloads the file via blob URL)

### Q: What format should I choose?
**A:**
- **DXF/DWG** - For AutoCAD
- **IFC** - For BIM software (Revit, ArchiCAD)
- **PDF** - For viewing/printing

---

## 🔗 Related Pages

- **Upload:** `/cad/upload` - Upload DXF/IFC files
- **Pipelines:** `/cad/pipelines` - Run automation pipelines
- **Detection:** `/cad/detection` - **YOU ARE HERE**

---

**Happy Testing! 🎉**

If buttons still don't work after following this guide, check the browser console and share the error message!
