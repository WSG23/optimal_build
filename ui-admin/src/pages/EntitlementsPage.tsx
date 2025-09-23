import { useCallback, useEffect, useMemo, useState } from 'react';
import Header from '../components/Header';
import { EntitlementsAPI } from '../api/client';
import type {
  EntLegalInstrument,
  EntRoadmapItem,
  EntStakeholder,
  EntStudy
} from '../types';

const STATUS_STYLES: Record<string, string> = {
  planned: 'bg-slate-700 text-slate-100',
  in_progress: 'bg-blue-600/60 text-blue-100',
  submitted: 'bg-amber-500/60 text-amber-100',
  approved: 'bg-emerald-600/60 text-emerald-100',
  rejected: 'bg-rose-600/60 text-rose-100',
  on_hold: 'bg-slate-500/60 text-slate-100',
  archived: 'bg-slate-800 text-slate-300'
};

const TABS = [
  { key: 'roadmap', label: 'Roadmap' },
  { key: 'studies', label: 'Studies' },
  { key: 'stakeholders', label: 'Stakeholders' },
  { key: 'legal', label: 'Legal' }
] as const;

type TabKey = (typeof TABS)[number]['key'];

const formatStatus = (status: string) => {
  const key = status?.toLowerCase() ?? 'planned';
  const classes = STATUS_STYLES[key] ?? STATUS_STYLES.planned;
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${classes}`}>
      {status.replace('_', ' ')}
    </span>
  );
};

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString();
};

const metadataSummary = (metadata?: Record<string, unknown>) => {
  if (!metadata) return '';
  const value = (metadata as Record<string, unknown>)['summary'];
  if (typeof value === 'string') {
    return value;
  }
  if (value === undefined || value === null) {
    return '';
  }
  return JSON.stringify(value);
};

const EntitlementsPage = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('roadmap');
  const [projectId, setProjectId] = useState<number>(101);
  const [roadmap, setRoadmap] = useState<EntRoadmapItem[]>([]);
  const [studies, setStudies] = useState<EntStudy[]>([]);
  const [stakeholders, setStakeholders] = useState<EntStakeholder[]>([]);
  const [legal, setLegal] = useState<EntLegalInstrument[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [roadmapResponse, studiesResponse, stakeholdersResponse, legalResponse] = await Promise.all([
        EntitlementsAPI.getRoadmap(projectId),
        EntitlementsAPI.getStudies(projectId),
        EntitlementsAPI.getStakeholders(projectId),
        EntitlementsAPI.getLegal(projectId)
      ]);
      setRoadmap(roadmapResponse.items);
      setStudies(studiesResponse.items);
      setStakeholders(stakeholdersResponse.items);
      setLegal(legalResponse.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load entitlements');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const headerActions = useMemo(
    () => (
      <div className="flex items-center space-x-2">
        <label className="text-xs uppercase tracking-wide text-slate-400">
          Project ID
          <input
            type="number"
            value={projectId}
            onChange={(event) => setProjectId(Number(event.target.value) || 0)}
            className="ml-2 w-24 rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100 focus:border-emerald-500 focus:outline-none"
          />
        </label>
        <button
          type="button"
          onClick={loadData}
          className="rounded-md bg-emerald-500/80 px-3 py-1 text-sm font-semibold text-slate-900 hover:bg-emerald-400"
        >
          Refresh
        </button>
      </div>
    ),
    [projectId, loadData]
  );

  const renderRoadmap = () => (
    <div className="overflow-hidden rounded-lg border border-slate-800">
      <table className="min-w-full divide-y divide-slate-800">
        <thead className="bg-slate-900">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Sequence</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Approval</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Status</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Target</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Notes</th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-400">Attachments</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {roadmap.map((item) => (
            <tr key={item.id} className="hover:bg-slate-900/70">
              <td className="px-4 py-3 text-sm text-slate-200">{item.sequence}</td>
              <td className="px-4 py-3 text-sm text-slate-100">
                <div className="font-semibold">{item.approval_type?.name ?? '—'}</div>
                <div className="text-xs text-slate-400">{item.approval_type?.code ?? ''}</div>
              </td>
              <td className="px-4 py-3 text-sm">{formatStatus(item.status)}</td>
              <td className="px-4 py-3 text-sm text-slate-200">{formatDate(item.target_submission_date)}</td>
              <td className="px-4 py-3 text-sm text-slate-300">{item.notes || '—'}</td>
              <td className="px-4 py-3 text-sm text-slate-300">
                <textarea
                  readOnly
                  value={item.attachments?.length ? JSON.stringify(item.attachments) : ''}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200"
                  placeholder="Add attachment metadata"
                />
              </td>
            </tr>
          ))}
          {roadmap.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                No roadmap items available.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );

  const renderStudies = () => (
    <div className="grid gap-4">
      {studies.map((study) => (
        <div key={study.id} className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">{study.name}</h3>
              <p className="text-xs uppercase tracking-wide text-slate-400">
                {study.study_type} · {formatStatus(study.status)}
              </p>
            </div>
            <span className="text-xs text-slate-400">
              Submitted {formatDate(study.submission_date)} · Approved {formatDate(study.approval_date)}
            </span>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Consultant
              <input
                type="text"
                readOnly
                value={study.consultant ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="Assign consultant"
              />
            </label>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Report URL
              <input
                type="url"
                readOnly
                value={study.report_uri ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="https://example.com/report.pdf"
              />
            </label>
          </div>
          <div className="mt-4">
              <label className="text-xs uppercase tracking-wide text-slate-400">
              Findings summary
              <textarea
                readOnly
                value={metadataSummary(study.metadata)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="Enter key findings"
              />
            </label>
          </div>
        </div>
      ))}
      {studies.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-400">
          No studies recorded yet.
        </div>
      )}
    </div>
  );

  const renderStakeholders = () => (
    <div className="grid gap-4">
      {stakeholders.map((stakeholder) => (
        <div key={stakeholder.id} className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">{stakeholder.stakeholder_name}</h3>
              <p className="text-xs uppercase tracking-wide text-slate-400">
                {stakeholder.stakeholder_type}
              </p>
            </div>
            {formatStatus(stakeholder.status)}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Contact email
              <input
                type="email"
                readOnly
                value={stakeholder.contact_email ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="name@example.com"
              />
            </label>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Meeting date
              <input
                type="text"
                readOnly
                value={formatDate(stakeholder.meeting_date)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
              />
            </label>
          </div>
          <div className="mt-4">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Summary
              <textarea
                readOnly
                value={stakeholder.summary ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="Document discussion notes"
              />
            </label>
          </div>
          <div className="mt-3">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Next steps
              <textarea
                readOnly
                value={stakeholder.next_steps?.length ? stakeholder.next_steps.join('\n') : ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="Capture follow-up actions"
              />
            </label>
          </div>
        </div>
      ))}
      {stakeholders.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-400">
          No stakeholder engagements tracked.
        </div>
      )}
    </div>
  );

  const renderLegal = () => (
    <div className="grid gap-4">
      {legal.map((instrument) => (
        <div key={instrument.id} className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-100">{instrument.title}</h3>
              <p className="text-xs uppercase tracking-wide text-slate-400">{instrument.instrument_type}</p>
            </div>
            {formatStatus(instrument.status)}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Reference
              <input
                type="text"
                readOnly
                value={instrument.reference_code ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="Reference code"
              />
            </label>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Effective date
              <input
                type="text"
                readOnly
                value={formatDate(instrument.effective_date)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
              />
            </label>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Expiry date
              <input
                type="text"
                readOnly
                value={formatDate(instrument.expiry_date)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
              />
            </label>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Storage URI
              <input
                type="url"
                readOnly
                value={instrument.storage_uri ?? ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="https://example.com/legal.pdf"
              />
            </label>
            <label className="text-xs uppercase tracking-wide text-slate-400">
              Attachments
              <textarea
                readOnly
                value={instrument.attachments?.length ? JSON.stringify(instrument.attachments) : ''}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                placeholder="List uploaded documents"
              />
            </label>
          </div>
        </div>
      ))}
      {legal.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-400">
          No legal instruments captured.
        </div>
      )}
    </div>
  );

  return (
    <div>
      <Header title="Entitlements" actions={headerActions} />
      {error && <div className="mb-4 rounded-md border border-rose-700/60 bg-rose-900/30 px-4 py-3 text-sm text-rose-200">{error}</div>}
      {loading && <p className="text-sm text-slate-400">Loading entitlement data…</p>}
      <div className="mt-4 flex space-x-2 border-b border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            className={`px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === tab.key
                ? 'border-b-2 border-emerald-400 text-emerald-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-6 space-y-4">
        {activeTab === 'roadmap' && renderRoadmap()}
        {activeTab === 'studies' && renderStudies()}
        {activeTab === 'stakeholders' && renderStakeholders()}
        {activeTab === 'legal' && renderLegal()}
      </div>
    </div>
  );
};

export default EntitlementsPage;
