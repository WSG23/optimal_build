import { Box, Typography, Stack, useTheme, alpha } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area } from 'recharts';

export interface KPITickerCardProps {
  label: string;
  value: string | number;
  trend: number; // Percentage, e.g. 44.7
  data: number[]; // Array of numbers for the sparkline
  active?: boolean;
}

export function KPITickerCard({ label, value, trend, data, active }: KPITickerCardProps) {
  const theme = useTheme();

  // Transform flat array to object array for Recharts
  const chartData = data.map((val, i) => ({ i, val }));

  const isPositive = trend >= 0;
  const trendColor = isPositive ? theme.palette.success.main : theme.palette.error.main;

  return (
    <Box
      sx={{
        position: 'relative',
        p: 3,
        borderRadius: 4,
        overflow: 'hidden',
        bgcolor: alpha(theme.palette.background.paper, 0.6), // Glassmorphic base
        backdropFilter: 'blur(20px)',
        border: '1px solid',
        borderColor: active ? theme.palette.primary.main : alpha(theme.palette.divider, 0.1),
        boxShadow: active
          ? `0 0 20px -5px ${alpha(theme.palette.primary.main, 0.5)}`
          : '0 4px 24px -1px rgba(0, 0, 0, 0.05)',
        transition: 'all 0.3s ease',
        '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 30px -5px rgba(0, 0, 0, 0.1)'
        },
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between'
      }}
    >
      <Box mb={2}>
        <Typography variant="overline" sx={{ color: 'text.secondary', fontWeight: 600, letterSpacing: '0.1em' }}>
          {label}
        </Typography>
        <Stack direction="row" alignItems="baseline" spacing={1} sx={{ mt: 0.5 }}>
           <Typography variant="h3" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: '-0.02em' }}>
             {value}
           </Typography>
           <Box
             sx={{
               bgcolor: alpha(trendColor, 0.1),
               color: trendColor,
               px: 1,
               py: 0.25,
               borderRadius: 2,
               fontSize: '0.75rem',
               fontWeight: 700
             }}
           >
             {isPositive ? '+' : ''}{trend.toFixed(1)}%
           </Box>
        </Stack>
      </Box>

      <Box sx={{ height: 60, width: '100%', opacity: 0.8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id={`gradient-${label}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <Area
                type="monotone"
                dataKey="val"
                stroke={theme.palette.primary.main}
                strokeWidth={2}
                fill={`url(#gradient-${label})`}
                isAnimationActive={false} // Performance
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
}
