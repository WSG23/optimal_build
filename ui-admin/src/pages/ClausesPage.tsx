import { useEffect, useState } from 'react'
import Header from '../components/Header'
import { ReviewAPI } from '../api/client'
import type { ClauseRecord, DocumentRecord } from '../types'
import PDFViewer from '../components/PDFViewer'

const ClausesPage = () => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [clauses, setClauses] = useState<ClauseRecord[]>([])
  const [selectedDocument, setSelectedDocument] = useState<number | undefined>()
  const [previewDoc, setPreviewDoc] = useState<DocumentRecord | undefined>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    ReviewAPI.getDocuments().then((response) => setDocuments(response.items))
  }, [])

  useEffect(() => {
    setLoading(true)
    ReviewAPI.getClauses(selectedDocument)
      .then((response) => {
        setClauses(response.items)
        setError(null)
        if (selectedDocument) {
          setPreviewDoc(documents.find((doc) => doc.id === selectedDocument))
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedDocument, documents])

  return (
    <div>
      <Header
        title="Clauses"
        actions={
          <select
            className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm"
            value={selectedDocument ?? ''}
            onChange={(event) =>
              setSelectedDocument(
                event.target.value ? Number(event.target.value) : undefined,
              )
            }
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
