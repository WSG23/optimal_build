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
          project: projectName ?? t('finance.projectSelector.defaultLabel', { id: '' }),
        })}
      </p>
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
    </div>
  )
}
