import { useCallback, useEffect, useMemo, useState } from 'react'

import { useTranslation } from '../../i18n'

import {
  FeasibilityAssessmentRequest,
  FeasibilityAssessmentResponse,
  FeasibilityRulesResponse,
  FeasibilityRule,
  NewFeasibilityProjectInput,
} from './types'
import { fetchFeasibilityRules, submitFeasibilityAssessment } from './api'
import Step1NewProject from './Step1NewProject'
import Step2Rules from './Step2Rules'
import Step3Buildable from './Step3Buildable'

const stepKeys = ['projectDetails', 'complianceScope', 'buildabilityResults'] as const
type StepKey = (typeof stepKeys)[number]

type ExtractedError = 'default' | string

function extractErrorMessage(error: unknown): ExtractedError {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'default'
}

export function FeasibilityWizard() {
  const { t } = useTranslation()
  const [currentStep, setCurrentStep] = useState(0)
  const [project, setProject] = useState<NewFeasibilityProjectInput | null>(null)
  const [selectedRuleIds, setSelectedRuleIds] = useState<string[]>([])
  const [assessment, setAssessment] = useState<FeasibilityAssessmentResponse | null>(null)
  const [assessmentError, setAssessmentError] = useState<ExtractedError | null>(null)
  const [rulesData, setRulesData] = useState<FeasibilityRulesResponse | null>(null)
  const [isRulesLoading, setIsRulesLoading] = useState(false)
  const [rulesError, setRulesError] = useState<ExtractedError | null>(null)
  const [isAssessmentLoading, setIsAssessmentLoading] = useState(false)

  useEffect(() => {
    if (!project) {
      setRulesData(null)
      return
    }

    let cancelled = false
    setIsRulesLoading(true)
    setRulesError(null)

    fetchFeasibilityRules(project)
      .then((data) => {
        if (cancelled) {
          return
        }
        setRulesData(data)
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        setRulesError(extractErrorMessage(error))
        setRulesData(null)
      })
      .finally(() => {
        if (!cancelled) {
          setIsRulesLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [project])

  useEffect(() => {
    if (rulesData && selectedRuleIds.length === 0) {
      const { recommendedRuleIds, rules } = rulesData
      const defaults =
        recommendedRuleIds.length > 0
          ? recommendedRuleIds
          : rules
              .filter((rule: FeasibilityRule) => rule.defaultSelected)
              .map((rule: FeasibilityRule) => rule.id)

      if (defaults.length > 0) {
        setSelectedRuleIds(defaults)
      }
    }
  }, [rulesData, selectedRuleIds.length])

  const handleProjectSubmit = useCallback((values: NewFeasibilityProjectInput) => {
    setProject(values)
    setSelectedRuleIds([])
    setAssessment(null)
    setAssessmentError(null)
    setCurrentStep(1)
  }, [])

  const handleRunAssessment = useCallback(() => {
    if (!project) {
      return
    }

    setAssessmentError(null)
    setIsAssessmentLoading(true)
    setAssessment(null)
    setCurrentStep(2)

    const payload: FeasibilityAssessmentRequest = {
      project,
      selectedRuleIds,
    }

    submitFeasibilityAssessment(payload)
      .then((response) => {
        setAssessment(response)
      })
      .catch((error: unknown) => {
        setAssessmentError(extractErrorMessage(error))
        setCurrentStep(1)
      })
      .finally(() => {
        setIsAssessmentLoading(false)
      })
  }, [project, selectedRuleIds])

  const handleRestart = useCallback(() => {
    setProject(null)
    setSelectedRuleIds([])
    setAssessment(null)
    setAssessmentError(null)
    setCurrentStep(0)
    setRulesData(null)
    setRulesError(null)
  }, [])

  const stepIndicator = useMemo(() => {
    const stepLabels = stepKeys.map((key: StepKey) => t(`wizard.steps.${key}`))
    return (
      <ol className="feasibility-progress">
        {stepLabels.map((label, index) => {
          const isActive = index === currentStep
          const isCompleted = index < currentStep
          return (
            <li
              key={label}
              className={`feasibility-progress__item${
                isActive ? ' feasibility-progress__item--active' : ''
              }${isCompleted ? ' feasibility-progress__item--done' : ''}`}
            >
              <span className="feasibility-progress__index">{index + 1}</span>
              <span>{label}</span>
            </li>
          )
        })}
      </ol>
    )
  }, [currentStep, t])

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <Step1NewProject
            onSubmit={handleProjectSubmit}
            defaultValues={project ?? undefined}
            isSubmitting={isRulesLoading && Boolean(project)}
          />
        )
      case 1:
        if (!project) {
          return null
        }
        return (
          <Step2Rules
            project={project}
            rules={rulesData?.rules ?? []}
            summary={rulesData?.summary}
            isLoading={isRulesLoading}
            error={
              rulesError
                ? rulesError === 'default'
                  ? t('wizard.errors.generic')
                  : rulesError
                : null
            }
            selectedRuleIds={selectedRuleIds}
            onSelectionChange={setSelectedRuleIds}
            onBack={() => setCurrentStep(0)}
            onContinue={handleRunAssessment}
            isEvaluating={isAssessmentLoading}
          />
        )
      case 2:
        if (!assessment) {
          return (
            <Step3Buildable
              assessment={{
                projectId: project?.name ?? t('wizard.step3.placeholders.pendingProjectName'),
                summary: {
                  maxPermissibleGfaSqm: project?.targetGrossFloorAreaSqm ?? 0,
                  estimatedAchievableGfaSqm: project?.targetGrossFloorAreaSqm ?? 0,
                  estimatedUnitCount: 0,
                  siteCoveragePercent: 0,
                  remarks: t('wizard.step3.placeholders.preparingAssessment'),
                },
                rules: [],
                recommendations: [],
              }}
              onBack={() => setCurrentStep(1)}
              onRestart={handleRestart}
              isLoading
            />
          )
        }
        return (
          <Step3Buildable
            assessment={assessment}
            onBack={() => setCurrentStep(1)}
            onRestart={handleRestart}
            isLoading={isAssessmentLoading && !assessment}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="feasibility-wizard">
      <header className="feasibility-wizard__header">
        <h1>{t('wizard.title')}</h1>
        <p>{t('wizard.description')}</p>
        {stepIndicator}
      </header>

      {assessmentError && (
        <p className="feasibility-wizard__error">
          {assessmentError === 'default' ? t('wizard.errors.generic') : assessmentError}
        </p>
      )}

      <main>{renderStep()}</main>
    </div>
  )
}

export default FeasibilityWizard
