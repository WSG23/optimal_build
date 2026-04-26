import { GanttChart } from './GanttChart'
import { CriticalPathView } from './CriticalPathView'
import { HeritageView } from './HeritageView'
import { TenantRelocationDashboard } from './TenantRelocationDashboard'
import type {
  GanttChart as GanttChartData,
  CriticalPathResult,
  HeritageTracker,
  TenantCoordinationSummary,
} from '../../../../api/development'

export function DemoGanttChart({
  onTaskClick,
  selectedTaskId,
}: {
  onTaskClick: (id: string) => void
  selectedTaskId: string | null
}) {
  const demoData: GanttChartData = {
    projectId: 'demo-project',
    projectName: 'Heritage Mixed-Use Development',
    generatedAt: new Date().toISOString(),
    tasks: [
      {
        id: '1',
        name: 'Site Preparation',
        phaseType: 'site_preparation',
        status: 'completed',
        startDate: '2025-01-01',
        endDate: '2025-01-30',
        duration: 30,
        progress: 1.0,
        dependencies: [],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: 'var(--ob-color-status-success, #10b981)',
        budgetAmount: 500000,
        actualCostAmount: 480000,
      },
      {
        id: '2',
        name: 'Heritage Facade Restoration',
        phaseType: 'heritage_restoration',
        status: 'in_progress',
        startDate: '2025-02-01',
        endDate: '2025-04-15',
        duration: 74,
        progress: 0.45,
        dependencies: ['1'],
        isCritical: true,
        isHeritage: true,
        hasTenantCoordination: false,
        color: 'var(--ob-color-status-warning, #f59e0b)',
        budgetAmount: 2000000,
        actualCostAmount: null,
      },
      {
        id: '3',
        name: 'Tenant Relocation Phase 1',
        phaseType: 'tenant_renovation',
        status: 'in_progress',
        startDate: '2025-02-15',
        endDate: '2025-03-31',
        duration: 45,
        progress: 0.6,
        dependencies: ['1'],
        isCritical: false,
        isHeritage: false,
        hasTenantCoordination: true,
        color: 'var(--ob-color-status-info, #8b5cf6)',
        budgetAmount: 300000,
        actualCostAmount: null,
      },
      {
        id: '4',
        name: 'Structure Reinforcement',
        phaseType: 'structure',
        status: 'planning',
        startDate: '2025-04-16',
        endDate: '2025-06-30',
        duration: 76,
        progress: 0,
        dependencies: ['2'],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: 'var(--ob-color-text-muted, #78716c)',
        budgetAmount: 3500000,
        actualCostAmount: null,
      },
      {
        id: '5',
        name: 'MEP Installation',
        phaseType: 'mep_rough_in',
        status: 'not_started',
        startDate: '2025-07-01',
        endDate: '2025-09-15',
        duration: 77,
        progress: 0,
        dependencies: ['4'],
        isCritical: true,
        isHeritage: false,
        hasTenantCoordination: false,
        color: 'var(--ob-color-text-muted, #78716c)',
        budgetAmount: 2500000,
        actualCostAmount: null,
      },
      {
        id: '6',
        name: 'Interior Fit-Out',
        phaseType: 'interior_fit_out',
        status: 'not_started',
        startDate: '2025-09-16',
        endDate: '2025-11-30',
        duration: 76,
        progress: 0,
        dependencies: ['5'],
        isCritical: false,
        isHeritage: false,
        hasTenantCoordination: true,
        color: 'var(--ob-color-text-muted, #78716c)',
        budgetAmount: 1800000,
        actualCostAmount: null,
      },
    ],
    projectStartDate: '2025-01-01',
    projectEndDate: '2025-11-30',
    totalDuration: 334,
    criticalPathDuration: 257,
  }

  return (
    <GanttChart
      data={demoData}
      onTaskClick={onTaskClick}
      selectedTaskId={selectedTaskId}
    />
  )
}

export function DemoCriticalPath() {
  const demoData: CriticalPathResult = {
    projectId: 'demo-project',
    criticalPath: ['1', '2', '4', '5'],
    totalDuration: 257,
    criticalPhases: [
      {
        phaseId: 1,
        name: 'Site Preparation',
        earlyStart: 0,
        earlyFinish: 30,
        lateStart: 0,
        lateFinish: 30,
        float: 0,
      },
      {
        phaseId: 2,
        name: 'Heritage Facade Restoration',
        earlyStart: 31,
        earlyFinish: 104,
        lateStart: 31,
        lateFinish: 104,
        float: 0,
      },
      {
        phaseId: 4,
        name: 'Structure Reinforcement',
        earlyStart: 105,
        earlyFinish: 180,
        lateStart: 105,
        lateFinish: 180,
        float: 0,
      },
      {
        phaseId: 5,
        name: 'MEP Installation',
        earlyStart: 181,
        earlyFinish: 257,
        lateStart: 181,
        lateFinish: 257,
        float: 0,
      },
    ],
    nonCriticalPhases: [
      { phaseId: 3, name: 'Tenant Relocation Phase 1', float: 30 },
      { phaseId: 6, name: 'Interior Fit-Out', float: 15 },
    ],
  }
  return <CriticalPathView data={demoData} />
}

export function DemoHeritageView() {
  const demoData: HeritageTracker = {
    projectId: 'demo-project',
    heritageClassification: 'conservation_building',
    overallApprovalStatus: 'pending',
    phases: [
      {
        phaseId: 2,
        name: 'Heritage Facade Restoration',
        heritageClassification: 'conservation_building',
        approvalRequired: true,
        approvalStatus: 'approved',
        specialConsiderations: [
          'Original materials must be preserved',
          'Historical facade elements protected',
        ],
      },
      {
        phaseId: 4,
        name: 'Structure Reinforcement',
        heritageClassification: 'conservation_building',
        approvalRequired: true,
        approvalStatus: 'pending',
        specialConsiderations: ['Non-invasive reinforcement methods required'],
      },
    ],
    requiredApprovals: [
      'URA Conservation approval',
      'National Heritage Board review',
      'Structural engineer heritage certification',
    ],
    preservationRisks: [
      'Original facade materials may be fragile',
      'Hidden structural issues in heritage elements',
      'Limited documentation of original construction',
    ],
    recommendations: [
      'Engage heritage architect for facade work',
      'Conduct detailed photogrammetry before work',
      'Prepare contingency for material sourcing',
    ],
  }
  return <HeritageView data={demoData} />
}

export function DemoTenantCoordination() {
  const demoData: TenantCoordinationSummary = {
    projectId: 'demo-project',
    totalTenants: 8,
    statusBreakdown: {
      pending_notification: 1,
      notified: 2,
      confirmed: 2,
      in_progress: 1,
      relocated: 2,
    },
    relocations: [
      {
        id: 1,
        phaseId: 3,
        tenantName: 'ABC Trading Co.',
        currentUnit: '#01-01',
        relocationType: 'temporary',
        status: 'relocated',
        notificationDate: '2024-12-01',
        plannedMoveDate: '2025-02-15',
        actualMoveDate: '2025-02-14',
        temporaryLocation: '#05-01 (Temp)',
        compensationAmount: 15000,
        notes: null,
      },
      {
        id: 2,
        phaseId: 3,
        tenantName: 'XYZ Retail',
        currentUnit: '#01-02',
        relocationType: 'temporary',
        status: 'relocated',
        notificationDate: '2024-12-01',
        plannedMoveDate: '2025-02-20',
        actualMoveDate: '2025-02-19',
        temporaryLocation: '#05-02 (Temp)',
        compensationAmount: 12000,
        notes: null,
      },
      {
        id: 3,
        phaseId: 3,
        tenantName: 'Golden Restaurant',
        currentUnit: '#02-01',
        relocationType: 'permanent',
        status: 'in_progress',
        notificationDate: '2025-01-15',
        plannedMoveDate: '2025-03-15',
        actualMoveDate: null,
        temporaryLocation: null,
        compensationAmount: 50000,
        notes: 'Requires special kitchen equipment moving',
      },
      {
        id: 4,
        phaseId: 6,
        tenantName: 'Tech Startup Inc.',
        currentUnit: '#03-01',
        relocationType: 'temporary',
        status: 'confirmed',
        notificationDate: '2025-02-01',
        plannedMoveDate: '2025-09-01',
        actualMoveDate: null,
        temporaryLocation: '#06-01 (Temp)',
        compensationAmount: 8000,
        notes: null,
      },
      {
        id: 5,
        phaseId: 6,
        tenantName: 'Design Studio',
        currentUnit: '#03-02',
        relocationType: 'temporary',
        status: 'confirmed',
        notificationDate: '2025-02-01',
        plannedMoveDate: '2025-09-15',
        actualMoveDate: null,
        temporaryLocation: '#06-02 (Temp)',
        compensationAmount: 6000,
        notes: null,
      },
    ],
    upcomingMoves: [
      {
        id: 3,
        phaseId: 3,
        tenantName: 'Golden Restaurant',
        currentUnit: '#02-01',
        relocationType: 'permanent',
        status: 'in_progress',
        notificationDate: '2025-01-15',
        plannedMoveDate: '2025-03-15',
        actualMoveDate: null,
        temporaryLocation: null,
        compensationAmount: 50000,
        notes: null,
      },
    ],
    overdueNotifications: [],
    timeline: [
      {
        date: '2025-02-19',
        event: 'Move completed',
        tenantName: 'XYZ Retail',
        status: 'relocated',
      },
      {
        date: '2025-02-14',
        event: 'Move completed',
        tenantName: 'ABC Trading Co.',
        status: 'relocated',
      },
      {
        date: '2025-02-01',
        event: 'Notification sent',
        tenantName: 'Design Studio',
        status: 'notified',
      },
      {
        date: '2025-02-01',
        event: 'Notification sent',
        tenantName: 'Tech Startup Inc.',
        status: 'notified',
      },
      {
        date: '2025-01-15',
        event: 'Notification sent',
        tenantName: 'Golden Restaurant',
        status: 'notified',
      },
    ],
    warnings: [],
  }
  return <TenantRelocationDashboard data={demoData} />
}
