import { useState, useEffect, useCallback } from 'react'
import { PropertyType } from '../types/property'
import {
  MarketReport,
  MarketTransaction,
  ComparablesAnalysis,
  SupplyDynamics,
  YieldBenchmarks,
  AbsorptionTrends,
  MarketCyclePosition,
} from '../types/market'
import { apiClient } from '../services/api'

export const useMarketData = (
  propertyType: PropertyType,
  location: string = 'all',
  periodMonths: number = 12,
) => {
  const [marketReport, setMarketReport] = useState<MarketReport | null>(null)
  const [comparables, setComparables] = useState<MarketTransaction[]>([])
  const [comparablesSummary, setComparablesSummary] =
    useState<ComparablesAnalysis | null>(null)
  const [supplyDynamics, setSupplyDynamics] = useState<SupplyDynamics | null>(
    null,
  )
  const [yieldBenchmarks, setYieldBenchmarks] =
    useState<YieldBenchmarks | null>(null)
  const [absorptionTrends, setAbsorptionTrends] =
    useState<AbsorptionTrends | null>(null)
  const [marketCycle, setMarketCycle] = useState<MarketCyclePosition | null>(
    null,
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMarketData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const reportPromise = apiClient.post<MarketReport>(
        '/api/v1/agents/commercial-property/market-intelligence/report',
        {
          property_type: propertyType,
          location,
          period_months: periodMonths,
        },
      )

      const daysBack = periodMonths * 30
      const transactionsPromise = apiClient.get<MarketTransaction[]>(
        '/api/v1/agents/commercial-property/market-intelligence/transactions',
        {
          params: {
            property_type: propertyType,
            location: location !== 'all' ? location : undefined,
            days_back: daysBack,
            limit: 500,
          },
        },
      )

      const [reportResult, transactionsResult] = await Promise.allSettled([
        reportPromise,
        transactionsPromise,
      ])

      if (reportResult.status !== 'fulfilled') {
        throw reportResult.reason
      }

      const report = reportResult.value.data
      setMarketReport(report)
      setComparablesSummary(report.comparables_analysis)
      setSupplyDynamics(report.supply_dynamics)
      setYieldBenchmarks(report.yield_benchmarks)
      setAbsorptionTrends(report.absorption_trends)
      setMarketCycle(report.market_cycle_position)

      const partialErrors: string[] = []

      if (transactionsResult.status === 'fulfilled') {
        setComparables(transactionsResult.value.data || [])
      } else {
        console.error('Error fetching transactions:', transactionsResult.reason)
        partialErrors.push(
          'Some comparable transaction records could not be loaded.',
        )
        setComparables([])
      }

      if (partialErrors.length > 0) {
        setError(partialErrors.join(' '))
      }
    } catch (err) {
      console.error('Error fetching market data:', err)
      setError(
        err instanceof Error ? err.message : 'Failed to fetch market data',
      )
    } finally {
      setLoading(false)
    }
  }, [propertyType, location, periodMonths])

  useEffect(() => {
    fetchMarketData()
  }, [fetchMarketData])

  const refresh = useCallback(async () => {
    await fetchMarketData()
  }, [fetchMarketData])

  return {
    marketReport,
    comparables,
    comparablesSummary,
    supplyDynamics,
    yieldBenchmarks,
    absorptionTrends,
    marketCycle,
    loading,
    error,
    refresh,
  }
}
