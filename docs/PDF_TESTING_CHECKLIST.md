# PDF Generation Testing Checklist

## Purpose
This checklist ensures all PDF generation features work correctly across different browsers and environments before code is committed.

## When to Use This Checklist
- Modifying any PDF generation code (`*_pack.py`, `pdf_generator.py`)
- Adding new PDF types or templates
- Changing PDF styling, fonts, or layouts
- Modifying file serving endpoints

---

## Backend Testing

### 1. API Endpoint Testing
- [ ] PDF generation endpoint returns HTTP 200
- [ ] Response includes `download_url` field
- [ ] Response includes `size_bytes` > 0
- [ ] Response includes correct `filename`
- [ ] File is saved to storage location

### 2. PDF Structure Validation
- [ ] Generate PDF via API:
  ```bash
  curl -X POST "http://localhost:9400/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/universal"
  ```
- [ ] Verify file size > 10KB (not empty/minimal)
- [ ] Check file exists in `.storage/uploads/reports/`
- [ ] Use PyPDF to verify content:
  ```python
  from pypdf import PdfReader
  reader = PdfReader('path/to/pdf')
  print(f"Pages: {len(reader.pages)}")
  print(f"Page 1 text: {reader.pages[0].extract_text()[:200]}")
  ```
- [ ] Verify PDF has expected number of pages (e.g., 11 for Universal Site Pack)
- [ ] Verify text extraction returns non-empty strings

---

## Manual Browser Testing (MANDATORY)

### 3. Local File Testing
- [ ] Download generated PDF to local file
- [ ] **macOS Preview**: Open PDF, verify all content visible
- [ ] **Safari**: Open PDF, verify all content visible (Safari is strictest)
- [ ] **Chrome/Brave**: Open PDF, verify all content visible
- [ ] **Firefox** (if available): Open PDF, verify all content visible

### 4. Content Verification
- [ ] All section headers are visible
- [ ] All tables display correctly
- [ ] All text is readable (no font issues)
- [ ] Page numbers appear correctly
- [ ] Cover page displays property information
- [ ] No blank pages (except intentional page breaks)

---

## Frontend Integration Testing

### 5. Download Button Testing
- [ ] Navigate to Marketing page in frontend
- [ ] Click "Generate Pack" button
- [ ] Wait for generation to complete
- [ ] Click "Download" link
- [ ] **Brave**: Verify file downloads to Downloads folder
- [ ] **Safari**: Verify file downloads without errors
- [ ] **Chrome**: Verify file downloads without errors
- [ ] Open downloaded file, verify content visible

### 6. Error Handling
- [ ] Test with invalid property ID (should return 404)
- [ ] Test with missing property data (should handle gracefully)
- [ ] Test concurrent downloads (multiple users)

---

## Automated Testing

### 7. Unit Tests
- [ ] Run PDF generation unit tests:
  ```bash
  pytest backend/tests/test_services/test_universal_site_pack.py -v
  ```
- [ ] All tests pass
- [ ] Coverage includes content validation

### 8. Integration Tests
- [ ] Run PDF download flow integration tests:
  ```bash
  pytest backend/tests/test_integration/test_pdf_download_flow.py -v
  ```
- [ ] All tests pass
- [ ] Tests cover full generate → download → verify flow

---

## Common Issues Checklist

### PDF Appears Blank
- [ ] Check if using SimpleDocTemplate (not BaseDocTemplate)
- [ ] Verify PDF metadata is set (title, author)
- [ ] Check if fonts are standard (Helvetica, Times, etc.)
- [ ] Verify flowables are being added to story
- [ ] Check for frame size issues

### Download Fails (HTTP 500)
- [ ] Verify download_url is absolute (includes http://localhost:9400)
- [ ] Check file exists in storage before serving
- [ ] Verify file path security checks pass
- [ ] Check backend logs for exceptions

### Safari Shows Blank
- [ ] Ensure PDF has title and author metadata
- [ ] Verify using standard PDF fonts
- [ ] Test in Safari specifically (don't assume Chrome = Safari)

---

## Testing Commands Reference

```bash
# Generate test PDF
curl -X POST "http://localhost:9400/api/v1/agents/commercial-property/properties/d47174ee-bb6f-4f3f-8baa-141d7c5d9051/generate-pack/universal" -H "Content-Type: application/json"

# Download PDF directly
curl "http://localhost:9400/api/v1/agents/commercial-property/files/{property_id}/{filename}" -o test.pdf

# Validate PDF with Python
python3 << EOF
from pypdf import PdfReader
reader = PdfReader('test.pdf')
print(f'Pages: {len(reader.pages)}')
for i in range(min(3, len(reader.pages))):
    text = reader.pages[i].extract_text()
    print(f'Page {i+1}: {len(text)} chars')
    print(text[:150])
EOF

# Run automated tests
pytest backend/tests/test_services/test_universal_site_pack.py -v
pytest backend/tests/test_integration/test_pdf_download_flow.py -v
```

---

## Sign-Off

Before committing PDF-related changes:

**I confirm that I have:**
- [ ] Completed all backend testing steps
- [ ] Manually verified PDF in Safari, Chrome, and Brave
- [ ] Tested download functionality from frontend
- [ ] Run all automated tests (passing)
- [ ] Verified no regression in existing PDF types

**Developer Signature:** ________________
**Date:** ________________

---

## Related Documentation
- [CODING_RULES.md](CODING_RULES.md) - General coding standards
- [CONTRIBUTING.md](CONTRIBUTING.md) - PDF development guidelines
- [Known Testing Issues](all_steps_to_product_completion.md#-known-testing-issues) - Known test limitations
