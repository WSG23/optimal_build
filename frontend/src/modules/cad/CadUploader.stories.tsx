import CadUploader from './CadUploader'
import type { ParseStatusUpdate } from '../../api/client'
import { TranslationProvider } from '../../i18n'

const meta = {
  title: 'CAD/Uploader',
  component: CadUploader,
}

export default meta

const sampleStatus: ParseStatusUpdate = {
  jobId: 'demo',
  status: 'ready',
  overlays: ['fire_access', 'coastal'],
  hints: ['Ensure secondary egress'],
  zoneCode: 'RA',
  updatedAt: new Date().toISOString(),
}

export const Ready = () => (
  <TranslationProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader onUpload={console.log} status={sampleStatus} zoneCode="RA" />
    </div>
  </TranslationProvider>
)

export const Loading = () => (
  <TranslationProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader
        onUpload={console.log}
        isUploading
        status={{ ...sampleStatus, status: 'processing', overlays: [], hints: [] }}
        zoneCode="RCR"
      />
    </div>
  </TranslationProvider>
)
