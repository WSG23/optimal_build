import { useCallback, useState } from 'react'

import { useTranslation } from '../../../i18n'

interface FinancePrivacyNoticeProps {
  projectName?: string | null
}

export function FinancePrivacyNotice({
  projectName,
}: FinancePrivacyNoticeProps) {
  const { t } = useTranslation()
  return (
    <div className="finance-privacy-banner" role="note">
      <strong>{t('finance.privacy.privateTitle')}</strong>
      <p>
        {t('finance.privacy.privateBody', {
          project:
            projectName ??
            t('finance.projectSelector.defaultLabel', { id: '' }),
        })}
      </p>
    </div>
  )
}

type IdentityStatus = 'idle' | 'success' | 'error'

function useDemoIdentitySetter(): {
  status: IdentityStatus
  apply: () => void
} {
  const [status, setStatus] = useState<IdentityStatus>('idle')

  const apply = useCallback(() => {
    if (typeof window === 'undefined') {
      return
    }
    try {
      window.localStorage.setItem('app:api-role', 'developer')
      window.localStorage.setItem(
        'app:api-user-email',
        'demo-owner@example.com',
      )
      window.localStorage.setItem('app:api-user-id', 'developer-owner-401')
      setStatus('success')
    } catch (error) {
      console.warn('[finance] unable to persist demo finance identity', error)
      setStatus('error')
    }
  }, [])

  return { status, apply }
}

interface FinanceIdentityHelperProps {
  compact?: boolean
}

export function FinanceIdentityHelper({
  compact = false,
}: FinanceIdentityHelperProps) {
  const { t } = useTranslation()
  const { status, apply } = useDemoIdentitySetter()
  return (
    <div
      className={
        compact
          ? 'finance-identity-helper finance-identity-helper--compact'
          : 'finance-identity-helper'
      }
    >
      <button
        type="button"
        className="finance-access-gate__action"
        onClick={apply}
      >
        {t('finance.privacy.applyDemoIdentity')}
      </button>
      {status === 'success' && (
        <p className="finance-access-gate__status" role="status">
          {t('finance.privacy.applyDemoIdentityHint')}
        </p>
      )}
      {status === 'error' && (
        <p className="finance-access-gate__status finance-access-gate__status--error">
          {t('finance.privacy.applyDemoIdentityError')}
        </p>
      )}
    </div>
  )
}

interface FinanceAccessGateProps {
  role: string | null
}

export function FinanceAccessGate({ role }: FinanceAccessGateProps) {
  const { t } = useTranslation()
  return (
    <div className="finance-access-gate" role="alert">
      <h3>{t('finance.privacy.restrictedTitle')}</h3>
      <p>{t('finance.privacy.restrictedBody')}</p>
      <code>localStorage.setItem('app:api-role', 'developer')</code>
      <p className="finance-access-gate__role">
        {t('finance.privacy.roleHint', { role: role ?? 'unknown' })}
      </p>
      <FinanceIdentityHelper />
    </div>
  )
}
