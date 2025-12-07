import React, { useState, useEffect, useMemo } from 'react'
import {
  Box,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tooltip,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material'
import {
  CheckCircle as ApprovedIcon,
  Schedule as DurationIcon,
  AccountBalance as AgencyIcon,
} from '@mui/icons-material'
import {
  regulatoryApi,
  AssetCompliancePath,
  AssetType,
  RegulatoryAgency,
} from '../../../../api/regulatory'

interface CompliancePathVisualizationProps {
  projectId: string
  initialAssetType?: AssetType
}

const ASSET_TYPE_LABELS: Record<AssetType, string> = {
  office: 'Office Building',
  retail: 'Retail / Commercial',
  residential: 'Residential',
  industrial: 'Industrial',
  heritage: 'Heritage / Conservation',
  mixed_use: 'Mixed-Use Development',
  hospitality: 'Hospitality / Hotel',
}

const AGENCY_COLORS: Record<string, string> = {
  URA: '#2563eb',
  BCA: '#059669',
  SCDF: '#dc2626',
  NEA: '#7c3aed',
  LTA: '#ea580c',
  PUB: '#0891b2',
  NPARKS: '#16a34a',
  SLA: '#4f46e5',
  STB: '#be185d',
  JTC: '#ca8a04',
}

const STEP_WIDTH = 180
const STEP_HEIGHT = 100
const CONNECTOR_LENGTH = 60
const ROW_HEIGHT = 140

export const CompliancePathVisualization: React.FC<
  CompliancePathVisualizationProps
> = ({ initialAssetType }) => {
  const [selectedAssetType, setSelectedAssetType] = useState<AssetType>(
    initialAssetType || 'office',
  )
  const [compliancePaths, setCompliancePaths] = useState<AssetCompliancePath[]>(
    [],
  )
  const [agencies, setAgencies] = useState<RegulatoryAgency[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAgencies = async () => {
      try {
        const data = await regulatoryApi.listAgencies()
        setAgencies(data)
      } catch {
        // Agencies may not be seeded yet, use defaults
      }
    }
    fetchAgencies()
  }, [])

  useEffect(() => {
    const fetchPaths = async () => {
      setLoading(true)
      setError(null)
      try {
        const data =
          await regulatoryApi.getCompliancePathsForAsset(selectedAssetType)
        setCompliancePaths(data)
      } catch {
        // If no paths found, use demo data
        setCompliancePaths(getDemoCompliancePaths(selectedAssetType))
      } finally {
        setLoading(false)
      }
    }
    fetchPaths()
  }, [selectedAssetType])

  const getAgencyName = (agencyId: string): string => {
    const agency = agencies.find((a) => a.id === agencyId)
    return agency?.code || agencyId.substring(0, 3).toUpperCase()
  }

  const totalDuration = useMemo(() => {
    return compliancePaths.reduce(
      (sum, path) => sum + (path.typical_duration_days || 30),
      0,
    )
  }, [compliancePaths])

  const getStepColor = (path: AssetCompliancePath): string => {
    const agencyCode = getAgencyName(path.agency_id)
    return AGENCY_COLORS[agencyCode] || '#64748b'
  }

  return (
    <Paper
      sx={{
        p: 3,
        border: '1px solid rgba(255,255,255,0.1)',
        bgcolor: 'background.paper',
        borderRadius: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Compliance Path Visualization
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Regulatory approval sequence for Singapore development projects
          </Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Asset Type</InputLabel>
          <Select
            value={selectedAssetType}
            label="Asset Type"
            onChange={(e) => setSelectedAssetType(e.target.value as AssetType)}
          >
            {Object.entries(ASSET_TYPE_LABELS).map(([value, label]) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : compliancePaths.length === 0 ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No compliance path defined for{' '}
            {ASSET_TYPE_LABELS[selectedAssetType]}. Contact your regulatory
            consultant for guidance.
          </Typography>
        </Box>
      ) : (
        <>
          {/* Summary Stats */}
          <Box
            sx={{
              display: 'flex',
              gap: 3,
              mb: 3,
              p: 2,
              bgcolor: 'rgba(255,255,255,0.03)',
              borderRadius: 1,
            }}
          >
            <Box>
              <Typography variant="caption" color="text.secondary">
                Total Steps
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {compliancePaths.length}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Est. Duration
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {totalDuration} days
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Mandatory Steps
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {compliancePaths.filter((p) => p.is_mandatory).length}
              </Typography>
            </Box>
          </Box>

          {/* Gantt-style Timeline */}
          <Box
            sx={{
              overflowX: 'auto',
              pb: 2,
            }}
          >
            <Box
              sx={{
                minWidth: `${compliancePaths.length * (STEP_WIDTH + CONNECTOR_LENGTH) + 100}px`,
                position: 'relative',
                height: `${ROW_HEIGHT + 60}px`,
              }}
            >
              {/* Timeline Base */}
              <Box
                sx={{
                  position: 'absolute',
                  top: ROW_HEIGHT / 2 + 20,
                  left: 40,
                  right: 40,
                  height: 4,
                  background:
                    'linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 100%)',
                  borderRadius: 2,
                }}
              />

              {/* Steps */}
              {compliancePaths.map((path, index) => {
                const stepColor = getStepColor(path)
                const xPos = index * (STEP_WIDTH + CONNECTOR_LENGTH) + 40
                const agencyCode = getAgencyName(path.agency_id)

                return (
                  <React.Fragment key={path.id}>
                    {/* Connector Line */}
                    {index > 0 && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: ROW_HEIGHT / 2 + 18,
                          left: xPos - CONNECTOR_LENGTH + 10,
                          width: CONNECTOR_LENGTH - 20,
                          height: 8,
                          background: `linear-gradient(90deg, ${getStepColor(compliancePaths[index - 1])} 0%, ${stepColor} 100%)`,
                          borderRadius: 4,
                          boxShadow: `0 0 10px ${stepColor}40`,
                        }}
                      />
                    )}

                    {/* Step Card */}
                    <Tooltip
                      title={
                        <Box sx={{ p: 1 }}>
                          <Typography
                            variant="subtitle2"
                            sx={{ fontWeight: 600 }}
                          >
                            {path.submission_type}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            Agency: {agencyCode}
                          </Typography>
                          <Typography variant="body2">
                            Duration: {path.typical_duration_days || 30} days
                          </Typography>
                          {path.description && (
                            <Typography
                              variant="body2"
                              sx={{ mt: 1, color: 'text.secondary' }}
                            >
                              {path.description}
                            </Typography>
                          )}
                        </Box>
                      }
                      arrow
                      placement="top"
                    >
                      <Paper
                        elevation={3}
                        sx={{
                          position: 'absolute',
                          top: 20,
                          left: xPos,
                          width: STEP_WIDTH,
                          height: STEP_HEIGHT,
                          borderRadius: 2,
                          border: `2px solid ${stepColor}`,
                          background: `linear-gradient(135deg, ${stepColor}20 0%, ${stepColor}10 100%)`,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: `0 8px 24px ${stepColor}40`,
                          },
                        }}
                      >
                        <Box sx={{ p: 1.5 }}>
                          {/* Step Number */}
                          <Box
                            sx={{
                              position: 'absolute',
                              top: -12,
                              left: -12,
                              width: 28,
                              height: 28,
                              borderRadius: '50%',
                              background: stepColor,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 'bold',
                              fontSize: '0.75rem',
                              color: '#fff',
                              boxShadow: `0 0 12px ${stepColor}`,
                            }}
                          >
                            {index + 1}
                          </Box>

                          {/* Agency Badge */}
                          <Chip
                            size="small"
                            label={agencyCode}
                            icon={<AgencyIcon sx={{ fontSize: 14 }} />}
                            sx={{
                              bgcolor: stepColor,
                              color: '#fff',
                              fontWeight: 600,
                              fontSize: '0.7rem',
                              mb: 1,
                            }}
                          />

                          {/* Submission Type */}
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 600,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {path.submission_type}
                          </Typography>

                          {/* Duration */}
                          <Stack
                            direction="row"
                            spacing={0.5}
                            alignItems="center"
                            sx={{ mt: 0.5 }}
                          >
                            <DurationIcon
                              sx={{ fontSize: 14, color: 'text.secondary' }}
                            />
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              {path.typical_duration_days || 30} days
                            </Typography>
                            {path.is_mandatory ? (
                              <Chip
                                size="small"
                                label="Required"
                                sx={{
                                  ml: 'auto',
                                  height: 18,
                                  fontSize: '0.6rem',
                                  bgcolor: 'error.main',
                                  color: '#fff',
                                }}
                              />
                            ) : (
                              <Chip
                                size="small"
                                label="Optional"
                                sx={{
                                  ml: 'auto',
                                  height: 18,
                                  fontSize: '0.6rem',
                                  bgcolor: 'rgba(255,255,255,0.1)',
                                }}
                              />
                            )}
                          </Stack>
                        </Box>
                      </Paper>
                    </Tooltip>
                  </React.Fragment>
                )
              })}

              {/* End Marker */}
              <Box
                sx={{
                  position: 'absolute',
                  top: ROW_HEIGHT / 2 + 5,
                  left:
                    compliancePaths.length * (STEP_WIDTH + CONNECTOR_LENGTH) +
                    20,
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background:
                    'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)',
                }}
              >
                <ApprovedIcon sx={{ color: '#fff' }} />
              </Box>
            </Box>
          </Box>

          {/* Legend */}
          <Box
            sx={{
              display: 'flex',
              gap: 2,
              flexWrap: 'wrap',
              pt: 2,
              borderTop: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ mr: 2 }}>
              Agencies:
            </Typography>
            {Object.entries(AGENCY_COLORS).map(([agency, color]) => (
              <Stack
                key={agency}
                direction="row"
                spacing={0.5}
                alignItems="center"
              >
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: color,
                  }}
                />
                <Typography variant="caption">{agency}</Typography>
              </Stack>
            ))}
          </Box>
        </>
      )}
    </Paper>
  )
}

// Demo data for when API returns empty
function getDemoCompliancePaths(assetType: AssetType): AssetCompliancePath[] {
  const now = new Date().toISOString()

  const basePaths: Record<AssetType, AssetCompliancePath[]> = {
    office: [
      {
        id: '1',
        asset_type: 'office',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Planning permission and plot ratio approval',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'office',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Structural and architectural approval',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'office',
        agency_id: 'SCDF',
        submission_type: 'Fire Safety Plan',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Fire safety and egress requirements',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'office',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'office',
        agency_id: 'BCA',
        submission_type: 'CSC Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Certificate of Statutory Completion',
        typical_duration_days: 14,
        created_at: now,
      },
    ],
    retail: [
      {
        id: '1',
        asset_type: 'retail',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Planning permission for retail use',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'retail',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Structural approval with retail specifications',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'retail',
        agency_id: 'SCDF',
        submission_type: 'Fire Safety Plan',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Fire safety with crowd management',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'retail',
        agency_id: 'NEA',
        submission_type: 'F&B Licensing',
        sequence_order: 4,
        is_mandatory: false,
        description: 'Food and beverage licensing (if applicable)',
        typical_duration_days: 21,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'retail',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
    residential: [
      {
        id: '1',
        asset_type: 'residential',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Planning permission for residential use',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'residential',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Structural approval with residential standards',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'residential',
        agency_id: 'SCDF',
        submission_type: 'Fire Safety Plan',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Fire safety for residential buildings',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'residential',
        agency_id: 'PUB',
        submission_type: 'Sewerage Plan',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Water and sewerage connection approval',
        typical_duration_days: 21,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'residential',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
    industrial: [
      {
        id: '1',
        asset_type: 'industrial',
        agency_id: 'JTC',
        submission_type: 'Industrial Development Permit',
        sequence_order: 1,
        is_mandatory: true,
        description: 'JTC approval for industrial land use',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'industrial',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Planning permission confirmation',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'industrial',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Structural approval for industrial specs',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'industrial',
        agency_id: 'NEA',
        submission_type: 'Environmental Impact',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Environmental compliance assessment',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'industrial',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
    heritage: [
      {
        id: '1',
        asset_type: 'heritage',
        agency_id: 'STB',
        submission_type: 'Heritage Assessment',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Conservation status and heritage element assessment',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'heritage',
        agency_id: 'URA',
        submission_type: 'Conservation DC',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Development control with conservation guidelines',
        typical_duration_days: 90,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'heritage',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Structural approval with heritage considerations',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'heritage',
        agency_id: 'STB',
        submission_type: 'Conservation Approval',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Final STB approval for heritage compliance',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'heritage',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
    mixed_use: [
      {
        id: '1',
        asset_type: 'mixed_use',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Planning permission for mixed-use development',
        typical_duration_days: 90,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'mixed_use',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 2,
        is_mandatory: true,
        description: 'Comprehensive structural approval',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'mixed_use',
        agency_id: 'SCDF',
        submission_type: 'Fire Safety Plan',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Complex fire safety for multiple uses',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'mixed_use',
        agency_id: 'LTA',
        submission_type: 'Traffic Impact',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Traffic and parking assessment',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'mixed_use',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
    hospitality: [
      {
        id: '1',
        asset_type: 'hospitality',
        agency_id: 'URA',
        submission_type: 'Development Control (DC)',
        sequence_order: 1,
        is_mandatory: true,
        description: 'Planning permission for hotel use',
        typical_duration_days: 60,
        created_at: now,
      },
      {
        id: '2',
        asset_type: 'hospitality',
        agency_id: 'STB',
        submission_type: 'Hotel License Pre-approval',
        sequence_order: 2,
        is_mandatory: true,
        description: 'STB preliminary hotel license review',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '3',
        asset_type: 'hospitality',
        agency_id: 'BCA',
        submission_type: 'Building Plan (BP)',
        sequence_order: 3,
        is_mandatory: true,
        description: 'Structural approval for hospitality',
        typical_duration_days: 45,
        created_at: now,
      },
      {
        id: '4',
        asset_type: 'hospitality',
        agency_id: 'SCDF',
        submission_type: 'Fire Safety Plan',
        sequence_order: 4,
        is_mandatory: true,
        description: 'Fire safety for hospitality buildings',
        typical_duration_days: 30,
        created_at: now,
      },
      {
        id: '5',
        asset_type: 'hospitality',
        agency_id: 'BCA',
        submission_type: 'TOP Application',
        sequence_order: 5,
        is_mandatory: true,
        description: 'Temporary Occupation Permit',
        typical_duration_days: 21,
        created_at: now,
      },
    ],
  }

  return basePaths[assetType] || basePaths.office
}
