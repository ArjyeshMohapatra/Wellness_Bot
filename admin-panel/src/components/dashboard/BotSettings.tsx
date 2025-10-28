import React, { Suspense, lazy } from 'react';
import {
    Typography,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Box,
    Alert,
} from '@mui/material';

// Lazy load the heavy SlotConfiguration component
const SlotConfiguration = lazy(() => import('./SlotConfiguration'));

interface Slot {
    name: string;
    compulsory: boolean;
    startTime: string;
    endTime: string;
    points: number;
    type: 'media' | 'button';
    buttonCount?: number;
    buttonNames?: string[];
    buttonValues?: number[];
    botResponse?: string;
    postResponse?: string;
    image?: string; // Base64 encoded image or image URL
}

interface BotSettingsProps {
    eventType: 'normal' | 'time-limited';
    eventName: string;
    eventDays: string;
    passPoints: string;
    slotsPerDay: string;
    welcomeMessage: string;
    kickResponse: string;
    undesignatedSlotResponse: string;
    leaderboardTime: string;
    slots: Slot[];
    slotErrors: { totalPoints: boolean; overlaps: boolean };
    currentSlotIndex: number;
    currentButtonIndex: number;
    slotButtonIndices: { [key: number]: number };
    onEventTypeChange: (type: 'normal' | 'time-limited') => void;
    onEventNameChange: (name: string) => void;
    onEventDaysChange: (days: string) => void;
    onPassPointsChange: (points: string) => void;
    onSlotsPerDayChange: (slots: string) => void;
    onWelcomeMessageChange: (message: string) => void;
    onKickResponseChange: (response: string) => void;
    onUndesignatedSlotResponseChange: (response: string) => void;
    onLeaderboardTimeChange: (time: string) => void;
    onSlotChange: (index: number, field: keyof Slot, value: string | number | boolean | string[] | number[]) => void;
    onCurrentSlotIndexChange: (index: number) => void;
    onCurrentButtonIndexChange: (index: number) => void;
    onSlotTypeChange: (index: number, type: 'media' | 'button') => void;
    onSlotButtonCountChange: (index: number, count: number) => void;
    onSlotButtonIndexChange: (index: number, buttonIndex: number) => void;
}

const BotSettings: React.FC<BotSettingsProps> = ({
    eventType,
    eventName,
    eventDays,
    passPoints,
    slotsPerDay,
    welcomeMessage,
    kickResponse,
    undesignatedSlotResponse,
    leaderboardTime,
    slots,
    slotErrors,
    currentSlotIndex,
    currentButtonIndex,
    slotButtonIndices,
    onEventTypeChange,
    onEventNameChange,
    onEventDaysChange,
    onPassPointsChange,
    onSlotsPerDayChange,
    onWelcomeMessageChange,
    onKickResponseChange,
    onUndesignatedSlotResponseChange,
    onLeaderboardTimeChange,
    onSlotChange,
    onCurrentSlotIndexChange,
    onCurrentButtonIndexChange,
    onSlotTypeChange,
    onSlotButtonCountChange,
    onSlotButtonIndexChange
}) => {
    return (
        <Box sx={{ mt: 3, px: 2 }}>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
                Bot Settings
            </Typography>

            {/* Basic Event Configuration */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
                <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(33.333% - 16px)' } }}>
                    <TextField
                        fullWidth
                        label="Event Name"
                        value={eventName}
                        onChange={(e) => onEventNameChange(e.target.value)}
                        placeholder="Enter event name"
                        variant="outlined"
                    />
                </Box>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)' } }}>
                    <FormControl fullWidth>
                        <InputLabel>Event Type</InputLabel>
                        <Select
                            value={eventType}
                            label="Event Type"
                            onChange={(e) => onEventTypeChange(e.target.value as 'normal' | 'time-limited')}
                        >
                            <MenuItem value="normal">Normal</MenuItem>
                            <MenuItem value="time-limited">Time-Limited</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)' } }}>
                    <TextField
                        fullWidth
                        label="Slots Per Day"
                        type="number"
                        value={slotsPerDay}
                        onChange={(e) => onSlotsPerDayChange(e.target.value)}
                        placeholder="Enter number of slots per day"
                        variant="outlined"
                    />
                </Box>
            </Box>

            {/* Bot Response Messages */}
            <Typography variant="h6" sx={{ mb: 1, color: 'text.secondary', fontSize: '1rem' }}>
                Bot Response Messages
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 6px)' } }}>
                    <TextField
                        fullWidth
                        size="small"
                        label="Welcome Message"
                        multiline
                        rows={2}
                        value={welcomeMessage}
                        onChange={(e) => onWelcomeMessageChange(e.target.value)}
                        placeholder="Welcome message"
                        variant="outlined"
                        sx={{ '& .MuiInputBase-root': { fontSize: '0.875rem' } }}
                    />
                </Box>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 6px)' } }}>
                    <TextField
                        fullWidth
                        size="small"
                        label="Kick Response"
                        multiline
                        rows={2}
                        value={kickResponse}
                        onChange={(e) => onKickResponseChange(e.target.value)}
                        placeholder="Kick response"
                        variant="outlined"
                        sx={{ '& .MuiInputBase-root': { fontSize: '0.875rem' } }}
                    />
                </Box>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 6px)' } }}>
                    <TextField
                        fullWidth
                        size="small"
                        label="Undesignated Response"
                        multiline
                        rows={2}
                        value={undesignatedSlotResponse}
                        onChange={(e) => onUndesignatedSlotResponseChange(e.target.value)}
                        placeholder="Undesignated response"
                        variant="outlined"
                        sx={{ '& .MuiInputBase-root': { fontSize: '0.875rem' } }}
                    />
                </Box>
                <Box sx={{ flex: { xs: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 6px)' } }}>
                    <TextField
                        fullWidth
                        size="small"
                        label="Leaderboard Time"
                        type="time"
                        value={leaderboardTime}
                        onChange={(e) => onLeaderboardTimeChange(e.target.value)}
                        variant="outlined"
                        InputLabelProps={{ shrink: true }}
                        sx={{ '& .MuiInputBase-root': { fontSize: '0.875rem' } }}
                    />
                </Box>
            </Box>

            {eventType === 'time-limited' && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
                    <Box sx={{ flex: { xs: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)' } }}>
                        <TextField
                            fullWidth
                            label="Number of Days"
                            type="number"
                            value={eventDays}
                            onChange={(e) => onEventDaysChange(e.target.value)}
                            placeholder="Enter number of days"
                            variant="outlined"
                        />
                    </Box>
                    <Box sx={{ flex: { xs: '1 1 calc(50% - 12px)', md: '1 1 calc(33.333% - 16px)' } }}>
                        <TextField
                            fullWidth
                            label="Pass Points"
                            type="number"
                            value={passPoints}
                            onChange={(e) => onPassPointsChange(e.target.value)}
                            placeholder="Enter pass points"
                            variant="outlined"
                        />
                    </Box>
                </Box>
            )}

            {slots.length > 0 && (
                <>
                    <Typography variant="h5" sx={{ mt: 3, mb: 2 }}>
                        Configure Slots
                    </Typography>
                    {slotErrors.totalPoints && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            Total points cannot exceed 100.
                        </Alert>
                    )}
                    {slotErrors.overlaps && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            Time slots overlap.
                        </Alert>
                    )}

                    <Suspense fallback={
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                            <Typography>Loading slot configuration...</Typography>
                        </Box>
                    }>
                        <SlotConfiguration
                            slots={slots}
                            slotButtonIndices={slotButtonIndices}
                            currentSlotIndex={currentSlotIndex}
                            currentButtonIndex={currentButtonIndex}
                            onSlotChange={onSlotChange}
                            onSlotTypeChange={onSlotTypeChange}
                            onSlotButtonCountChange={onSlotButtonCountChange}
                            onSlotButtonIndexChange={onSlotButtonIndexChange}
                            onCurrentSlotIndexChange={onCurrentSlotIndexChange}
                            onCurrentButtonIndexChange={onCurrentButtonIndexChange}
                        />
                    </Suspense>
                </>
            )}
        </Box>
    );
};

export default BotSettings;