import CadUploader from './CadUploader'
import type { ParseStatusUpdate } from '../../api/client'
import { TranslationProvider } from '../../i18n'

const meta = {
  title: 'CAD/Uploader',
  component: CadUploader,
}

export default meta

const baseStatus: ParseStatusUpdate = {
  importId: 'demo-import',
  status: 'completed',
  requestedAt: new Date(Date.now() - 120000).toISOString(),
  completedAt: new Date().toISOString(),
  jobId: 'demo-job',
  detectedFloors: [
    { name: 'Level 01', unitIds: ['101', '102'] },
    { name: 'Level 02', unitIds: ['201'] },
  ],
  detectedUnits: ['101', '102', '201'],
  metadata: { parser: 'storybook' },
  error: null,
}

export const Ready = () => (
  <TranslationProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader onUpload={console.log} status={baseStatus} />
    </div>
  </TranslationProvider>
)

export const Loading = () => (
  <TranslationProvider>
    <div style={{ maxWidth: 960 }}>
      <CadUploader
        onUpload={console.log}
        isUploading
        status={{
          ...baseStatus,
          status: 'running',
          completedAt: null,
          metadata: { parser: 'storybook', progress: 65 },
        }}
      />
    </div>
  </TranslationProvider>
)
