import { useEffect, useState, type ChangeEvent } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { DocumentRecord, SourceRecord } from '../types'
import { toErrorMessage } from '../utils/error'

const DocumentsPage = () => {
  const [sources, setSources] = useState<SourceRecord[]>([])
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [selectedSource, setSelectedSource] = useState<number | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSources = async () => {
      try {
        const response = await ReviewAPI.getSources()
        setSources(response.items)
        setError(null)
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load sources'))
      }
    }

    void loadSources()
  }, [])

  useEffect(() => {
    const loadDocuments = async () => {
      setLoading(true)
      try {
        const response = await ReviewAPI.getDocuments(selectedSource)
        setDocuments(response.items)
        setError(null)
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load documents'))
      } finally {
        setLoading(false)
      }
    }

    void loadDocuments()
  }, [selectedSource])

  const handleSourceChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setSelectedSource(
      event.target.value ? Number(event.target.value) : undefined,
    )
  }

  return (
    <div>
      <Header
        title="Documents"
        actions={
          <select
            className="bg-surface-inverse/70 border border-border-neutral/40 rounded-md px-3 py-2 text-sm text-text-inverse"
            value={selectedSource ?? ''}
            onChange={handleSourceChange}
          >
            <option value="">All sources</option>
            {sources.map((source) => (
              <option key={source.id} value={source.id}>
                {source.authority} · {source.topic}
              </option>
            ))}
          </select>
        }
      />
      {loading && (
        <p className="text-sm text-text-inverse/70">Loading documents…</p>
      )}
      {error && <p className="text-sm text-error-strong/85">{error}</p>}
      {!loading && !error && (
        <ul className="space-y-3">
          {documents.map((document) => (
            <li
              key={document.id}
              className="border border-border-neutral/40 rounded-lg p-4 bg-surface-inverse/40"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-text-inverse">
                    Version {document.version_label || 'N/A'}
                  </p>
                  <p className="text-xs text-text-inverse-muted/90">
                    Storage: {document.storage_path}
                  </p>
                </div>
                {document.retrieved_at && (
                  <span className="text-xs text-text-inverse/70">
                    Retrieved {new Date(document.retrieved_at).toLocaleString()}
                  </span>
                )}
              </div>
            </li>
          ))}
          {documents.length === 0 && (
            <li className="border border-border-neutral/40 rounded-lg p-6 text-center text-sm text-text-inverse/70">
              No documents available for the selected filter.
            </li>
          )}
        </ul>
      )}
    </div>
  )
}

export default DocumentsPage
