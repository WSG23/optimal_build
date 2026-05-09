import { Skeleton, Box, Stack } from '@mui/material'

interface SkeletonLoaderProps {
  variant?: 'text' | 'rectangular' | 'circular' | 'card' | 'chart'
  height?: number | string
  width?: number | string
  count?: number
}

export function SkeletonLoader({
  variant = 'text',
  height,
  width,
  count = 1,
}: SkeletonLoaderProps) {
  if (variant === 'card') {
    return (
      <Stack spacing="var(--ob-space-200)">
        {Array.from(new Array(count)).map((_, index) => (
          <Box
            key={index}
            sx={{
              p: 'var(--ob-space-200)',
              border: 1,
              borderColor: 'divider',
              borderRadius: 'var(--ob-radius-sm)',
              bgcolor: 'background.paper',
            }}
          >
            <Stack spacing="var(--ob-space-100)">
              <Skeleton variant="text" width="60%" height={32} />
              <Skeleton variant="text" width="40%" height={20} />
              <Skeleton
                variant="rectangular"
                height={100}
                sx={{
                  mt: 'var(--ob-space-200)',
                  borderRadius: 'var(--ob-radius-sm)',
                }}
              />
              <Stack
                direction="row"
                spacing="var(--ob-space-100)"
                sx={{ mt: 'var(--ob-space-100)' }}
              >
                <Skeleton variant="circular" width={24} height={24} />
                <Skeleton variant="text" width="30%" />
              </Stack>
            </Stack>
          </Box>
        ))}
      </Stack>
    )
  }

  if (variant === 'chart') {
    return (
      <Box
        sx={{
          p: 'var(--ob-space-200)',
          border: 1,
          borderColor: 'divider',
          borderRadius: 'var(--ob-radius-sm)',
          bgcolor: 'background.paper',
          height: height || 300,
          width: width || '100%',
          display: 'flex',
          alignItems: 'flex-end',
          gap: 'var(--ob-space-100)',
        }}
      >
        {Array.from(new Array(7)).map((_, index) => (
          <Skeleton
            key={index}
            variant="rectangular"
            width={`${100 / 7}%`}
            height={`${Math.random() * 80 + 20}%`}
            sx={{ borderRadius: 'var(--ob-radius-sm)' }}
          />
        ))}
      </Box>
    )
  }

  return (
    <Stack spacing="var(--ob-space-100)">
      {Array.from(new Array(count)).map((_, index) => (
        <Skeleton
          key={index}
          variant={
            variant === 'circular'
              ? 'circular'
              : variant === 'rectangular'
                ? 'rectangular'
                : 'text'
          }
          width={width}
          height={height}
        />
      ))}
    </Stack>
  )
}
