import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface Plan {
    name: string;
    basePrice?: number;
    billingOptions: {
        type: string;
        label: string;
        price: string;
        duration: number;
        total: number;
        savings?: string;
    }[];
    maxMembers: number;
    features: string[];
}

interface UsePaymentProps {
    plans: Plan[];
    selectedPlan: string | null;
    selectedBilling: string | null;
    setPaymentCompleted: (completed: boolean) => void;
    setHasActiveSubscription: (has: boolean) => void;
}

export const usePayment = ({
    plans,
    selectedPlan,
    selectedBilling,
    setPaymentCompleted,
    setHasActiveSubscription
}: UsePaymentProps) => {
    const navigate = useNavigate();
    const [paymentLoading, setPaymentLoading] = useState(false);
    const [paymentSuccess, setPaymentSuccess] = useState(false);
    const [showPaymentPopup, setShowPaymentPopup] = useState(false);

    const handlePayment = async () => {
        setPaymentLoading(true);
        try {
            // Get user ID from localStorage (assuming it's stored during login)
            const userEmail = localStorage.getItem('adminEmail');
            const userId = localStorage.getItem('userId');

            console.log('Payment attempt - userEmail:', userEmail, 'userId:', userId);

            // Generate transaction ID with user-specific information
            const userIdentifier = userEmail ? userEmail.split('@')[0] : 'unknown';
            const transactionId = `TXN_${userIdentifier}_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

            // Get plan details
            const selectedPlanData = plans.find(p => p.name === selectedPlan);
            const selectedBillingData = selectedPlanData?.billingOptions.find(opt => opt.type === selectedBilling);

            console.log('Payment details:', {
                userEmail,
                userId,
                selectedPlan,
                selectedBilling,
                selectedPlanData: !!selectedPlanData,
                selectedBillingData: !!selectedBillingData
            });

            if (!userEmail || !userId || !selectedPlanData || !selectedBillingData) {
                const missing = [];
                if (!userEmail) missing.push('userEmail');
                if (!userId) missing.push('userId');
                if (!selectedPlanData) missing.push('selectedPlanData');
                if (!selectedBillingData) missing.push('selectedBillingData');
                console.error('Missing payment information:', missing);
                alert(`Payment failed: Missing ${missing.join(', ')}. Please make sure you're logged in and have selected a plan.`);
                setPaymentLoading(false);
                return;
            }

            // Save transaction to database
            const response = await fetch('http://localhost:8001/api/payment/transaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transaction_id: transactionId,
                    user_id: parseInt(userId),
                    plan_name: selectedPlan,
                    billing_type: selectedBilling,
                    duration_months: selectedBillingData.duration,
                    amount: selectedBillingData.total
                }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                console.log('Payment successful:', data);
                setPaymentLoading(false);
                setPaymentSuccess(true);
            } else {
                console.error('Payment API error:', data.message);
                if (data.message && data.message.includes('User not found')) {
                    alert('Your session has expired. Please login again.');
                    localStorage.clear();
                    navigate('/login');
                    return;
                }
                throw new Error(data.message || 'Payment failed');
            }
        } catch (error) {
            console.error('Payment error:', error);
            setPaymentLoading(false);
            alert('Payment failed. Please try again.');
        }
    };

    const handlePaymentClose = () => {
        setShowPaymentPopup(false);
        setPaymentSuccess(false);
        setPaymentCompleted(true);
        setHasActiveSubscription(true);
    };

    return {
        paymentLoading,
        paymentSuccess,
        showPaymentPopup,
        setShowPaymentPopup,
        handlePayment,
        handlePaymentClose
    };
};