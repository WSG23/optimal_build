import { useState, useEffect, useCallback } from 'react';
import { PropertyType } from '../types/property';
import { 
  MarketReport, 
  MarketTransaction, 
  DevelopmentPipeline, 
  YieldBenchmark, 
  AbsorptionData,
  MarketCycle 
} from '../types/market';
import { apiClient } from '../services/api';

export const useMarketData = (
  propertyType: PropertyType,
  location: string = 'all',
  periodMonths: number = 12
) => {
  const [marketReport, setMarketReport] = useState<MarketReport | null>(null);
  const [comparables, setComparables] = useState<MarketTransaction[]>([]);
  const [supplyPipeline, setSupplyPipeline] = useState<DevelopmentPipeline[]>([]);
  const [yieldBenchmarks, setYieldBenchmarks] = useState<YieldBenchmark[]>([]);
  const [absorptionData, setAbsorptionData] = useState<AbsorptionData[]>([]);
  const [marketCycles, setMarketCycles] = useState<MarketCycle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMarketData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch market report
      const reportResponse = await apiClient.post<MarketReport>(
        '/api/v1/agents/commercial-property/market-intelligence/report',
        {
          property_type: propertyType,
          location: location,
          period_months: periodMonths
        }
      );
      setMarketReport(reportResponse.data);

      // Extract data from report
      if (reportResponse.data) {
        setComparables(reportResponse.data.comparables?.transactions || []);
        setSupplyPipeline(reportResponse.data.supply_pipeline?.projects || []);
        setYieldBenchmarks(reportResponse.data.yield_analysis?.benchmarks || []);
        setAbsorptionData(reportResponse.data.absorption_trends?.data || []);
        setMarketCycles(reportResponse.data.market_dynamics?.cycles || []);
      }

      // Fetch additional transaction data if needed
      const daysBack = periodMonths * 30;
      const transactionsResponse = await apiClient.get<MarketTransaction[]>(
        '/api/v1/agents/commercial-property/market-intelligence/transactions',
        {
          params: {
            property_type: propertyType,
            location: location !== 'all' ? location : undefined,
            days_back: daysBack,
            limit: 500
          }
        }
      );
      
      // Merge with report comparables if more detailed data available
      if (transactionsResponse.data && transactionsResponse.data.length > comparables.length) {
        setComparables(transactionsResponse.data);
      }

    } catch (err) {
      console.error('Error fetching market data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch market data');
    } finally {
      setLoading(false);
    }
  }, [propertyType, location, periodMonths]);

  useEffect(() => {
    fetchMarketData();
  }, [fetchMarketData]);

  const refresh = useCallback(async () => {
    await fetchMarketData();
  }, [fetchMarketData]);

  return {
    marketReport,
    comparables,
    supplyPipeline,
    yieldBenchmarks,
    absorptionData,
    marketCycles,
    loading,
    error,
    refresh
  };
};