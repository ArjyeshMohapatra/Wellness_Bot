import React, { useEffect, useState } from 'react';
import { Box, Snackbar, Alert, Typography, Button, Dialog, DialogTitle, DialogContent, TextField, DialogActions } from '@mui/material';
import PaymentPopup from './dashboard/PaymentPopup';
import BotSettings from './dashboard/BotSettings';
import Subscription from './dashboard/Subscription';
import Header from './dashboard/Header';
import SubscriptionStatus from './dashboard/SubscriptionStatus';
import BotInfo from './dashboard/BotInfo';
import ConfigurationSuccessDialog from './dashboard/ConfigurationSuccessDialog';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { usePayment } from '../hooks/usePayment';
import { useSlotConfiguration } from '../hooks/useSlotConfiguration';
import { useDashboardState } from '../hooks/useDashboard';

const Dashboard: React.FC = () => {
    const { logout } = useAuth();
    const [shownLicenseKeys, setShownLicenseKeys] = useState<Set<number>>(new Set());
    const [showSaveNotification, setShowSaveNotification] = useState(false);
    const [showAddEventDialog, setShowAddEventDialog] = useState(false);
    const [newEventName, setNewEventName] = useState('');

    // Use the updated dashboard state hook for events
    const {
        events,
        currentEvent,
        showConfigurationDialog,
        configurationDialogData,
        loadedSlots,
        botUsername,
        hasAdminPermissions,
        licenseKey,
        setShowConfigurationDialog,
        setConfigurationDialogData,
        setLoadedSlots,
        setBotUsername,
        setLicenseKey,
        selectEvent,
        addEvent,
        refreshAdminPermissions,
        // Expose bot settings for sync effect
        botSettings,
    } = useDashboardState();

    const {
        selectedPlan,
        selectedBilling,
        paymentCompleted,
        hasActiveSubscription,
        subscriptionLoading,
        plans,
        setPaymentCompleted,
        setHasActiveSubscription,
        getCurrentMaxMembers,
        handlePlanSelect,
        setSelectedBilling
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

    // Save selectedGroupId to localStorage whenever it changes - removed for single group

    // Sync settings from hook with slot configuration
    useEffect(() => {
        if (botSettings) {
            setEventType(botSettings.event_type || 'normal');
            setEventName(botSettings.event_name || '');
            setEventDays(String(botSettings.event_days || ''));
            setPassPoints(String(botSettings.pass_points || ''));
            setSlotsPerDay(String(botSettings.slots_per_day || ''));
            setWelcomeMessage(botSettings.welcome_message || '');
            setKickResponse(botSettings.kick_response || '');
            setUndesignatedSlotResponse(botSettings.undesignated_slot_response || '');
            setLeaderboardTime(botSettings.leaderboard_time || '');
            setBannedWords(Array.isArray(botSettings.banned_words) ? botSettings.banned_words : (botSettings.banned_words ? (botSettings.banned_words as string).split(', ').filter((w: string) => w.trim()) : []));

            // This will be picked up by useSlotConfiguration via its initialSlots prop
            setLoadedSlots(botSettings.loaded_slots || []);
        }
    }, [botSettings, setEventType, setEventName, setEventDays, setPassPoints, setSlotsPerDay, setWelcomeMessage, setKickResponse, setUndesignatedSlotResponse, setLeaderboardTime, setBannedWords, setLoadedSlots]);

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
            // Check if this is the first save (no license key loaded from DB)
            const isFirstSave = !licenseKey;
            // Get current user info from localStorage (same way as payment system)
            const adminUserId = localStorage.getItem('userId');
            console.log('handleSaveConfiguration: adminUserId from localStorage:', adminUserId);

            if (!adminUserId) {
                alert('User not logged in. Please login again.');
                return;
            }

            const parsedAdminUserId = parseInt(adminUserId);
            console.log('handleSaveConfiguration: parsed adminUserId:', parsedAdminUserId);

            if (isNaN(parsedAdminUserId)) {
                alert('Invalid user ID. Please login again.');
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
            const response = await fetch('http://localhost:8001/api/admin/bot/settings/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    event_id: currentEvent?.event_id,
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

                if ((isFirstSave || !currentEvent || !shownLicenseKeys.has(currentEvent.event_id))) {
                    // FIRST SAVE FOR THIS EVENT: Show the big dialog with license key
                    setConfigurationDialogData({
                        botUsername: result.bot_username || botUsername,
                        licenseKey: result.license_key
                    });
                    setShowConfigurationDialog(true);
                    // Mark this event's license as shown
                    if (currentEvent) {
                        setShownLicenseKeys(prev => new Set([...prev, currentEvent.event_id]));
                    }
                } else {
                    // SUBSEQUENT SAVES: Show the simple "Saved!" notification
                    setShowSaveNotification(true);
                }

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
            console.log('saveDashboardSettings: adminUserId from localStorage:', adminUserId);
            if (!adminUserId) {
                console.error('No adminUserId found in localStorage');
                return false;
            }

            const parsedAdminUserId = parseInt(adminUserId);
            console.log('saveDashboardSettings: parsed adminUserId:', parsedAdminUserId);
            if (isNaN(parsedAdminUserId)) {
                console.error('Invalid adminUserId');
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
                    admin_user_id: parsedAdminUserId,
                    group_id: 0,
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

    // Handle add event
    const handleAddEvent = async () => {
        if (!newEventName.trim()) return;
        const success = await addEvent(newEventName.trim());
        if (success) {
            setNewEventName('');
            setShowAddEventDialog(false);
        }
    };

    return (
        <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8fafc 0%, #e0f2fe 25%, #e8eaf6 100%)' }}>
            <Header
                hasActiveSubscription={hasActiveSubscription}
                subscriptionLoading={subscriptionLoading}
                onLogout={logout}
            />

            <SubscriptionStatus
                paymentCompleted={paymentCompleted}
                subscriptionLoading={subscriptionLoading}
                selectedPlan={selectedPlan}
                selectedBilling={selectedBilling}
                plans={plans}
            />

            <BotInfo
                hasActiveSubscription={hasActiveSubscription}
                licenseKey={licenseKey}
                onCopyToClipboard={copyToClipboard}
            />

            {/* Main Content */}
            <>
                {!hasActiveSubscription && (
                    <Subscription
                        plans={plans}
                        selectedPlan={selectedPlan}
                        selectedBilling={selectedBilling}
                        hasActiveSubscription={hasActiveSubscription}
                        showSubscriptionPanel={true}
                        onPlanSelect={handlePlanSelect}
                        onBillingSelect={setSelectedBilling}
                        onProceedToPayment={() => setShowPaymentPopup(true)}
                    />
                )}
                {hasActiveSubscription && (
                    <>
                        {events.length === 0 ? (
                            <Box sx={{ textAlign: 'center', mt: 4 }}>
                                <Typography variant="h5" sx={{ mb: 2 }}>No events added yet</Typography>
                                <Button variant="contained" onClick={() => setShowAddEventDialog(true)}>
                                    Add Events
                                </Button>
                            </Box>
                        ) : (
                            <>
                                {/* Event selector */}
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="h6">Select Event:</Typography>
                                    {events.map(event => (
                                        <Box key={event.event_id} sx={{ mb: 2 }}>
                                            <Button
                                                variant={currentEvent?.event_id === event.event_id ? "contained" : "outlined"}
                                                onClick={() => selectEvent(event)}
                                                sx={{ mr: 1, mb: 1 }}
                                            >
                                                {event.event_name}
                                            </Button>
                                            {event.groups && event.groups.length > 0 && (
                                                <Box sx={{ ml: 2, mt: 1 }}>
                                                    <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>
                                                        Groups: {event.groups.map(group =>
                                                            `${group.group_name || `Group ${group.group_id}`}${group.is_active ? '' : ' (inactive)'}`
                                                        ).join(', ')}
                                                    </Typography>
                                                </Box>
                                            )}
                                        </Box>
                                    ))}
                                    <Button variant="outlined" onClick={() => setShowAddEventDialog(true)}>
                                        + Add Event
                                    </Button>
                                </Box>

                                {currentEvent && (
                                    <BotSettings
                                        groupId={0}
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
                        )}
                    </>
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
            <ConfigurationSuccessDialog
                open={showConfigurationDialog}
                onClose={() => setShowConfigurationDialog(false)}
                configurationDialogData={configurationDialogData}
                hasAdminPermissions={hasAdminPermissions}
                onRefreshAdminPermissions={refreshAdminPermissions}
                onCopyToClipboard={copyToClipboard}
            />

            <Snackbar
                open={showSaveNotification}
                autoHideDuration={4000}
                onClose={() => setShowSaveNotification(false)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    onClose={() => setShowSaveNotification(false)}
                    severity="success"
                    variant="filled"
                    sx={{ width: '100%' }}
                >
                    Settings saved successfully!
                </Alert>
            </Snackbar>

            {/* Add Event Dialog */}
            <Dialog open={showAddEventDialog} onClose={() => setShowAddEventDialog(false)}>
                <DialogTitle>Add New Event</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Event Name"
                        fullWidth
                        variant="standard"
                        value={newEventName}
                        onChange={(e) => setNewEventName(e.target.value)}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowAddEventDialog(false)}>Cancel</Button>
                    <Button onClick={handleAddEvent}>Add</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default Dashboard;