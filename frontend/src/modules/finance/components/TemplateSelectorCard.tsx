import { Box, Typography, Stack, alpha, useTheme } from '@mui/material'
import { Card } from '../../../components/canonical/Card'
import { Input } from '../../../components/canonical/Input'
import { useTranslation } from '../../../i18n'
import {
  SG_FINANCE_TEMPLATES,
  type FinanceTemplateDefinition,
} from './financeScenarioConstants'

interface TemplateSelectorCardProps {
  selectedTemplateId: string
  scenarioName: string
  onApplyTemplate: (templateId: string) => void
  onScenarioNameChange: (name: string) => void
}

export function TemplateSelectorCard({
  selectedTemplateId,
  scenarioName,
  onApplyTemplate,
  onScenarioNameChange,
}: TemplateSelectorCardProps) {
  const { t } = useTranslation()
  const theme = useTheme()

  const selectedTemplate: FinanceTemplateDefinition =
    SG_FINANCE_TEMPLATES.find(
      (template) => template.id === selectedTemplateId,
    ) ?? SG_FINANCE_TEMPLATES[0]

  return (
    <Card sx={{ p: 'var(--ob-space-100)', mb: 'var(--ob-space-100)' }}>
      <Stack spacing="var(--ob-space-125)">
        <Box>
          <Typography
            variant="subtitle2"
            component="h2"
            sx={{ mb: 'var(--ob-space-075)' }}
          >
            Singapore deal templates
          </Typography>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing="var(--ob-space-100)"
            useFlexGap
            flexWrap="wrap"
          >
            {SG_FINANCE_TEMPLATES.map((template) => {
              const active = template.id === selectedTemplateId
              return (
                <Box
                  key={template.id}
                  component="button"
                  type="button"
                  onClick={() => {
                    onApplyTemplate(template.id)
                  }}
                  sx={{
                    textAlign: 'left',
                    p: 'var(--ob-space-100)',
                    borderRadius: 'var(--ob-radius-sm)',
                    border: '1px solid',
                    borderColor: active ? 'primary.main' : 'divider',
                    backgroundColor: active
                      ? 'var(--ob-color-brand-muted)'
                      : 'transparent',
                    color: 'inherit',
                    cursor: 'pointer',
                    minWidth: { xs: '100%', md: 180 },
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 'var(--ob-font-weight-bold)' }}
                  >
                    {template.label}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{ color: 'text.secondary' }}
                  >
                    {template.description}
                  </Typography>
                </Box>
              )
            })}
          </Stack>
        </Box>

        <Box
          sx={{
            p: 'var(--ob-space-100)',
            borderRadius: 'var(--ob-radius-sm)',
            bgcolor: alpha(theme.palette.primary.main, 0.06),
          }}
        >
          <Typography
            variant="body2"
            sx={{ fontWeight: 'var(--ob-font-weight-bold)' }}
          >
            {selectedTemplate.label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {selectedTemplate.description}
          </Typography>
        </Box>

        <Input
          label={t('finance.scenarioCreator.fields.name')}
          value={scenarioName}
          onChange={(event) => {
            onScenarioNameChange(event.target.value)
          }}
          placeholder={t('finance.scenarioCreator.placeholders.name')}
        />
      </Stack>
    </Card>
  )
}
