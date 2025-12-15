import { useMemo } from 'react'

import { useTranslation } from '../../../i18n'

export interface FinanceTimelineJob {
  scenarioId?: number | null
  taskId?: string | null
  status?: string | null
  backend?: string | null
  queuedAt?: string | null
}

interface FinanceJobTimelineProps {
  jobs: FinanceTimelineJob[]
  pendingCount: number
}

function formatTimestamp(
  value: string | null | undefined,
  locale: string,
): string | null {
  if (!value) {
    return null
  }
  const timestamp = Date.parse(value)
  if (Number.isNaN(timestamp)) {
    return null
  }
  try {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(timestamp))
  } catch {
    return new Date(timestamp).toLocaleString()
  }
}

export function FinanceJobTimeline({
  jobs,
  pendingCount,
}: FinanceJobTimelineProps) {
  const { t, i18n } = useTranslation()
  const locale = i18n.language
  const fallback = t('common.fallback.dash')

  const sortedJobs = useMemo(() => {
    if (jobs.length === 0) {
      return []
    }
    const mapped = jobs.map((job, index) => {
      const timestamp = job.queuedAt ? Date.parse(job.queuedAt) : Number.NaN
      const sortKey = Number.isNaN(timestamp)
        ? Number.MAX_SAFE_INTEGER
        : timestamp
      return { job, index, sortKey }
    })
    mapped.sort((a, b) => {
      if (a.sortKey === b.sortKey) {
        return a.index - b.index
      }
      return a.sortKey - b.sortKey
    })
    return mapped.map((item) => item.job)
  }, [jobs])

  const statusLabels = useMemo(
    () =>
      ({
        queued: t('finance.jobs.status.queued'),
        started: t('finance.jobs.status.started'),
        in_progress: t('finance.jobs.status.in_progress'),
        processing: t('finance.jobs.status.in_progress'),
        completed: t('finance.jobs.status.completed'),
        success: t('finance.jobs.status.completed'),
        failed: t('finance.jobs.status.failed'),
        error: t('finance.jobs.status.failed'),
      }) as Record<string, string>,
    [t],
  )

  if (jobs.length === 0) {
    return (
      <section className="finance-job-timeline">
        <h2 className="finance-job-timeline__title">
          {t('finance.jobs.title')}
        </h2>
        <p className="finance-job-timeline__empty">{t('finance.jobs.empty')}</p>
      </section>
    )
  }

  return (
    <section className="finance-job-timeline">
      <h2 className="finance-job-timeline__title">{t('finance.jobs.title')}</h2>
      {pendingCount > 0 ? (
        <p className="finance-job-timeline__pending">
          {t('finance.sensitivity.pendingNotice', { count: pendingCount })}
        </p>
      ) : null}
      <ol className="finance-job-timeline__list">
        {sortedJobs.map((job, index) => {
          const statusKey = (job.status || '').toLowerCase()
          const statusLabel = statusLabels[statusKey] ?? job.status ?? fallback
          const formattedTime =
            formatTimestamp(job.queuedAt, locale) ?? fallback
          const backendLabel = job.backend
            ? t('finance.jobs.backend', { backend: job.backend })
            : null
          return (
            <li
              key={job.taskId ?? `job-${index}`}
              className={`finance-job-timeline__item finance-job-timeline__item--${statusKey || 'unknown'}`}
            >
              <div className="finance-job-timeline__status">
                <span className="finance-job-timeline__status-label">
                  {statusLabel}
                </span>
                <span className="finance-job-timeline__timestamp">
                  {formattedTime}
                </span>
              </div>
              <div className="finance-job-timeline__meta">
                {backendLabel ? (
                  <span className="finance-job-timeline__backend">
                    {backendLabel}
                  </span>
                ) : null}
                {job.taskId ? (
                  <span className="finance-job-timeline__task">
                    {t('finance.jobs.task', { id: job.taskId })}
                  </span>
                ) : null}
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
