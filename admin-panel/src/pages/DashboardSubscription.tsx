import React from 'react';
import Subscription from '../components/dashboard/Subscription';
import { useSubscription } from '../hooks/useSubscription';
import PaymentPopup from '../components/dashboard/PaymentPopup';
import { Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { usePayment } from '../hooks/usePayment';

const DashboardSubscription: React.FC = () => {
    const navigate = useNavigate();
    const {
        selectedPlan,
        selectedBilling,
        hasActiveSubscription,
        plans,
        handlePlanSelect,
        setSelectedBilling,
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

    return (
        <Box>
            <Box sx={{ p: 2 }}>
                <Button variant="outlined" onClick={() => navigate('/dashboard')}>← Back to Dashboard</Button>
            </Box>
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

            <PaymentPopup
                show={showPaymentPopup}
                onClose={handlePaymentClose}
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

export default DashboardSubscription;
