import React from 'react';

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

interface SubscriptionStatusProps {
    paymentCompleted: boolean;
    subscriptionLoading: boolean;
    selectedPlan: string | null;
    selectedBilling: string | null;
    plans: Plan[];
}

const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({
    paymentCompleted,
    subscriptionLoading,
    selectedPlan,
    selectedBilling,
    plans
}) => {
    if (!paymentCompleted) return null;

    return (
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
    );
};

export default SubscriptionStatus;