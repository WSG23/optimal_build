import { useCallback, useEffect, useRef, useState } from 'react'

import { type CadParseJob, type ParseStatusUpdate, useApiClient } from '../api/client'
import { AppLayout } from '../App'
import { useLocale } from '../i18n/LocaleContext'
import CadUploader from '../modules/cad/CadUploader'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import useRules from '../hooks/useRules'

export function CadUploadPage() {
  const apiClient = useApiClient()
  const { strings } = useLocale()
  const [job, setJob] = useState<CadParseJob | null>(null)
  const [status, setStatus] = useState<ParseStatusUpdate | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [zoneCode, setZoneCode] = useState('RA')
  const [error, setError] = useState<string | null>(null)
  const cancelRef = useRef<(() => void) | null>(null)
  const { rules, loading } = useRules(apiClient)

  useEffect(() => {
    return () => {
      cancelRef.current?.()
    }
  }, [])

  const handleUpload = useCallback(
    async (file: File) => {
      cancelRef.current?.()
      setIsUploading(true)
      setError(null)
      try {
        const nextJob = await apiClient.uploadCadDrawing(file, { zoneCode })
        setJob(nextJob)
        const initial: ParseStatusUpdate = {
          jobId: nextJob.jobId,
          status: nextJob.status === 'ready' ? 'ready' : 'processing',
          overlays: nextJob.overlays,
          hints: nextJob.hints,
          zoneCode: nextJob.zoneCode,
          updatedAt: new Date().toISOString(),
          message: nextJob.message,
        }
        setStatus(initial)

        cancelRef.current = apiClient.pollParseStatus({
          jobId: nextJob.jobId,
          zoneCode: nextJob.zoneCode ?? zoneCode,
          onUpdate: (update) => {
            setStatus(update)
          },
          intervalMs: 2500,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed')
      } finally {
        setIsUploading(false)
      }
    },
    [apiClient, zoneCode],
  )

  return (
    <AppLayout title={strings.uploader.title} subtitle={strings.uploader.subtitle}>
      <div className="cad-upload">
        <div className="cad-upload__controls">
          <label className="cad-upload__label">
            <span>{strings.uploader.zone}</span>
            <select value={zoneCode} onChange={(event) => setZoneCode(event.target.value)}>
              <option value="RA">RA</option>
              <option value="RCR">RCR</option>
              <option value="CBD">CBD</option>
            </select>
          </label>
          {error && <p className="cad-upload__error">{error}</p>}
        </div>

        <CadUploader
          onUpload={handleUpload}
          isUploading={isUploading}
          status={status}
          zoneCode={job?.zoneCode ?? zoneCode}
        />
      </div>

      <RulePackExplanationPanel rules={rules} loading={loading} />
    </AppLayout>
  )
}

export default CadUploadPage
