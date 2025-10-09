import { useCallback, useEffect, useId, useRef, useState } from 'react'

import {
  type CadImportSummary,
  type ParseStatusUpdate,
  useApiClient,
} from '../api/client'
import { AppLayout } from '../App'
import { useTranslation } from '../i18n'
import CadUploader from '../modules/cad/CadUploader'
import RulePackExplanationPanel from '../modules/cad/RulePackExplanationPanel'
import useRules from '../hooks/useRules'

const DEFAULT_PROJECT_ID = 5821
const DEFAULT_ZONE_CODE = 'SG:residential'

const ZONE_OPTIONS: Array<{ value: string; labelKey: string }> = [
  { value: 'SG:residential', labelKey: 'residential' },
  { value: 'SG:commercial', labelKey: 'commercial' },
  { value: 'SG:industrial', labelKey: 'industrial' },
  { value: 'SG:mixed_use', labelKey: 'mixedUse' },
  { value: 'SG:business_park', labelKey: 'businessPark' },
]

export function CadUploadPage() {
  const apiClient = useApiClient()
  const { t } = useTranslation()
  const [job, setJob] = useState<CadImportSummary | null>(null)
  const [status, setStatus] = useState<ParseStatusUpdate | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [projectId, setProjectId] = useState<number>(DEFAULT_PROJECT_ID)
  const [zoneCode, setZoneCode] = useState<string>(DEFAULT_ZONE_CODE)
  const cancelRef = useRef<(() => void) | null>(null)
  const { rules, loading } = useRules(apiClient)
  const projectIdInputId = useId()
  const zoneInputId = useId()

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
        const summary = await apiClient.uploadCadDrawing(file, {
          projectId,
          zoneCode,
        })
        setJob(summary)
        setStatus({
          importId: summary.importId,
          status: summary.parseStatus,
          requestedAt: null,
          completedAt: null,
          jobId: null,
          detectedFloors: summary.detectedFloors,
          detectedUnits: summary.detectedUnits,
          metadata: summary.vectorSummary ?? null,
          error: null,
        })
        const initial = await apiClient.triggerParse(summary.importId)
        setStatus(initial)
        cancelRef.current = apiClient.pollParseStatus({
          importId: summary.importId,
          onUpdate: (update) => {
            setStatus(update)
          },
          intervalMs: 2500,
        })
      } catch (err) {
        setError(
          err instanceof Error ? err.message : t('common.errors.uploadFailed'),
        )
      } finally {
        setIsUploading(false)
      }
    },
    [apiClient, projectId, t, zoneCode],
  )

  return (
    <AppLayout title={t('uploader.title')} subtitle={t('uploader.subtitle')}>
      <div className="cad-upload">
        <div className="cad-upload__controls">
          <label className="cad-upload__label" htmlFor={projectIdInputId}>
            <span>{t('uploader.projectLabel')}</span>
            <input
              id={projectIdInputId}
              type="number"
              min={1}
              value={projectId}
              onChange={(event) => {
                const value = Number(event.target.value)
                if (Number.isNaN(value) || value <= 0) {
                  setProjectId(DEFAULT_PROJECT_ID)
                  return
                }
                setProjectId(Math.trunc(value))
              }}
            />
          </label>
          <label className="cad-upload__label" htmlFor={zoneInputId}>
            <span>{t('uploader.zoneLabel')}</span>
            <select
              id={zoneInputId}
              value={zoneCode}
              onChange={(event) => {
                setZoneCode(event.target.value)
              }}
            >
              {ZONE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(`uploader.zoneOptions.${option.labelKey}`)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {error && <p className="cad-upload__error">{error}</p>}

        <CadUploader
          onUpload={(file) => {
            void handleUpload(file)
          }}
          isUploading={isUploading}
          status={status}
          summary={job}
        />
      </div>

      <RulePackExplanationPanel rules={rules} loading={loading} />
    </AppLayout>
  )
}

export default CadUploadPage
