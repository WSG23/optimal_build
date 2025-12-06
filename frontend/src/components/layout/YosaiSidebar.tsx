import { useState } from 'react';
import {
    Box,
    Typography,
    Stack,
    Button,
    IconButton,
    Tooltip,
    useTheme,
    alpha
} from '@mui/material';
import {
    Home as HomeIcon,
    UploadFile as UploadIcon,
    Search as DetectionIcon,
    AccountTree as PipelineIcon,
    Engineering as FeasibilityIcon,
    AttachMoney as FinanceIcon,
    GpsFixed as CaptureIcon,
    Speed as PerformanceIcon,
    Psychology as IntelligenceIcon,
    ViewTimeline as PhaseIcon,
    ChevronLeft as ChevronLeftIcon,
    ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { useTranslation } from '../../i18n';
import { useRouterPath, Link } from '../../router';

export function YosaiSidebar() {
    const { t } = useTranslation();
    const path = useRouterPath();
    const theme = useTheme();
    const [isCollapsed, setIsCollapsed] = useState(false);

    const navGroups = [
        {
            id: 'ops',
            title: 'OPERATIONS',
            items: [
                { path: '/', label: t('nav.home'), icon: <HomeIcon fontSize="small" /> },
                { path: '/cad/upload', label: t('nav.upload'), icon: <UploadIcon fontSize="small" /> },
                { path: '/cad/detection', label: t('nav.detection'), icon: <DetectionIcon fontSize="small" /> },
                { path: '/cad/pipelines', label: t('nav.pipelines'), icon: <PipelineIcon fontSize="small" /> },
                { path: '/feasibility', label: t('nav.feasibility'), icon: <FeasibilityIcon fontSize="small" /> },
                { path: '/agents/site-capture', label: t('nav.agentCapture'), icon: <CaptureIcon fontSize="small" /> },
                { path: '/app/phase-management', label: 'Phase Management', icon: <PhaseIcon fontSize="small" /> },
            ]
        },
        {
            id: 'biz',
            title: 'BUSINESS',
            items: [
                { path: '/finance', label: t('nav.finance'), icon: <FinanceIcon fontSize="small" /> },
                { path: '/visualizations/intelligence', label: t('nav.intelligence'), icon: <IntelligenceIcon fontSize="small" /> },
                { path: '/agents/performance', label: t('nav.agentPerformance'), icon: <PerformanceIcon fontSize="small" /> },
            ]
        }
    ];

    return (
        <Box
            component="aside"
            sx={{
                width: isCollapsed ? '80px' : '280px',
                height: '100vh',
                flexShrink: 0,
                borderRight: 1,
                borderColor: 'divider',
                bgcolor: 'background.default',
                display: 'flex',
                flexDirection: 'column',
                transition: theme.transitions.create('width', {
                    easing: theme.transitions.easing.sharp,
                    duration: theme.transitions.duration.leavingScreen,
                }),
                overflowX: 'hidden',
                zIndex: 20
            }}
        >
            {/* Brand Header */}
            <Box
                sx={{
                    p: isCollapsed ? 2 : 4,
                    height: '88px',
                    display: 'flex',
                    flexDirection: isCollapsed ? 'column' : 'row',
                    alignItems: isCollapsed ? 'center' : 'flex-start',
                    justifyContent: isCollapsed ? 'center' : 'space-between',
                    mb: 2
                }}
            >
                {isCollapsed ? (
                    <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold' }}>OB</Typography>
                ) : (
                    <Box>
                        <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold', letterSpacing: '0.05em' }}>
                            OPTIMAL BUILD
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
                            v2.0
                        </Typography>
                    </Box>
                )}
            </Box>

            {/* Navigation Groups */}
            <Box component="nav" sx={{ flexGrow: 1, px: 2, pb: 2, overflowY: 'auto' }}>
                <Stack spacing={4}>
                    {navGroups.map((group) => (
                        <Box key={group.id}>
                            {!isCollapsed && (
                                <Typography
                                    variant="caption"
                                    sx={{
                                        px: 2,
                                        mb: 1,
                                        display: 'block',
                                        color: 'text.secondary',
                                        fontWeight: 600,
                                        letterSpacing: '0.1em'
                                    }}
                                >
                                    {group.title}
                                </Typography>
                            )}
                            <Stack spacing={0.5}>
                                {group.items.map((item) => {
                                    const isActive = item.path === '/' ? path === '/' : path.startsWith(item.path);

                                    const ButtonContent = (
                                        <Button
                                            component={Link}
                                            to={item.path}
                                            variant="text"
                                            fullWidth
                                            sx={{
                                                justifyContent: isCollapsed ? 'center' : 'flex-start',
                                                minWidth: isCollapsed ? '48px' : 'auto',
                                                color: isActive ? 'primary.main' : 'text.secondary',
                                                bgcolor: isActive ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                                                borderLeft: isCollapsed ? 0 : 2,
                                                borderColor: isActive ? 'primary.main' : 'transparent',
                                                borderRadius: isCollapsed ? 2 : 0,
                                                px: isCollapsed ? 1 : 3,
                                                py: 1.5,
                                                textTransform: 'none',
                                                fontWeight: isActive ? 600 : 400,
                                                gap: isCollapsed ? 0 : 2,
                                                '&:hover': {
                                                    bgcolor: alpha(theme.palette.text.primary, 0.04),
                                                    color: 'text.primary',
                                                },
                                            }}
                                        >
                                            {item.icon}
                                            {!isCollapsed && <Box component="span">{item.label}</Box>}
                                        </Button>
                                    );

                                    return isCollapsed ? (
                                        <Tooltip key={item.path} title={item.label} placement="right" arrow>
                                            <Box>{ButtonContent}</Box>
                                        </Tooltip>
                                    ) : (
                                        <Box key={item.path}>{ButtonContent}</Box>
                                    );
                                })}
                            </Stack>
                        </Box>
                    ))}
                </Stack>
            </Box>

            {/* Collapse Toggle */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', justifyContent: isCollapsed ? 'center' : 'flex-end' }}>
                <IconButton onClick={() => setIsCollapsed(!isCollapsed)} size="small">
                    {isCollapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                </IconButton>
            </Box>
        </Box>
    );
}
