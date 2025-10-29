import React, { useEffect, useState } from 'react';
import Subscription from './dashboard/Subscription';
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
} from '@mui/material';
import {
    Logout as LogoutIcon,
    CreditCard as CreditCardIcon,
    LocalHospital as HospitalIcon,
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
    const { logout } = useAuth();
    const [loadedSlots, setLoadedSlots] = useState<Slot[]>([]);
    const [configurationSaved, setConfigurationSaved] = useState(false);
    const [botUsername, setBotUsername] = useState('WellnessBot');
    const [hasAdminPermissions, setHasAdminPermissions] = useState(false);
    const [licenseKey, setLicenseKey] = useState<string | null>(null);
    const [generatingLicense, setGeneratingLicense] = useState(false);
    const [generatingUserIds, setGeneratingUserIds] = useState(false);
    const [generatedUserIds, setGeneratedUserIds] = useState<string[]>([]);
    const [showUserIdSection, setShowUserIdSection] = useState(false);
    const {
        selectedPlan,
        selectedBilling,
        paymentCompleted,
        hasActiveSubscription,
        showSubscriptionPanel,
        subscriptionLoading,
        plans,
        handlePlanSelect,
        setSelectedBilling,
        setShowSubscriptionPanel,
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

    // Load saved configuration on component mount
    useEffect(() => {
        const loadConfiguration = async () => {
            try {
                // Load dashboard state from localStorage first
                const savedDashboardState = localStorage.getItem('dashboardState');
                if (savedDashboardState) {
                    const state = JSON.parse(savedDashboardState);
                    setBotUsername(state.botUsername || 'WellnessBot');
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
                    setBotUsername(dbSettings.bot_username || 'WellnessBot');
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
        };

        loadConfiguration();
    }, [setEventType, setEventName, setEventDays, setPassPoints, setSlotsPerDay, setWelcomeMessage, setKickResponse, setUndesignatedSlotResponse, setLeaderboardTime, setBannedWords]);

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
                const dashboardSaveSuccess = await saveDashboardSettings();
                if (!dashboardSaveSuccess) {
                    alert('Configuration saved to bot, but dashboard persistence failed. Settings may not be restored on next login.');
                }

                // Show setup instructions instead of dialog
                setConfigurationSaved(true);
                // Store bot username for the instructions
                if (result.bot_username) {
                    setBotUsername(result.bot_username);
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

    // Publish configuration handler
    const handlePublishConfiguration = async () => {
        try {
            setGeneratingLicense(true);

            // Get current user info
            const adminUserId = localStorage.getItem('userId');

            if (!adminUserId) {
                alert('User not logged in. Please login again.');
                setGeneratingLicense(false);
                return;
            }

            // Call API to generate license key
            const response = await fetch('http://localhost:8001/api/admin/generate-license', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    group_id: null  // Will be assigned when bot joins group
                })
            });

            const result = await response.json();

            if (result.success) {
                setLicenseKey(result.license_key);
                alert(`License key generated successfully: ${result.license_key}`);

                // Save dashboard settings to database with the new license key
                const dashboardSaveSuccess = await saveDashboardSettings(result.license_key);
                if (!dashboardSaveSuccess) {
                    alert('License generated, but dashboard persistence failed. Settings may not be restored on next login.');
                }
            } else {
                alert(`Failed to generate license key: ${result.message}`);
            }
        } catch (error) {
            console.error('Error generating license key:', error);
            alert('Error generating license key. Please check your connection and try again.');
        } finally {
            setGeneratingLicense(false);
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

            // Generate unique user IDs
            const response = await fetch('http://localhost:8001/api/admin/generate-unique-user-ids', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    group_id: groupId,
                    count: getCurrentMaxMembers()
                })
            });

            const result = await response.json();

            if (result.success) {
                setGeneratedUserIds(result.user_ids);
                setShowUserIdSection(true);
                alert(`Successfully generated ${result.user_ids.length} unique user IDs!`);
            } else {
                alert(`Failed to generate user IDs: ${result.message}`);
            }
        } catch (error) {
            console.error('Error generating user IDs:', error);
            alert('Error generating user IDs. Please check your connection and try again.');
        } finally {
            setGeneratingUserIds(false);
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
                            <Button
                                variant="outlined"
                                color="primary"
                                size="small"
                                onClick={() => setShowSubscriptionPanel(!showSubscriptionPanel)}
                                disabled={subscriptionLoading}
                                startIcon={subscriptionLoading ? <CircularProgress size={16} /> : <CreditCardIcon />}
                                sx={{ mr: 1, whiteSpace: 'nowrap' }}
                            >
                                {subscriptionLoading ? 'Loading...' : (showSubscriptionPanel ? 'Hide' : 'Manage')} Subscription
                            </Button>
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
                            <IconButton
                                color="primary"
                                size="small"
                                onClick={() => setShowSubscriptionPanel(!showSubscriptionPanel)}
                                disabled={subscriptionLoading}
                                sx={{ p: 1 }}
                            >
                                {subscriptionLoading ? <CircularProgress size={20} /> : <CreditCardIcon />}
                            </IconButton>
                        )}
                        <IconButton
                            color="error"
                            size="small"
                            onClick={logout}
                            sx={{ p: 1 }}
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
            {hasActiveSubscription && !showSubscriptionPanel && (
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
                                    <Typography variant="body1" sx={{
                                        color: 'info.contrastText',
                                        fontWeight: 'bold',
                                        fontFamily: 'monospace',
                                        mt: 1,
                                        wordBreak: 'break-all'
                                    }}>
                                        {licenseKey}
                                    </Typography>
                                </Box>
                            )}
                        </Box>
                    </Box>
                </Box>
            )}

            {/* Main Content */}
            {(!hasActiveSubscription || showSubscriptionPanel) && (
                <Subscription
                    plans={plans}
                    selectedPlan={selectedPlan}
                    selectedBilling={selectedBilling}
                    hasActiveSubscription={hasActiveSubscription}
                    showSubscriptionPanel={showSubscriptionPanel}
                    onPlanSelect={handlePlanSelect}
                    onBillingSelect={setSelectedBilling}
                    onProceedToPayment={() => setShowPaymentPopup(true)}
                />
            )}

            {hasActiveSubscription && !showSubscriptionPanel && (
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

            {/* Bot Setup Instructions - Show after saving configuration */}
            {configurationSaved && (
                <Box sx={{ mt: 4, mb: 4 }}>
                    <Box sx={{
                        bgcolor: 'success.light',
                        p: 3,
                        borderRadius: 2,
                        mb: 3,
                        border: '2px solid',
                        borderColor: 'success.main'
                    }}>
                        <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: 'success.contrastText' }}>
                            🎉 Configuration Saved Successfully!
                        </Typography>
                        <Typography variant="body1" sx={{ color: 'success.contrastText' }}>
                            Your bot configuration has been saved. Follow the steps below to set up your bot in your Telegram group.
                        </Typography>
                    </Box>

                    <Box sx={{
                        bgcolor: 'background.paper',
                        p: 4,
                        borderRadius: 2,
                        border: '2px solid',
                        borderColor: 'primary.main'
                    }}>
                        <Typography variant="h4" sx={{ mb: 3, color: 'primary.main', fontWeight: 'bold' }}>
                            🚀 Bot Setup Instructions
                        </Typography>

                        <Box sx={{
                            bgcolor: 'grey.100',
                            p: 3,
                            borderRadius: 2,
                            mb: 3,
                            border: '2px solid',
                            borderColor: 'primary.main'
                        }}>
                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                                🔗 Bot Link
                            </Typography>
                            <Button
                                variant="contained"
                                color="primary"
                                size="large"
                                href={`https://t.me/BeHumanAgainBot`}
                                target="_blank"
                                sx={{ fontSize: '1.1rem', py: 1.5, px: 3 }}
                            >
                                Open Bot: @{"BeHumanAgainBot"}
                            </Button>
                        </Box>

                        <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
                            📋 Step-by-Step Setup Guide:
                        </Typography>

                        <Box sx={{ pl: 2 }}>
                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                1️⃣ Start the Bot
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 3, pl: 3 }}>
                                Click the bot link above and click "Start" to begin interacting with the bot.
                            </Typography>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                2️⃣ Add Bot to Your Group
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 3, pl: 3 }}>
                                Go to your Telegram group → Click group name → "Add Members" → Search for "@{botUsername}" → Add the bot.
                            </Typography>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                3️⃣ Make Bot Administrator
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 2, pl: 3 }}>
                                In your group: Group Settings → Administrators → Add Administrator → Select "@{botUsername}"
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 3, pl: 3 }}>
                                Grant these permissions:
                            </Typography>
                            <Box component="ul" sx={{ pl: 6, mb: 3 }}>
                                <Typography component="li" variant="body1" sx={{ mb: 1 }}>✅ Delete messages</Typography>
                                <Typography component="li" variant="body1" sx={{ mb: 1 }}>✅ Ban users</Typography>
                                <Typography component="li" variant="body1" sx={{ mb: 1 }}>✅ Manage chat</Typography>
                                <Typography component="li" variant="body1" sx={{ mb: 1 }}>✅ Post messages</Typography>
                            </Box>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                4️⃣ Wait for Confirmation
                            </Typography>
                            <Typography variant="body1" sx={{ mb: 3, pl: 3 }}>
                                Once the bot detects its admin status, you'll see a green checkmark and a "Publish" button will appear.
                            </Typography>
                        </Box>

                        <Box sx={{
                            bgcolor: 'info.light',
                            p: 3,
                            borderRadius: 1,
                            mt: 3,
                            color: 'info.contrastText'
                        }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                💡 Important: Complete all steps above before proceeding. The bot needs admin permissions to function properly in your group.
                            </Typography>
                        </Box>

                        {/* Admin Permission Status */}
                        <Box sx={{
                            bgcolor: hasAdminPermissions ? 'success.light' : 'warning.light',
                            p: 3,
                            borderRadius: 2,
                            mt: 3,
                            border: '2px solid',
                            borderColor: hasAdminPermissions ? 'success.main' : 'warning.main'
                        }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                {hasAdminPermissions ? (
                                    <Typography variant="h6" sx={{ color: 'success.main', fontWeight: 'bold' }}>
                                        ✅ Admin Permissions Confirmed
                                    </Typography>
                                ) : (
                                    <Typography variant="h6" sx={{ color: 'warning.main', fontWeight: 'bold' }}>
                                        ⏳ Waiting for Admin Setup
                                    </Typography>
                                )}
                            </Box>

                            {!hasAdminPermissions && (
                                <Typography variant="body1" sx={{ mb: 2 }}>
                                    After completing the setup steps above, click the button below to confirm that the bot has been added to your group and granted admin permissions.
                                </Typography>
                            )}

                            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                {!hasAdminPermissions && (
                                    <Button
                                        variant="contained"
                                        color="primary"
                                        onClick={() => setHasAdminPermissions(true)}
                                        sx={{ minWidth: 200 }}
                                    >
                                        Confirm Admin Setup Complete
                                    </Button>
                                )}

                                {hasAdminPermissions && !licenseKey && (
                                    <Button
                                        variant="contained"
                                        color="success"
                                        size="large"
                                        onClick={handlePublishConfiguration}
                                        disabled={generatingLicense}
                                        sx={{ minWidth: 200, py: 1.5 }}
                                    >
                                        {generatingLicense ? 'Generating...' : '🚀 Publish Configuration'}
                                    </Button>
                                )}
                            </Box>
                        </Box>

                        {/* License Key Display */}
                        {licenseKey && (
                            <Box sx={{
                                bgcolor: 'success.light',
                                p: 3,
                                borderRadius: 2,
                                mt: 3,
                                border: '2px solid',
                                borderColor: 'success.main'
                            }}>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'success.main' }}>
                                    🎉 License Key Generated!
                                </Typography>
                                <Typography variant="body1" sx={{ mb: 2 }}>
                                    Your license key has been generated and saved. Copy this key and send it to your bot in the group:
                                </Typography>

                                <Box sx={{
                                    bgcolor: 'grey.100',
                                    p: 2,
                                    borderRadius: 1,
                                    border: '1px solid',
                                    borderColor: 'grey.300',
                                    fontFamily: 'monospace',
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold',
                                    textAlign: 'center',
                                    mb: 2
                                }}>
                                    {licenseKey}
                                </Box>

                                <Typography variant="body2" sx={{ color: 'success.contrastText' }}>
                                    <strong>Next step:</strong> Copy this license key and paste it in your Telegram group. The bot will automatically detect it and activate your configuration for that group.
                                </Typography>

                                {/* Unique User ID Generation Section */}
                                <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1, border: '1px solid', borderColor: 'info.main' }}>
                                    <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'info.contrastText' }}>
                                        🔐 Generate Unique User IDs
                                    </Typography>
                                    <Typography variant="body2" sx={{ mb: 2, color: 'info.contrastText' }}>
                                        Generate unique user IDs for your group members. Each member will need one of these IDs to join your group after completing KYC verification.
                                    </Typography>
                                    <Button
                                        variant="contained"
                                        color="primary"
                                        onClick={handleGenerateUserIds}
                                        disabled={generatingUserIds}
                                        sx={{ minWidth: 200 }}
                                    >
                                        {generatingUserIds ? 'Generating...' : '🎯 Generate User IDs'}
                                    </Button>
                                </Box>
                            </Box>
                        )}

                        {/* Generated User IDs Display */}
                        {showUserIdSection && generatedUserIds.length > 0 && (
                            <Box sx={{
                                bgcolor: 'primary.light',
                                p: 3,
                                borderRadius: 2,
                                mt: 3,
                                border: '2px solid',
                                borderColor: 'primary.main'
                            }}>
                                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.contrastText' }}>
                                    🎉 Unique User IDs Generated!
                                </Typography>
                                <Typography variant="body1" sx={{ mb: 2, color: 'primary.contrastText' }}>
                                    Here are your generated unique user IDs. Share these with your potential group members along with the bot link:
                                </Typography>

                                <Box sx={{
                                    bgcolor: 'grey.100',
                                    p: 2,
                                    borderRadius: 1,
                                    border: '1px solid',
                                    borderColor: 'grey.300',
                                    mb: 2,
                                    maxHeight: '200px',
                                    overflowY: 'auto'
                                }}>
                                    {generatedUserIds.map((userId, index) => (
                                        <Box key={index} sx={{
                                            fontFamily: 'monospace',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            p: 1,
                                            mb: 1,
                                            bgcolor: 'white',
                                            borderRadius: 1,
                                            border: '1px solid',
                                            borderColor: 'grey.200',
                                            textAlign: 'center'
                                        }}>
                                            {userId}
                                        </Box>
                                    ))}
                                </Box>

                                <Typography variant="body2" sx={{ color: 'primary.contrastText', fontWeight: 'bold' }}>
                                    📋 Instructions for members:
                                </Typography>
                                <Typography variant="body2" sx={{ color: 'primary.contrastText', mt: 1 }}>
                                    1. Share the bot link (@{botUsername}) and one unique user ID with each potential member<br />
                                    2. Members will DM the bot and provide their user ID<br />
                                    3. Bot will collect their KYC information (name, DOB, phone, profile pic, age, gender)<br />
                                    4. After verification, bot will provide the group invitation link<br />
                                    5. Members can then join the group freely
                                </Typography>
                            </Box>
                        )}
                    </Box>
                </Box>
            )}
        </Box>
    );
};

export default Dashboard;