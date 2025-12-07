import React, { useState } from 'react'
import {
  Box,
  Button,
  Card,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
} from '@mui/material'
import { Add as AddIcon, Business as AgencyIcon } from '@mui/icons-material'

// Mock Data for frontend visualization (since backend connection is unstable)
const MOCK_AGENCIES = [
    { id: '1', code: 'URA', name: 'Urban Redevelopment Authority', description: 'Land use planning and conservation' },
    { id: '2', code: 'BCA', name: 'Building & Construction Authority', description: 'Building safety and structural integrity' },
    { id: '3', code: 'SCDF', name: 'Singapore Civil Defence Force', description: 'Fire safety and shelter requirements' },
    { id: '4', code: 'NEA', name: 'National Environment Agency', description: 'Pollution control and environmental health' },
]

const MOCK_SUBMISSIONS = [
    {
        id: '101',
        title: 'Main Tower Development Control',
        agency: 'URA',
        type: 'DC',
        status: 'approved',
        submission_no: 'ES20251120-44912',
        updated_at: '2025-11-20'
    },
    {
        id: '102',
        title: 'Fire Safety Plan - Tower A',
        agency: 'SCDF',
        type: 'BP',
        status: 'in_review',
        submission_no: 'ES20251205-11822',
        updated_at: '2025-12-05'
    },
]

export const RegulatoryDashboardPage: React.FC = () => {
    const [openDialog, setOpenDialog] = useState(false)
    const [mockSubmissions, setMockSubmissions] = useState(MOCK_SUBMISSIONS)

    // Form State
    const [title, setTitle] = useState('')
    const [agencyId, setAgencyId] = useState('')
    const [type, setType] = useState('DC')
    const [simulating, setSimulating] = useState(false)

    const handleSubmit = async () => {
        setSimulating(true)

        // Simulate "submission" delay
        await new Promise(resolve => setTimeout(resolve, 1500))

        const agency = MOCK_AGENCIES.find(a => a.id === agencyId)
        const newSubmission = {
            id: String(Date.now()),
            title: title,
            agency: agency?.code || 'Unknown',
            type: type,
            status: 'submitted',
            submission_no: `ES${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${Math.floor(Math.random()*10000)}`,
            updated_at: new Date().toISOString().split('T')[0]
        }

        setMockSubmissions([newSubmission, ...mockSubmissions])
        setSimulating(false)
        setOpenDialog(false)
        resetForm()
    }

    const resetForm = () => {
        setTitle('')
        setAgencyId('')
        setType('DC')
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'approved': return 'success'
            case 'rejected': return 'error'
            case 'in_review': return 'info'
            case 'submitted': return 'warning'
            case 'draft': return 'default'
            default: return 'default'
        }
    }

    return (
        <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
             <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4, alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
                        Regulatory Navigation
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Manage Singapore authority submissions (CORENET 2.0 Integration)
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenDialog(true)}
                    sx={{
                        background: 'linear-gradient(135deg, #00C9FF 0%, #92FE9D 100%)',
                        color: '#000',
                        fontWeight: 'bold',
                        boxShadow: '0px 4px 12px rgba(0, 201, 255, 0.3)',
                    }}
                >
                    New Submission
                </Button>
            </Box>

            <Grid container spacing={4}>
                {/* Agency Status Cards */}
                <Grid item xs={12}>
                     <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>Connected Agencies</Typography>
                     <Grid container spacing={2}>
                        {MOCK_AGENCIES.map(agency => (
                            <Grid item xs={12} sm={6} md={3} key={agency.id}>
                                <Card sx={{
                                    p: 2,
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    bgcolor: 'rgba(255,255,255,0.03)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 2
                                }}>
                                    <AgencyIcon color="primary" fontSize="large" />
                                    <Box>
                                        <Typography variant="subtitle1" fontWeight="bold">{agency.code}</Typography>
                                        <Typography variant="caption" color="text.secondary">Online</Typography>
                                    </Box>
                                </Card>
                            </Grid>
                        ))}
                     </Grid>
                </Grid>

                {/* Submissions List */}
                <Grid item xs={12}>
                    <Card sx={{
                        border: '1px solid rgba(255,255,255,0.1)',
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        overflow: 'hidden'
                    }}>
                        <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            <Typography variant="h6">Active Submissions</Typography>
                        </Box>

                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Reference No.</TableCell>
                                    <TableCell>Title</TableCell>
                                    <TableCell>Agency</TableCell>
                                    <TableCell>Type</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>Last Updated</TableCell>
                                    <TableCell align="right">Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {mockSubmissions.map((row) => (
                                    <TableRow key={row.id} hover>
                                        <TableCell sx={{ fontFamily: 'monospace' }}>{row.submission_no}</TableCell>
                                        <TableCell sx={{ fontWeight: 500 }}>{row.title}</TableCell>
                                        <TableCell>{row.agency}</TableCell>
                                        <TableCell>{row.type}</TableCell>
                                        <TableCell>
                                            <Chip
                                                label={row.status.replace('_', ' ')}
                                                size="small"
                                                color={getStatusColor(row.status) as any}
                                                variant="outlined"
                                                sx={{ textTransform: 'capitalize' }}
                                            />
                                        </TableCell>
                                        <TableCell>{row.updated_at}</TableCell>
                                        <TableCell align="right">
                                            <Button size="small">Track</Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </Card>
                </Grid>
            </Grid>

            {/* New Submission Dialog */}
            <Dialog
                open={openDialog}
                onClose={() => setOpenDialog(false)}
                PaperProps={{
                    sx: {
                        bgcolor: '#1A1D1F',
                        border: '1px solid rgba(255,255,255,0.1)',
                        minWidth: 500
                    }
                }}
            >
                <DialogTitle>New Authority Submission</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                        <TextField
                            label="Submission Title"
                            fullWidth
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                        <TextField
                            select
                            label="Select Agency"
                            fullWidth
                            value={agencyId}
                            onChange={(e) => setAgencyId(e.target.value)}
                        >
                            {MOCK_AGENCIES.map((option) => (
                                <MenuItem key={option.id} value={option.id}>
                                    {option.code} - {option.name}
                                </MenuItem>
                            ))}
                        </TextField>
                        <TextField
                            select
                            label="Submission Type"
                            fullWidth
                            value={type}
                            onChange={(e) => setType(e.target.value)}
                        >
                            <MenuItem value="DC">Development Control (DC)</MenuItem>
                            <MenuItem value="BP">Building Plan (BP)</MenuItem>
                            <MenuItem value="TOP">Temporary Occupation Permit (TOP)</MenuItem>
                            <MenuItem value="CSC">Certificate of Statutory Completion (CSC)</MenuItem>
                        </TextField>

                        <Alert severity="info" sx={{ bgcolor: 'rgba(2, 136, 209, 0.1)' }}>
                            This will create a draft submission and attempt to register it with the agency's mock portal.
                        </Alert>
                    </Box>
                </DialogContent>
                <DialogActions sx={{ p: 2 }}>
                    <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={handleSubmit}
                        disabled={simulating || !title || !agencyId}
                    >
                        {simulating ? 'Submitting...' : 'Submit to Agency'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    )
}
