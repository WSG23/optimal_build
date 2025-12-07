import { useEffect, useMemo, useState } from 'react'

import {
  DEAL_STAGE_ORDER,
  fetchDeals,
  type DealStage,
  type DealSummary,
} from '../../../api/deals'
import { isAbortError } from '../utils/formatters'

function groupDealsByStage(
  deals: DealSummary[],
): Record<DealStage, DealSummary[]> {
  return deals.reduce<Record<DealStage, DealSummary[]>>(
    (acc, deal) => {
      const stage = deal.pipelineStage
      const bucket = acc[stage] ?? []
      bucket.push(deal)
      acc[stage] = bucket
      return acc
    },
    {} as Record<DealStage, DealSummary[]>,
  )
}

interface UseDealsOptions {
  t: (key: string) => string
}

interface UseDealsResult {
  deals: DealSummary[]
  loadingDeals: boolean
  dealError: string | null
  selectedDealId: string | null
  selectedDeal: DealSummary | null
  groupedDeals: Record<DealStage, DealSummary[]>
  stageOrder: readonly DealStage[]
  setSelectedDealId: (id: string | null) => void
}

export function useDeals({ t }: UseDealsOptions): UseDealsResult {
  const [deals, setDeals] = useState<DealSummary[]>([])
  const [loadingDeals, setLoadingDeals] = useState<boolean>(false)
  const [dealError, setDealError] = useState<string | null>(null)
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null)

  useEffect(() => {
    const abort = new AbortController()
    setLoadingDeals(true)
    setDealError(null)
    fetchDeals(abort.signal)
      .then((payload) => {
        setDeals(payload)
        if (payload.length > 0) {
          setSelectedDealId(payload[0].id)
        } else {
          setSelectedDealId(null)
        }
      })
      .catch((error: unknown) => {
        if (isAbortError(error, abort)) {
          return
        }
        console.error('Failed to load deals', error)
        setDealError(t('agentPerformance.errors.loadDeals'))
      })
      .finally(() => {
        setLoadingDeals(false)
      })
    return () => {
      abort.abort()
    }
  }, [t])

  const selectedDeal = useMemo(
    () => deals.find((deal) => deal.id === selectedDealId) ?? null,
    [deals, selectedDealId],
  )

  const groupedDeals = useMemo(() => groupDealsByStage(deals), [deals])

  return {
    deals,
    loadingDeals,
    dealError,
    selectedDealId,
    selectedDeal,
    groupedDeals,
    stageOrder: DEAL_STAGE_ORDER,
    setSelectedDealId,
  }
}
