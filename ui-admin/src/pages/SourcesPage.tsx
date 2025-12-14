import { useEffect, useState } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { SourceRecord } from '../types'
import { toErrorMessage } from '../utils/error'
import { useTranslation } from '../i18n'

const SourcesPage = () => {
  const [sources, setSources] = useState<SourceRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { t } = useTranslation()

  useEffect(() => {
    const loadSources = async () => {
      setLoading(true)
      try {
        const response = await ReviewAPI.getSources()
        setSources(response.items)
        setError(null)
      } catch (error) {
        setError(toErrorMessage(error, t('sources.loadError')))
      } finally {
        setLoading(false)
      }
    }

    void loadSources()
  }, [t])

  return (
    <div>
      <Header title={t('sources.title')} />
      {loading && (
        <p className="text-sm text-text-muted">{t('sources.loading')}</p>
      )}
      {error && <p className="text-sm text-error-muted">{error}</p>}
      {!loading && !error && (
        <div className="overflow-hidden rounded border border-border-subtle bg-surface">
          <table className="min-w-full divide-y divide-border-subtle">
            <thead className="bg-surface-alt">
              <tr>
                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium uppercase text-text-muted"
                >
                  {t('sources.columns.authority')}
                </th>
                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium uppercase text-text-muted"
                >
                  {t('sources.columns.topic')}
                </th>
                <th
                  scope="col"
                  className="px-4 py-3 text-left text-xs font-medium uppercase text-text-muted"
                >
                  {t('sources.columns.document')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {sources.map((source) => (
                <tr key={source.id} className="hover:bg-surface-alt/70">
                  <td className="px-4 py-3 text-sm text-text-primary">
                    <div className="font-semibold">{source.authority}</div>
                    <div className="text-xs text-text-muted">
                      {source.jurisdiction}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-text-secondary">
                    {source.topic}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <a
                      href={source.landing_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-success-strong hover:text-success-strong/80"
                    >
                      {source.doc_title}
                    </a>
                  </td>
                </tr>
              ))}
              {sources.length === 0 && (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-6 text-center text-sm text-text-muted"
                  >
                    {t('sources.empty')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default SourcesPage
