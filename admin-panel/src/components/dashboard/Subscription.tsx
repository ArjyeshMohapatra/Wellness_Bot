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

interface SubscriptionProps {
    plans: Plan[];
    selectedPlan: string | null;
    selectedBilling: string | null;
    hasActiveSubscription: boolean;
    showSubscriptionPanel: boolean;
    onPlanSelect: (plan: string) => void;
    onBillingSelect: (billing: string) => void;
    onProceedToPayment: () => void;
}

const Subscription: React.FC<SubscriptionProps> = ({
    plans,
    selectedPlan,
    selectedBilling,
    hasActiveSubscription,
    showSubscriptionPanel,
    onPlanSelect,
    onBillingSelect,
    onProceedToPayment
}) => {
    return (
        <div className="mt-4 px-1">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h3>{hasActiveSubscription ? 'Manage Your Subscription' : 'Select a Plan'}</h3>
            </div>

            {/* Plan Selection */}
            <div className="mb-4">
                <h5 className="text-muted mb-3">
                    {hasActiveSubscription ? 'Choose a Different Plan:' : 'Available Plans:'}
                </h5>
            </div>

            <div className="row g-3">
                {plans.map(plan => (
                    <div key={plan.name} className="col-12 col-md-4 mb-4">
                        <div
                            className={`card h-100 border-0 shadow-sm position-relative overflow-hidden ${selectedPlan === plan.name
                                ? 'shadow-lg border-primary'
                                : 'hover-lift'
                                }`}
                            style={{
                                minHeight: '380px',
                                background: selectedPlan === plan.name
                                    ? 'linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%)'
                                    : 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                cursor: 'pointer'
                            }}
                            onClick={() => {
                                if (!selectedPlan || selectedPlan !== plan.name) {
                                    onPlanSelect(plan.name);
                                    // Auto-select first billing option
                                    onBillingSelect(plan.billingOptions[0]?.type);
                                }
                            }}
                        >
                            {selectedPlan === plan.name && (
                                <div className={`position-absolute top-0 end-0 text-white px-3 py-1 rounded-bottom-start fw-semibold ${hasActiveSubscription && showSubscriptionPanel && selectedPlan === plan.name
                                    ? 'bg-success'
                                    : 'bg-primary'
                                    }`} style={{ fontSize: '0.75rem' }}>
                                    {hasActiveSubscription && showSubscriptionPanel && selectedPlan === plan.name
                                        ? 'CURRENT PLAN'
                                        : 'SELECTED'
                                    }
                                </div>
                            )}

                            <div className="card-body d-flex flex-column p-4">
                                <div className="text-center mb-4">
                                    <h4 className="plan-card-title mb-2">
                                        {plan.name}
                                    </h4>
                                    <div className="d-flex align-items-center justify-content-center mb-3">
                                        <span className="badge bg-primary-subtle text-primary px-3 py-2 rounded-pill fw-semibold">
                                            <i className="fas fa-users me-1"></i>
                                            Up to {plan.maxMembers} Members
                                        </span>
                                    </div>
                                </div>

                                <div className="mb-4 flex-grow-1">
                                    <h6 className="section-header mb-3">
                                        <i className="fas fa-star text-warning me-2"></i>
                                        Features Included:
                                    </h6>
                                    <ul className="list-unstyled mb-0">
                                        {plan.features.map((feature, index) => (
                                            <li key={index} className="mb-2 d-flex align-items-start">
                                                <i className="fas fa-check-circle text-success me-2 mt-1" style={{ fontSize: '0.9rem' }}></i>
                                                <span className="feature-item">
                                                    {feature}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="mt-auto">
                                    <h6 className="section-header mb-3">
                                        <i className="fas fa-credit-card text-primary me-2"></i>
                                        Choose Billing:
                                    </h6>
                                    <div className="d-flex flex-column gap-2">
                                        {plan.billingOptions.map((option, index) => (
                                            <label
                                                key={index}
                                                className={`billing-option-modern p-3 rounded-3 border-2 cursor-pointer transition-all ${selectedPlan === plan.name && selectedBilling === option.type
                                                    ? 'border-primary bg-primary-subtle shadow-sm'
                                                    : 'border-light-subtle bg-white hover-bg-light'
                                                    }`}
                                                htmlFor={`${plan.name}-${option.type}`}
                                                style={{
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease'
                                                }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onPlanSelect(plan.name);
                                                    onBillingSelect(option.type);
                                                }}
                                            >
                                                <div className="d-flex align-items-center justify-content-between">
                                                    <div className="d-flex align-items-center">
                                                        <div className={`radio-custom me-3 ${selectedPlan === plan.name && selectedBilling === option.type
                                                            ? 'active'
                                                            : ''
                                                            }`}>
                                                            <input
                                                                type="radio"
                                                                name={`billing-${plan.name}`}
                                                                id={`${plan.name}-${option.type}`}
                                                                checked={selectedPlan === plan.name && selectedBilling === option.type}
                                                                onChange={() => {
                                                                    onPlanSelect(plan.name);
                                                                    onBillingSelect(option.type);
                                                                }}
                                                                className="d-none"
                                                            />
                                                            <div className="radio-indicator"></div>
                                                        </div>
                                                        <div>
                                                            <div className="billing-label mb-1">
                                                                {option.label}
                                                            </div>
                                                            {option.savings && (
                                                                <div className="badge bg-success-subtle text-success px-2 py-1 rounded-pill savings-badge">
                                                                    {option.savings}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="text-end">
                                                        <div className="billing-price">
                                                            {option.price}
                                                        </div>
                                                    </div>
                                                </div>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {selectedPlan && selectedBilling && (
                <>
                    <div className="text-center mt-4">
                        <button className="btn btn-success btn-lg" onClick={onProceedToPayment}>
                            {hasActiveSubscription && showSubscriptionPanel
                                ? 'Change Plan & Proceed to Payment'
                                : 'Proceed to Payment'
                            }
                        </button>
                        {hasActiveSubscription && showSubscriptionPanel && (
                            <p className="text-muted mt-2">
                                <small>Your current plan will be changed after payment confirmation.</small>
                            </p>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default Subscription;