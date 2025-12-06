import { ReactNode } from 'react';
import { Box, Typography, Button, Stack, useTheme, alpha } from '@mui/material';
import { useTranslation } from '../../i18n';
import { useRouterPath, Link } from '../../router';
import { LocaleSwitcher } from '../../i18n/LocaleSwitcher';
import { ThemeToggle } from '../../theme/ThemeToggle';

export interface AppShellProps {
    title: string;
    subtitle?: string;
    actions?: ReactNode;
    children: ReactNode;
}

/**
 * @deprecated Use AppShell from './AppShell' instead
 */
export type YosaiShellProps = AppShellProps;

/**
 * AppShell
 * Main application layout with sidebar navigation and header.
 * Supports dark and light modes via the theme system.
 */
export function AppShell({ title, subtitle, actions, children }: AppShellProps) {
    const { t } = useTranslation();
    const path = useRouterPath();
    const theme = useTheme();

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
    ];

    return (
        <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
            {/* "The Wall" - Sidebar */}
            <Box
                component="aside"
                sx={{
                    width: '280px',
                    flexShrink: 0,
                    borderRight: 1,
                    borderColor: 'divider',
                    bgcolor: 'background.default',
                    display: 'flex',
                    flexDirection: 'column',
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
                <Box component="nav" sx={{ flexGrow: 1, px: 2 }}>
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

            {/* Main Content Area */}
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                {/* Header */}
                <Box
                    component="header"
                    sx={{
                        py: 3,
                        px: 4,
                        borderBottom: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        bgcolor: alpha(theme.palette.background.default, 0.8),
                        backdropFilter: 'blur(12px)',
                        position: 'sticky',
                        top: 0,
                        zIndex: 10,
                    }}
                >
                    <Box>
                        <Typography variant="h2" sx={{ color: 'text.primary' }}>
                            {title}
                        </Typography>
                        {subtitle && (
                            <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5 }}>
                                {subtitle}
                            </Typography>
                        )}
                    </Box>
                    <Stack direction="row" spacing={2} alignItems="center">
                        <ThemeToggle />
                        <LocaleSwitcher />
                        {actions}
                    </Stack>
                </Box>

                {/* Content */}
                <Box component="main" sx={{ flexGrow: 1, p: 0, overflow: 'auto', scrollbarGutter: 'stable' }}>
                    {children}
                </Box>
            </Box>
        </Box>
    );
}

/**
 * @deprecated Use AppShell instead
 */
export const YosaiShell = AppShell;
