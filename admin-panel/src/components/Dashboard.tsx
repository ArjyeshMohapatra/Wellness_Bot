import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Slot {
    name: string;
    mandatory: boolean;
    startTime: string;
    endTime: string;
    points: number;
}

const Dashboard: React.FC = () => {
    const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
    const [eventType, setEventType] = useState<'normal' | 'time-limited'>('normal');
    const [eventName, setEventName] = useState('');
    const [eventDays, setEventDays] = useState('');
    const [passPoints, setPassPoints] = useState('');
    const [slotsPerDay, setSlotsPerDay] = useState('');
    const [slots, setSlots] = useState<Slot[]>([]);
    const [slotErrors, setSlotErrors] = useState<{ totalPoints: boolean; overlaps: boolean }>({ totalPoints: false, overlaps: false });

    const timeToMinutes = (time: string) => {
        if (!time) return 0;
        const [h, m] = time.split(':').map(Number);
        return h * 60 + m;
    };

    const [selectedBilling, setSelectedBilling] = useState<string | null>(null);
    const [paymentCompleted, setPaymentCompleted] = useState(false);

    const plans = [
        {
            name: 'Monthly Plan',
            basePrice: 300,
            billingOptions: [
                { type: 'monthly', label: 'Pay Monthly', price: '₹300/month', duration: 1, total: 300 },
                { type: '6monthly', label: 'Pay for 6 Months', price: '₹1,650 (₹275/month)', duration: 6, total: 1650, savings: 'Save ₹150' },
                { type: 'yearly', label: 'Pay Yearly', price: '₹3,000 (₹250/month)', duration: 12, total: 3300, savings: 'Save ₹600' }
            ],
            maxMembers: 25,
            features: ['Basic wellness tracking']
        },
        {
            name: '6-Monthly Plan',
            billingOptions: [
                { type: '6monthly', label: 'Pay for 6 Months', price: '₹1,800', duration: 6, total: 1800 },
                { type: 'yearly', label: 'Pay for 12 Months', price: '₹3,200', duration: 12, total: 3200, savings: 'Save ₹400' }
            ],
            maxMembers: 50,
            features: ['Advanced wellness tracking', 'Priority support']
        },
        {
            name: 'Yearly Plan',
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

    // runs every time slotsPerDay filed's value changes
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
                    <div className="d-flex">
                        <span className="navbar-text me-3">Welcome, Admin</span>
                        {/* <Link to="/developer" className="btn btn-outline-primary btn-sm">Developer View</Link> */}
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <div className="container mt-4">
                <h3>Select a Plan</h3>
                <div className="row">
                    {plans.map(plan => (
                        <div key={plan.name} className="col-md-4 mb-4">
                            <div className={`card h-100 ${selectedPlan === plan.name ? 'border-primary shadow' : ''}`}>
                                <div className="card-body d-flex flex-column">
                                    <h5 className="card-title fw-bold">{plan.name}</h5>
                                    <p className="text-muted small mb-3">Max Members: {plan.maxMembers}</p>

                                    <div className="mb-3">
                                        <strong className="text-muted small">Features:</strong>
                                        <ul className="list-unstyled small mt-1">
                                            {plan.features.map((feature, index) => (
                                                <li key={index}>✓ {feature}</li>
                                            ))}
                                        </ul>
                                    </div>

                                    <div className="mb-3">
                                        <strong className="text-muted small">Billing Options:</strong>
                                        <div className="mt-2">
                                            {plan.billingOptions.map((option, index) => (
                                                <div key={index} className="form-check mb-2">
                                                    <input
                                                        className="form-check-input"
                                                        type="radio"
                                                        name={`billing-${plan.name}`}
                                                        id={`${plan.name}-${option.type}`}
                                                        checked={selectedPlan === plan.name && selectedBilling === option.type}
                                                        onChange={() => {
                                                            setSelectedPlan(plan.name);
                                                            setSelectedBilling(option.type);
                                                        }}
                                                    />
                                                    <label className="form-check-label small" htmlFor={`${plan.name}-${option.type}`}>
                                                        <div>
                                                            <strong>{option.label}</strong>
                                                            <br />
                                                            <span className="text-primary">{option.price}</span>
                                                            {option.savings && (
                                                                <span className="text-success ms-2">({option.savings})</span>
                                                            )}
                                                        </div>
                                                    </label>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="mt-auto">
                                        {selectedPlan === plan.name && selectedBilling && (
                                            <div className="alert alert-success py-2 small">
                                                <strong>Selected:</strong> {plan.billingOptions.find(opt => opt.type === selectedBilling)?.label}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {selectedPlan && selectedBilling && (
                    <>
                        <div className="text-center mt-4">
                            <button className="btn btn-success btn-lg" onClick={() => setPaymentCompleted(true)}>
                                Proceed to Payment
                            </button>
                        </div>
                    </>
                )}

                {paymentCompleted && (
                    <>
                        <h3 className="mt-5">Bot Settings</h3>
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
                    </>
                )}
            </div>
        </div>
    );
};

export default Dashboard;