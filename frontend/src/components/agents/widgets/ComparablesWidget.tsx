import React, { useState, useMemo } from 'react';
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
  IconButton,
  Tooltip,
  TextField,
  InputAdornment,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { MarketTransaction } from '../../../types/market';
import { PropertyType } from '../../../types/property';
import { format, parseISO } from 'date-fns';

interface ComparablesWidgetProps {
  comparables: MarketTransaction[];
  propertyType: PropertyType;
  location: string;
}

const ComparablesWidget: React.FC<ComparablesWidgetProps> = ({
  comparables,
  propertyType,
  location
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter comparables based on search
  const filteredComparables = useMemo(() => {
    return comparables.filter(comp => 
      comp.property_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      comp.district?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [comparables, searchTerm]);

  // Calculate statistics
  const statistics = useMemo(() => {
    if (filteredComparables.length === 0) return null;

    const prices = filteredComparables
      .filter(c => c.psf_price)
      .map(c => c.psf_price!);
    
    const sortedPrices = [...prices].sort((a, b) => a - b);
    const median = sortedPrices[Math.floor(sortedPrices.length / 2)];
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const min = Math.min(...prices);
    const max = Math.max(...prices);

    const totalVolume = filteredComparables.reduce((sum, c) => sum + c.sale_price, 0);

    return {
      count: filteredComparables.length,
      medianPsf: median,
      meanPsf: mean,
      minPsf: min,
      maxPsf: max,
      totalVolume
    };
  }, [filteredComparables]);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPsf = (value: number) => {
    return new Intl.NumberFormat('en-SG', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getPriceTrend = (transaction: MarketTransaction) => {
    // This would compare to historical average
    const avgPsf = statistics?.meanPsf || 0;
    if (!transaction.psf_price) return null;
    
    const diff = ((transaction.psf_price - avgPsf) / avgPsf) * 100;
    if (Math.abs(diff) < 5) return null;
    
    return diff > 0 ? 'above' : 'below';
  };

  return (
    <Box>
      {/* Statistics Cards */}
      {statistics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Transactions
                </Typography>
                <Typography variant="h5">
                  {statistics.count}
                </Typography>
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
                  ${formatPsf(statistics.minPsf)} - ${formatPsf(statistics.maxPsf)}
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

      {/* Search and Table */}
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ p: 2 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search by property name or district..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
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
                  const trend = getPriceTrend(transaction);
                  return (
                    <TableRow key={transaction.id}>
                      <TableCell>
                        {format(parseISO(transaction.transaction_date), 'dd MMM yyyy')}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {transaction.property_name}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          icon={<LocationOnIcon />}
                          label={transaction.district || 'N/A'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        {transaction.floor_area_sqm 
                          ? formatPsf(transaction.floor_area_sqm)
                          : '-'}
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {formatCurrency(transaction.sale_price)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {transaction.psf_price 
                            ? `$${formatPsf(transaction.psf_price)}`
                            : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        {trend && (
                          <Tooltip title={trend === 'above' ? 'Above average' : 'Below average'}>
                            {trend === 'above' ? (
                              <TrendingUpIcon color="success" />
                            ) : (
                              <TrendingDownIcon color="error" />
                            )}
                          </Tooltip>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredComparables.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
};

export default ComparablesWidget;