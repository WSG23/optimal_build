import { useEffect, useState } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { SourceRecord } from '../types'
import { toErrorMessage } from '../utils/error'

const SourcesPage = () => {
  const [sources, setSources] = useState<SourceRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSources = async () => {
      setLoading(true)
      try {
        const response = await ReviewAPI.getSources()
        setSources(response.items)
        setError(null)
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load sources'))
      } finally {
        setLoading(false)
      }
    }

    void loadSources()
  }, [])

  return (
    <div>
      <Header title="Sources" />
      {loading && <p className="text-sm text-slate-400">Loading sources…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <div className="overflow-hidden rounded-lg border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">
                  Authority
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">
                  Topic
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-slate-400">
                  Document
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {sources.map((source) => (
                <tr key={source.id} className="hover:bg-slate-900/70">
                  <td className="px-4 py-3 text-sm text-slate-200">
                    <div className="font-semibold">{source.authority}</div>
                    <div className="text-xs text-slate-400">
                      {source.jurisdiction}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">
                    {source.topic}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <a
                      href={source.landing_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-400 hover:text-emerald-300"
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
                    className="px-4 py-6 text-center text-sm text-slate-400"
                  >
                    No sources available.
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
