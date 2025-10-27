import React from 'react';
import Subscription from './dashboard/Subscription';
import PaymentPopup from './dashboard/PaymentPopup';
import BotSettings from './dashboard/BotSettings';
import { useAuth } from '../hooks/useAuth';
import { useSubscription } from '../hooks/useSubscription';
import { usePayment } from '../hooks/usePayment';
import { useSlotConfiguration } from '../hooks/useSlotConfiguration';

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
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
            {/* Header */}
            <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm border-bottom">
                <div className="container-fluid">
                    <span className="navbar-brand fw-bold text-primary">🏥 Wellness Bot Admin</span>
                    <div className="d-flex align-items-center">
                        <span className="navbar-text me-3 text-muted">Welcome, Admin</span>
                        {hasActiveSubscription && (
                            <button
                                className="btn btn-outline-primary btn-sm me-2"
                                onClick={() => setShowSubscriptionPanel(!showSubscriptionPanel)}
                                disabled={subscriptionLoading}
                            >
                                <i className="fas fa-credit-card me-1"></i>
                                {subscriptionLoading ? 'Loading...' : (showSubscriptionPanel ? 'Hide' : 'Manage')} Subscription
                            </button>
                        )}
                        <button
                            className="btn btn-outline-danger btn-sm"
                            onClick={logout}
                        >
                            <i className="fas fa-sign-out-alt me-1"></i>
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

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
        </div>
    );
};

export default Dashboard;