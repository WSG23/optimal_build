import CadUploader from './CadUploader'
import type { ParseStatusUpdate } from '../../api/client'
import { LocaleProvider } from '../../i18n/LocaleContext'

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
  <LocaleProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader onUpload={console.log} status={sampleStatus} zoneCode="RA" />
    </div>
  </LocaleProvider>
)

export const Loading = () => (
  <LocaleProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader
        onUpload={console.log}
        isUploading
        status={{ ...sampleStatus, status: 'processing', overlays: [], hints: [] }}
        zoneCode="RCR"
      />
    </div>
  </LocaleProvider>
)
