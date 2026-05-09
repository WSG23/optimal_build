import { Alert, Box, Stack, Typography } from '@mui/material'

import { Button } from '../../components/canonical/Button'
import { FinanceIdentityHelper } from './components/FinancePrivacyNotice'
import type { FinanceWorkbookImportPreview } from '../../api/finance'
import type { QuickScreenFinanceDraft } from './quickScreenDraft'
import type { TranslationOptions } from '../../i18n/i18n'

type TranslateFn = (key: string, options?: TranslationOptions) => string

interface FinanceAlertsProps {
  error: string | null
  scenarioError: string | null
  seedError: string | null
  scenarioMessage: string | null
  needsScenarioIdentity: boolean
  needsScenarioCreateIdentity: boolean
  onboardingMode: string | null
  effectiveProjectId: string
  previewingWorkbook: boolean
  importingWorkbook: boolean
  handleImportWorkbookClick: () => void
  navigate: (path: string) => void
  t: TranslateFn
  quickScreenDraft: QuickScreenFinanceDraft | null
  quickScreenAssessmentLines: string[]
  handleImportQuickScreenDraft: () => void
  clearQuickScreenDraft: () => void
  workbookPreview: FinanceWorkbookImportPreview | null
  handleConfirmWorkbookImport: () => void
  handleDismissWorkbookPreview: () => void
}

export function FinanceAlerts({
  error,
  scenarioError,
  seedError,
  scenarioMessage,
  needsScenarioIdentity,
  needsScenarioCreateIdentity,
  onboardingMode,
  effectiveProjectId,
  previewingWorkbook,
  importingWorkbook,
  handleImportWorkbookClick,
  navigate,
  t,
  quickScreenDraft,
  quickScreenAssessmentLines,
  handleImportQuickScreenDraft,
  clearQuickScreenDraft,
  workbookPreview,
  handleConfirmWorkbookImport,
  handleDismissWorkbookPreview,
}: FinanceAlertsProps) {
  return (
    <>
      {error && (
        <Alert
          severity="error"
          role="alert"
          aria-live="assertive"
          sx={{ mb: 'var(--ob-space-150)' }}
        >
          <strong>{t('finance.errors.generic')}</strong>
          <Box component="span" sx={{ display: 'block' }}>
            {error}
          </Box>
          {needsScenarioIdentity && <FinanceIdentityHelper compact />}
        </Alert>
      )}

      {scenarioError && (
        <Alert
          severity="error"
          role="alert"
          aria-live="assertive"
          sx={{ mb: 'var(--ob-space-150)' }}
        >
          {scenarioError}
          {needsScenarioCreateIdentity && <FinanceIdentityHelper compact />}
        </Alert>
      )}
      {seedError && (
        <Alert
          severity="error"
          role="alert"
          aria-live="assertive"
          sx={{ mb: 'var(--ob-space-150)' }}
        >
          {seedError}
          {needsScenarioCreateIdentity && <FinanceIdentityHelper compact />}
        </Alert>
      )}
      {scenarioMessage && (
        <Alert
          severity="success"
          role="status"
          aria-live="polite"
          sx={{ mb: 'var(--ob-space-150)' }}
        >
          {scenarioMessage}
        </Alert>
      )}
      {onboardingMode === 'workbook' && (
        <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
          <Stack spacing="var(--ob-space-100)">
            <Typography variant="body2">
              Workbook onboarding is active for this project. Import an existing
              Excel model to structure it into the Singapore finance workflow
              without rebuilding assumptions manually.
            </Typography>
            <Box>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleImportWorkbookClick}
                disabled={previewingWorkbook || importingWorkbook}
              >
                {previewingWorkbook || importingWorkbook
                  ? 'Preparing workbook import...'
                  : 'Choose workbook'}
              </Button>
            </Box>
          </Stack>
        </Alert>
      )}
      {onboardingMode === 'sample' && (
        <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
          <Stack spacing="var(--ob-space-100)">
            <Typography variant="body2">
              This sample project starts with a Singapore underwriting template.
              Review the template guidance below, then export lender or investor
              materials once the scenario is ready.
            </Typography>
            <Stack direction="row" spacing="var(--ob-space-100)">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate('/developers/why-not-excel')}
              >
                Why not Excel?
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  navigate(`/projects/${effectiveProjectId}/evidence`)
                }
              >
                Review evidence pack
              </Button>
            </Stack>
          </Stack>
        </Alert>
      )}
      {quickScreenDraft && (
        <Alert severity="info" sx={{ mb: 'var(--ob-space-150)' }}>
          <Stack spacing="var(--ob-space-125)">
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              spacing="var(--ob-space-100)"
              justifyContent="space-between"
              alignItems={{ xs: 'flex-start', md: 'center' }}
            >
              <Box>
                <strong>
                  {t('finance.actions.importQuickScreen', {
                    defaultValue: 'Quick screen draft ready.',
                  })}
                </strong>
                <Box component="span" sx={{ display: 'block' }}>
                  {quickScreenDraft.scenario.name}
                </Box>
                {quickScreenDraft.assessment?.generatedAt ? (
                  <Box
                    component="span"
                    sx={{
                      display: 'block',
                      fontSize: 'var(--ob-font-size-2xs)',
                      color: 'var(--ob-color-text-tertiary)',
                      mt: 'var(--ob-space-050)',
                    }}
                  >
                    Screened{' '}
                    {new Date(
                      quickScreenDraft.assessment.generatedAt,
                    ).toLocaleString()}
                  </Box>
                ) : null}
              </Box>
              <Stack direction="row" spacing="var(--ob-space-100)">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleImportQuickScreenDraft}
                >
                  {t('finance.actions.importQuickScreen', {
                    defaultValue: 'Import quick screen',
                  })}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearQuickScreenDraft}
                >
                  {t('common.actions.cancel')}
                </Button>
              </Stack>
            </Stack>
            {quickScreenAssessmentLines.length > 0 ? (
              <Box component="ul" sx={{ m: 0, pl: 3 }}>
                {quickScreenAssessmentLines.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </Box>
            ) : null}
          </Stack>
        </Alert>
      )}
      {workbookPreview && (
        <Alert
          severity={workbookPreview.isValid ? 'info' : 'warning'}
          sx={{ mb: 'var(--ob-space-150)' }}
        >
          <Stack spacing="var(--ob-space-125)">
            <Box>
              <strong>{workbookPreview.filename}</strong>
              <Box component="span" sx={{ display: 'block' }}>
                {workbookPreview.scenarioName ?? 'Workbook preview'} •{' '}
                {workbookPreview.assetCount} assets •{' '}
                {workbookPreview.detectedSheets.length} sheets mapped
              </Box>
            </Box>
            {workbookPreview.warnings.length > 0 && (
              <Box component="ul" sx={{ m: 0, pl: 3 }}>
                {workbookPreview.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </Box>
            )}
            {workbookPreview.validationErrors.length > 0 && (
              <Box component="ul" sx={{ m: 0, pl: 3 }}>
                {workbookPreview.validationErrors.map((issue) => (
                  <li key={`${issue.field}:${issue.message}`}>
                    {issue.field}: {issue.message}
                  </li>
                ))}
              </Box>
            )}
            <Stack direction="row" spacing="var(--ob-space-100)">
              {workbookPreview.isValid ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleConfirmWorkbookImport}
                  disabled={importingWorkbook}
                >
                  {importingWorkbook
                    ? t('finance.actions.importingWorkbook', {
                        defaultValue: 'Importing workbook…',
                      })
                    : t('finance.actions.importWorkbook', {
                        defaultValue: 'Import workbook',
                      })}
                </Button>
              ) : null}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismissWorkbookPreview}
              >
                {t('common.actions.cancel')}
              </Button>
            </Stack>
          </Stack>
        </Alert>
      )}
    </>
  )
}
