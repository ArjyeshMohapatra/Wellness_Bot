import React from 'react';
import SlotTable from './SlotTable';
import SlotCard from './SlotCard';

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

interface SlotConfigurationProps {
    slots: Slot[];
    slotButtonIndices: { [key: number]: number };
    currentSlotIndex: number;
    currentButtonIndex: number;
    onSlotChange: (index: number, field: keyof Slot, value: string | number | boolean | string[] | number[]) => void;
    onSlotTypeChange: (index: number, type: 'media' | 'button') => void;
    onSlotButtonCountChange: (index: number, count: number) => void;
    onSlotButtonIndexChange: (index: number, buttonIndex: number) => void;
    onCurrentSlotIndexChange: (index: number) => void;
    onCurrentButtonIndexChange: (index: number) => void;
}

const SlotConfiguration: React.FC<SlotConfigurationProps> = ({
    slots,
    slotButtonIndices,
    currentSlotIndex,
    currentButtonIndex,
    onSlotChange,
    onSlotTypeChange,
    onSlotButtonCountChange,
    onSlotButtonIndexChange,
    onCurrentSlotIndexChange,
    onCurrentButtonIndexChange
}) => {
    return (
        <>
            {/* Desktop Table View */}
            <div className="d-none d-md-block">
                <SlotTable
                    slots={slots}
                    slotButtonIndices={slotButtonIndices}
                    onSlotChange={onSlotChange}
                    onSlotTypeChange={onSlotTypeChange}
                    onSlotButtonCountChange={onSlotButtonCountChange}
                    onSlotButtonIndexChange={onSlotButtonIndexChange}
                />
            </div>

            {/* Mobile Card View */}
            <SlotCard
                slots={slots}
                currentSlotIndex={currentSlotIndex}
                currentButtonIndex={currentButtonIndex}
                onSlotChange={onSlotChange}
                onCurrentSlotIndexChange={onCurrentSlotIndexChange}
                onCurrentButtonIndexChange={onCurrentButtonIndexChange}
            />
        </>
    );
};

export default SlotConfiguration;