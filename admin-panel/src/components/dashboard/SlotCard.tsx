import React from 'react';

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

interface SlotCardProps {
    slots: Slot[];
    currentSlotIndex: number;
    currentButtonIndex: number;
    onSlotChange: (index: number, field: keyof Slot, value: string | number | boolean | string[] | number[]) => void;
    onCurrentSlotIndexChange: (index: number) => void;
    onCurrentButtonIndexChange: (index: number) => void;
}

const SlotCard: React.FC<SlotCardProps> = ({
    slots,
    currentSlotIndex,
    currentButtonIndex,
    onSlotChange,
    onCurrentSlotIndexChange,
    onCurrentButtonIndexChange
}) => {
    return (
        <div className="d-md-none mt-3">
            <div className="col-12 col-md-8 col-lg-6">
                <div className="card border-0 shadow-sm">
                    <div className="card-header bg-light d-flex justify-content-between align-items-center">
                        <div className="d-flex align-items-center">
                            <h6 className="card-title mb-0 me-2">Slot {currentSlotIndex + 1}</h6>
                            <span className={`badge ${slots[currentSlotIndex]?.type === 'media' ? 'bg-info' : 'bg-warning'}`}>
                                {slots[currentSlotIndex]?.type === 'media' ? '📷 Media' : '🔘 Button'}
                            </span>
                        </div>
                        <div className="form-check mb-0">
                            <input
                                type="checkbox"
                                className="form-check-input"
                                id={`compulsory-${currentSlotIndex}`}
                                checked={slots[currentSlotIndex]?.compulsory || false}
                                onChange={(e) => onSlotChange(currentSlotIndex, 'compulsory', e.target.checked)}
                            />
                            <label className="form-check-label" htmlFor={`compulsory-${currentSlotIndex}`}>
                                Compulsory
                            </label>
                        </div>
                    </div>
                    <div className="card-body">
                        <div className="d-flex gap-2 mb-2">
                            <div className="flex-fill">
                                <label htmlFor={`name-${currentSlotIndex}`} className="form-label fw-bold">Slot Name</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    id={`name-${currentSlotIndex}`}
                                    value={slots[currentSlotIndex]?.name || ''}
                                    onChange={(e) => onSlotChange(currentSlotIndex, 'name', e.target.value)}
                                    placeholder="Enter slot name"
                                />
                            </div>

                            {/* Slot Type Selection */}
                            <div className="flex-fill">
                                <label htmlFor={`type-${currentSlotIndex}`} className="form-label fw-bold">Slot Type</label>
                                <select
                                    className="form-select"
                                    id={`type-${currentSlotIndex}`}
                                    value={slots[currentSlotIndex]?.type || 'media'}
                                    onChange={(e) => onSlotChange(currentSlotIndex, 'type', e.target.value)}
                                >
                                    <option value="media">Media</option>
                                    <option value="button">Button</option>
                                </select>
                            </div>
                        </div>

                        {/* Button Configuration - Only show when type is 'button' */}
                        {slots[currentSlotIndex]?.type === 'button' && (
                            <div className="d-flex gap-2 mb-2">
                                <div className="flex-fill">
                                    <label htmlFor={`buttonCount-${currentSlotIndex}`} className="form-label fw-bold">Number of Buttons</label>
                                    <input
                                        type="number"
                                        className="form-control"
                                        id={`buttonCount-${currentSlotIndex}`}
                                        value={slots[currentSlotIndex]?.buttonCount || 2}
                                        onChange={(e) => onSlotChange(currentSlotIndex, 'buttonCount', Number(e.target.value))}
                                        min="1"
                                        max="10"
                                        placeholder="Enter number of buttons"
                                    />
                                </div>

                                {/* Button Configuration - Name and Value with navigation */}
                                <div className="flex-fill">
                                    <label className="form-label fw-bold">Button Configuration</label>
                                    <div className="d-flex align-items-center gap-2 mb-2">
                                        <button
                                            type="button"
                                            className="btn btn-outline-secondary btn-sm"
                                            onClick={() => {
                                                const maxIndex = (slots[currentSlotIndex]?.buttonCount || 2) - 1;
                                                onCurrentButtonIndexChange(currentButtonIndex > 0 ? currentButtonIndex - 1 : maxIndex);
                                            }}
                                            disabled={(slots[currentSlotIndex]?.buttonCount || 2) <= 1}
                                        >
                                            ←
                                        </button>
                                        <div className="flex-grow-1 d-flex gap-1">
                                            <input
                                                type="text"
                                                className="form-control"
                                                placeholder={`Button ${currentButtonIndex + 1} name`}
                                                value={slots[currentSlotIndex]?.buttonNames?.[currentButtonIndex] ?? `Button ${currentButtonIndex + 1}`}
                                                onChange={(e) => {
                                                    const newNames = [...(slots[currentSlotIndex]?.buttonNames || [])];
                                                    newNames[currentButtonIndex] = e.target.value;
                                                    onSlotChange(currentSlotIndex, 'buttonNames', newNames);
                                                }}
                                            />
                                            <input
                                                type="number"
                                                className="form-control flex-shrink-0"
                                                placeholder="Value"
                                                value={slots[currentSlotIndex]?.buttonValues?.[currentButtonIndex] ?? 0}
                                                onChange={(e) => {
                                                    const newValues = [...(slots[currentSlotIndex]?.buttonValues || [])];
                                                    newValues[currentButtonIndex] = Number(e.target.value) || 0;
                                                    onSlotChange(currentSlotIndex, 'buttonValues', newValues);
                                                }}
                                                min="0"
                                            />
                                        </div>
                                        <button
                                            type="button"
                                            className="btn btn-outline-secondary btn-sm"
                                            onClick={() => {
                                                const maxIndex = (slots[currentSlotIndex]?.buttonCount || 2) - 1;
                                                onCurrentButtonIndexChange(currentButtonIndex < maxIndex ? currentButtonIndex + 1 : 0);
                                            }}
                                            disabled={(slots[currentSlotIndex]?.buttonCount || 2) <= 1}
                                        >
                                            →
                                        </button>
                                    </div>
                                    <div className="text-center">
                                        <small className="text-muted">
                                            Button {currentButtonIndex + 1} of {slots[currentSlotIndex]?.buttonCount || 2}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div className="row g-2">
                            <div className="col-6">
                                <label htmlFor={`start-${currentSlotIndex}`} className="form-label fw-bold">Start Time</label>
                                <input
                                    type="time"
                                    className="form-control"
                                    id={`start-${currentSlotIndex}`}
                                    value={slots[currentSlotIndex]?.startTime || ''}
                                    onChange={(e) => onSlotChange(currentSlotIndex, 'startTime', e.target.value)}
                                />
                            </div>
                            <div className="col-6">
                                <label htmlFor={`end-${currentSlotIndex}`} className="form-label fw-bold">End Time</label>
                                <input
                                    type="time"
                                    className="form-control"
                                    id={`end-${currentSlotIndex}`}
                                    value={slots[currentSlotIndex]?.endTime || ''}
                                    onChange={(e) => onSlotChange(currentSlotIndex, 'endTime', e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="mt-2">
                            <label htmlFor={`points-${currentSlotIndex}`} className="form-label fw-bold">Points</label>
                            <input
                                type="number"
                                className="form-control"
                                id={`points-${currentSlotIndex}`}
                                value={slots[currentSlotIndex]?.points || 0}
                                onChange={(e) => onSlotChange(currentSlotIndex, 'points', Number(e.target.value))}
                                min="0"
                                max="100"
                            />
                        </div>
                        <div className="mt-2">
                            <label htmlFor={`botResponse-${currentSlotIndex}`} className="form-label fw-bold">Bot Response</label>
                            <input
                                type="text"
                                className="form-control"
                                id={`botResponse-${currentSlotIndex}`}
                                value={slots[currentSlotIndex]?.botResponse || ''}
                                onChange={(e) => onSlotChange(currentSlotIndex, 'botResponse', e.target.value)}
                                placeholder="Enter bot response message"
                            />
                        </div>
                        <div className="mt-2">
                            <label htmlFor={`postResponse-${currentSlotIndex}`} className="form-label fw-bold">Post Response</label>
                            <input
                                type="text"
                                className="form-control"
                                id={`postResponse-${currentSlotIndex}`}
                                value={slots[currentSlotIndex]?.postResponse || ''}
                                onChange={(e) => onSlotChange(currentSlotIndex, 'postResponse', e.target.value)}
                                placeholder="Enter post response action"
                            />
                        </div>
                    </div>
                </div>

                {/* Numbered Navigation Buttons */}
                <div className="mt-4 text-center">
                    <div className="d-flex flex-wrap justify-content-center gap-2">
                        {Array.from({ length: slots.length }, (_, index) => (
                            <div key={index} className="d-inline-block mx-1 mb-2">
                                <button
                                    className={`btn ${index === currentSlotIndex ? 'btn-primary' : 'btn-outline-secondary'} d-block w-100`}
                                    onClick={() => onCurrentSlotIndexChange(index)}
                                    style={{ height: '60px', borderRadius: '8px' }}
                                >
                                    <div className="text-center">
                                        <div className="h5 mb-1">
                                            {slots[index]?.type === 'media' ? '📷' : '🔘'}
                                        </div>
                                        <div className="small">{index + 1}</div>
                                    </div>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SlotCard;