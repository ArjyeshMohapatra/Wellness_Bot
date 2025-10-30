import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box,
    IconButton,
    CircularProgress,
} from '@mui/material';
import {
    Logout as LogoutIcon,
    CreditCard as CreditCardIcon,
    LocalHospital as HospitalIcon,
    PersonAdd as PersonAddIcon,
} from '@mui/icons-material';

interface HeaderProps {
    hasActiveSubscription: boolean;
    subscriptionLoading: boolean;
    onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({
    hasActiveSubscription,
    subscriptionLoading,
    onLogout
}) => {
    const navigate = useNavigate();

    return (
        <AppBar position="static" sx={{ backgroundColor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <Toolbar>
                <HospitalIcon sx={{ mr: { xs: 1, sm: 2 }, color: 'primary.main' }} />
                <Typography
                    variant="h6"
                    component="div"
                    sx={{
                        flexGrow: 1,
                        color: 'primary.main',
                        fontWeight: 'bold',
                        fontSize: { xs: '1rem', sm: '1.25rem' }
                    }}
                >
                    <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                        Wellness Bot Admin
                    </Box>
                    <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
                        Wellness Admin
                    </Box>
                </Typography>

                {/* Desktop Layout */}
                <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
                    <Typography variant="body1" sx={{ mr: 2, color: 'text.secondary' }}>
                        Welcome, Admin
                    </Typography>
                    {hasActiveSubscription && (
                        <>
                            <Button
                                variant="outlined"
                                color="primary"
                                size="small"
                                onClick={() => navigate('/dashboard/subscription')}
                                disabled={subscriptionLoading}
                                startIcon={subscriptionLoading ? <CircularProgress size={16} /> : <CreditCardIcon />}
                                sx={{ mr: 1, whiteSpace: 'nowrap' }}
                            >
                                {subscriptionLoading ? 'Loading...' : 'Manage Subscription'}
                            </Button>
                            <Button
                                variant="outlined"
                                color="secondary"
                                size="small"
                                onClick={() => navigate('/dashboard/generateid')}
                                sx={{ mr: 1, whiteSpace: 'nowrap' }}
                            >
                                Generate User IDs
                            </Button>
                        </>
                    )}
                    <Button
                        variant="outlined"
                        color="error"
                        size="small"
                        onClick={onLogout}
                        startIcon={<LogoutIcon />}
                    >
                        Logout
                    </Button>
                </Box>

                {/* Mobile Layout */}
                <Box sx={{ display: { xs: 'flex', md: 'none' }, alignItems: 'center', gap: 1 }}>
                    {hasActiveSubscription && (
                        <>
                            <IconButton
                                color="primary"
                                size="small"
                                onClick={() => navigate('/dashboard/subscription')}
                                disabled={subscriptionLoading}
                                sx={{ p: 1 }}
                                title={subscriptionLoading ? 'Loading...' : 'Manage Subscription'}
                            >
                                {subscriptionLoading ? <CircularProgress size={20} /> : <CreditCardIcon />}
                            </IconButton>
                            <IconButton
                                color="secondary"
                                size="small"
                                onClick={() => navigate('/dashboard/generateid')}
                                sx={{ p: 1 }}
                                title={'Generate User IDs'}
                            >
                                <PersonAddIcon />
                            </IconButton>
                        </>
                    )}
                    <IconButton
                        color="error"
                        size="small"
                        onClick={onLogout}
                        sx={{ p: 1 }}
                        title="Logout"
                    >
                        <LogoutIcon />
                    </IconButton>
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default Header;