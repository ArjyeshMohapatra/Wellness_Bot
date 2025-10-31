import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    IconButton,
    Accordion,
    AccordionSummary,
    AccordionDetails,
} from '@mui/material';
import {
    ContentCopy as ContentCopyIcon,
    ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';

interface ConfigurationSuccessDialogProps {
    open: boolean;
    onClose: () => void;
    configurationDialogData: {
        botUsername: string;
        licenseKey: string | null;
    } | null;
    hasAdminPermissions: boolean;
    onRefreshAdminPermissions: () => void;
    onCopyToClipboard: (text: string, label: string) => void;
}

const ConfigurationSuccessDialog: React.FC<ConfigurationSuccessDialogProps> = ({
    open,
    onClose,
    configurationDialogData,
    hasAdminPermissions,
    onRefreshAdminPermissions,
    onCopyToClipboard
}) => {
    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="md"
            fullWidth
        >
            <DialogTitle sx={{ textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    🎉 Congratulations!
                </Typography>
                <Typography variant="h6">
                    Bot's settings saved successfully
                </Typography>
            </DialogTitle>
            <DialogContent sx={{ p: 3 }}>
                {/* Bot Link */}
                <Box sx={{ mb: 3, textAlign: 'center' }}>
                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                        🤖 Bot Link
                    </Typography>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        href={`https://t.me/${configurationDialogData?.botUsername || 'trackmyhealthbot'}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ minWidth: 200 }}
                    >
                        @{configurationDialogData?.botUsername || 'trackmyhealthbot'}
                    </Button>
                </Box>

                {/* Collapsible Bot Setup Instructions */}
                <Accordion defaultExpanded={false} sx={{ mb: 3 }}>
                    <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls="setup-instructions-content"
                        id="setup-instructions-header"
                    >
                        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                            📋 Bot Setup Instructions (Step-by-Step Guide)
                        </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Typography variant="body1" sx={{ mb: 2 }}>
                            Follow these steps to set up your bot in your Telegram group:
                        </Typography>
                        <Box component="ol" sx={{ pl: 2 }}>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Add the bot to your group:</strong> Click the bot link above and add @{configurationDialogData?.botUsername || 'BeHumanAgainBot'} to your Telegram group as an administrator.
                            </Box>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Grant admin permissions:</strong> Make sure the bot has admin permissions in your group (can delete messages, ban users, etc.).
                            </Box>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Activate the license:</strong> Copy the license key below and send it to your group chat. The bot will automatically detect it and confirm admin permissions.
                            </Box>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Generate user IDs:</strong> Once activated, use the "Generate User IDs" option in the navbar to create unique IDs for your group members.
                            </Box>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Share with members:</strong> Distribute the bot link and unique IDs to your potential group members.
                            </Box>
                            <Box component="li" sx={{ mb: 1 }}>
                                <strong>Monitor activity:</strong> The bot will now manage your wellness program according to your configured settings.
                            </Box>
                        </Box>
                    </AccordionDetails>
                </Accordion>

                {/* Admin Permission Status & License Key */}
                <Box sx={{ textAlign: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: hasAdminPermissions ? 'success.main' : 'warning.main' }}>
                            {hasAdminPermissions ? '✅ Admin Permission Confirmed' : '⚠️ Admin Permission Required'}
                        </Typography>
                        <IconButton
                            size="small"
                            onClick={onRefreshAdminPermissions}
                            sx={{
                                '&:hover': {
                                    bgcolor: 'rgba(0, 0, 0, 0.1)'
                                }
                            }}
                            title="Refresh Admin Permission Status"
                        >
                            🔄
                        </IconButton>
                    </Box>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                        {hasAdminPermissions
                            ? 'Your admin permissions have been verified and your bot configuration is ready.'
                            : 'Your license key has been generated. Please complete the setup steps below to activate your bot.'
                        }
                    </Typography>

                    {configurationDialogData?.licenseKey && (
                        <Box sx={{ mt: 3 }}>
                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                                🔑 License Key
                            </Typography>
                            <Box sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 1,
                                bgcolor: 'grey.100',
                                p: 2,
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'grey.300'
                            }}>
                                <Typography variant="body1" sx={{
                                    fontFamily: 'monospace',
                                    fontSize: '1.1rem',
                                    fontWeight: 'bold'
                                }}>
                                    {configurationDialogData.licenseKey}
                                </Typography>
                                <IconButton
                                    size="small"
                                    onClick={() => onCopyToClipboard(configurationDialogData.licenseKey!, 'License Key')}
                                    sx={{
                                        '&:hover': {
                                            bgcolor: 'rgba(0, 0, 0, 0.1)'
                                        }
                                    }}
                                    title="Copy License Key"
                                >
                                    <ContentCopyIcon />
                                </IconButton>
                            </Box>
                            <Typography variant="body2" sx={{ mt: 1, color: 'text.secondary' }}>
                                Copy this license key and send it to your group chat to activate the bot and verify admin permissions.
                            </Typography>
                        </Box>
                    )}
                </Box>
            </DialogContent>
            <DialogActions sx={{ p: 3, justifyContent: 'center' }}>
                <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    onClick={onClose}
                    sx={{ minWidth: 150 }}
                >
                    Proceed
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default ConfigurationSuccessDialog;