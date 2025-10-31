import React from 'react';
import {
    Box,
    Typography,
    Button,
    IconButton,
} from '@mui/material';
import {
    ContentCopy as ContentCopyIcon,
} from '@mui/icons-material';

interface BotInfoProps {
    hasActiveSubscription: boolean;
    licenseKey: string | null;
    onCopyToClipboard: (text: string, label: string) => void;
}

const BotInfo: React.FC<BotInfoProps> = ({
    hasActiveSubscription,
    licenseKey,
    onCopyToClipboard
}) => {
    if (!hasActiveSubscription || !licenseKey) return null;

    return (
        <Box sx={{ mt: 2, mb: 2 }}>
            <Box sx={{
                bgcolor: 'info.light',
                p: 3,
                borderRadius: 2,
                border: '2px solid',
                borderColor: 'info.main'
            }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'info.contrastText' }}>
                    🤖 Bot Information
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ color: 'info.contrastText', opacity: 0.9 }}>
                            Bot Link
                        </Typography>
                        <Button
                            variant="contained"
                            color="primary"
                            size="small"
                            href={`https://t.me/trackmyhealthbot`}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ mt: 1 }}
                        >
                            @{"trackmyhealthbot"}
                        </Button>
                    </Box>
                    {licenseKey && (
                        <Box sx={{ flex: 1 }}>
                            <Typography variant="body2" sx={{ color: 'info.contrastText', opacity: 0.9 }}>
                                License Key
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                <Typography variant="body1" sx={{
                                    color: 'info.contrastText',
                                    fontWeight: 'bold',
                                    fontFamily: 'monospace',
                                    wordBreak: 'break-all',
                                    flex: 1
                                }}>
                                    {licenseKey}
                                </Typography>
                                <IconButton
                                    size="small"
                                    onClick={() => onCopyToClipboard(licenseKey, 'License Key')}
                                    sx={{
                                        color: 'info.contrastText',
                                        '&:hover': {
                                            bgcolor: 'rgba(255, 255, 255, 0.1)'
                                        }
                                    }}
                                >
                                    <ContentCopyIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        </Box>
                    )}
                </Box>
            </Box>
        </Box>
    );
};

export default BotInfo;