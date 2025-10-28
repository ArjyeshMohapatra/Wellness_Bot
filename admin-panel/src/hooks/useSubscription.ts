import { useState, useEffect } from 'react';

interface BillingOption {
    type: string;
    label: string;
    price: string;
    duration: number;
    total: number;
    savings?: string;
}

interface Plan {
    name: string;
    basePrice?: number;
    billingOptions: BillingOption[];
    maxMembers: number;
    features: string[];
}

export const useSubscription = () => {
    const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
    const [selectedBilling, setSelectedBilling] = useState<string | null>(null);
    const [paymentCompleted, setPaymentCompleted] = useState(false);
    const [hasActiveSubscription, setHasActiveSubscription] = useState(false);
    const [showSubscriptionPanel, setShowSubscriptionPanel] = useState(false);
    const [subscriptionLoading, setSubscriptionLoading] = useState(true);

    const plans: Plan[] = [
        {
            name: 'Basic Plan',
            basePrice: 300,
            billingOptions: [
                { type: 'monthly', label: 'Pay Monthly', price: '₹300/month', duration: 1, total: 300 },
                { type: 'half-yearly', label: 'Pay Half Yearly', price: '₹1,650 (₹275/month)', duration: 6, total: 1650, savings: 'Save ₹150' },
                { type: 'yearly', label: 'Pay Yearly', price: '₹3,000 (₹250/month)', duration: 12, total: 3300, savings: 'Save ₹600' }
            ],
            maxMembers: 25,
            features: ['Basic wellness tracking']
        },
        {
            name: 'Pro Plan',
            billingOptions: [
                { type: 'half-yearly', label: 'Pay Half Yearly', price: '₹1,800', duration: 6, total: 1800 },
                { type: 'yearly', label: 'Pay Yearly', price: '₹3,200', duration: 12, total: 3200, savings: 'Save ₹400' }
            ],
            maxMembers: 50,
            features: ['Advanced wellness tracking', 'Priority support']
        },
        {
            name: 'Premium Plan',
            basePrice: 3200,
            billingOptions: [
                { type: 'yearly', label: 'Pay Yearly', price: '₹3,600/year', duration: 12, total: 3200 }
            ],
            maxMembers: 100,
            features: ['Premium wellness tracking', '24/7 support']
        }
    ];

    const handlePlanSelect = (plan: string) => {
        setSelectedPlan(plan);
    };

    const getValidity = (months: number) => {
        const start = new Date();
        const end = new Date();
        end.setMonth(end.getMonth() + months);
        return `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
    };

    const getCurrentMaxMembers = () => {
        if (!selectedPlan) return 25; // Default to basic
        const plan = plans.find(p => p.name === selectedPlan);
        return plan ? plan.maxMembers : 25;
    };

    // Check for active subscription on component mount
    useEffect(() => {
        const checkSubscriptionStatus = async () => {
            setSubscriptionLoading(true);
            const userEmail = localStorage.getItem('adminEmail');
            console.log('Checking subscription for email:', userEmail);

            if (userEmail) {
                try {
                    // Always check with database for subscription status
                    const response = await fetch(`http://localhost:8001/api/payment/check-subscription?email=${encodeURIComponent(userEmail)}`);
                    const data = await response.json();
                    console.log('Subscription API response:', data);

                    if (data.hasActiveSubscription) {
                        console.log('Setting active subscription to true');
                        setHasActiveSubscription(true);
                        setPaymentCompleted(true);
                        setSelectedPlan(data.planName);
                        setSelectedBilling(data.billingType);
                    } else {
                        console.log('No active subscription found in API response');
                        console.log('API Response:', data);
                        setHasActiveSubscription(false);
                        setPaymentCompleted(false);
                        setSelectedPlan(null);
                        setSelectedBilling(null);
                    }
                } catch (error) {
                    console.error('Error checking subscription status:', error);
                    // On error, assume no subscription
                    setHasActiveSubscription(false);
                    setPaymentCompleted(false);
                    setSelectedPlan(null);
                    setSelectedBilling(null);
                }
            } else {
                console.log('No user email found in localStorage');
            }
            setSubscriptionLoading(false);
        };

        checkSubscriptionStatus();
    }, []);

    return {
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
        getValidity,
        getCurrentMaxMembers
    };
};
