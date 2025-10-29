import React from 'react';
import UserIDGenerator from '../components/UserIDGenerator';
import { Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const DashboardGenerateId: React.FC = () => {
    const navigate = useNavigate();

    return (
        <Box>
            <Box sx={{ p: 2 }}>
                <Button variant="outlined" onClick={() => navigate('/dashboard')}>← Back to Dashboard</Button>
            </Box>
            <UserIDGenerator />
        </Box>
    );
};

export default DashboardGenerateId;
