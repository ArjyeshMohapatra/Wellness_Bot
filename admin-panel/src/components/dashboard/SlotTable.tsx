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

interface SlotTableProps {
    slots: Slot[];
    slotButtonIndices: { [key: number]: number };
    onSlotChange: (index: number, field: keyof Slot, value: string | number | boolean | string[] | number[]) => void;
    onSlotTypeChange: (index: number, type: 'media' | 'button') => void;
    onSlotButtonCountChange: (index: number, count: number) => void;
    onSlotButtonIndexChange: (index: number, buttonIndex: number) => void;
}

const SlotTable: React.FC<SlotTableProps> = ({
    slots,
    slotButtonIndices,
    onSlotChange,
    onSlotTypeChange,
    onSlotButtonCountChange,
    onSlotButtonIndexChange
}) => {
    return (
        <div className="d-none d-md-block mt-3">
            <div className="table-responsive">
                <table className="table table-striped table-hover shadow-sm" style={{ borderRadius: '12px', overflow: 'hidden', borderCollapse: 'separate', borderSpacing: '0', boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)', border: '1px solid #dee2e6' }}>
                    <thead style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', borderBottom: '2px solid #dee2e6' }}>
                        <tr>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Slot<br />Name</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Type</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Compulsory</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Start<br />Time</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>End<br />Time</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Points</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Button<br />Count</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Config<br />Button</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600', borderRight: '1px solid rgba(255,255,255,0.2)' }}>Bot<br />Response</th>
                            <th style={{ padding: '12px 8px', textAlign: 'center', fontSize: '0.85rem', fontWeight: '600' }}>Post<br />Response</th>
                        </tr>
                    </thead>
                    <tbody style={{ backgroundColor: '#f8f9fa' }}>
                        {slots.map((slot, index) => (
                            <tr key={index} style={{ borderBottom: '1px solid #dee2e6', transition: 'background-color 0.2s ease' }}>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm"
                                        style={{ width: '120px' }}
                                        value={slot.name}
                                        onChange={(e) => onSlotChange(index, 'name', e.target.value)}
                                        placeholder="Enter slot name"
                                    />
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle', width: '60px', minWidth: '60px' }}>
                                    <select
                                        className="form-select form-select-sm"
                                        value={slot.type}
                                        onChange={(e) => {
                                            const newType = e.target.value as 'media' | 'button';
                                            onSlotTypeChange(index, newType);
                                        }}
                                    >
                                        <option value="media">📷 Media</option>
                                        <option value="button">🔘 Button</option>
                                    </select>
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle', width: '60px', minWidth: '60px' }}>
                                    <div className="form-check d-flex justify-content-center">
                                        <input
                                            type="checkbox"
                                            className="form-check-input"
                                            checked={slot.compulsory}
                                            onChange={(e) => onSlotChange(index, 'compulsory', e.target.checked)}
                                        />
                                    </div>
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="time"
                                        className="form-control form-control-sm"
                                        style={{ width: '100px' }}
                                        value={slot.startTime}
                                        onChange={(e) => onSlotChange(index, 'startTime', e.target.value)}
                                    />
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="time"
                                        className="form-control form-control-sm"
                                        style={{ width: '100px' }}
                                        value={slot.endTime}
                                        onChange={(e) => onSlotChange(index, 'endTime', e.target.value)}
                                    />
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="number"
                                        className="form-control form-control-sm"
                                        style={{ width: '60px' }}
                                        value={slot.points}
                                        onChange={(e) => onSlotChange(index, 'points', Number(e.target.value))}
                                        min="0"
                                        max="100"
                                    />
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    {slot.type === 'button' ? (
                                        <input
                                            type="number"
                                            className="form-control form-control-sm"
                                            style={{ width: '60px' }}
                                            value={slot.buttonCount || 2}
                                            onChange={(e) => {
                                                const count = Math.max(1, Number(e.target.value));
                                                onSlotButtonCountChange(index, count);
                                            }}
                                            min="1"
                                            max="10"
                                        />
                                    ) : (
                                        <span className="text-muted">-</span>
                                    )}
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    {slot.type === 'button' ? (
                                        <div className="d-flex align-items-center gap-1">
                                            <div className="flex-grow-1">
                                                <input
                                                    type="text"
                                                    className="form-control form-control-sm mb-0"
                                                    style={{ width: '100px' }}
                                                    value={slot.buttonNames?.[slotButtonIndices[index] || 0] ?? `Button ${(slotButtonIndices[index] || 0) + 1}`}
                                                    onChange={(e) => {
                                                        const newNames = [...(slot.buttonNames || [])];
                                                        newNames[slotButtonIndices[index] || 0] = e.target.value;
                                                        onSlotChange(index, 'buttonNames', newNames);
                                                    }}
                                                    placeholder={`Button ${(slotButtonIndices[index] || 0) + 1} name`}
                                                />
                                                <input
                                                    type="number"
                                                    className="form-control form-control-sm"
                                                    style={{ width: '60px' }}
                                                    value={slot.buttonValues?.[slotButtonIndices[index] || 0] ?? 0}
                                                    onChange={(e) => {
                                                        const newValues = [...(slot.buttonValues || [])];
                                                        newValues[slotButtonIndices[index] || 0] = Number(e.target.value) || 0;
                                                        onSlotChange(index, 'buttonValues', newValues);
                                                    }}
                                                    placeholder="Value"
                                                    min="0"
                                                />
                                            </div>
                                            <button
                                                type="button"
                                                className="btn btn-outline-secondary btn-sm align-self-start"
                                                onClick={() => {
                                                    const currentIndex = slotButtonIndices[index] || 0;
                                                    const maxIndex = (slot.buttonCount || 2) - 1;
                                                    const nextIndex = currentIndex < maxIndex ? currentIndex + 1 : 0;
                                                    onSlotButtonIndexChange(index, nextIndex);
                                                }}
                                                title={`Button ${(slotButtonIndices[index] || 0) + 1} of ${slot.buttonCount || 2}`}
                                            >
                                                →
                                            </button>
                                        </div>
                                    ) : (
                                        <span className="text-muted">-</span>
                                    )}
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm"
                                        style={{ width: '200px' }}
                                        value={slot.botResponse || ''}
                                        onChange={(e) => onSlotChange(index, 'botResponse', e.target.value)}
                                        placeholder="Bot response"
                                    />
                                </td>
                                <td style={{ padding: '8px', verticalAlign: 'middle' }}>
                                    <input
                                        type="text"
                                        className="form-control form-control-sm"
                                        style={{ width: '200px' }}
                                        value={slot.postResponse || ''}
                                        onChange={(e) => onSlotChange(index, 'postResponse', e.target.value)}
                                        placeholder="Post response"
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default SlotTable;