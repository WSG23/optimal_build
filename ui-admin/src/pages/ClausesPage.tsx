import { useEffect, useState, type ChangeEvent } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { ClauseRecord, DocumentRecord } from '../types'
import PDFViewer from '../components/PDFViewer'
import { toErrorMessage } from '../utils/error'

const ClausesPage = () => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [clauses, setClauses] = useState<ClauseRecord[]>([])
  const [selectedDocument, setSelectedDocument] = useState<number | undefined>()
  const [previewDoc, setPreviewDoc] = useState<DocumentRecord | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await ReviewAPI.getDocuments()
        setDocuments(response.items)
        setError(null)
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load documents'))
      }
    }

    void loadDocuments()
  }, [])

  useEffect(() => {
    const loadClauses = async () => {
      setLoading(true)
      try {
        const response = await ReviewAPI.getClauses(selectedDocument)
        setClauses(response.items)
        setError(null)
        if (selectedDocument) {
          setPreviewDoc(documents.find((doc) => doc.id === selectedDocument))
        } else {
          setPreviewDoc(undefined)
        }
      } catch (error) {
        setError(toErrorMessage(error, 'Failed to load clauses'))
      } finally {
        setLoading(false)
      }
    }

    void loadClauses()
  }, [selectedDocument, documents])

  const handleDocumentChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setSelectedDocument(
      event.target.value ? Number(event.target.value) : undefined,
    )
  }

  return (
    <div>
      <Header
        title="Clauses"
        actions={
          <select
            className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm"
            value={selectedDocument ?? ''}
            onChange={handleDocumentChange}
          >
            <option value="">All documents</option>
            {documents.map((document) => (
              <option key={document.id} value={document.id}>
                {document.storage_path}
              </option>
            ))}
          </select>
        }
      />
      {loading && <p className="text-sm text-slate-400">Loading clauses…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="space-y-3">
            {clauses.map((clause) => (
              <article
                key={clause.id}
                className="border border-slate-800 rounded p-4 bg-slate-900/40"
              >
                <h3 className="text-sm font-semibold text-slate-200">
                  {clause.clause_ref || 'Unnamed clause'}
                </h3>
                {clause.section_heading && (
                  <p className="text-xs text-slate-400 mb-2">
                    {clause.section_heading}
                  </p>
                )}
                <p className="text-sm leading-relaxed text-slate-300 whitespace-pre-line">
                  {clause.text_span}
                </p>
              </article>
            ))}
            {clauses.length === 0 && (
              <div className="border border-slate-800 rounded p-6 text-center text-sm text-slate-400">
                No clauses available for the selected document.
              </div>
            )}
          </div>
          <div className="border border-slate-800 rounded p-4 bg-slate-900/40">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">
              Document Preview
            </h3>
            <PDFViewer url={previewDoc?.storage_path} />
          </div>
        </div>
      )}
    </div>
  )
}

export default ClausesPage
