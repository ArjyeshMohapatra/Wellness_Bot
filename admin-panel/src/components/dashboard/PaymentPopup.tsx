import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    CircularProgress,
    Alert
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

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
    return (
        <Dialog open={show} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>Confirm Payment</DialogTitle>
            <DialogContent>
                {!paymentLoading && !paymentSuccess && (
                    <Box>
                        <Typography variant="body1" gutterBottom>
                            You have selected <strong>{selectedPlan}</strong> for{' '}
                            <strong>
                                {plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.duration} month
                                {plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.duration !== 1 ? 's' : ''}
                            </strong>.
                        </Typography>
                        <Typography variant="body1" gutterBottom>
                            Price: <strong>{plans.find(p => p.name === selectedPlan)?.billingOptions.find(opt => opt.type === selectedBilling)?.price}</strong>
                        </Typography>
                        <Alert severity="info" sx={{ mt: 2 }}>
                            Click "Proceed to Pay" to complete your payment.
                        </Alert>
                    </Box>
                )}

                {paymentLoading && (
                    <Box textAlign="center" py={3}>
                        <CircularProgress color="primary" />
                        <Typography variant="body1" sx={{ mt: 2 }}>
                            Processing your payment...
                        </Typography>
                    </Box>
                )}

                {paymentSuccess && (
                    <Box textAlign="center" py={3}>
                        <CheckCircleIcon color="success" sx={{ fontSize: 64, mb: 2 }} />
                        <Typography variant="h5" color="success.main" gutterBottom>
                            Payment Successful!
                        </Typography>
                        <Typography variant="body1">
                            You have successfully paid for your selected plan.
                        </Typography>
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                {!paymentLoading && !paymentSuccess && (
                    <>
                        <Button onClick={onClose} color="inherit">
                            Cancel
                        </Button>
                        <Button onClick={onPayment} variant="contained" color="success">
                            Proceed to Pay
                        </Button>
                    </>
                )}

                {paymentSuccess && (
                    <Button onClick={onPaymentClose} variant="contained" color="primary">
                        Close
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default PaymentPopup;