import React from 'react';

interface EventConfigProps {
    eventType: 'normal' | 'time-limited';
    eventName: string;
    eventDays: string;
    passPoints: string;
    slotsPerDay: string;
    onEventTypeChange: (type: 'normal' | 'time-limited') => void;
    onEventNameChange: (name: string) => void;
    onEventDaysChange: (days: string) => void;
    onPassPointsChange: (points: string) => void;
    onSlotsPerDayChange: (slots: string) => void;
}

const EventConfig: React.FC<EventConfigProps> = ({
    eventType,
    eventName,
    eventDays,
    passPoints,
    slotsPerDay,
    onEventTypeChange,
    onEventNameChange,
    onEventDaysChange,
    onPassPointsChange,
    onSlotsPerDayChange
}) => {
    return (
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

            {eventType === 'time-limited' && (
                <>
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
                </>
            )}
        </div>
    );
};

export default EventConfig;