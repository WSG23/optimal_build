import { afterEach, describe, expect, it } from 'vitest'

import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'

import i18n from '../../../../i18n'
import { TranslationProvider } from '../../../../i18n'
import { FinanceJobTimeline } from '../FinanceJobTimeline'

describe('FinanceJobTimeline component', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders empty state when no jobs are provided', () => {
    render(
      <TranslationProvider>
        <FinanceJobTimeline jobs={[]} pendingCount={0} />
      </TranslationProvider>,
    )

    expect(screen.getByText(i18n.t('finance.jobs.title'))).toBeVisible()
    expect(screen.getByText(i18n.t('finance.jobs.empty'))).toBeVisible()
  })

  it('renders job entries with status, timestamp and meta', () => {
    const jobs = [
      {
        taskId: 'task-1',
        status: 'queued',
        backend: 'celery',
        queuedAt: '2025-10-22T12:00:00Z',
      },
      {
        taskId: 'task-2',
        status: 'completed',
        backend: 'celery',
        queuedAt: '2025-10-22T12:05:00Z',
      },
    ]

    render(
      <TranslationProvider>
        <FinanceJobTimeline jobs={jobs} pendingCount={1} />
      </TranslationProvider>,
    )

    expect(screen.getByText(i18n.t('finance.jobs.title'))).toBeVisible()
    expect(
      screen.getByText(
        i18n.t('finance.sensitivity.pendingNotice', { count: 1 }),
      ),
    ).toBeVisible()
    expect(
      screen.getByText(i18n.t('finance.jobs.task', { id: 'task-1' })),
    ).toBeVisible()
    expect(
      screen.getByText(i18n.t('finance.jobs.task', { id: 'task-2' })),
    ).toBeVisible()
    expect(
      screen.getAllByText(
        i18n.t('finance.jobs.backend', { backend: 'celery' }),
      )[0],
    ).toBeVisible()
    expect(screen.getByText(i18n.t('finance.jobs.status.queued'))).toBeVisible()
    expect(
      screen.getByText(i18n.t('finance.jobs.status.completed')),
    ).toBeVisible()
  })
})
