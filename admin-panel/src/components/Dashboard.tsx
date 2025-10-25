import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface Slot {
    name: string;
    mandatory: boolean;
    startTime: string;
    endTime: string;
    points: number;
}

const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
    const [eventType, setEventType] = useState<'normal' | 'time-limited'>('normal');
    const [eventName, setEventName] = useState('');
    const [eventDays, setEventDays] = useState('');
    const [passPoints, setPassPoints] = useState('');
    const [slotsPerDay, setSlotsPerDay] = useState('');
    const [slots, setSlots] = useState<Slot[]>([]);
    const [slotErrors, setSlotErrors] = useState<{ totalPoints: boolean; overlaps: boolean }>({ totalPoints: false, overlaps: false });

    // Check authentication on component mount
    useEffect(() => {
        const isLoggedIn = localStorage.getItem('isLoggedIn');
        if (!isLoggedIn || isLoggedIn !== 'true') {
            navigate('/login');
        }
    }, [navigate]);

    const timeToMinutes = (time: string) => {
        if (!time) return 0;
        const [h, m] = time.split(':').map(Number);
        return h * 60 + m;
    };

    const [selectedBilling, setSelectedBilling] = useState<string | null>(null);
    const [paymentCompleted, setPaymentCompleted] = useState(false);
    const [showPaymentPopup, setShowPaymentPopup] = useState(false);
    const [paymentLoading, setPaymentLoading] = useState(false);
    const [paymentSuccess, setPaymentSuccess] = useState(false);
    const [hasActiveSubscription, setHasActiveSubscription] = useState(false);
    const [showSubscriptionPanel, setShowSubscriptionPanel] = useState(false);
    const [subscriptionLoading, setSubscriptionLoading] = useState(true);

    const plans = [
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

    useEffect(() => {
        const num = parseInt(slotsPerDay) || 0;
        setSlots(Array.from({ length: num }, () => ({
            name: '',
            mandatory: false,
            startTime: '',
            endTime: '',
            points: 0,
        })));
    }, [slotsPerDay]);

    const handleSlotChange = (index: number, field: keyof Slot, value: string | number | boolean) => {
        const newSlots = [...slots]; // makes shallow copy of existing slots array so that we dont modify the original state directly
        newSlots[index] = { ...newSlots[index], [field]: value };
        setSlots(newSlots);
    };

    // runs every time a slot's data changes
    useEffect(() => {
        let totalPoints = 0;
        for (const slot of slots) totalPoints += slot.points;

        let overlaps = false;
        for (let i = 0; i < slots.length; i++) {
            for (let j = i + 1; j < slots.length; j++) {
                const start1 = timeToMinutes(slots[i].startTime);
                const end1 = timeToMinutes(slots[i].endTime);
                const start2 = timeToMinutes(slots[j].startTime);
                const end2 = timeToMinutes(slots[j].endTime);
                if (start1 < end2 && end1 > start2) {
                    overlaps = true;
                    break;
                }
            }
            if (overlaps) break;
        }
        setSlotErrors({ totalPoints: totalPoints > 100, overlaps });
    }, [slots]);

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
                        // For debugging: temporarily force subscription to test UI logic
                        // setHasActiveSubscription(true);
                        // setPaymentCompleted(true);
                        // setSelectedPlan('Basic Plan');
                        // setSelectedBilling('monthly');
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

    const getValidity = (months: number) => {
        const start = new Date();
        const end = new Date();
        end.setMonth(end.getMonth() + months);
        return `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;
    };
    const selectedPlanDetails = plans.find(plan => plan.name === selectedPlan)
    return (
        <div>
            {/* Header */}
            <nav className="navbar navbar-expand-lg navbar-light bg-light">
                <div className="container-fluid">
                    <span className="navbar-brand">Admin Panel</span>
                    <div className="d-flex align-items-center">
                        <span className="navbar-text me-3">Welcome, Admin</span>
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
                            onClick={() => {
                                localStorage.clear();
                                navigate('/login');
                            }}
                        >
                            <i className="fas fa-sign-out-alt me-1"></i>
                            Logout
                        </button>
                    </div>
                </div>
            </nav>

            {/* Selected Plan Display */}
            {paymentCompleted && (
                <div className="bg-primary text-white py-3">
                    <div className="container">
                        <div className="row align-items-center">
                            <div className="col-md-8">
                                <h5 className="mb-1">
                                    <i className="bi bi-check-circle-fill me-2"></i>
                                    Active : {subscriptionLoading ? 'Checking...' : (selectedPlan || 'No Plan')}
                                </h5>
                                <p className="mb-0 opacity-75">
                                    {(() => {
                                        const duration = plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.duration;
                                        if (duration === 1) return 'Monthly Subscription';
                                        if (duration === 6) return 'Half yearly Subscriptio';
                                        if (duration === 12) return 'Annual Subscription';
                                        return `${duration}`;
                                    })()}
                                </p>
                            </div>
                            <div className="col-md-4 text-md-end">
                                <span className="badge bg-light text-primary fs-6">
                                    {plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.price}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Content */}
            {(!hasActiveSubscription || showSubscriptionPanel) && (
                <div className="container mt-4">
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
                                            setSelectedPlan(plan.name);
                                            // Auto-select first billing option
                                            setSelectedBilling(plan.billingOptions[0]?.type);
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
                                                            setSelectedPlan(plan.name);
                                                            setSelectedBilling(option.type);
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
                                                                            setSelectedPlan(plan.name);
                                                                            setSelectedBilling(option.type);
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
                                <button className="btn btn-success btn-lg" onClick={() => setShowPaymentPopup(true)}>
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
            )}

            {hasActiveSubscription && !showSubscriptionPanel && (
                <div className="container mt-4">
                    <h3 className="mb-4">Bot Settings</h3>
                    <div className="row">
                        <div className="col-md-4 mb-3">
                            <label htmlFor="eventType" className="form-label">Event Type</label>
                            <select
                                className="form-select"
                                id="eventType"
                                value={eventType}
                                onChange={(e) => setEventType(e.target.value as 'normal' | 'time-limited')}
                            >
                                <option value="normal">Normal</option>
                                <option value="time-limited">Time-Limited</option>
                            </select>
                        </div>
                        <div className="col-md-4 mb-3">
                            <label htmlFor="eventName" className="form-label">Event Name</label>
                            <input
                                type="text"
                                className="form-control"
                                id="eventName"
                                value={eventName}
                                onChange={(e) => setEventName(e.target.value)}
                                placeholder="Enter event name"
                            />
                        </div>
                        <div className="col-md-4 mb-3">
                            <label htmlFor="slotsPerDay" className="form-label">Slots Per Day</label>
                            <input
                                type="number"
                                className="form-control"
                                id="slotsPerDay"
                                value={slotsPerDay}
                                onChange={(e) => setSlotsPerDay(e.target.value)}
                                placeholder="Enter number of slots per day"
                            />
                        </div>
                    </div>

                    {eventType === 'time-limited' && (
                        <div className="row">
                            <div className="col-md-4 mb-3">
                                <label htmlFor="eventDays" className="form-label">Number of Days</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    id="eventDays"
                                    value={eventDays}
                                    onChange={(e) => setEventDays(e.target.value)}
                                    placeholder="Enter number of days"
                                />
                            </div>
                            <div className="col-md-4 mb-3">
                                <label htmlFor="passPoints" className="form-label">Pass Points</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    id="passPoints"
                                    value={passPoints}
                                    onChange={(e) => setPassPoints(e.target.value)}
                                    placeholder="Enter pass points"
                                />
                            </div>
                        </div>
                    )}

                    {slots.length > 0 && (
                        <>
                            <h4 className="mt-4">Configure Slots</h4>
                            {slotErrors.totalPoints && <div className="alert alert-danger mt-3">Total points cannot exceed 100.</div>}
                            {slotErrors.overlaps && <div className="alert alert-danger mt-3">Time slots overlap.</div>}
                            {slots.map((slot, index) => (
                                <div key={index} className="border p-3 mb-3">
                                    <h5>Slot {index + 1}</h5>
                                    <div className="row">
                                        <div className="col-md-1 mb-3">
                                            <label className="form-label">Mandatory</label><br></br>
                                            <input
                                                type="checkbox"
                                                className="form-check-input"
                                                checked={slot.mandatory}
                                                onChange={(e) => handleSlotChange(index, 'mandatory', e.target.checked)}
                                            />
                                        </div>
                                        <div className="col-md-2 mb-3">
                                            <label className="form-label">Slot Name</label>
                                            <input
                                                type="text"
                                                className="form-control"
                                                value={slot.name}
                                                onChange={(e) => handleSlotChange(index, 'name', e.target.value)}
                                            />
                                        </div>
                                        <div className="col-md-2 mb-3">
                                            <label className="form-label">Start Time</label>
                                            <input
                                                type="time"
                                                className="form-control"
                                                value={slot.startTime}
                                                onChange={(e) => handleSlotChange(index, 'startTime', e.target.value)}
                                            />
                                        </div>
                                        <div className="col-md-2 mb-3">
                                            <label className="form-label">End Time</label>
                                            <input
                                                type="time"
                                                className="form-control"
                                                value={slot.endTime}
                                                onChange={(e) => handleSlotChange(index, 'endTime', e.target.value)}
                                            />
                                        </div>
                                        <div className="col-md-2 mb-3">
                                            <label className="form-label">Points</label>
                                            <input
                                                type="number"
                                                className="form-control"
                                                value={slot.points}
                                                onChange={(e) => handleSlotChange(index, 'points', Number(e.target.value))}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            )}

            {/* Payment Confirmation Popup */}
            {showPaymentPopup && (
                <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex={-1}>
                    <div className="modal-dialog modal-dialog-centered">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Confirm Payment</h5>
                            </div>
                            <div className="modal-body">
                                {!paymentLoading && !paymentSuccess && (
                                    <>
                                        <p>You have selected <strong>{selectedPlan}</strong> for <strong>{plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.duration} month</strong>.</p>
                                        <p>Price: <strong>{plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.price}</strong></p>
                                        <div className="alert alert-info">
                                            <small>Click "Proceed to Pay" to complete your payment.</small>
                                        </div>
                                    </>
                                )}

                                {paymentLoading && (
                                    <div className="text-center">
                                        <div className="spinner-border text-primary" role="status">
                                            <span className="visually-hidden">Processing...</span>
                                        </div>
                                        <p className="mt-2">Processing your payment...</p>
                                    </div>
                                )}

                                {paymentSuccess && (
                                    <div className="text-center">
                                        <div className="text-success mb-3">
                                            <i className="bi bi-check-circle-fill fs-1"></i>
                                        </div>
                                        <h5 className="text-success">Payment Successful!</h5>
                                        <p>You have successfully paid for your selected plan.</p>
                                    </div>
                                )}
                            </div>
                            <div className="modal-footer">
                                {!paymentLoading && !paymentSuccess && (
                                    <>
                                        <button type="button" className="btn btn-secondary" onClick={() => setShowPaymentPopup(false)}>
                                            Cancel
                                        </button>
                                        <button type="button" className="btn btn-success" onClick={handlePayment}>
                                            Proceed to Pay
                                        </button>
                                    </>
                                )}

                                {paymentSuccess && (
                                    <button type="button" className="btn btn-primary" onClick={handlePaymentClose}>
                                        Close
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;