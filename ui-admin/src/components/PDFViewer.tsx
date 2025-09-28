import { useEffect, useRef, useState } from 'react'
import { GlobalWorkerOptions, getDocument, version } from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - Vite query parameter import
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.js?url'

GlobalWorkerOptions.workerSrc = pdfWorker

interface PDFViewerProps {
  url?: string | null
}

const PDFViewer = ({ url }: PDFViewerProps) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    async function render() {
      if (!url || !canvasRef.current) {
        return
      }
      try {
        const doc: PDFDocumentProxy = await getDocument(url).promise
        const page = await doc.getPage(1)
        if (!mounted || !canvasRef.current) {
          return
        }
        const viewport = page.getViewport({ scale: 1.2 })
        const context = canvasRef.current.getContext('2d')
        if (!context) {
          return
        }
        canvasRef.current.height = viewport.height
        canvasRef.current.width = viewport.width
        await page.render({ canvasContext: context, viewport }).promise
        setError(null)
      } catch (err) {
        setError('Unable to preview PDF')
        console.warn('PDF preview error', err)
      }
    }
    render()
    return () => {
      mounted = false
    }
  }, [url])

  if (!url) {
    return (
      <p className="text-sm text-slate-400">
        Select a document to preview its PDF.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-400">Powered by PDF.js v{version}</p>
      {error ? (
        <p className="text-sm text-red-400">{error}</p>
      ) : (
        <canvas
          ref={canvasRef}
          className="rounded shadow border border-slate-800"
        />
      )}
    </div>
  )
}

export default PDFViewer
