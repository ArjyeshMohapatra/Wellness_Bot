import React from 'react';
import Subscription from './dashboard/Subscription';
import PaymentPopup from './dashboard/PaymentPopup';
import BotSettings from './dashboard/BotSettings';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { usePayment } from '../hooks/usePayment';
import { useSlotConfiguration } from '../hooks/useSlotConfiguration';
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
        setHasActiveSubscription
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
        setCurrentSlotIndex,
        setCurrentButtonIndex,
        handleSlotTypeChange,
        handleSlotButtonCountChange,
        handleSlotButtonIndexChange,
        handleSlotChange
    } = useSlotConfiguration();

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
                    onSlotChange={handleSlotChange}
                    onCurrentSlotIndexChange={setCurrentSlotIndex}
                    onCurrentButtonIndexChange={setCurrentButtonIndex}
                    onSlotTypeChange={handleSlotTypeChange}
                    onSlotButtonCountChange={handleSlotButtonCountChange}
                    onSlotButtonIndexChange={handleSlotButtonIndexChange}
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