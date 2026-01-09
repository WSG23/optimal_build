import React, { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Tab,
  Tabs,
  Paper,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import DownloadIcon from '@mui/icons-material/Download'
import FilterListIcon from '@mui/icons-material/FilterList'
import { PropertyType } from '../../types/property'
import { useMarketData } from '../../hooks/useMarketData'
import ComparablesWidget from './widgets/ComparablesWidget'
import PipelineTimelineWidget from './widgets/PipelineTimelineWidget'
import YieldBenchmarkChart from './widgets/YieldBenchmarkChart'
import AbsorptionTrendsChart from './widgets/AbsorptionTrendsChart'
import MarketHeatmap from './widgets/MarketHeatmap'
import MarketCycleIndicator from './widgets/MarketCycleIndicator'
import QuickInsights from './widgets/QuickInsights'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`market-tabpanel-${index}`}
      aria-labelledby={`market-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const MarketIntelligenceDashboard: React.FC = () => {
  const [propertyType, setPropertyType] = useState<PropertyType>(
    PropertyType.OFFICE,
  )
  const [location, setLocation] = useState<string>('all')
  const [periodMonths, setPeriodMonths] = useState<number>(12)
  const [tabValue, setTabValue] = useState(0)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const {
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
  } = useMarketData(propertyType, location, periodMonths)

  useEffect(() => {
    if (marketReport) {
      setLastRefresh(new Date(marketReport.generated_at))
    }
  }, [marketReport])

  const handleRefresh = async () => {
    await refresh()
    setLastRefresh(new Date())
  }

  const handleExportReport = () => {
    if (!marketReport) return

    const dataStr = JSON.stringify(marketReport, null, 2)
    const dataUri =
      'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)

    const exportFileDefaultName = `market-report-${propertyType}-${new Date().toISOString().split('T')[0]}.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  if (loading && !marketReport) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="400px"
      >
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h4" component="h1">
          Market Intelligence Dashboard
        </Typography>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh data">
            <span>
              <IconButton onClick={handleRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Export report">
            <span>
              <IconButton onClick={handleExportReport} disabled={!marketReport}>
                <DownloadIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <FilterListIcon color="action" />
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Property Type</InputLabel>
              <Select
                value={propertyType}
                label="Property Type"
                onChange={(e) =>
                  setPropertyType(e.target.value as PropertyType)
                }
              >
                <MenuItem value={PropertyType.OFFICE}>Office</MenuItem>
                <MenuItem value={PropertyType.RETAIL}>Retail</MenuItem>
                <MenuItem value={PropertyType.INDUSTRIAL}>Industrial</MenuItem>
                <MenuItem value={PropertyType.RESIDENTIAL}>
                  Residential
                </MenuItem>
                <MenuItem value={PropertyType.MIXED_USE}>Mixed Use</MenuItem>
                <MenuItem value={PropertyType.HOTEL}>Hotel</MenuItem>
                <MenuItem value={PropertyType.WAREHOUSE}>Warehouse</MenuItem>
                <MenuItem value={PropertyType.LAND}>Land</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Location</InputLabel>
              <Select
                value={location}
                label="Location"
                onChange={(e) => setLocation(e.target.value)}
              >
                <MenuItem value="all">All Locations</MenuItem>
                <MenuItem value="CBD">CBD</MenuItem>
                <MenuItem value="Orchard">Orchard</MenuItem>
                <MenuItem value="Marina Bay">Marina Bay</MenuItem>
                <MenuItem value="Jurong">Jurong</MenuItem>
                <MenuItem value="Tampines">Tampines</MenuItem>
                <MenuItem value="Woodlands">Woodlands</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Period</InputLabel>
              <Select
                value={periodMonths}
                label="Period"
                onChange={(e) => setPeriodMonths(Number(e.target.value))}
              >
                <MenuItem value={3}>Last 3 months</MenuItem>
                <MenuItem value={6}>Last 6 months</MenuItem>
                <MenuItem value={12}>Last 12 months</MenuItem>
                <MenuItem value={24}>Last 24 months</MenuItem>
                <MenuItem value={36}>Last 36 months</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={12} md={3}>
            <Typography variant="caption" color="textSecondary">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Quick Insights */}
      {marketReport && (
        <QuickInsights
          marketReport={marketReport}
          comparables={comparablesSummary}
          supplyDynamics={supplyDynamics}
          yieldBenchmarks={yieldBenchmarks}
          absorptionTrends={absorptionTrends}
        />
      )}

      {/* Main Content Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="market intelligence tabs"
          >
            <Tab label="Overview" />
            <Tab label="Comparables" />
            <Tab label="Supply Pipeline" />
            <Tab label="Yield Analysis" />
            <Tab label="Market Dynamics" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <MarketHeatmap
                transactions={comparables}
                propertyType={propertyType}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <MarketCycleIndicator
                cycleData={marketCycle}
                propertyType={propertyType}
              />
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ComparablesWidget
            comparables={comparables}
            summary={comparablesSummary}
            propertyType={propertyType}
            location={location}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <PipelineTimelineWidget
            supplyDynamics={supplyDynamics}
            propertyType={propertyType}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <YieldBenchmarkChart
            yieldBenchmarks={yieldBenchmarks}
            propertyType={propertyType}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <AbsorptionTrendsChart
            absorptionTrends={absorptionTrends}
            propertyType={propertyType}
          />
        </TabPanel>
      </Paper>
    </Box>
  )
}

export default MarketIntelligenceDashboard
