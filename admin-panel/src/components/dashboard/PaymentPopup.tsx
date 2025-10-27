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

interface PaymentPopupProps {
    show: boolean;
    onClose: () => void;
    selectedPlan: string | null;
    selectedBilling: string | null;
    plans: Plan[];
    paymentLoading: boolean;
    paymentSuccess: boolean;
    onPayment: () => void;
    onPaymentClose: () => void;
}

const PaymentPopup: React.FC<PaymentPopupProps> = ({
    show,
    onClose,
    selectedPlan,
    selectedBilling,
    plans,
    paymentLoading,
    paymentSuccess,
    onPayment,
    onPaymentClose
}) => {
    if (!show) return null;

    return (
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
                                <button type="button" className="btn btn-secondary" onClick={onClose}>
                                    Cancel
                                </button>
                                <button type="button" className="btn btn-success" onClick={onPayment}>
                                    Proceed to Pay
                                </button>
                            </>
                        )}

                        {paymentSuccess && (
                            <button type="button" className="btn btn-primary" onClick={onPaymentClose}>
                                Close
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaymentPopup;