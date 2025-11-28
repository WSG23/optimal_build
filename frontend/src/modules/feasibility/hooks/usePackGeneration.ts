import type { FormEvent } from 'react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  generateProfessionalPack,
  type ProfessionalPackSummary,
  type ProfessionalPackType,
} from '../../../api/agents'
import type { StoredAssetOptimization, FinancialSummary } from '../types'
import { ASSET_MIX_STORAGE_PREFIX, PACK_OPTIONS } from '../types'

interface UsePackGenerationOptions {
  propertyIdFromQuery: string
  generatePackFn?: typeof generateProfessionalPack
  t: (key: string, options?: Record<string, unknown>) => string
}

interface UsePackGenerationResult {
  packPropertyId: string
  setPackPropertyId: (id: string) => void
  packType: ProfessionalPackType
  setPackType: (type: ProfessionalPackType) => void
  packSummary: ProfessionalPackSummary | null
  packLoading: boolean
  packError: string | null
  handlePackSubmit: (event: FormEvent<HTMLFormElement>) => void
  selectedPackOption: (typeof PACK_OPTIONS)[number]
  capturedAssetMix: StoredAssetOptimization[]
  capturedFinancialSummary: FinancialSummary | null
}

export function usePackGeneration({
  propertyIdFromQuery,
  generatePackFn = generateProfessionalPack,
  t,
}: UsePackGenerationOptions): UsePackGenerationResult {
  const [packPropertyId, setPackPropertyId] = useState<string>('')
  const [packType, setPackType] = useState<ProfessionalPackType>('universal')
  const [packSummary, setPackSummary] = useState<ProfessionalPackSummary | null>(null)
  const [packLoading, setPackLoading] = useState(false)
  const [packError, setPackError] = useState<string | null>(null)
  const [capturedAssetMix, setCapturedAssetMix] = useState<StoredAssetOptimization[]>([])
  const [capturedFinancialSummary, setCapturedFinancialSummary] =
    useState<FinancialSummary | null>(null)

  useEffect(() => {
    setPackPropertyId((current) =>
      current === propertyIdFromQuery ? current : propertyIdFromQuery,
    )
    setPackSummary(null)
    setPackError(null)
    setPackLoading(false)

    if (propertyIdFromQuery) {
      try {
        const raw = sessionStorage.getItem(
          `${ASSET_MIX_STORAGE_PREFIX}${propertyIdFromQuery}`,
        )
        if (raw) {
          const parsed = JSON.parse(raw) as {
            optimizations?: StoredAssetOptimization[]
            financialSummary?: {
              totalEstimatedRevenueSgd: number | null
              totalEstimatedCapexSgd: number | null
              dominantRiskProfile: string | null
              notes?: string[]
            }
          }
          if (Array.isArray(parsed.optimizations)) {
            setCapturedAssetMix(parsed.optimizations)
          } else {
            setCapturedAssetMix([])
          }
          if (parsed.financialSummary) {
            setCapturedFinancialSummary({
              totalEstimatedRevenueSgd:
                parsed.financialSummary.totalEstimatedRevenueSgd ?? null,
              totalEstimatedCapexSgd:
                parsed.financialSummary.totalEstimatedCapexSgd ?? null,
              dominantRiskProfile:
                parsed.financialSummary.dominantRiskProfile ?? null,
              notes: parsed.financialSummary.notes ?? [],
            })
          } else {
            setCapturedFinancialSummary(null)
          }
        } else {
          setCapturedAssetMix([])
          setCapturedFinancialSummary(null)
        }
      } catch (error) {
        console.warn('Unable to load stored asset mix', error)
        setCapturedAssetMix([])
        setCapturedFinancialSummary(null)
      }
    } else {
      setCapturedAssetMix([])
      setCapturedFinancialSummary(null)
    }
  }, [propertyIdFromQuery])

  const selectedPackOption = useMemo(() => {
    return PACK_OPTIONS.find((option) => option.value === packType) ?? PACK_OPTIONS[0]
  }, [packType])

  const handlePackSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = packPropertyId.trim()
      if (!trimmed) {
        setPackError(t('wizard.pack.missingProperty'))
        setPackSummary(null)
        return
      }

      setPackLoading(true)
      setPackError(null)

      Promise.resolve(generatePackFn(trimmed, packType))
        .then((summary) => {
          setPackSummary(summary)
        })
        .catch((error) => {
          setPackSummary(null)
          setPackError(
            error instanceof Error
              ? error.message
              : t('wizard.pack.errorFallback'),
          )
        })
        .finally(() => {
          setPackLoading(false)
        })
    },
    [generatePackFn, packPropertyId, packType, t],
  )

  return {
    packPropertyId,
    setPackPropertyId,
    packType,
    setPackType,
    packSummary,
    packLoading,
    packError,
    handlePackSubmit,
    selectedPackOption,
    capturedAssetMix,
    capturedFinancialSummary,
  }
}
