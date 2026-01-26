import { useTranslation } from '../../../i18n'
import {
  resolveDefaultRole,
  resolveDefaultUserEmail,
  resolveDefaultUserId,
} from '../../../api/identity'

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

interface FinanceIdentityHelperProps {
  compact?: boolean
}

export function FinanceIdentityHelper({
  compact = false,
}: FinanceIdentityHelperProps) {
  const { t } = useTranslation()
  const role = resolveDefaultRole()
  const email = resolveDefaultUserEmail()
  const userId = resolveDefaultUserId()
  const hasIdentity = Boolean(role || email || userId)
  return (
    <div
      className={
        compact
          ? 'finance-identity-helper finance-identity-helper--compact'
          : 'finance-identity-helper'
      }
    >
      <p className="finance-access-gate__status" role="status">
        {hasIdentity
          ? t('finance.privacy.identityDetected')
          : t('finance.privacy.identityMissing')}
      </p>
      {role && (
        <p className="finance-access-gate__status">
          {t('finance.privacy.roleHint', { role })}
        </p>
      )}
      {email && (
        <p className="finance-access-gate__status">
          {t('finance.privacy.emailHint', { email })}
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
      <p className="finance-access-gate__role">
        {role
          ? t('finance.privacy.roleHint', { role })
          : t('finance.privacy.roleUnknown')}
      </p>
      <FinanceIdentityHelper />
    </div>
  )
}
