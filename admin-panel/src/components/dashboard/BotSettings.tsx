import React from 'react';
import SlotConfiguration from './SlotConfiguration';

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
}

interface BotSettingsProps {
    eventType: 'normal' | 'time-limited';
    eventName: string;
    eventDays: string;
    passPoints: string;
    slotsPerDay: string;
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
    onSlotChange,
    onCurrentSlotIndexChange,
    onCurrentButtonIndexChange,
    onSlotTypeChange,
    onSlotButtonCountChange,
    onSlotButtonIndexChange
}) => {
    return (
        <div className="mt-4 px-3">
            <h3 className="mb-4">Bot Settings</h3>
            <div className="row">
                <div className="col-12 col-md-4 mb-3">
                    <label htmlFor="eventName" className="form-label">Event Name</label>
                    <input
                        type="text"
                        className="form-control"
                        id="eventName"
                        value={eventName}
                        onChange={(e) => onEventNameChange(e.target.value)}
                        placeholder="Enter event name"
                    />
                </div>
                <div className="col-6 col-md-4 mb-3">
                    <label htmlFor="eventType" className="form-label">Event Type</label>
                    <select
                        className="form-select"
                        id="eventType"
                        value={eventType}
                        onChange={(e) => onEventTypeChange(e.target.value as 'normal' | 'time-limited')}
                    >
                        <option value="normal">Normal</option>
                        <option value="time-limited">Time-Limited</option>
                    </select>
                </div>
                <div className="col-6 col-md-4 mb-3">
                    <label htmlFor="slotsPerDay" className="form-label">Slots Per Day</label>
                    <input
                        type="number"
                        className="form-control"
                        id="slotsPerDay"
                        value={slotsPerDay}
                        onChange={(e) => onSlotsPerDayChange(e.target.value)}
                        placeholder="Enter number of slots per day"
                    />
                </div>
            </div>

            {eventType === 'time-limited' && (
                <div className="row">
                    <div className="col-6 col-md-4 mb-3">
                        <label htmlFor="eventDays" className="form-label">Number of Days</label>
                        <input
                            type="number"
                            className="form-control"
                            id="eventDays"
                            value={eventDays}
                            onChange={(e) => onEventDaysChange(e.target.value)}
                            placeholder="Enter number of days"
                        />
                    </div>
                    <div className="col-6 col-md-4 mb-3">
                        <label htmlFor="passPoints" className="form-label">Pass Points</label>
                        <input
                            type="number"
                            className="form-control"
                            id="passPoints"
                            value={passPoints}
                            onChange={(e) => onPassPointsChange(e.target.value)}
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
                </>
            )}
        </div>
    );
};

export default BotSettings;