import React, { useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Tooltip
} from '@mui/material';
import BusinessIcon from '@mui/icons-material/Business';
import ConstructionIcon from '@mui/icons-material/Construction';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import { DevelopmentPipeline } from '../../../types/market';
import { PropertyType } from '../../../types/property';
import { format, parseISO, differenceInMonths } from 'date-fns';

interface PipelineTimelineWidgetProps {
  pipeline: DevelopmentPipeline[];
  propertyType: PropertyType;
}

const PipelineTimelineWidget: React.FC<PipelineTimelineWidgetProps> = ({
  pipeline,
  propertyType
}) => {
  // Group pipeline by year
  const pipelineByYear = useMemo(() => {
    const grouped = pipeline.reduce((acc, project) => {
      const year = new Date(project.expected_completion).getFullYear();
      if (!acc[year]) acc[year] = [];
      acc[year].push(project);
      return acc;
    }, {} as Record<number, DevelopmentPipeline[]>);

    return Object.entries(grouped)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([year, projects]) => ({
        year: Number(year),
        projects: projects.sort((a, b) => 
          new Date(a.expected_completion).getTime() - new Date(b.expected_completion).getTime()
        )
      }));
  }, [pipeline]);

  // Calculate total supply by year
  const supplyByYear = useMemo(() => {
    return pipelineByYear.map(({ year, projects }) => ({
      year,
      totalGFA: projects.reduce((sum, p) => sum + (p.total_gfa_sqm || 0), 0),
      totalUnits: projects.reduce((sum, p) => sum + (p.units_total || 0), 0),
      projectCount: projects.length
    }));
  }, [pipelineByYear]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'under_construction':
        return <ConstructionIcon />;
      case 'approved':
      case 'planned':
        return <ScheduleIcon />;
      default:
        return <BusinessIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'under_construction':
        return 'warning';
      case 'approved':
        return 'info';
      case 'planned':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatGFA = (value: number) => {
    return new Intl.NumberFormat('en-SG', {
      maximumFractionDigits: 0
    }).format(value);
  };

  const getCompletionProgress = (project: DevelopmentPipeline) => {
    if (project.development_status === 'completed') return 100;
    if (project.development_status === 'planned') return 0;
    
    // Calculate based on time if under construction
    if (project.development_status === 'under_construction') {
      const today = new Date();
      const completion = parseISO(project.expected_completion);
      const monthsToCompletion = differenceInMonths(completion, today);
      
      // Assume 24-month construction period
      const progress = Math.max(0, Math.min(100, ((24 - monthsToCompletion) / 24) * 100));
      return Math.round(progress);
    }
    
    return 10; // Approved projects
  };

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {supplyByYear.slice(0, 3).map(({ year, totalGFA, totalUnits, projectCount }) => (
          <Grid item xs={12} sm={4} key={year}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  {year} Supply
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {formatGFA(totalGFA)} sqm
                </Typography>
                <Box display="flex" gap={1}>
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

      {/* Timeline */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Development Pipeline Timeline
        </Typography>
        
        <Timeline position="alternate">
          {pipelineByYear.map(({ year, projects }) => (
            <React.Fragment key={year}>
              {projects.map((project, index) => (
                <TimelineItem key={project.id}>
                  <TimelineOppositeContent color="textSecondary">
                    {format(parseISO(project.expected_completion), 'MMM yyyy')}
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color={getStatusColor(project.development_status) as any}>
                      {getStatusIcon(project.development_status)}
                    </TimelineDot>
                    {index < projects.length - 1 || year < pipelineByYear[pipelineByYear.length - 1].year ? (
                      <TimelineConnector />
                    ) : null}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {project.project_name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary" gutterBottom>
                          {project.developer}
                        </Typography>
                        
                        <Box mt={1} mb={1}>
                          <Chip 
                            size="small" 
                            label={project.development_status.replace(/_/g, ' ')}
                            color={getStatusColor(project.development_status) as any}
                          />
                          {project.district && (
                            <Chip 
                              size="small" 
                              label={project.district}
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          GFA: {formatGFA(project.total_gfa_sqm)} sqm
                          {project.units_total && ` • ${project.units_total} units`}
                        </Typography>
                        
                        {project.pre_commitment_rate !== undefined && (
                          <Box>
                            <Box display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="caption">
                                Pre-commitment
                              </Typography>
                              <Typography variant="caption">
                                {Math.round(project.pre_commitment_rate * 100)}%
                              </Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={project.pre_commitment_rate * 100}
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                        )}
                        
                        {project.development_status === 'under_construction' && (
                          <Box mt={1}>
                            <Box display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="caption">
                                Construction Progress
                              </Typography>
                              <Typography variant="caption">
                                {getCompletionProgress(project)}%
                              </Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={getCompletionProgress(project)}
                              sx={{ height: 6, borderRadius: 3 }}
                              color="secondary"
                            />
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </React.Fragment>
          ))}
        </Timeline>
      </Paper>
    </Box>
  );
};

export default PipelineTimelineWidget;