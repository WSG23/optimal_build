import { Box, Typography, Stack, Button, useTheme, alpha } from '@mui/material';
import { useTranslation } from '../../i18n';
import { useRouterPath, Link } from '../../router';

type NavGroup = {
    title: string;
    items: Array<{ path: string; label: string }>;
};

export function YosaiSidebar() {
    const { t } = useTranslation();
    const path = useRouterPath();
    const theme = useTheme();

    const navGroups: NavGroup[] = [
        {
            title: 'Build',
            items: [
                { path: '/cad/upload', label: t('nav.upload') },
                { path: '/cad/detection', label: t('nav.detection') },
                { path: '/cad/pipelines', label: t('nav.pipelines') },
            ]
        },
        {
            title: 'Analyze',
            items: [
                { path: '/visualizations/intelligence', label: t('nav.intelligence') },
                { path: '/feasibility', label: t('nav.feasibility') },
                { path: '/finance', label: t('nav.finance') },
            ]
        },
        {
            title: 'Manage',
            items: [
                { path: '/agents/site-capture', label: t('nav.agentCapture') },
                { path: '/app/phase-management', label: 'Phase Management' },
            ]
        }
    ];

    return (
        <Box
            component="aside"
            sx={{
                width: '280px',
                height: '100vh',
                flexShrink: 0,
                borderRight: 1,
                borderColor: 'divider',
                bgcolor: 'background.default',
                display: 'flex',
                flexDirection: 'column',
                overflowY: 'auto',
            }}
        >
            {/* Brand */}
            <Box sx={{ p: 4, mb: 1 }}>
                <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold', letterSpacing: '0.05em' }}>
                    OPTIMAL BUILD
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontFamily: 'monospace' }}>
                    v2.0 Command Center
                </Typography>
            </Box>

            {/* Nav */}
            <Box component="nav" sx={{ flexGrow: 1, px: 2, pb: 4 }}>
                <Box sx={{ mb: 2 }}>
                    <Button
                        component={Link}
                        to="/"
                        fullWidth
                        sx={{
                             justifyContent: 'flex-start',
                             color: path === '/' ? 'primary.main' : 'text.secondary',
                             px: 2,
                             mb: 2
                        }}
                    >
                         {t('nav.home')}
                    </Button>
                </Box>

                <Stack spacing={3}>
                    {navGroups.map((group) => (
                        <Box key={group.title}>
                             <Typography
                                variant="caption"
                                sx={{
                                    px: 2,
                                    mb: 1,
                                    display: 'block',
                                    fontWeight: 700,
                                    color: 'text.disabled',
                                    textTransform: 'uppercase',
                                    fontSize: '0.7rem',
                                    letterSpacing: '0.1em'
                                }}
                             >
                                {group.title}
                             </Typography>
                             <Stack spacing={0.5}>
                                {group.items.map((item) => {
                                    const isActive = path.startsWith(item.path);
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
                                                borderLeft: 3,
                                                borderColor: isActive ? 'primary.main' : 'transparent',
                                                borderRadius: '0 4px 4px 0',
                                                px: 3,
                                                py: 1,
                                                textAlign: 'left',
                                                textTransform: 'none',
                                                fontWeight: isActive ? 600 : 400,
                                                transition: 'all 0.2s ease-in-out',
                                                position: 'relative',
                                                overflow: 'hidden',
                                                '&::before': isActive ? {
                                                    content: '""',
                                                    position: 'absolute',
                                                    left: 0,
                                                    top: 0,
                                                    bottom: 0,
                                                    width: '3px',
                                                    bgcolor: 'primary.main',
                                                    boxShadow: `0 0 10px 1px ${theme.palette.primary.main}`
                                                } : {},
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
                    ))}
                </Stack>
            </Box>
        </Box>
    );
}
