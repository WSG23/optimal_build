import { useEffect, useRef, useState } from 'react'
import { GlobalWorkerOptions, getDocument, version } from 'pdfjs-dist'
import type { PDFDocumentProxy } from 'pdfjs-dist'
// @ts-expect-error - Vite query parameter import
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

GlobalWorkerOptions.workerSrc = pdfWorker

interface PDFViewerProps {
  url?: string | null
}

const PDFViewer = ({ url }: PDFViewerProps) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!url) {
      setError(null)
      return
    }
    let mounted = true
    const render = async () => {
      try {
        const doc: PDFDocumentProxy = await getDocument(url).promise
        const page = await doc.getPage(1)
        // Guard against component unmount before rendering completes.
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        if (!mounted) {
          return
        }
        const canvas = canvasRef.current
        if (!canvas) {
          return
        }
        const viewport = page.getViewport({ scale: 1.2 })
        const context = canvas.getContext('2d')
        if (!context) {
          return
        }
        canvas.height = viewport.height
        canvas.width = viewport.width
        await page.render({ canvasContext: context, viewport }).promise
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        if (!mounted) {
          return
        }
        setError(null)
      } catch (err) {
        setError('Unable to preview PDF')
        console.warn('PDF preview error', err)
      }
    }
    void render()
    return () => {
      mounted = false
    }
  }, [url])

  if (!url) {
    return (
      <p className="text-sm text-text-muted">
        Select a document to preview its PDF.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-text-muted">Powered by PDF.js v{version}</p>
      {error ? (
        <p className="text-sm text-error-muted">{error}</p>
      ) : (
        <canvas
          ref={canvasRef}
          className="rounded border border-border-subtle shadow"
        />
      )}
    </div>
  )
}

export default PDFViewer
