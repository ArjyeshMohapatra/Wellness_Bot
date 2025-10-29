import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PaymentPopup from './dashboard/PaymentPopup';
import BotSettings from './dashboard/BotSettings';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { usePayment } from '../hooks/usePayment';
import { useSlotConfiguration, type Slot } from '../hooks/useSlotConfiguration';
import {
    AppBar,
    Toolbar,
    Typography,
    Button,
    Box,
    IconButton,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Accordion,
    AccordionSummary,
    AccordionDetails,
} from '@mui/material';
import {
    Logout as LogoutIcon,
    CreditCard as CreditCardIcon,
    LocalHospital as HospitalIcon,
    ContentCopy as ContentCopyIcon,
    ExpandMore as ExpandMoreIcon,
    PersonAdd as PersonAddIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
    const { logout } = useAuth();
    const [loadedSlots, setLoadedSlots] = useState<Slot[]>([]);
    const [botUsername, setBotUsername] = useState('BeHumanAgainBot');
    const [hasAdminPermissions, setHasAdminPermissions] = useState(false);
    const [licenseKey, setLicenseKey] = useState<string | null>(null);
    const [showConfigurationDialog, setShowConfigurationDialog] = useState(false);
    const [configurationDialogData, setConfigurationDialogData] = useState<{
        botUsername: string;
        licenseKey: string | null;
    } | null>(null);
    const navigate = useNavigate();

    const {
        selectedPlan,
        selectedBilling,
        paymentCompleted,
        hasActiveSubscription,
        subscriptionLoading,
        plans,
        setPaymentCompleted,
        setHasActiveSubscription,
        getCurrentMaxMembers
    } = useSubscription();
    const {
        paymentLoading,
        paymentSuccess,
        showPaymentPopup,
        setShowPaymentPopup,
        handlePayment,
        handlePaymentClose
    } = usePayment({
        plans,
        selectedPlan,
        selectedBilling,
        setPaymentCompleted,
        setHasActiveSubscription
    });
    const {
        eventType,
        eventName,
        eventDays,
        passPoints,
        slotsPerDay,
        welcomeMessage,
        kickResponse,
        undesignatedSlotResponse,
        leaderboardTime,
        bannedWords,
        slots,
        slotErrors,
        currentSlotIndex,
        currentButtonIndex,
        slotButtonIndices,
        setEventType,
        setEventName,
        setEventDays,
        setPassPoints,
        setSlotsPerDay,
        setWelcomeMessage,
        setKickResponse,
        setUndesignatedSlotResponse,
        setLeaderboardTime,
        setBannedWords,
        setCurrentSlotIndex,
        setCurrentButtonIndex,
        handleSlotTypeChange,
        handleSlotButtonCountChange,
        handleSlotButtonIndexChange,
        handleSlotChange
    } = useSlotConfiguration(loadedSlots);

    // Function to load configuration
    const loadConfiguration = useCallback(async () => {
        try {
            // Load dashboard state from localStorage first
            const savedDashboardState = localStorage.getItem('dashboardState');
            if (savedDashboardState) {
                const state = JSON.parse(savedDashboardState);
                setBotUsername(state.botUsername || 'BeHumanAgainBot');
                setHasAdminPermissions(state.hasAdminPermissions || false);
                setLicenseKey(state.licenseKey || null);
                setLoadedSlots(state.loadedSlots || []);
            }

            // Load dashboard settings from database
            const adminUserId = localStorage.getItem('userId');
            console.log('Loading dashboard for adminUserId:', adminUserId);

            if (!adminUserId) {
                console.error('No adminUserId found');
                return;
            }

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                const dbSettings = dashboardResult.settings;
                setBotUsername(dbSettings.bot_username || 'BeHumanAgainBot');
                setHasAdminPermissions(dbSettings.has_admin_permissions || false);
                setLicenseKey(dbSettings.license_key || null);
                setLoadedSlots(dbSettings.loaded_slots || []);

                // Load event configuration
                setEventType(dbSettings.event_type || 'normal');
                setEventName(dbSettings.event_name || '');
                setEventDays(dbSettings.event_days?.toString() || '');
                setPassPoints(dbSettings.pass_points?.toString() || '');
                setSlotsPerDay(dbSettings.slots_per_day?.toString() || '');
                setWelcomeMessage(dbSettings.welcome_message || '');
                setKickResponse(dbSettings.kick_response || '');
                setUndesignatedSlotResponse(dbSettings.undesignated_slot_response || '');
                setLeaderboardTime(dbSettings.leaderboard_time || '');
                setBannedWords(dbSettings.banned_words || []);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }, [setEventType, setEventName, setEventDays, setPassPoints, setSlotsPerDay, setWelcomeMessage, setKickResponse, setUndesignatedSlotResponse, setLeaderboardTime, setBannedWords]);

    // Function to refresh admin permissions
    const refreshAdminPermissions = useCallback(async () => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) return;

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                const dbSettings = dashboardResult.settings;
                setHasAdminPermissions(dbSettings.has_admin_permissions || false);
                setLicenseKey(dbSettings.license_key || null);
            }
        } catch (error) {
            console.error('Error refreshing admin permissions:', error);
        }
    }, []);

    // Load saved configuration on component mount
    useEffect(() => {
        loadConfiguration();

        // Set up periodic refresh of admin permissions (every 30 seconds)
        const interval = setInterval(() => {
            refreshAdminPermissions();
        }, 30000);

        return () => clearInterval(interval);
    }, [loadConfiguration, refreshAdminPermissions]);

    // Save dashboard state to localStorage whenever it changes
    useEffect(() => {
        const dashboardState = {
            botUsername,
            hasAdminPermissions,
            licenseKey,
            loadedSlots: slots // Save current slots instead of loadedSlots
        };
        localStorage.setItem('dashboardState', JSON.stringify(dashboardState));
    }, [botUsername, hasAdminPermissions, licenseKey, slots]);

    // Validation logic for save button
    const isConfigurationValid = () => {
        // Basic required fields
        if (!eventName.trim()) return false;
        if (!eventType) return false;
        if (!slotsPerDay || parseInt(slotsPerDay) <= 0) return false;
        if (!welcomeMessage.trim()) return false;
        if (!kickResponse.trim()) return false;
        if (!undesignatedSlotResponse.trim()) return false;
        if (!leaderboardTime) return false;

        // Time-limited event specific fields
        if (eventType === 'time-limited') {
            if (!eventDays || parseInt(eventDays) <= 0) return false;
            if (!passPoints || parseInt(passPoints) <= 0) return false;
        }

        // Slot validation
        const validSlots = slots.filter(slot => slot.name.trim() !== '');
        if (validSlots.length === 0) return false;

        // Check each slot has required fields
        for (const slot of validSlots) {
            if (!slot.name.trim()) return false;
            if (!slot.startTime) return false;
            if (!slot.endTime) return false;
            if (!slot.points || slot.points <= 0) return false;
        }

        // Check for slot errors
        if (slotErrors.totalPoints || slotErrors.overlaps) return false;

        return true;
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

    // Save configuration handler
    const handleSaveConfiguration = async () => {
        try {
            // Get current user info from localStorage (same way as payment system)
            const adminUserId = localStorage.getItem('userId');

            if (!adminUserId) {
                alert('User not logged in. Please login again.');
                return;
            }

            // Prepare configuration data
            const configData = {
                event_type: eventType,
                event_name: eventName,
                event_days: eventDays,
                pass_points: passPoints,
                slots_per_day: slotsPerDay,
                welcome_message: welcomeMessage,
                kick_response: kickResponse,
                undesignated_slot_response: undesignatedSlotResponse,
                leaderboard_time: leaderboardTime,
                banned_words: bannedWords.filter(w => w.trim()).join(', '),
                max_members: getCurrentMaxMembers(),
                slots: slots.filter(slot => slot.name.trim() !== '').map(slot => ({
                    name: slot.name,
                    compulsory: slot.compulsory,
                    startTime: slot.startTime,
                    endTime: slot.endTime,
                    points: slot.points,
                    type: slot.type,
                    botResponse: slot.botResponse || '',
                    postResponse: slot.postResponse || '',
                    image: slot.image || '',
                    buttonCount: slot.buttonCount || 0,
                    buttonNames: slot.buttonNames || [],
                    buttonValues: slot.buttonValues || [],
                }))
            };

            // Show loading (you could add a loading state here)
            console.log('Saving configuration...');

            // Call API to save configuration
            const response = await fetch('http://localhost:8001/api/admin/panel/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    config_data: configData
                })
            });

            const result = await response.json();

            if (result.success) {
                // Update loadedSlots to reflect the current slots configuration
                setLoadedSlots(slots);

                // Also save dashboard settings to persist across sessions
                const dashboardSaveSuccess = await saveDashboardSettings(result.license_key);
                if (!dashboardSaveSuccess) {
                    alert('Configuration saved to bot, but dashboard persistence failed. Settings may not be restored on next login.');
                }

                // Show configuration dialog instead of setting configurationSaved
                setConfigurationDialogData({
                    botUsername: result.bot_username || botUsername,
                    licenseKey: result.license_key || licenseKey
                });
                setShowConfigurationDialog(true);
                // Store bot username for future use
                if (result.bot_username) {
                    setBotUsername(result.bot_username);
                }
                // Update license key if returned by API
                if (result.license_key) {
                    setLicenseKey(result.license_key);
                }
            } else {
                alert(`Failed to save configuration: ${result.message}`);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            alert('Error saving configuration. Please check your connection and try again.');
        }
    };

    // Save dashboard settings to database
    const saveDashboardSettings = async (overrideLicenseKey?: string | null): Promise<boolean> => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) {
                console.error('No adminUserId found in localStorage');
                return false;
            }

            const settings = {
                bot_username: botUsername,
                has_admin_permissions: hasAdminPermissions,
                license_key: overrideLicenseKey !== undefined ? overrideLicenseKey : licenseKey,
                loaded_slots: slots, // Use current slots instead of loadedSlots
                // Event configuration
                event_type: eventType,
                event_name: eventName,
                event_days: eventDays,
                pass_points: passPoints,
                slots_per_day: slotsPerDay,
                welcome_message: welcomeMessage,
                kick_response: kickResponse,
                undesignated_slot_response: undesignatedSlotResponse,
                leaderboard_time: leaderboardTime,
                banned_words: bannedWords
            };

            console.log('Saving dashboard settings:', { adminUserId, settings });

            const response = await fetch('http://localhost:8001/api/admin/dashboard/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    settings
                })
            });

            const result = await response.json();
            console.log('Save dashboard settings response:', result);

            if (!result.success) {
                console.error('Failed to save dashboard settings:', result.message);
                return false;
            }
            return true;
        } catch (error) {
            console.error('Error saving dashboard settings:', error);
            return false;
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8fafc 0%, #e0f2fe 25%, #e8eaf6 100%)' }}>
            {/* Header */}
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
                            onClick={logout}
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
                            onClick={logout}
                            sx={{ p: 1 }}
                            title="Logout"
                        >
                            <LogoutIcon />
                        </IconButton>
                    </Box>
                </Toolbar>
            </AppBar>

            {/* Selected Plan Display */}
            {paymentCompleted && (
                <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 shadow-lg">
                    <div className="container">
                        <div className="row align-items-center">
                            <div className="col-md-8">
                                <div className="d-flex align-items-center">
                                    <div className="bg-white bg-opacity-20 rounded-full p-2 me-3">
                                        <i className="bi bi-check-circle-fill fs-4"></i>
                                    </div>
                                    <div>
                                        <h5 className="mb-1 fw-bold">
                                            Active Plan: {subscriptionLoading ? 'Checking...' : (selectedPlan || 'No Plan')}
                                        </h5>
                                        <p className="mb-0 opacity-90">
                                            {(() => {
                                                const duration = plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.duration;
                                                if (duration === 1) return 'Monthly Subscription';
                                                if (duration === 6) return 'Half yearly Subscription';
                                                if (duration === 12) return 'Annual Subscription';
                                                return `${duration}`;
                                            })()}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="col-md-4 text-md-end">
                                <span className="badge bg-white text-success fs-6 px-3 py-2 shadow-sm fw-bold">
                                    {plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.price}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Bot Information Display */}
            {hasActiveSubscription && licenseKey && (
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
                                    href={`https://t.me/BeHumanAgainBot`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    sx={{ mt: 1 }}
                                >
                                    @{"BeHumanAgainBot"}
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
                                            onClick={() => copyToClipboard(licenseKey, 'License Key')}
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
            )}

            {/* Main Content */}
            <>
                {/* Bot settings remain on dashboard when subscription is not being managed */}
                {hasActiveSubscription && (
                    <BotSettings
                        eventType={eventType}
                        eventName={eventName}
                        eventDays={eventDays}
                        passPoints={passPoints}
                        slotsPerDay={slotsPerDay}
                        welcomeMessage={welcomeMessage}
                        kickResponse={kickResponse}
                        undesignatedSlotResponse={undesignatedSlotResponse}
                        leaderboardTime={leaderboardTime}
                        bannedWords={bannedWords}
                        slots={slots}
                        slotErrors={slotErrors}
                        currentSlotIndex={currentSlotIndex}
                        currentButtonIndex={currentButtonIndex}
                        slotButtonIndices={slotButtonIndices}
                        onEventTypeChange={setEventType}
                        onEventNameChange={setEventName}
                        onEventDaysChange={setEventDays}
                        onPassPointsChange={setPassPoints}
                        onSlotsPerDayChange={setSlotsPerDay}
                        onWelcomeMessageChange={setWelcomeMessage}
                        onKickResponseChange={setKickResponse}
                        onUndesignatedSlotResponseChange={setUndesignatedSlotResponse}
                        onLeaderboardTimeChange={setLeaderboardTime}
                        onBannedWordsChange={setBannedWords}
                        onSlotChange={handleSlotChange}
                        onCurrentSlotIndexChange={setCurrentSlotIndex}
                        onCurrentButtonIndexChange={setCurrentButtonIndex}
                        onSlotTypeChange={handleSlotTypeChange}
                        onSlotButtonCountChange={handleSlotButtonCountChange}
                        onSlotButtonIndexChange={handleSlotButtonIndexChange}
                        onSaveConfiguration={handleSaveConfiguration}
                        isConfigurationValid={isConfigurationValid()}
                    />
                )}
            </>



            {/* Payment Confirmation Popup */}
            <PaymentPopup
                show={showPaymentPopup}
                onClose={() => setShowPaymentPopup(false)}
                selectedPlan={selectedPlan}
                selectedBilling={selectedBilling}
                plans={plans}
                paymentLoading={paymentLoading}
                paymentSuccess={paymentSuccess}
                onPayment={handlePayment}
                onPaymentClose={handlePaymentClose}
            />

            {/* Configuration Success Dialog */}
            <Dialog
                open={showConfigurationDialog}
                onClose={() => setShowConfigurationDialog(false)}
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
                            href={`https://t.me/${configurationDialogData?.botUsername || 'BeHumanAgainBot'}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ minWidth: 200 }}
                        >
                            @{configurationDialogData?.botUsername || 'BeHumanAgainBot'}
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
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Add the bot to your group:</strong> Click the bot link above and add @{configurationDialogData?.botUsername || 'BeHumanAgainBot'} to your Telegram group as an administrator.
                                </li>
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Grant admin permissions:</strong> Make sure the bot has admin permissions in your group (can delete messages, ban users, etc.).
                                </li>
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Activate the license:</strong> Copy the license key below and send it to your group chat. The bot will automatically detect it and confirm admin permissions.
                                </li>
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Generate user IDs:</strong> Once activated, use the "Generate User IDs" option in the navbar to create unique IDs for your group members.
                                </li>
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Share with members:</strong> Distribute the bot link and unique user IDs to your potential group members.
                                </li>
                                <li style={{ marginBottom: '8px' }}>
                                    <strong>Monitor activity:</strong> The bot will now manage your wellness program according to your configured settings.
                                </li>
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
                                onClick={refreshAdminPermissions}
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
                                        onClick={() => copyToClipboard(configurationDialogData.licenseKey!, 'License Key')}
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
                        onClick={() => setShowConfigurationDialog(false)}
                        sx={{ minWidth: 150 }}
                    >
                        Proceed
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default Dashboard;