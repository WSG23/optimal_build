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
} from '@mui/material'
import { Add as AddIcon, Person as PersonIcon } from '@mui/icons-material'

// Mock data for initial display until backend integration
const MOCK_MEMBERS = [
  { id: '1', name: 'John Doe', email: 'john@example.com', role: 'developer', status: 'active' },
  { id: '2', name: 'Sarah Smith', email: 'sarah.architect@firm.com', role: 'consultant', status: 'active' },
  { id: '3', name: 'Mike Engineer', email: 'mike.struct@eng.com', role: 'consultant', status: 'pending' },
]

export const TeamManagementPage: React.FC = () => {
  const [inviteOpen, setInviteOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('consultant')

  const handleInvite = () => {
    // TODO: Integrate with backend
    console.log('Inviting', inviteEmail, inviteRole)
    setInviteOpen(false)
    setInviteEmail('')
  }

  return (
    <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4, alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Team Coordination
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your project team, consultants, and approval workflows.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setInviteOpen(true)}
          sx={{
            background: 'linear-gradient(135deg, #FF3366 0%, #FF6B3D 100%)',
            boxShadow: '0px 4px 12px rgba(255, 51, 102, 0.3)',
          }}
        >
          Invite Member
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card
            sx={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 4,
              overflow: 'hidden',
            }}
          >
            <Box sx={{ p: 3, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon color="primary" />
                Team Members
              </Typography>
            </Box>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {MOCK_MEMBERS.map((member) => (
                  <TableRow key={member.id} hover>
                    <TableCell sx={{ fontWeight: 500 }}>{member.name}</TableCell>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>
                      <Chip
                        label={member.role}
                        size="small"
                        sx={{
                          textTransform: 'capitalize',
                          bgcolor: member.role === 'developer' ? 'primary.main' : 'default',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={member.status}
                        size="small"
                        color={member.status === 'active' ? 'success' : 'warning'}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button size="small" color="error">
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </Grid>
      </Grid>

      <Dialog
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        PaperProps={{
            sx: {
                background: '#1A1D1F',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                minWidth: 400
            }
        }}
      >
        <DialogTitle>Invite New Member</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Email Address"
              fullWidth
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
            />
            <TextField
              select
              label="Role"
              fullWidth
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
            >
              <MenuItem value="consultant">Consultant</MenuItem>
              <MenuItem value="architect">Architect</MenuItem>
              <MenuItem value="engineer">Engineer</MenuItem>
              <MenuItem value="viewer">Viewer</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setInviteOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleInvite}>
            Send Invitation
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
