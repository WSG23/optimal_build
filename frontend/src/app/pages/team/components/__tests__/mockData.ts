/**
 * Mock data for ProjectProgressDashboard tests.
 * These types and data mirror the internal structures of ProjectProgressDashboard.tsx
 */

export interface TeamMemberActivity {
  id: string
  name: string
  email: string
  role: string
  lastActive: string
  pendingTasks: number
  completedTasks: number
}

export interface ProjectPhase {
  id: string
  name: string
  progress: number
  status: 'not_started' | 'in_progress' | 'completed' | 'delayed'
  startDate?: string
  endDate?: string
  milestones: {
    name: string
    completed: boolean
  }[]
}

export interface PendingApproval {
  id: string
  title: string
  workflowName: string
  requiredBy: string
  dueDate?: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
}

/**
 * Get mock project phases for testing.
 */
export const getMockPhases = (): ProjectPhase[] => [
  {
    id: 'phase-1',
    name: 'Site Acquisition',
    progress: 100,
    status: 'completed',
    startDate: '2025-01-15',
    endDate: '2025-03-01',
    milestones: [
      { name: 'Site Survey', completed: true },
      { name: 'Due Diligence', completed: true },
      { name: 'Purchase Agreement', completed: true },
    ],
  },
  {
    id: 'phase-2',
    name: 'Concept Design',
    progress: 75,
    status: 'in_progress',
    startDate: '2025-03-01',
    milestones: [
      { name: 'Massing Study', completed: true },
      { name: 'GFA Optimization', completed: true },
      { name: 'Financial Feasibility', completed: true },
      { name: 'Design Review', completed: false },
    ],
  },
  {
    id: 'phase-3',
    name: 'Regulatory Submission',
    progress: 30,
    status: 'in_progress',
    startDate: '2025-04-15',
    milestones: [
      { name: 'URA Outline Approval', completed: true },
      { name: 'BCA Structural Plans', completed: false },
      { name: 'SCDF Fire Safety', completed: false },
      { name: 'NEA Environmental', completed: false },
    ],
  },
  {
    id: 'phase-4',
    name: 'Construction',
    progress: 0,
    status: 'not_started',
    milestones: [
      { name: 'Foundation', completed: false },
      { name: 'Superstructure', completed: false },
      { name: 'M&E Works', completed: false },
      { name: 'Finishing', completed: false },
    ],
  },
]

/**
 * Get mock team member activity data for testing.
 */
export const getMockTeamActivity = (): TeamMemberActivity[] => [
  {
    id: 'u1',
    name: 'John Smith',
    email: 'john.smith@example.com',
    role: 'Project Manager',
    lastActive: '2 hours ago',
    pendingTasks: 3,
    completedTasks: 12,
  },
  {
    id: 'u2',
    name: 'Sarah Chen',
    email: 'sarah.chen@example.com',
    role: 'Architect',
    lastActive: '30 mins ago',
    pendingTasks: 2,
    completedTasks: 8,
  },
  {
    id: 'u3',
    name: 'Michael Wong',
    email: 'michael.wong@example.com',
    role: 'Structural Engineer',
    lastActive: '1 hour ago',
    pendingTasks: 4,
    completedTasks: 6,
  },
  {
    id: 'u4',
    name: 'Emily Tan',
    email: 'emily.tan@example.com',
    role: 'Quantity Surveyor',
    lastActive: '3 hours ago',
    pendingTasks: 1,
    completedTasks: 5,
  },
]

/**
 * Get mock pending approvals data for testing.
 */
export const getMockPendingApprovals = (): PendingApproval[] => [
  {
    id: 'a1',
    title: 'Structural Feasibility Review',
    workflowName: 'Concept Design Sign-off',
    requiredBy: 'Michael Wong',
    dueDate: '2025-12-10',
    priority: 'high',
  },
  {
    id: 'a2',
    title: 'Cost Estimate Approval',
    workflowName: 'Financial Review',
    requiredBy: 'Emily Tan',
    priority: 'normal',
  },
  {
    id: 'a3',
    title: 'Heritage Assessment',
    workflowName: 'Regulatory Compliance',
    requiredBy: 'Sarah Chen',
    priority: 'urgent',
  },
]

/**
 * Create a single mock team member for targeted testing.
 */
export const createMockTeamMember = (
  overrides: Partial<TeamMemberActivity> = {},
): TeamMemberActivity => ({
  id: 'test-member-1',
  name: 'Test User',
  email: 'test@example.com',
  role: 'Developer',
  lastActive: 'Just now',
  pendingTasks: 0,
  completedTasks: 0,
  ...overrides,
})

/**
 * Create a single mock phase for targeted testing.
 */
export const createMockPhase = (
  overrides: Partial<ProjectPhase> = {},
): ProjectPhase => ({
  id: 'test-phase-1',
  name: 'Test Phase',
  progress: 50,
  status: 'in_progress',
  milestones: [
    { name: 'Milestone 1', completed: true },
    { name: 'Milestone 2', completed: false },
  ],
  ...overrides,
})

/**
 * Create a single mock approval for targeted testing.
 */
export const createMockApproval = (
  overrides: Partial<PendingApproval> = {},
): PendingApproval => ({
  id: 'test-approval-1',
  title: 'Test Approval',
  workflowName: 'Test Workflow',
  requiredBy: 'Test User',
  priority: 'normal',
  ...overrides,
})
