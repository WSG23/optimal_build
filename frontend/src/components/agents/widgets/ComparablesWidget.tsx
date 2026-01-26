import React, { useMemo, useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Tooltip,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import LocationOnIcon from '@mui/icons-material/LocationOn'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import { format, parseISO } from 'date-fns'
import { MarketTransaction, ComparablesAnalysis } from '../../../types/market'
import { PropertyType } from '../../../types/property'

interface ComparablesWidgetProps {
  comparables: MarketTransaction[]
  summary?: ComparablesAnalysis | null
  propertyType: PropertyType
  location: string
}

const ComparablesWidget: React.FC<ComparablesWidgetProps> = ({
  comparables,
  summary,
  propertyType,
  location,
}) => {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredComparables = useMemo(() => {
    return comparables.filter(
      (comp) =>
        comp.property_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.district?.toLowerCase().includes(searchTerm.toLowerCase()),
    )
  }, [comparables, searchTerm])

  const statistics = useMemo(() => {
    const hasFilter = searchTerm.trim().length > 0

    if (!hasFilter && summary) {
      return {
        count: summary.transaction_count,
        medianPsf: summary.median_psf,
        meanPsf: summary.average_psf,
        minPsf: summary.psf_range?.min ?? summary.average_psf,
        maxPsf: summary.psf_range?.max ?? summary.average_psf,
        totalVolume: summary.total_volume,
      }
    }

    if (filteredComparables.length === 0) {
      return null
    }

    const prices = filteredComparables
      .filter(
        (item) =>
          typeof item.psf_price === 'number' && !Number.isNaN(item.psf_price),
      )
      .map((item) => item.psf_price as number)

    if (prices.length === 0) {
      return {
        count: filteredComparables.length,
        medianPsf: 0,
        meanPsf: 0,
        minPsf: 0,
        maxPsf: 0,
        totalVolume: filteredComparables.reduce(
          (sum, c) => sum + (c.sale_price || 0),
          0,
        ),
      }
    }

    const sortedPrices = [...prices].sort((a, b) => a - b)
    const median = sortedPrices[Math.floor(sortedPrices.length / 2)]
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length
    const min = Math.min(...prices)
    const max = Math.max(...prices)
    const totalVolume = filteredComparables.reduce(
      (sum, c) => sum + (c.sale_price || 0),
      0,
    )

    return {
      count: filteredComparables.length,
      medianPsf: median,
      meanPsf: mean,
      minPsf: min,
      maxPsf: max,
      totalVolume,
    }
  }, [filteredComparables, summary, searchTerm])

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null) return '—'
    return new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const formatPsf = (value?: number | null) => {
    if (value === undefined || value === null || Number.isNaN(value)) return '—'
    return new Intl.NumberFormat('en-SG', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const getPriceTrend = (transaction: MarketTransaction) => {
    const avgPsf = statistics?.meanPsf || 0
    if (!transaction.psf_price || avgPsf === 0) return null

    const diff = ((transaction.psf_price - avgPsf) / avgPsf) * 100
    if (!Number.isFinite(diff) || Math.abs(diff) < 5) {
      return null
    }

    return diff > 0 ? 'above' : 'below'
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb="var(--ob-space-200)"
      >
        <Typography variant="h6">Recent Comparables</Typography>
        <Typography variant="caption" color="textSecondary">
          {propertyType.replace(/_/g, ' ').toUpperCase()} •{' '}
          {location.toUpperCase()}
        </Typography>
      </Box>

      {statistics && (
        <Grid
          container
          spacing="var(--ob-space-200)"
          sx={{ mb: 'var(--ob-space-300)' }}
        >
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Comparable Count
                </Typography>
                <Typography variant="h5">{statistics.count}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Median PSF
                </Typography>
                <Typography variant="h5">
                  ${formatPsf(statistics.medianPsf)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Price Range PSF
                </Typography>
                <Typography variant="h5">
                  ${formatPsf(statistics.minPsf)} - $
                  {formatPsf(statistics.maxPsf)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Volume
                </Typography>
                <Typography variant="h5">
                  {formatCurrency(statistics.totalVolume)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Paper sx={{ width: '100%', mb: 'var(--ob-space-200)' }}>
        <Box sx={{ p: 'var(--ob-space-200)' }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search by property name or district..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Property</TableCell>
                <TableCell>District</TableCell>
                <TableCell align="right">Size (sqm)</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">PSF</TableCell>
                <TableCell align="center">Trend</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredComparables
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((transaction) => {
                  const trend = getPriceTrend(transaction)
                  return (
                    <TableRow key={transaction.transaction_id} hover>
                      <TableCell>
                        {format(
                          parseISO(transaction.transaction_date),
                          'dd MMM yyyy',
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {transaction.property_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {transaction.property_type.replace(/_/g, ' ')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          icon={<LocationOnIcon fontSize="small" />}
                          label={transaction.district || 'N/A'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {transaction.floor_area_sqm
                          ? formatPsf(transaction.floor_area_sqm)
                          : '—'}
                      </TableCell>
                      <TableCell align="right">
                        {formatCurrency(transaction.sale_price)}
                      </TableCell>
                      <TableCell align="right">
                        {transaction.psf_price
                          ? `$${formatPsf(transaction.psf_price)}`
                          : '—'}
                      </TableCell>
                      <TableCell align="center">
                        {trend && (
                          <Tooltip
                            title={
                              trend === 'above'
                                ? 'Above average'
                                : 'Below average'
                            }
                          >
                            {trend === 'above' ? (
                              <TrendingUpIcon color="success" />
                            ) : (
                              <TrendingDownIcon color="error" />
                            )}
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={filteredComparables.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Paper>
    </Box>
  )
}

export default ComparablesWidget
