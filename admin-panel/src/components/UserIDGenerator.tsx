import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Button,
    Paper,
    CircularProgress,
    IconButton,
} from '@mui/material';
import {
    ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';

const UserIDGenerator: React.FC = () => {
    const [generatingUserIds, setGeneratingUserIds] = useState(false);
    const [generatedUserIds, setGeneratedUserIds] = useState<string[]>([]);
    const [showUserIdSection, setShowUserIdSection] = useState(false);
    const [loadingExisting, setLoadingExisting] = useState(true);

    // Load existing user IDs on component mount
    useEffect(() => {
        loadExistingUserIds();
    }, []);

    const loadExistingUserIds = async () => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) {
                setLoadingExisting(false);
                return;
            }

            const response = await fetch(`http://localhost:8001/api/admin/get-available-user-ids?admin_user_id=${adminUserId}`);
            const result = await response.json();

            if (result.success && result.user_ids && result.user_ids.length > 0) {
                setGeneratedUserIds(result.user_ids);
                setShowUserIdSection(true);
            }
        } catch (error) {
            console.error('Error loading existing user IDs:', error);
        } finally {
            setLoadingExisting(false);
        }
    };

    // Copy to clipboard function
    const copyToClipboard = async (text: string, label: string) => {
        try {
            await navigator.clipboard.writeText(text);
            alert(`${label} copied to clipboard!`);
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert(`${label} copied to clipboard!`);
        }
    };

    const handleGenerateUserIds = async () => {
        try {
            setGeneratingUserIds(true);
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) {
                alert('User not logged in. Please login again.');
                return;
            }

            // First, get the group ID for this admin (we need it to generate user IDs)
            const groupResponse = await fetch(`http://localhost:8001/api/admin/get-group-id?admin_user_id=${adminUserId}`);
            const groupResult = await groupResponse.json();

            if (!groupResult.success || !groupResult.group_id) {
                alert('No group found for this admin. Please make sure the bot has been added to your group and license key has been activated.');
                return;
            }

            const groupId = groupResult.group_id;

            // Generate a single unique user ID
            const response = await fetch('http://localhost:8001/api/admin/generate-unique-user-ids', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    group_id: groupId,
                    count: 1  // Generate one ID per click
                })
            });

            const result = await response.json();

            if (result.success) {
                // Add the new ID to the list (result.user_ids should be an array with one element)
                const newId = result.user_ids[0];
                setGeneratedUserIds(prev => [newId, ...prev]); // Add to beginning of list
                setShowUserIdSection(true);
                alert(`Successfully generated new user ID: ${newId}`);
            } else {
                alert(`Failed to generate user ID: ${result.message}`);
            }
        } catch (error) {
            console.error('Error generating user ID:', error);
            alert('Error generating user ID. Please check your connection and try again.');
        } finally {
            setGeneratingUserIds(false);
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8fafc 0%, #e0f2fe 25%, #e8eaf6 100%)' }}>
            {/* Header */}

            {/* Main Content */}
            <Box sx={{ p: 4, maxWidth: '1200px', mx: 'auto' }}>
                <Paper sx={{ p: 4, borderRadius: 2, boxShadow: 3 }}>
                    <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: 'primary.main', textAlign: 'center' }}>
                        🔐 Generate Unique User IDs
                    </Typography>

                    <Typography variant="body1" sx={{ mb: 4, textAlign: 'center', color: 'text.secondary' }}>
                        Generate unique user IDs for your group members. Each member will need one of these IDs to join your group after completing KYC verification.
                    </Typography>

                    {/* Generate Button */}
                    <Box sx={{ textAlign: 'center', mb: 4 }}>
                        <Button
                            variant="contained"
                            color="primary"
                            size="large"
                            onClick={handleGenerateUserIds}
                            disabled={generatingUserIds || loadingExisting}
                            sx={{ minWidth: 250, py: 1.5, fontSize: '1.1rem' }}
                        >
                            {loadingExisting ? (
                                <>
                                    <CircularProgress size={20} sx={{ mr: 1 }} />
                                    Loading existing IDs...
                                </>
                            ) : generatingUserIds ? (
                                <>
                                    <CircularProgress size={20} sx={{ mr: 1 }} />
                                    Generating...
                                </>
                            ) : (
                                '🎯 Generate New ID'
                            )}
                        </Button>
                    </Box>

                    {/* Generated User IDs Display */}
                    {showUserIdSection && generatedUserIds.length > 0 && (
                        <Box sx={{
                            bgcolor: 'primary.light',
                            p: 3,
                            borderRadius: 2,
                            border: '2px solid',
                            borderColor: 'primary.main'
                        }}>
                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.contrastText' }}>
                                🎉 Generated User IDs ({generatedUserIds.length})
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 2, color: 'primary.contrastText' }}>
                                Here are your generated unique user IDs. Share these with your potential group members along with the bot link:
                            </Typography>

                            {/* Highlight the most recent ID */}
                            {generatedUserIds.length > 0 && (
                                <Box sx={{
                                    bgcolor: 'success.light',
                                    p: 2,
                                    borderRadius: 1,
                                    border: '2px solid',
                                    borderColor: 'success.main',
                                    mb: 3
                                }}>
                                    <Typography variant="body1" sx={{ mb: 1, fontWeight: 'bold', color: 'success.contrastText' }}>
                                        🆕 Latest Generated ID:
                                    </Typography>
                                    <Box sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 1,
                                        fontFamily: 'monospace',
                                        fontSize: '1.2rem',
                                        fontWeight: 'bold',
                                        p: 2,
                                        bgcolor: 'white',
                                        borderRadius: 1,
                                        border: '1px solid',
                                        borderColor: 'success.main'
                                    }}>
                                        <Typography variant="body1" sx={{ fontFamily: 'monospace', flexGrow: 1 }}>
                                            {generatedUserIds[0]}
                                        </Typography>
                                        <IconButton
                                            onClick={() => copyToClipboard(generatedUserIds[0], `User ID ${generatedUserIds[0]}`)}
                                            sx={{
                                                color: 'success.main',
                                                '&:hover': {
                                                    bgcolor: 'rgba(76, 175, 80, 0.1)'
                                                }
                                            }}
                                            title={`Copy ${generatedUserIds[0]}`}
                                        >
                                            <ContentCopyIcon />
                                        </IconButton>
                                    </Box>
                                </Box>
                            )}

                            <Box sx={{
                                bgcolor: 'grey.100',
                                p: 2,
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'grey.300',
                                mb: 2
                            }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                    <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: 'bold' }}>
                                        All Generated User IDs ({generatedUserIds.length}):
                                    </Typography>
                                    <IconButton
                                        size="small"
                                        onClick={() => copyToClipboard(generatedUserIds.join('\n'), 'All User IDs')}
                                        sx={{
                                            color: 'primary.contrastText',
                                            '&:hover': {
                                                bgcolor: 'rgba(255, 255, 255, 0.1)'
                                            }
                                        }}
                                        title="Copy All User IDs"
                                    >
                                        <ContentCopyIcon fontSize="small" />
                                    </IconButton>
                                </Box>
                                <Box sx={{
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: 1,
                                    border: '2px solid',
                                    borderColor: 'primary.main',
                                    borderRadius: 1,
                                    p: 2,
                                    bgcolor: 'white',
                                    maxHeight: '300px',
                                    overflowY: 'auto'
                                }}>
                                    {generatedUserIds.map((userId, index) => (
                                        <Box key={index} sx={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 0.5,
                                            fontFamily: 'monospace',
                                            fontSize: '0.9rem',
                                            fontWeight: 'bold',
                                            p: 1,
                                            bgcolor: index === 0 ? 'success.light' : 'grey.50',
                                            borderRadius: 1,
                                            border: '1px solid',
                                            borderColor: index === 0 ? 'success.main' : 'grey.200',
                                            whiteSpace: 'nowrap'
                                        }}>
                                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                                {userId}
                                            </Typography>
                                            <IconButton
                                                size="small"
                                                onClick={() => copyToClipboard(userId, `User ID ${userId}`)}
                                                sx={{
                                                    p: 0.5,
                                                    '&:hover': {
                                                        bgcolor: 'rgba(0, 0, 0, 0.1)'
                                                    }
                                                }}
                                                title={`Copy ${userId}`}
                                            >
                                                <ContentCopyIcon fontSize="small" />
                                            </IconButton>
                                        </Box>
                                    ))}
                                </Box>
                            </Box>

                            <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: 'bold' }}>
                                📋 Instructions for members:
                            </Typography>
                            <Typography variant="body2" sx={{ color: 'primary.contrastText', mt: 1 }}>
                                1. Share the bot link and one unique user ID with each potential member<br />
                                2. Members will DM the bot and provide their user ID<br />
                                3. Bot will collect their KYC information (name, DOB, phone, profile pic, age, gender)<br />
                                4. After verification, bot will provide the group invitation link<br />
                                5. Members can then join the group freely
                            </Typography>
                        </Box>
                    )}
                </Paper>
            </Box>
        </Box>
    );
};

export default UserIDGenerator;