import type {
  CrossCorrelationIntelligenceResponse,
  GraphIntelligenceResponse,
  PredictiveIntelligenceResponse,
} from './advancedAnalytics'

function isoTimestamp(): string {
  return new Date().toISOString()
}

export function buildSampleGraphIntelligence(): GraphIntelligenceResponse {
  const generatedAt = isoTimestamp()
  return {
    kind: 'graph',
    status: 'ok',
    summary:
      'Sample relationship graph highlighting the busiest compliance touch points.',
    generatedAt,
    graph: {
      nodes: [
        {
          id: 'lead_ops',
          label: 'Lead Operations',
          category: 'team',
          score: 0.92,
        },
        {
          id: 'capital_stack',
          label: 'Capital Stack Review',
          category: 'workflow',
          score: 0.87,
        },
        {
          id: 'feasibility',
          label: 'Feasibility Analysis',
          category: 'workflow',
          score: 0.81,
        },
        {
          id: 'legal',
          label: 'Legal Counsel',
          category: 'partner',
          score: 0.76,
        },
        {
          id: 'compliance',
          label: 'Compliance Ops',
          category: 'team',
          score: 0.7,
        },
      ],
      edges: [
        {
          id: 'lead_ops-capital_stack',
          source: 'lead_ops',
          target: 'capital_stack',
          weight: 0.8,
        },
        {
          id: 'lead_ops-feasibility',
          source: 'lead_ops',
          target: 'feasibility',
          weight: 0.7,
        },
        {
          id: 'capital_stack-legal',
          source: 'capital_stack',
          target: 'legal',
          weight: 0.6,
        },
        {
          id: 'feasibility-compliance',
          source: 'feasibility',
          target: 'compliance',
          weight: 0.5,
        },
        {
          id: 'legal-compliance',
          source: 'legal',
          target: 'compliance',
          weight: 0.4,
        },
      ],
    },
  }
}

export function buildSamplePredictiveIntelligence(): PredictiveIntelligenceResponse {
  const generatedAt = isoTimestamp()
  return {
    kind: 'predictive',
    status: 'ok',
    summary:
      'Predictive models indicate strong momentum in projects with early capital alignment and legal review engagement.',
    generatedAt,
    horizonMonths: 6,
    segments: [
      {
        segmentId: 'segment-ops-champions',
        segmentName: 'Operations champions',
        baseline: 120,
        projection: 168,
        probability: 0.74,
      },
      {
        segmentId: 'segment-compliance-fastlane',
        segmentName: 'Compliance fast-lane',
        baseline: 90,
        projection: 135,
        probability: 0.68,
      },
      {
        segmentId: 'segment-legal-review',
        segmentName: 'Early legal engagement',
        baseline: 75,
        projection: 108,
        probability: 0.62,
      },
    ],
  }
}

export function buildSampleCorrelationIntelligence(): CrossCorrelationIntelligenceResponse {
  const updatedAt = isoTimestamp()
  return {
    kind: 'correlation',
    status: 'ok',
    summary:
      'Cross correlations highlight that finance readiness and early legal review have the strongest relationship with approval speed.',
    updatedAt,
    relationships: [
      {
        pairId: 'finance-readiness_approval-speed',
        driver: 'Finance readiness score',
        outcome: 'Approval speed (days)',
        coefficient: 0.68,
        pValue: 0.012,
      },
      {
        pairId: 'legal-review_iteration-count',
        driver: 'Legal review latency',
        outcome: 'Iteration count',
        coefficient: -0.54,
        pValue: 0.025,
      },
      {
        pairId: 'capital-stack_alignment',
        driver: 'Capital stack completeness',
        outcome: 'Stakeholder alignment index',
        coefficient: 0.49,
        pValue: 0.041,
      },
      {
        pairId: 'site-logistics_schedule-risk',
        driver: 'Site logistics score',
        outcome: 'Schedule risk',
        coefficient: -0.37,
        pValue: 0.09,
      },
    ],
  }
}
