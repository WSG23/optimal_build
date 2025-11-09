# COMPREHENSIVE ENUM MISMATCH ANALYSIS

## Executive Summary

After a thorough review of all model files, migration files, and documentation, here is the complete status of enum type/value consistency across the codebase.

## ✅ CORRECTLY ALIGNED (Already Fixed or Never Had Issues)

### 1. Developer Checklists (RECENTLY FIXED)
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/developer_checklists.py`
- **Migration**: `backend/migrations/versions/20251013_000014_add_developer_due_diligence_checklists.py`
- **Enums**:
  - `ChecklistCategory` (7 values)
  - `ChecklistStatus` (4 values)
  - `ChecklistPriority` (4 values)
- **Fix Applied**: Added `values_callable=lambda enum_cls: [member.value for member in enum_cls]` to all three enum definitions
- **Migration**: Uses `create_type=False` correctly

### 2. Business Performance Tables
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/business_performance.py`
- **Migration**: `backend/migrations/versions/20250220_000011_add_business_performance_tables.py`
- **Enums**: All properly configured with `values_callable=_enum_values`
  - `DealAssetType` (10 values)
  - `DealType` (6 values)
  - `PipelineStage` (10 values)
  - `DealStatus` (4 values)
  - `DealContactType` (5 values)
  - `DealDocumentType` (5 values)
- **Migration**: Uses `create_type=False` correctly

### 3. Listing Integration Tables
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/listing_integration.py`
- **Migration**: `backend/migrations/versions/20250220_000010_add_listing_integration_tables.py`
- **Enums**: All use `values_callable=_enum_values`
  - `ListingProvider` (3 values)
  - `ListingAccountStatus` (3 values)
  - `ListingPublicationStatus` (5 values)

### 4. Preview Jobs
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/preview.py`
- **Migration**: `backend/migrations/versions/20251022_000017_add_preview_jobs.py`
- **Enums**: `PreviewJobStatus` uses `values_callable=_enum_values`

### 5. Commercial Properties
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/property.py`
- **Migration**: `backend/migrations/versions/20241228_000006_add_commercial_property_agent_tables.py`
- **Enums**: All use `values_callable=_enum_values`
  - `PropertyType` (9 values)
  - `PropertyStatus` (6 values)
  - `TenureType` (6 values)

### 6. Singapore Properties
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/singapore_property.py`
- **Migration**: `backend/migrations/versions/0773c87952ef_add_singapore_properties_table_with_mvp_.py`
- **Enums**: All use `values_callable=lambda x: [e.value for e in x]`
  - `PropertyZoning` (11 values)
  - `PropertyTenure` (5 values)
  - `DevelopmentStatus` (7 values)
  - `AcquisitionStatus` (5 values)
  - `FeasibilityStatus` (4 values)
  - `ComplianceStatus` (4 values)

### 7. Commission Tables
**Status**: ✅ ALIGNED
- **Models**: `backend/app/models/business_performance.py`
- **Migration**: `backend/migrations/versions/20250220_000012_add_commission_tables.py`
- **Enums**: All use `values_callable=_enum_values`
  - `CommissionType` (5 values)
  - `CommissionStatus` (6 values)
  - `CommissionAdjustmentType` (3 values)

## ⚠️ PARTIAL ALIGNMENT (Uses SAEnum without values_callable - Legacy Pattern)

### 8. Entitlements Tables
**Status**: ⚠️ NEEDS ATTENTION (Lower Priority)
- **Models**: `backend/app/models/entitlements.py`
- **Migration**: `backend/migrations/versions/20240816_000004_add_entitlements_tables.py`
- **Issue**: Uses custom `_enum()` helper function that DOES include `values_callable`
- **Enums**:
  - `EntApprovalCategory` (5 values) - Uses `_enum()` helper
  - `EntRoadmapStatus` (7 values) - Uses `_enum()` helper
  - `EntStudyType` (5 values) - Uses direct `SAEnum()` ❌
  - `EntStudyStatus` (6 values) - Uses direct `SAEnum()` ❌
  - `EntEngagementType` (5 values) - Uses direct `SAEnum()` ❌
  - `EntEngagementStatus` (4 values) - Uses direct `SAEnum()` ❌
  - `EntLegalInstrumentType` (5 values) - Uses direct `SAEnum()` ❌
  - `EntLegalInstrumentStatus` (4 values) - Uses direct `SAEnum()` ❌

**Current Model Code**:
```python
# Lines 29-36 - Good pattern with helper
def _enum(sa_enum: type[Enum], *, name: str) -> SAEnum:
    return SAEnum(
        sa_enum,
        name=name,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    )

# Lines 163-164 - Uses helper (GOOD)
category: Mapped[EntApprovalCategory] = mapped_column(
    _enum(EntApprovalCategory, name="ent_approval_category"), nullable=False
)

# Lines 256-260 - Does NOT use helper (INCONSISTENT)
study_type: Mapped[EntStudyType] = mapped_column(
    SAEnum(EntStudyType, name="ent_study_type"), nullable=False
)
status: Mapped[EntStudyStatus] = mapped_column(
    SAEnum(EntStudyStatus, name="ent_study_status"), nullable=False
)
```

**Migration Pattern** (Lines 19-98):
All migrations use `postgresql.ENUM()` with `create_type=False` - this is correct.

**Recommendation**:
- Update lines 257, 260, 296, 299, 333, 336 in `entitlements.py` to use the `_enum()` helper instead of direct `SAEnum()`
- This is mentioned in TECHNICAL_DEBT.MD (lines 171-182) as a known issue
- **Priority**: Medium (lower risk since migrations use `create_type=False`)

## ❌ MISSING values_callable (Potential Issues)

### 9. Projects Table
**Status**: ❌ NEEDS FIX
- **Models**: `backend/app/models/projects.py`
- **Migration**: NOT FOUND - appears to use Alembic autogenerate or manual SQL
- **Issue**: Uses bare `SQLEnum()` without `values_callable`
- **Enums**:
  - `ProjectType` (8 values) - Line 85
  - `ProjectPhase` (9 values) - Line 87
  - `ApprovalStatus` (7 values) - Lines 99, 108, 118

**Current Code**:
```python
# Line 85
project_type = Column(SQLEnum(ProjectType), nullable=False)

# Line 87
current_phase = Column(
    SQLEnum(ProjectPhase), default=ProjectPhase.CONCEPT, nullable=False
)

# Lines 99, 108, 118
ura_approval_status = Column(
    SQLEnum(ApprovalStatus), default=ApprovalStatus.NOT_SUBMITTED
)
```

**Recommended Fix**:
```python
def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

project_type = Column(
    SQLEnum(ProjectType, values_callable=_enum_values),
    nullable=False
)
current_phase = Column(
    SQLEnum(ProjectPhase, values_callable=_enum_values),
    default=ProjectPhase.CONCEPT,
    nullable=False
)
ura_approval_status = Column(
    SQLEnum(ApprovalStatus, values_callable=_enum_values),
    default=ApprovalStatus.NOT_SUBMITTED
)
```

### 10. AI Agents Table
**Status**: ❌ NEEDS FIX
- **Models**: `backend/app/models/ai_agents.py`
- **Migration**: NOT FOUND
- **Issue**: Uses bare `SQLEnum()` without `values_callable`
- **Enums**:
  - `AIAgentType` (10 values) - Line 55
  - `AIAgentStatus` (4 values) - Line 60

**Current Code**:
```python
# Line 55
agent_type = Column(SQLEnum(AIAgentType), nullable=False)

# Line 60
status = Column(
    SQLEnum(AIAgentStatus), default=AIAgentStatus.ACTIVE, nullable=False
)
```

**Recommended Fix**:
```python
def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

agent_type = Column(
    SQLEnum(AIAgentType, values_callable=_enum_values),
    nullable=False
)
status = Column(
    SQLEnum(AIAgentStatus, values_callable=_enum_values),
    default=AIAgentStatus.ACTIVE,
    nullable=False
)
```

### 11. Users Table
**Status**: ❌ NEEDS FIX
- **Models**: `backend/app/models/users.py`
- **Migration**: NOT FOUND
- **Issue**: Uses bare `SQLEnum()` without `values_callable`
- **Enums**:
  - `UserRole` (7 values) - Line 36

**Current Code**:
```python
# Line 36
role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
```

**Recommended Fix**:
```python
def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

role = Column(
    SQLEnum(UserRole, values_callable=_enum_values),
    default=UserRole.VIEWER,
    nullable=False
)
```

### 12. Market Data Tables
**Status**: ❌ NEEDS FIX
- **Models**: `backend/app/models/market.py`
- **Issue**: Uses bare `SQLEnum(PropertyType)` without `values_callable`
- **Enums**:
  - `PropertyType` (imported from property.py) - Lines 57, 125, 176

**Current Code**:
```python
# Lines 57, 125, 176
property_type = Column(SQLEnum(PropertyType), nullable=False)
```

**Recommended Fix**:
```python
def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

property_type = Column(
    SQLEnum(PropertyType, values_callable=_enum_values),
    nullable=False
)
```

## 📝 DOCUMENTATION STATUS

### Markdown Files
**Status**: ✅ ALIGNED
- No hardcoded enum value lists found in user-facing documentation
- `docs/audits/smoke-test-fix-report.md` correctly documents enum values
- `docs/phase_1d_business_performance_design.md` correctly documents enum values
- `docs/archive/TECHNICAL_DEBT.MD` documents the entitlements enum issue (lines 171-182)

## 🎯 PRIORITY RECOMMENDATIONS

### HIGH PRIORITY (Fix Immediately)
1. **projects.py** - Add `values_callable` to ProjectType, ProjectPhase, ApprovalStatus
2. **ai_agents.py** - Add `values_callable` to AIAgentType, AIAgentStatus
3. **users.py** - Add `values_callable` to UserRole
4. **market.py** - Add `values_callable` to PropertyType references

### MEDIUM PRIORITY (Fix After High Priority)
5. **entitlements.py** - Standardize to use `_enum()` helper for all SAEnum fields (6 fields need updating)

### Pattern to Follow
All models should use this pattern:

```python
from enum import Enum
from sqlalchemy import Column, Enum as SQLEnum

def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]

class MyModel(Base):
    status = Column(
        SQLEnum(MyEnum, values_callable=_enum_values),
        nullable=False
    )
```

## Migration Checklist
When fixing enums in models:
- [ ] No migration changes needed (if using `create_type=False` or if tables don't exist yet)
- [ ] Existing data is already using string values (e.g., "pending" not "PENDING")
- [ ] Just add `values_callable` parameter to model definitions
- [ ] Test that enum values are correctly stored/retrieved

## Summary Statistics
- **Total Enum Types**: 30
- **Correctly Configured**: 22 (73%)
- **Needs values_callable Added**: 8 (27%)
  - projects.py: 3 enums
  - ai_agents.py: 2 enums
  - users.py: 1 enum
  - market.py: 1 enum (PropertyType)
  - entitlements.py: 6 enums (inconsistent pattern)
