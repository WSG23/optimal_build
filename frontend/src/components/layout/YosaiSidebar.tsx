import { Box, Typography, Stack, Button, useTheme, alpha } from '@mui/material';
import { useTranslation } from '../../i18n';
import { useRouterPath, Link } from '../../router';

export function YosaiSidebar() {
    const { t } = useTranslation();
    const path = useRouterPath();
    const theme = useTheme();

    // NOTE: Keep distinct from YosaiShell navItems if dynamic later,
    // but for now this duplicates the static list to allow standalone use.
    const navItems = [
        { path: '/', label: t('nav.home') },
        { path: '/cad/upload', label: t('nav.upload') },
        { path: '/cad/detection', label: t('nav.detection') },
        { path: '/cad/pipelines', label: t('nav.pipelines') },
        { path: '/feasibility', label: t('nav.feasibility') },
        { path: '/finance', label: t('nav.finance') },
        { path: '/agents/site-capture', label: t('nav.agentCapture') },
        { path: '/agents/performance', label: t('nav.agentPerformance') },
        { path: '/visualizations/intelligence', label: t('nav.intelligence') },
        { path: '/app/phase-management', label: 'Phase Management' }, // Added explictly as it was missing in shell list but present in router
    ];

    return (
        <Box
            component="aside"
            sx={{
                width: '280px',
                height: '100vh', // Full height for fixed positioning context
                flexShrink: 0,
                borderRight: 1,
                borderColor: 'divider',
                bgcolor: 'background.default',
                display: 'flex',
                flexDirection: 'column',
                overflowY: 'auto', // Allow scrolling within sidebar if needed
            }}
        >
            {/* Brand */}
            <Box sx={{ p: 4, mb: 2 }}>
                <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold', letterSpacing: '0.05em' }}>
                    OPTIMAL BUILD
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
                    v2.0
                </Typography>
            </Box>

            {/* Nav */}
            <Box component="nav" sx={{ flexGrow: 1, px: 2, pb: 2 }}>
                <Stack spacing={0.5}>
                    {navItems.map((item) => {
                        const isActive = item.path === '/' ? path === '/' : path.startsWith(item.path);
                        return (
                            <Button
                                key={item.path}
                                component={Link}
                                to={item.path}
                                variant="text"
                                sx={{
                                    justifyContent: 'flex-start',
                                    color: isActive ? 'primary.main' : 'text.secondary',
                                    bgcolor: isActive ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                                    borderLeft: 2,
                                    borderColor: isActive ? 'primary.main' : 'transparent',
                                    borderRadius: 0,
                                    px: 3,
                                    py: 1.5,
                                    textTransform: 'none',
                                    fontWeight: isActive ? 600 : 400,
                                    '&:hover': {
                                        bgcolor: alpha(theme.palette.text.primary, 0.04),
                                        color: 'text.primary',
                                    },
                                }}
                            >
                                {item.label}
                            </Button>
                        );
                    })}
                </Stack>
            </Box>
        </Box>
    );
}
