import React, { useMemo } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material'
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
} from '@mui/lab'
import type { TimelineDotProps } from '@mui/lab/TimelineDot'
import BusinessIcon from '@mui/icons-material/Business'
import ConstructionIcon from '@mui/icons-material/Construction'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ScheduleIcon from '@mui/icons-material/Schedule'
import { format } from 'date-fns'
import { SupplyDynamics, MajorDevelopment } from '../../../types/market'
import { PropertyType } from '../../../types/property'

interface PipelineTimelineWidgetProps {
  supplyDynamics?: SupplyDynamics | null
  propertyType: PropertyType
}

const PipelineTimelineWidget: React.FC<PipelineTimelineWidgetProps> = ({
  supplyDynamics,
  propertyType,
}) => {
  const supplyByYear = useMemo(() => {
    if (!supplyDynamics) {
      return []
    }

    return Object.entries(supplyDynamics.supply_by_year || {})
      .map(([year, entry]) => ({
        year: Number(year),
        totalGFA: entry.total_gfa,
        totalUnits: entry.total_units,
        projectCount: entry.projects,
      }))
      .sort((a, b) => a.year - b.year)
  }, [supplyDynamics])

  const majorDevelopments = useMemo(() => {
    if (!supplyDynamics) {
      return [] as MajorDevelopment[]
    }

    return [...supplyDynamics.major_developments].sort((a, b) => {
      if (!a.completion && !b.completion) return 0
      if (!a.completion) return 1
      if (!b.completion) return -1
      return new Date(a.completion).getTime() - new Date(b.completion).getTime()
    })
  }, [supplyDynamics])

  const formatGFA = (value?: number | null) => {
    if (!value) return '0'
    return new Intl.NumberFormat('en-SG', { maximumFractionDigits: 0 }).format(
      value,
    )
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />
      case 'under_construction':
        return <ConstructionIcon />
      case 'approved':
      case 'planned':
        return <ScheduleIcon />
      default:
        return <BusinessIcon />
    }
  }

  type TimelineColor = NonNullable<TimelineDotProps['color']>

  const statusColorTimeline = (status: string): TimelineColor => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'under_construction':
        return 'warning'
      case 'approved':
        return 'info'
      case 'planned':
        return 'grey'
      default:
        return 'grey'
    }
  }

  const statusColorChip = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success' as const
      case 'under_construction':
        return 'warning' as const
      case 'approved':
        return 'info' as const
      case 'planned':
        return 'default' as const
      default:
        return 'default' as const
    }
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h6">Supply Pipeline</Typography>
        <Typography variant="caption" color="textSecondary">
          {propertyType.replace(/_/g, ' ').toUpperCase()}
        </Typography>
      </Box>

      {supplyByYear.length > 0 ? (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {supplyByYear
            .slice(0, 3)
            .map(({ year, totalGFA, totalUnits, projectCount }) => (
              <Grid item xs={12} sm={4} key={year}>
                <Card>
                  <CardContent>
                    <Typography
                      color="textSecondary"
                      gutterBottom
                      variant="body2"
                    >
                      {year} Supply
                    </Typography>
                    <Typography variant="h6" gutterBottom>
                      {formatGFA(totalGFA)} sqm
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      <Chip
                        size="small"
                        label={`${projectCount} projects`}
                        variant="outlined"
                      />
                      {totalUnits > 0 && (
                        <Chip
                          size="small"
                          label={`${formatGFA(totalUnits)} units`}
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
        </Grid>
      ) : (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography color="textSecondary">
            No pipeline summary is available for the selected filters.
          </Typography>
        </Paper>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Major Developments
        </Typography>

        {majorDevelopments.length === 0 ? (
          <Typography color="textSecondary">
            No development projects found.
          </Typography>
        ) : (
          <Timeline position="alternate">
            {majorDevelopments.map((project, index) => {
              const completionLabel = project.completion
                ? format(new Date(project.completion), 'MMM yyyy')
                : 'TBC'

              return (
                <TimelineItem key={`${project.name}-${index}`}>
                  <TimelineOppositeContent color="textSecondary">
                    {completionLabel}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color={statusColorTimeline(project.status)}>
                      {statusIcon(project.status)}
                    </TimelineDot>
                    {index < majorDevelopments.length - 1 && (
                      <TimelineConnector />
                    )}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {project.name}
                        </Typography>
                        {project.developer && (
                          <Typography
                            variant="body2"
                            color="textSecondary"
                            gutterBottom
                          >
                            {project.developer}
                          </Typography>
                        )}
                        <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                          <Chip
                            size="small"
                            label={project.status.replace(/_/g, ' ')}
                            color={statusColorChip(project.status)}
                          />
                          {project.units ? (
                            <Chip
                              size="small"
                              label={`${project.units} units`}
                              variant="outlined"
                            />
                          ) : null}
                        </Box>
                        <Typography variant="body2">
                          GFA: {formatGFA(project.gfa)} sqm
                        </Typography>
                      </CardContent>
                    </Card>
                  </TimelineContent>
                </TimelineItem>
              )
            })}
          </Timeline>
        )}
      </Paper>
    </Box>
  )
}

export default PipelineTimelineWidget
