# Advanced Intelligence Module - Data Sources & Integration Plan

> **Last Updated:** 2025-01-12
> **Status:** Planning Document
> **Related Files:**
> - Frontend: `frontend/src/pages/visualizations/AdvancedIntelligence.tsx`
> - Backend: `backend/app/api/v1/advanced_intelligence.py`
> - RAG Service: `backend/app/services/intelligence.py`
> - Vector Store: `backend/app/core/rag.py`

---

## Overview

The Advanced Intelligence module provides predictive analytics and relationship insights across the platform. Currently, all endpoints return **stubbed sample data**. This document outlines the real data sources and implementation plan for each component.

---

## 1. Workspace Signals (Hero KPI Cards)

### Current Implementation
- **Location:** `AdvancedIntelligencePage` lines 42-64
- **Status:** Derived from predictive segments (stubbed)
- **Components:** 4 KPI cards with sparkline trends

### Metrics to Implement

| Metric | Description | Data Source | Calculation |
|--------|-------------|-------------|-------------|
| **Adoption Likelihood** | Probability users will adopt recommended actions | `agent_performance_snapshots`, `agent_deals` | % of recommendations acted upon in last 30 days |
| **Projected Uplift** | Expected improvement from optimizations | `fin_scenarios` comparisons, deal outcomes | Average improvement % when suggestions followed |
| **Active Experiments** | Number of concurrent A/B tests or pilot features | New `experiments` table or feature flags | COUNT of active experiments |
| **Intelligence Score** | Overall platform intelligence health | Composite metric | Weighted average of data freshness, model accuracy, coverage |

### Required Database Queries

```sql
-- Adoption Likelihood: % of suggestions acted upon
SELECT
  COUNT(CASE WHEN acted_upon = true THEN 1 END)::float /
  NULLIF(COUNT(*), 0) * 100 as adoption_rate
FROM ai_suggestions
WHERE created_at > NOW() - INTERVAL '30 days';

-- Projected Uplift: Average improvement when suggestions followed
SELECT AVG(
  (outcome_value - baseline_value) / NULLIF(baseline_value, 0) * 100
) as avg_uplift
FROM ai_suggestion_outcomes
WHERE followed = true AND outcome_date > NOW() - INTERVAL '90 days';
```

### New Tables Required

```python
# backend/app/models/intelligence.py
class AISuggestion(Base):
    """Tracks AI-generated suggestions and their outcomes."""
    __tablename__ = "ai_suggestions"

    id = Column(UUID, primary_key=True, default=uuid4)
    workspace_id = Column(String, index=True)
    suggestion_type = Column(String)  # 'deal_optimization', 'pricing', 'timing'
    suggestion_text = Column(Text)
    confidence_score = Column(Numeric(4, 3))
    acted_upon = Column(Boolean, default=False)
    outcome_value = Column(Numeric(16, 2), nullable=True)
    baseline_value = Column(Numeric(16, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    outcome_date = Column(DateTime(timezone=True), nullable=True)
```

---

## 2. Relationship Intelligence (Network Graph)

### Current Implementation
- **Location:** `_sample_graph_payload()` in backend
- **Status:** Hardcoded nodes (Lead Operations, Capital Stack Review, etc.)
- **Component:** Force-directed graph with D3.js

### Real Data Sources

| Node Type | Source Table | Attributes |
|-----------|--------------|------------|
| **Team Members** | `users` | id, name, role, department |
| **Workflows** | `agent_deals.pipeline_stage` | stage names, frequency |
| **Partners** | `agent_deal_contacts` | contact_type, company |
| **Projects** | `projects` | id, name, status |

| Edge Type | Source | Weight Calculation |
|-----------|--------|-------------------|
| **Team ↔ Team** | `audit_logs` | Co-occurrence in same project actions |
| **Team ↔ Workflow** | `agent_deal_stage_events` | User's stage transition frequency |
| **Workflow ↔ Workflow** | `agent_deals` | Sequential stage progression patterns |

### Implementation Service

```python
# backend/app/services/intelligence/graph_builder.py
from collections import defaultdict
from sqlalchemy import select, func
from app.models import AuditLog, AgentDeal, AgentDealStageEvent, User

class RelationshipGraphBuilder:
    """Builds collaboration graph from operational data."""

    async def build_graph(self, workspace_id: str, db: AsyncSession) -> dict:
        nodes = []
        edges = []

        # 1. Get active users as team nodes
        users = await self._get_active_users(db, workspace_id)
        for user in users:
            nodes.append({
                "id": f"user_{user.id}",
                "label": user.name,
                "category": "team",
                "score": await self._calculate_user_activity_score(db, user.id)
            })

        # 2. Get workflow stages as workflow nodes
        stages = await self._get_active_stages(db, workspace_id)
        for stage in stages:
            nodes.append({
                "id": f"stage_{stage}",
                "label": stage.replace("_", " ").title(),
                "category": "workflow",
                "score": await self._calculate_stage_throughput(db, stage)
            })

        # 3. Calculate co-occurrence edges
        edges = await self._calculate_cooccurrence_edges(db, workspace_id)

        return {
            "kind": "graph",
            "status": "ok",
            "summary": f"Collaboration graph with {len(nodes)} nodes and {len(edges)} connections",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "graph": {"nodes": nodes, "edges": edges}
        }

    async def _calculate_cooccurrence_edges(self, db: AsyncSession, workspace_id: str) -> list:
        """Calculate edges based on users working on same deals."""
        # Query audit_logs for users who touched same deals
        query = """
            SELECT
                a1.user_id as user1,
                a2.user_id as user2,
                COUNT(*) as cooccurrence
            FROM audit_logs a1
            JOIN audit_logs a2 ON a1.entity_id = a2.entity_id
                AND a1.entity_type = a2.entity_type
                AND a1.user_id < a2.user_id
            WHERE a1.entity_type = 'deal'
                AND a1.created_at > NOW() - INTERVAL '90 days'
            GROUP BY a1.user_id, a2.user_id
            HAVING COUNT(*) >= 3
        """
        # ... implementation
```

---

## 3. Predictive Forecast (Confidence Gauges)

### Current Implementation
- **Location:** `_sample_predictive_payload()` in backend
- **Status:** Hardcoded segments (Operations champions, Compliance fast-lane, etc.)
- **Component:** Progress bars with probability %

### Real Data Sources

| Segment | Description | Prediction Target | Features |
|---------|-------------|-------------------|----------|
| **Deal Conversion** | Likelihood deal closes successfully | `agent_deals.status = 'closed_won'` | stage duration, confidence %, contact count |
| **Timeline Adherence** | Project stays on schedule | `development_phases.actual_end_date <= planned_end_date` | phase type, heritage flag, dependencies |
| **Finance Approval** | Scenario gets stakeholder sign-off | `fin_scenarios.status = 'approved'` | NPV, IRR, LTV, sensitivity results |
| **Compliance Speed** | Regulatory approval timeline | `regulatory_submissions.approved_at - submitted_at` | authority type, heritage classification |

### ML Pipeline Requirements

```python
# backend/app/services/intelligence/predictive_model.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib

class DealConversionPredictor:
    """Predicts deal conversion probability."""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = ".storage/models/deal_conversion_v1.joblib"

    def extract_features(self, deal: AgentDeal) -> list:
        """Extract features from a deal for prediction."""
        return [
            deal.confidence or 0.5,
            len(deal.contacts),
            self._days_in_current_stage(deal),
            self._stage_to_ordinal(deal.pipeline_stage),
            deal.estimated_value_amount or 0,
            1 if deal.project_id else 0,  # has linked project
        ]

    def predict(self, deal: AgentDeal) -> dict:
        """Predict conversion probability for a deal."""
        if not self.model:
            self.model = joblib.load(self.model_path)

        features = self.extract_features(deal)
        features_scaled = self.scaler.transform([features])
        probability = self.model.predict_proba(features_scaled)[0][1]

        return {
            "segmentId": f"deal_{deal.id}",
            "segmentName": deal.title,
            "baseline": deal.estimated_value_amount or 0,
            "projection": (deal.estimated_value_amount or 0) * probability,
            "probability": round(probability, 2)
        }
```

### Training Data Collection

To train the model, we need historical deal outcomes:

```sql
-- Training data for deal conversion model
SELECT
    d.id,
    d.confidence,
    (SELECT COUNT(*) FROM agent_deal_contacts WHERE deal_id = d.id) as contact_count,
    EXTRACT(DAYS FROM d.actual_close_date - d.created_at) as days_to_close,
    d.pipeline_stage,
    d.estimated_value_amount,
    CASE WHEN d.status = 'closed_won' THEN 1 ELSE 0 END as converted
FROM agent_deals d
WHERE d.status IN ('closed_won', 'closed_lost')
    AND d.created_at > '2024-01-01';
```

---

## 4. Cross-Correlation (Heatmap)

### Current Implementation
- **Location:** `_sample_correlation_payload()` in backend
- **Status:** Hardcoded correlations (Finance readiness ↔ Approval speed, etc.)
- **Component:** Color-coded correlation matrix

### Real Data Sources

| Driver Metric | Outcome Metric | Source Tables |
|---------------|----------------|---------------|
| Finance readiness score | Approval speed (days) | `fin_scenarios`, `regulatory_submissions` |
| Legal review latency | Iteration count | `agent_deal_documents`, `agent_deal_stage_events` |
| Capital stack completeness | Stakeholder alignment | `capital_stack_tranches`, `project_team_members` |
| Site logistics score | Schedule risk | `development_phases`, `phase_milestones` |

### Statistical Service

```python
# backend/app/services/intelligence/correlation_analyzer.py
import numpy as np
from scipy import stats
from sqlalchemy import select, func

class CorrelationAnalyzer:
    """Computes cross-correlations between operational metrics."""

    async def analyze(self, workspace_id: str, db: AsyncSession) -> dict:
        relationships = []

        # 1. Finance readiness vs Approval speed
        finance_data = await self._get_finance_readiness_data(db, workspace_id)
        approval_data = await self._get_approval_speed_data(db, workspace_id)

        if len(finance_data) >= 10:  # Minimum sample size
            corr, pvalue = stats.pearsonr(finance_data, approval_data)
            relationships.append({
                "pairId": "finance-readiness_approval-speed",
                "driver": "Finance readiness score",
                "outcome": "Approval speed (days)",
                "coefficient": round(corr, 2),
                "pValue": round(pvalue, 3)
            })

        # 2. Legal latency vs Iterations
        # ... similar pattern

        return {
            "kind": "correlation",
            "status": "ok",
            "summary": f"Cross-correlations based on {len(relationships)} metric pairs",
            "updatedAt": datetime.utcnow().isoformat() + "Z",
            "relationships": relationships
        }

    async def _get_finance_readiness_data(self, db: AsyncSession, workspace_id: str) -> list:
        """Calculate finance readiness scores for projects."""
        query = """
            SELECT
                p.id,
                CASE
                    WHEN fs.npv IS NOT NULL AND fs.irr IS NOT NULL
                         AND cs.total_equity > 0 THEN 1.0
                    WHEN fs.npv IS NOT NULL THEN 0.6
                    ELSE 0.3
                END as readiness_score
            FROM projects p
            LEFT JOIN fin_projects fp ON fp.project_id = p.id
            LEFT JOIN fin_scenarios fs ON fs.project_id = fp.id
            LEFT JOIN capital_stacks cs ON cs.scenario_id = fs.id
            WHERE p.workspace_id = :workspace_id
        """
        result = await db.execute(text(query), {"workspace_id": workspace_id})
        return [row.readiness_score for row in result]
```

---

## 5. OpenAI/RAG Integration (Already Implemented)

### Current Implementation
- **Service:** `backend/app/services/intelligence.py`
- **Vector Store:** ChromaDB at `.storage/chroma_db/`
- **Model:** GPT-4 Turbo via LangChain
- **Status:** Code complete, requires `OPENAI_API_KEY`

### How to Enable

1. **Add to `.env`:**
   ```bash
   OPENAI_API_KEY=sk-your-api-key-here
   ```

2. **Test the endpoint:**
   ```bash
   curl "http://localhost:8000/api/v1/analytics/intelligence/predictive?workspaceId=test&query=What%20are%20the%20key%20factors%20for%20deal%20success?"
   ```

3. **Ingest knowledge (optional):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analytics/intelligence/ingest?text=Your%20knowledge%20content&source=manual"
   ```

### RAG Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Query    │────▶│  Vector Search   │────▶│   GPT-4 Turbo   │
│                 │     │   (ChromaDB)     │     │   (LangChain)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Embedded Docs   │     │    Response     │
                        │  (k=3 retrieval) │     │                 │
                        └──────────────────┘     └─────────────────┘
```

---

## Implementation Priority

| Component | Priority | Effort | Dependencies |
|-----------|----------|--------|--------------|
| **OpenAI/RAG Integration** | P0 | 10 min | `OPENAI_API_KEY` only |
| **Workspace Signals** | P1 | 1 week | Aggregation service |
| **Cross-Correlation** | P2 | 2 weeks | Statistical service, sufficient historical data |
| **Relationship Intelligence** | P2 | 2 weeks | Graph builder service |
| **Predictive Forecast** | P3 | 4-6 weeks | ML pipeline, training data, model validation |

---

## Testing Strategy

### Unit Tests
- Service methods for each component
- Mock database responses
- Validation of output schemas

### Integration Tests
- Full API endpoint tests with test database
- Verify Zod schema validation on frontend

### Data Quality Tests
- Minimum sample size checks
- Outlier detection for correlations
- Model accuracy monitoring

---

## References

- Frontend Component: `frontend/src/pages/visualizations/AdvancedIntelligence.tsx`
- Backend Endpoints: `backend/app/api/v1/advanced_intelligence.py`
- Analytics Hook: `frontend/src/hooks/useInvestigationAnalytics.ts`
- Analytics Service: `frontend/src/services/analytics/advancedAnalytics.ts`
- RAG Engine: `backend/app/core/rag.py`
- Intelligence Service: `backend/app/services/intelligence.py`
