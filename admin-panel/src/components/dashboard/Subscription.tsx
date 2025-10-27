import React from 'react';
import {
    Card,
    CardContent,
    Typography,
    Box,
    Chip,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    RadioGroup,
    FormControlLabel,
    Radio,
    Button
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StarIcon from '@mui/icons-material/Star';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import PeopleIcon from '@mui/icons-material/People';

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
        <Box sx={{ mt: 4, px: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Typography variant="h4">
                    {hasActiveSubscription ? 'Manage Your Subscription' : 'Select a Plan'}
                </Typography>
            </Box>

            {/* Plan Selection */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                    {hasActiveSubscription ? 'Choose a Different Plan:' : 'Available Plans:'}
                </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                {plans.map(plan => (
                    <Box key={plan.name} sx={{ flex: '1 1 300px', maxWidth: '400px' }}>
                        <Card
                            sx={{
                                height: '100%',
                                minHeight: 380,
                                cursor: 'pointer',
                                position: 'relative',
                                overflow: 'visible',
                                border: selectedPlan === plan.name ? 2 : 1,
                                borderColor: selectedPlan === plan.name ? 'primary.main' : 'divider',
                                boxShadow: selectedPlan === plan.name ? 4 : 1,
                                background: selectedPlan === plan.name
                                    ? 'linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%)'
                                    : 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                '&:hover': {
                                    boxShadow: 3,
                                    transform: 'translateY(-2px)'
                                }
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
                                <Box
                                    sx={{
                                        position: 'absolute',
                                        top: 0,
                                        right: 0,
                                        bgcolor: hasActiveSubscription && showSubscriptionPanel && selectedPlan === plan.name
                                            ? 'success.main'
                                            : 'primary.main',
                                        color: 'white',
                                        px: 2,
                                        py: 0.5,
                                        borderBottomLeftRadius: 8,
                                        fontSize: '0.75rem',
                                        fontWeight: 'bold',
                                        zIndex: 1
                                    }}
                                >
                                    {hasActiveSubscription && showSubscriptionPanel && selectedPlan === plan.name
                                        ? 'CURRENT PLAN'
                                        : 'SELECTED'
                                    }
                                </Box>
                            )}

                            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', height: '100%' }}>
                                <Box sx={{ textAlign: 'center', mb: 3 }}>
                                    <Typography variant="h5" gutterBottom>
                                        {plan.name}
                                    </Typography>
                                    <Chip
                                        icon={<PeopleIcon />}
                                        label={`Up to ${plan.maxMembers} Members`}
                                        color="primary"
                                        variant="outlined"
                                        sx={{ mb: 2 }}
                                    />
                                </Box>

                                <Box sx={{ mb: 3, flexGrow: 1 }}>
                                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                                        <StarIcon color="warning" sx={{ mr: 1 }} />
                                        Features Included:
                                    </Typography>
                                    <List dense>
                                        {plan.features.map((feature, index) => (
                                            <ListItem key={index} sx={{ px: 0 }}>
                                                <ListItemIcon sx={{ minWidth: 32 }}>
                                                    <CheckCircleIcon color="success" fontSize="small" />
                                                </ListItemIcon>
                                                <ListItemText primary={feature} />
                                            </ListItem>
                                        ))}
                                    </List>
                                </Box>

                                <Box sx={{ mt: 'auto' }}>
                                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                                        <CreditCardIcon color="primary" sx={{ mr: 1 }} />
                                        Choose Billing:
                                    </Typography>
                                    <RadioGroup
                                        value={selectedPlan === plan.name ? selectedBilling : ''}
                                        onChange={(e) => {
                                            onPlanSelect(plan.name);
                                            onBillingSelect(e.target.value);
                                        }}
                                    >
                                        {plan.billingOptions.map((option, index) => (
                                            <Box
                                                key={index}
                                                sx={{
                                                    p: 2,
                                                    border: 2,
                                                    borderColor: selectedPlan === plan.name && selectedBilling === option.type
                                                        ? 'primary.main'
                                                        : 'grey.300',
                                                    borderRadius: 2,
                                                    bgcolor: selectedPlan === plan.name && selectedBilling === option.type
                                                        ? 'primary.light'
                                                        : 'background.paper',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease',
                                                    mb: 1,
                                                    '&:hover': {
                                                        borderColor: 'primary.main',
                                                        bgcolor: 'primary.light'
                                                    }
                                                }}
                                                onClick={() => {
                                                    onPlanSelect(plan.name);
                                                    onBillingSelect(option.type);
                                                }}
                                            >
                                                <FormControlLabel
                                                    value={option.type}
                                                    control={<Radio />}
                                                    label={
                                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                                                            <Box>
                                                                <Typography variant="body1" fontWeight="medium">
                                                                    {option.label}
                                                                </Typography>
                                                                {option.savings && (
                                                                    <Chip
                                                                        label={option.savings}
                                                                        color="success"
                                                                        size="small"
                                                                        variant="outlined"
                                                                        sx={{ mt: 0.5 }}
                                                                    />
                                                                )}
                                                            </Box>
                                                            <Typography variant="h6" color="primary" sx={{ ml: 2 }}>
                                                                {option.price}
                                                            </Typography>
                                                        </Box>
                                                    }
                                                    sx={{ width: '100%', m: 0 }}
                                                />
                                            </Box>
                                        ))}
                                    </RadioGroup>
                                </Box>
                            </CardContent>
                        </Card>
                    </Box>
                ))}
            </Box>

            {selectedPlan && selectedBilling && (
                <Box sx={{ textAlign: 'center', mt: 4 }}>
                    <Button
                        variant="contained"
                        color="success"
                        size="large"
                        onClick={onProceedToPayment}
                    >
                        {hasActiveSubscription && showSubscriptionPanel
                            ? 'Change Plan & Proceed to Payment'
                            : 'Proceed to Payment'
                        }
                    </Button>
                    {hasActiveSubscription && showSubscriptionPanel && (
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Your current plan will be changed after payment confirmation.
                        </Typography>
                    )}
                </Box>
            )}
        </Box>
    );
};

export default Subscription;