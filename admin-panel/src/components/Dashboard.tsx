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
                const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
                const adminUserId = userInfo.id;

                if (!adminUserId) return;

                // TODO: Make group ID dynamic
                const groupId = "";
                const response = await fetch(`http://localhost:8001/api/admin/panel/config?group_id=${groupId}&admin_user_id=${adminUserId}`);
                const result = await response.json();

                if (result.success && result.config) {
                    const config = result.config;

                    // Load all the saved values
                    setEventType(config.event_type || 'normal');
                    setEventName(config.event_name || '');
                    setEventDays(config.event_days?.toString() || '');
                    setPassPoints(config.pass_points?.toString() || '');
                    setSlotsPerDay(config.slots_per_day?.toString() || '');
                    setWelcomeMessage(config.welcome_message || '');
                    setKickResponse(config.kick_response || '');
                    setUndesignatedSlotResponse(config.undesignated_slot_response || '');
                    setLeaderboardTime(config.leaderboard_time || '');
                    setBannedWords(config.banned_words || '');

                    // Load slots if they exist
                    if (config.slots && config.slots.length > 0) {
                        // Transform loaded slots to match the expected format
                        const transformedSlots: Slot[] = config.slots.map((slot: any) => ({
                            name: slot.name || '',
                            compulsory: slot.compulsory || false,
                            startTime: slot.startTime || '',
                            endTime: slot.endTime || '',
                            points: slot.points || 0,
                            type: slot.type || 'media',
                            botResponse: slot.botResponse || '',
                            postResponse: slot.postResponse || '',
                            image: slot.image || '',
                            buttonCount: slot.buttonCount || 0,
                            buttonNames: slot.buttonNames || [],
                            buttonValues: slot.buttonValues || []
                        }));
                        setLoadedSlots(transformedSlots);
                    }
                }
            } catch (error) {
                console.error('Error loading configuration:', error);
            }
        };

        loadConfiguration();
    }, [setEventType, setEventName, setEventDays, setPassPoints, setSlotsPerDay, setWelcomeMessage, setKickResponse, setUndesignatedSlotResponse, setLeaderboardTime, setBannedWords]);

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
                banned_words: bannedWords,
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
                    buttonValues: slot.buttonValues || []
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
                alert('Configuration saved successfully!');
            } else {
                alert(`Failed to save configuration: ${result.message}`);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            alert('Error saving configuration. Please check your connection and try again.');
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
        </Box>
    );
};

export default Dashboard;