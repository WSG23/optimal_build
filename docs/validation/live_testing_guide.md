# ✅ Live Testing Guide - Finance & Intelligence Pages

> Need the broader feature plan or next development step? See `docs/feature_delivery_plan_v2.md` for the current roadmap and where implementation last paused.

## 🎯 You should now have http://localhost:4400/#/finance open

---

## **Test 1: Finance Page** ✅ **DATA CONFIRMED: 4 Scenarios**

### **What You Should See:**

#### **Top Section - Scenario Table**
Look for a table with 4 rows:
1. **Scenario A – Base Case**
   - NPV: -$375,862 SGD (negative)
   - IRR: 6.88%

2. **Scenario B – Upside Release**
   - NPV: $1,270,733 SGD (positive!)
   - IRR: 10.91%

3. **Scenario C – Downside Stress**
   - NPV: -$4,160,673 SGD (very negative)
   - IRR: -7.45% (negative return!)

4. **Debug Scenario**
   - NPV: -$537 SGD
   - IRR: -50%

#### **✨ Test the Refresh Button:**
- **Location:** Top right corner
- **Action:** Click "Refresh" button
- **Expected:** Button text changes to "Refreshing..." then back to "Refresh"
- **Result:** Table data reloads (may flash briefly)

---

### **Middle Section - Capital Stack Chart**

**Scroll down** - You should see:

#### **Bar Chart Visualization**
- Shows Equity vs Debt breakdown for each scenario
- **Scenario A:** 40% Equity (green), 60% Debt (red)
- **Scenario B:** Has 3 slices - Equity, Senior Loan, Mezzanine Loan
- **Scenario C:** Has Bridge Facility

#### **Summary Stats**
Each scenario shows:
- Total amount
- Loan-to-Cost ratio
- Weighted average debt rate

**✅ This proves charts are rendering!**

---

### **Bottom Section - Drawdown Schedule**

**Keep scrolling** - You should see:

#### **Timeline Chart**
- Shows how equity and debt are drawn over 6 months (M1-M6)
- Area chart with two colors:
  - Equity draws (one color)
  - Debt draws (another color)

#### **Key Metrics**
- Total Equity
- Total Debt
- Peak Debt Balance
- Final Debt Balance

**✅ This proves interactive charts work!**

---

## 📸 **Screenshot Checklist - Finance Page**

Take screenshots of:
- [ ] Scenario table (top)
- [ ] Capital stack chart (middle)
- [ ] Drawdown schedule (bottom)
- [ ] Refresh button (before & after click)

---

## **Test 2: Intelligence Page** (Next!)

Now click on **"Intelligence"** in the left sidebar, or open:
```
http://localhost:4400/#/visualizations/intelligence
```

### **What You Should See:**

#### **Section 1: Graph Intelligence**
- **Network visualization** (even if simple stub data)
- Shows nodes and edges
- Summary text about relationships

#### **Section 2: Predictive Intelligence**
- **Segment analysis**
- Shows adoption rates
- Predicted segments with probabilities

#### **Section 3: Cross-Correlation Analysis**
- **Factor relationships**
- Correlation matrix or list
- P-values and significance

---

## 🎯 **Interactive Tests You Can Do**

### **On Finance Page:**
1. ✅ **Click Refresh** → See network request in DevTools
2. ✅ **Scroll through all sections** → Verify charts render
3. ✅ **Read scenario data** → Compare NPV/IRR values
4. ✅ **Check if charts animate** → Some may have transitions

### **On Intelligence Page:**
1. ✅ **Read each section** → See what data displays
2. ✅ **Check for loading states** → Should show data immediately (no loading spinner)
3. ✅ **Look for error messages** → Should be none
4. ✅ **Open DevTools Console** → Check for JavaScript errors

---

## 🐛 **If You Don't See Data:**

### **Finance Page Troubleshooting:**
```javascript
// Paste in browser console:
fetch('http://localhost:9400/api/v1/finance/scenarios?project_id=401', {
  headers: {'X-Role': 'admin'}
}).then(r => r.json()).then(d => console.log(`Found ${d.length} scenarios`, d))
```

**Expected:** Console shows: `Found 4 scenarios`

### **Intelligence Page Troubleshooting:**
```javascript
// Paste in browser console:
Promise.all([
  fetch('http://localhost:9400/api/v1/analytics/intelligence/graph?workspaceId=default-investigation', {headers: {'X-Role': 'admin'}}).then(r => r.json()),
  fetch('http://localhost:9400/api/v1/analytics/intelligence/predictive?workspaceId=default-investigation', {headers: {'X-Role': 'admin'}}).then(r => r.json()),
  fetch('http://localhost:9400/api/v1/analytics/intelligence/cross-correlation?workspaceId=default-investigation', {headers: {'X-Role': 'admin'}}).then(r => r.json())
]).then(([graph, pred, corr]) => {
  console.log('Graph:', graph.status)
  console.log('Predictive:', pred.status)
  console.log('Correlation:', corr.status)
})
```

**Expected:** All show `status: "ok"`

---

## 📊 **What This Proves:**

If you see data on these pages, it means:

✅ **Backend API works**
✅ **Frontend React components render**
✅ **Charts/visualizations work**
✅ **Data flows from API → UI correctly**
✅ **Buttons trigger actions**
✅ **State management works**

**In other words: THE APP WORKS!** 🎉

The Detection page just needs data - it's not broken.

---

## 🎬 **After Testing:**

Tell me what you see:

1. **Finance Page:**
   - Do you see 4 scenarios? YES / NO
   - Do you see charts? YES / NO
   - Does Refresh button work? YES / NO

2. **Intelligence Page:**
   - Do you see all 3 sections? YES / NO
   - Do you see data in each? YES / NO
   - Any errors in console? YES / NO

Then we can decide:
- **Option A:** Keep testing other features
- **Option B:** Build the CAD workflow to populate Detection page
- **Option C:** Build something brand new

**Your feedback will guide what we do next!** 🚀
