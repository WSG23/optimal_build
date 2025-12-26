import { FormEvent, useEffect, useMemo, useState } from 'react'
import Header from '../components/Header'
import { EntitlementsAPI } from '../api/client'
import type {
  EntEngagementRecord,
  EntLegalInstrumentRecord,
  EntRoadmapItemRecord,
  EntStudyRecord,
} from '../types'
import { toErrorMessage } from '../utils/error'

const PROJECT_ID = 501

type TabKey = 'roadmap' | 'studies' | 'stakeholders' | 'legal'

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'roadmap', label: 'Roadmap' },
  { key: 'studies', label: 'Studies' },
  { key: 'stakeholders', label: 'Stakeholders' },
  { key: 'legal', label: 'Legal' },
]

const statusStyles: Record<string, string> = {
  planned: 'bg-surface-alt text-text-secondary',
  in_progress: 'bg-brand-primary text-text-inverse',
  submitted: 'bg-warning-soft text-warning-strong',
  approved: 'bg-success-soft text-success-strong',
  accepted: 'bg-success-soft text-success-strong',
  rejected: 'bg-error-soft text-error-strong',
  blocked: 'bg-error-soft text-error-strong',
  complete: 'bg-success-strong text-text-inverse',
  active: 'bg-brand-primary-emphasis text-text-inverse',
  completed: 'bg-success-soft text-success-strong',
  in_review: 'bg-info-soft text-info-strong',
  executed: 'bg-success-strong text-text-inverse',
  expired: 'bg-surface-alt text-text-muted',
}

const studyTypes = [
  { value: 'traffic', label: 'Traffic' },
  { value: 'environmental', label: 'Environmental' },
  { value: 'heritage', label: 'Heritage' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'community', label: 'Community' },
]

const studyStatuses = [
  'draft',
  'scope_defined',
  'in_progress',
  'submitted',
  'accepted',
  'rejected',
]

const engagementTypes = [
  { value: 'agency', label: 'Agency' },
  { value: 'community', label: 'Community' },
  { value: 'political', label: 'Political' },
  { value: 'private_partner', label: 'Private Partner' },
  { value: 'regulator', label: 'Regulator' },
]

const engagementStatuses = ['planned', 'active', 'completed', 'blocked']

const legalTypes = [
  { value: 'agreement', label: 'Agreement' },
  { value: 'licence', label: 'Licence' },
  { value: 'memorandum', label: 'Memorandum' },
  { value: 'waiver', label: 'Waiver' },
  { value: 'variation', label: 'Variation' },
]

const legalStatuses = ['draft', 'in_review', 'executed', 'expired']

const describeAttachment = (attachment: Record<string, unknown>): string => {
  const candidate = ['url', 'label', 'href']
    .map((key) => attachment[key])
    .find(
      (value): value is string =>
        typeof value === 'string' && value.trim() !== '',
    )

  return candidate ?? 'Attachment'
}

interface StudyFormState {
  name: string
  study_type: string
  status: string
  consultant: string
  due_date: string
  report_url: string
}

interface EngagementFormState {
  name: string
  organisation: string
  engagement_type: string
  status: string
  contact_email: string
  contact_phone: string
  notes: string
}

interface LegalFormState {
  name: string
  instrument_type: string
  status: string
  reference_code: string
  effective_date: string
  expiry_date: string
  attachment_url: string
}

const defaultStudyForm: StudyFormState = {
  name: '',
  study_type: 'traffic',
  status: 'draft',
  consultant: '',
  due_date: '',
  report_url: '',
}

const defaultEngagementForm: EngagementFormState = {
  name: '',
  organisation: '',
  engagement_type: 'agency',
  status: 'planned',
  contact_email: '',
  contact_phone: '',
  notes: '',
}

const defaultLegalForm: LegalFormState = {
  name: '',
  instrument_type: 'agreement',
  status: 'draft',
  reference_code: '',
  effective_date: '',
  expiry_date: '',
  attachment_url: '',
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

function StatusPill({ status }: { status: string }) {
  const classes = statusStyles[status] ?? 'bg-surface-alt text-text-secondary'
  const label = status.replace(/_/g, ' ')
  return (
    <span className={`px-2 py-1 text-xs rounded-xs font-semibold ${classes}`}>
      {label}
    </span>
  )
}

const EntitlementsPage = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('roadmap')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [roadmap, setRoadmap] = useState<EntRoadmapItemRecord[]>([])
  const [studies, setStudies] = useState<EntStudyRecord[]>([])
  const [stakeholders, setStakeholders] = useState<EntEngagementRecord[]>([])
  const [legal, setLegal] = useState<EntLegalInstrumentRecord[]>([])

  const [studyForm, setStudyForm] = useState<StudyFormState>(defaultStudyForm)
  const [engagementForm, setEngagementForm] = useState<EngagementFormState>(
    defaultEngagementForm,
  )
  const [legalForm, setLegalForm] = useState<LegalFormState>(defaultLegalForm)

  const statusOptions = useMemo(
    () => ({
      roadmap: [
        'planned',
        'in_progress',
        'submitted',
        'approved',
        'rejected',
        'blocked',
        'complete',
      ],
      studies: studyStatuses,
      stakeholders: engagementStatuses,
      legal: legalStatuses,
    }),
    [],
  )

  const refreshData = async () => {
    setLoading(true)
    try {
      const [roadmapResp, studiesResp, stakeholdersResp, legalResp] =
        await Promise.all([
          EntitlementsAPI.getRoadmap(PROJECT_ID),
          EntitlementsAPI.getStudies(PROJECT_ID),
          EntitlementsAPI.getStakeholders(PROJECT_ID),
          EntitlementsAPI.getLegalInstruments(PROJECT_ID),
        ])
      setRoadmap(roadmapResp.items)
      setStudies(studiesResp.items)
      setStakeholders(stakeholdersResp.items)
      setLegal(legalResp.items)
      setError(null)
    } catch (error) {
      setError(toErrorMessage(error, 'Failed to load entitlements'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refreshData()
  }, [])

  const handleRoadmapStatusChange = async (
    item: EntRoadmapItemRecord,
    status: string,
  ) => {
    try {
      await EntitlementsAPI.updateRoadmap(PROJECT_ID, item.id, { status })
      void refreshData()
    } catch (error) {
      setError(toErrorMessage(error, 'Failed to update roadmap item'))
    }
  }

  const handleStudySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const payload = {
        project_id: PROJECT_ID,
        name: studyForm.name,
        study_type: studyForm.study_type,
        status: studyForm.status,
        consultant: studyForm.consultant || undefined,
        due_date: studyForm.due_date || undefined,
        attachments: studyForm.report_url
          ? [{ label: 'Report', url: studyForm.report_url.trim() }]
          : [],
      }
      await EntitlementsAPI.createStudy(PROJECT_ID, payload)
      setStudyForm(defaultStudyForm)
      void refreshData()
    } catch (error) {
      setError(toErrorMessage(error, 'Failed to create study'))
    }
  }

  const handleEngagementSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const payload = {
        project_id: PROJECT_ID,
        name: engagementForm.name,
        organisation: engagementForm.organisation || undefined,
        engagement_type: engagementForm.engagement_type,
        status: engagementForm.status,
        contact_email: engagementForm.contact_email || undefined,
        contact_phone: engagementForm.contact_phone || undefined,
        notes: engagementForm.notes || undefined,
      }
      await EntitlementsAPI.createStakeholder(PROJECT_ID, payload)
      setEngagementForm(defaultEngagementForm)
      void refreshData()
    } catch (error) {
      setError(toErrorMessage(error, 'Failed to create stakeholder'))
    }
  }

  const handleLegalSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const payload = {
        project_id: PROJECT_ID,
        name: legalForm.name,
        instrument_type: legalForm.instrument_type,
        status: legalForm.status,
        reference_code: legalForm.reference_code || undefined,
        effective_date: legalForm.effective_date || undefined,
        expiry_date: legalForm.expiry_date || undefined,
        attachments: legalForm.attachment_url
          ? [{ label: 'Attachment', url: legalForm.attachment_url.trim() }]
          : [],
      }
      await EntitlementsAPI.createLegalInstrument(PROJECT_ID, payload)
      setLegalForm(defaultLegalForm)
      void refreshData()
    } catch (error) {
      setError(toErrorMessage(error, 'Failed to create legal instrument'))
    }
  }

  const renderRoadmap = () => (
    <div className="space-y-4">
      {roadmap.map((item) => (
        <div
          key={item.id}
          className="rounded border border-border-subtle bg-surface/60 p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-muted">
                {`Sequence #${item.sequence_order.toString()}`}
              </p>
              <p className="text-lg font-semibold text-text-primary">
                {`Approval #${
                  item.approval_type_id === null
                    ? 'Unassigned'
                    : item.approval_type_id.toString()
                }`}
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <StatusPill status={item.status} />
              <select
                value={item.status}
                onChange={(event) => {
                  void handleRoadmapStatusChange(item, event.target.value)
                }}
                className="rounded-md border border-border-neutral bg-surface/80 px-2 py-1 text-xs text-text-primary focus:outline-none focus:ring focus:ring-success-strong"
              >
                {statusOptions.roadmap.map((status) => (
                  <option key={status} value={status}>
                    {status.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm text-text-secondary">
            <div>
              <dt className="text-xs uppercase text-text-subtle">
                Target Submission
              </dt>
              <dd>{formatDate(item.target_submission_date)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-text-subtle">
                Target Decision
              </dt>
              <dd>{formatDate(item.target_decision_date)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-text-subtle">
                Actual Submission
              </dt>
              <dd>{formatDate(item.actual_submission_date)}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-text-subtle">
                Actual Decision
              </dt>
              <dd>{formatDate(item.actual_decision_date)}</dd>
            </div>
          </dl>
          {item.notes && (
            <p className="mt-3 text-sm text-text-secondary">{item.notes}</p>
          )}
        </div>
      ))}
      {roadmap.length === 0 && !loading && (
        <p className="text-sm text-text-muted">No roadmap items seeded yet.</p>
      )}
    </div>
  )

  const renderStudies = () => (
    <div className="space-y-6">
      <form
        onSubmit={(event) => {
          void handleStudySubmit(event)
        }}
        className="rounded border border-border-subtle bg-surface/70 p-4"
      >
        <h3 className="text-sm font-semibold text-text-primary">Add study</h3>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="text-xs uppercase text-text-muted">
            Name
            <input
              required
              value={studyForm.name}
              onChange={(event) => {
                setStudyForm((prev) => ({ ...prev, name: event.target.value }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring focus:ring-success-strong"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Study Type
            <select
              value={studyForm.study_type}
              onChange={(event) => {
                setStudyForm((prev) => ({
                  ...prev,
                  study_type: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {studyTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Status
            <select
              value={studyForm.status}
              onChange={(event) => {
                setStudyForm((prev) => ({
                  ...prev,
                  status: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {studyStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Consultant
            <input
              value={studyForm.consultant}
              onChange={(event) => {
                setStudyForm((prev) => ({
                  ...prev,
                  consultant: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Due Date
            <input
              type="date"
              value={studyForm.due_date}
              onChange={(event) => {
                setStudyForm((prev) => ({
                  ...prev,
                  due_date: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Report URL
            <input
              type="url"
              value={studyForm.report_url}
              onChange={(event) => {
                setStudyForm((prev) => ({
                  ...prev,
                  report_url: event.target.value,
                }))
              }}
              placeholder="https://"
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
        </div>
        <button
          type="submit"
          className="mt-4 rounded-md bg-success-strong px-4 py-2 text-sm font-semibold text-text-inverse hover:bg-success-strong/80"
        >
          Add study
        </button>
      </form>

      <div className="space-y-4">
        {studies.map((study) => (
          <div
            key={study.id}
            className="rounded border border-border-subtle bg-surface/60 p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-text-primary">
                  {study.name}
                </h4>
                <p className="text-sm text-text-muted">
                  {study.study_type.replace(/_/g, ' ')}
                </p>
              </div>
              <StatusPill status={study.status} />
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm text-text-secondary">
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Consultant
                </dt>
                <dd>{study.consultant || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">Due Date</dt>
                <dd>{formatDate(study.due_date)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Completed
                </dt>
                <dd>{formatDate(study.completed_at)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Attachments
                </dt>
                <dd>
                  {study.attachments.length === 0 && '—'}
                  {study.attachments.map((attachment, index) => (
                    <span key={index} className="block truncate">
                      {describeAttachment(attachment)}
                    </span>
                  ))}
                </dd>
              </div>
            </dl>
            {study.summary && (
              <p className="mt-3 text-sm text-text-secondary">
                {study.summary}
              </p>
            )}
          </div>
        ))}
        {studies.length === 0 && !loading && (
          <p className="text-sm text-text-muted">
            No studies recorded for this project.
          </p>
        )}
      </div>
    </div>
  )

  const renderStakeholders = () => (
    <div className="space-y-6">
      <form
        onSubmit={(event) => {
          void handleEngagementSubmit(event)
        }}
        className="rounded border border-border-subtle bg-surface/70 p-4"
      >
        <h3 className="text-sm font-semibold text-text-primary">
          Add stakeholder
        </h3>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="text-xs uppercase text-text-muted">
            Name
            <input
              required
              value={engagementForm.name}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  name: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Organisation
            <input
              value={engagementForm.organisation}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  organisation: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Engagement Type
            <select
              value={engagementForm.engagement_type}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  engagement_type: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {engagementTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Status
            <select
              value={engagementForm.status}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  status: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {engagementStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Contact Email
            <input
              type="email"
              value={engagementForm.contact_email}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  contact_email: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Contact Phone
            <input
              value={engagementForm.contact_phone}
              onChange={(event) => {
                setEngagementForm((prev) => ({
                  ...prev,
                  contact_phone: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
        </div>
        <label className="mt-3 block text-xs uppercase text-text-muted">
          Notes
          <textarea
            value={engagementForm.notes}
            onChange={(event) => {
              setEngagementForm((prev) => ({
                ...prev,
                notes: event.target.value,
              }))
            }}
            className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            rows={3}
          />
        </label>
        <button
          type="submit"
          className="mt-4 rounded-md bg-success-strong px-4 py-2 text-sm font-semibold text-text-inverse hover:bg-success-strong/80"
        >
          Add stakeholder
        </button>
      </form>

      <div className="space-y-4">
        {stakeholders.map((record) => (
          <div
            key={record.id}
            className="rounded border border-border-subtle bg-surface/60 p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-text-primary">
                  {record.name}
                </h4>
                <p className="text-sm text-text-muted">
                  {record.organisation || 'Unspecified organisation'}
                </p>
              </div>
              <StatusPill status={record.status} />
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm text-text-secondary">
              <div>
                <dt className="text-xs uppercase text-text-subtle">Type</dt>
                <dd>{record.engagement_type.replace(/_/g, ' ')}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">Contact</dt>
                <dd>{record.contact_email || record.contact_phone || '—'}</dd>
              </div>
            </dl>
            {record.notes && (
              <p className="mt-3 text-sm text-text-secondary">{record.notes}</p>
            )}
          </div>
        ))}
        {stakeholders.length === 0 && !loading && (
          <p className="text-sm text-text-muted">
            No stakeholder engagements recorded.
          </p>
        )}
      </div>
    </div>
  )

  const renderLegal = () => (
    <div className="space-y-6">
      <form
        onSubmit={(event) => {
          void handleLegalSubmit(event)
        }}
        className="rounded border border-border-subtle bg-surface/70 p-4"
      >
        <h3 className="text-sm font-semibold text-text-primary">
          Add legal instrument
        </h3>
        <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="text-xs uppercase text-text-muted">
            Name
            <input
              required
              value={legalForm.name}
              onChange={(event) => {
                setLegalForm((prev) => ({ ...prev, name: event.target.value }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Instrument Type
            <select
              value={legalForm.instrument_type}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  instrument_type: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {legalTypes.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Status
            <select
              value={legalForm.status}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  status: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            >
              {legalStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs uppercase text-text-muted">
            Reference Code
            <input
              value={legalForm.reference_code}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  reference_code: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Effective Date
            <input
              type="date"
              value={legalForm.effective_date}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  effective_date: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Expiry Date
            <input
              type="date"
              value={legalForm.expiry_date}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  expiry_date: event.target.value,
                }))
              }}
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
          <label className="text-xs uppercase text-text-muted">
            Attachment URL
            <input
              type="url"
              value={legalForm.attachment_url}
              onChange={(event) => {
                setLegalForm((prev) => ({
                  ...prev,
                  attachment_url: event.target.value,
                }))
              }}
              placeholder="https://"
              className="mt-1 w-full rounded-md border border-border-neutral bg-surface/80 px-3 py-2 text-sm text-text-primary"
            />
          </label>
        </div>
        <button
          type="submit"
          className="mt-4 rounded-md bg-success-strong px-4 py-2 text-sm font-semibold text-text-inverse hover:bg-success-strong/80"
        >
          Add legal instrument
        </button>
      </form>

      <div className="space-y-4">
        {legal.map((record) => (
          <div
            key={record.id}
            className="rounded border border-border-subtle bg-surface/60 p-4"
          >
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-lg font-semibold text-text-primary">
                  {record.name}
                </h4>
                <p className="text-sm text-text-muted">
                  {record.instrument_type.replace(/_/g, ' ')}
                </p>
              </div>
              <StatusPill status={record.status} />
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-4 text-sm text-text-secondary">
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Reference
                </dt>
                <dd>{record.reference_code || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Effective
                </dt>
                <dd>{formatDate(record.effective_date)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">Expiry</dt>
                <dd>{formatDate(record.expiry_date)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-text-subtle">
                  Attachments
                </dt>
                <dd>
                  {record.attachments.length === 0 && '—'}
                  {record.attachments.map((attachment, index) => (
                    <span key={index} className="block truncate">
                      {describeAttachment(attachment)}
                    </span>
                  ))}
                </dd>
              </div>
            </dl>
          </div>
        ))}
        {legal.length === 0 && !loading && (
          <p className="text-sm text-text-muted">
            No legal instruments recorded.
          </p>
        )}
      </div>
    </div>
  )

  return (
    <div>
      <Header title="Entitlements" />
      <p className="mt-1 text-sm text-text-muted">
        Monitor entitlement authorities, studies, stakeholder engagement, and
        legal commitments for project #{PROJECT_ID.toString()}.
      </p>
      <div className="mt-6 flex space-x-3 border-b border-border-subtle">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key)
            }}
            className={`px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'border-b-2 border-brand-primary text-brand-primary'
                : 'text-text-muted hover:text-text-primary'
            }`}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && <p className="mt-4 text-sm text-error-muted">{error}</p>}
      {loading && !error && (
        <p className="mt-4 text-sm text-text-muted">Loading entitlements…</p>
      )}

      <div className="mt-6">
        {activeTab === 'roadmap' && renderRoadmap()}
        {activeTab === 'studies' && renderStudies()}
        {activeTab === 'stakeholders' && renderStakeholders()}
        {activeTab === 'legal' && renderLegal()}
      </div>
    </div>
  )
}

export default EntitlementsPage
