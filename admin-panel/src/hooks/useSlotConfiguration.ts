import { useState, useEffect } from 'react';

export interface Slot {
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

export const useSlotConfiguration = (initialSlots?: Slot[]) => {
    const [eventType, setEventType] = useState<'normal' | 'time-limited'>('normal');
    const [eventName, setEventName] = useState('');
    const [eventDays, setEventDays] = useState('');
    const [passPoints, setPassPoints] = useState('');
    const [slotsPerDay, setSlotsPerDay] = useState('');
    const [welcomeMessage, setWelcomeMessage] = useState('');
    const [kickResponse, setKickResponse] = useState('');
    const [undesignatedSlotResponse, setUndesignatedSlotResponse] = useState('');
    const [leaderboardTime, setLeaderboardTime] = useState('');
    const [slots, setSlots] = useState<Slot[]>([]);
    const [slotErrors, setSlotErrors] = useState<{ totalPoints: boolean; overlaps: boolean }>({ totalPoints: false, overlaps: false });
    const [currentSlotIndex, setCurrentSlotIndex] = useState<number>(0);
    const [currentButtonIndex, setCurrentButtonIndex] = useState<number>(0);
    const [slotButtonIndices, setSlotButtonIndices] = useState<{ [key: number]: number }>({});

    const timeToMinutes = (time: string) => {
        if (!time) return 0;
        const [h, m] = time.split(':').map(Number);
        return h * 60 + m;
    };

    // Initialize slots when slotsPerDay changes or initialSlots is provided
    useEffect(() => {
        if (initialSlots && initialSlots.length > 0) {
            // Use provided initial slots
            setSlots(initialSlots);
        } else {
            // Initialize empty slots based on slotsPerDay
            const num = parseInt(slotsPerDay) || 0;
            setSlots(Array.from({ length: num }, () => ({
                name: '',
                compulsory: false,
                startTime: '',
                endTime: '',
                points: 0,
                type: 'media' as const,
            })));
        }
    }, [slotsPerDay, initialSlots]);

    const handleSlotTypeChange = (index: number, type: 'media' | 'button') => {
        const newSlots = [...slots];
        newSlots[index] = { ...newSlots[index], type };
        if (type === 'button' && !newSlots[index].buttonCount) {
            newSlots[index].buttonCount = 2;
            newSlots[index].buttonNames = ['Button 1', 'Button 2'];
            newSlots[index].buttonValues = [0, 0];
        }
        setSlots(newSlots);
    };

    const handleSlotButtonCountChange = (index: number, count: number) => {
        const currentNames = slots[index]?.buttonNames || [];
        const currentValues = slots[index]?.buttonValues || [];
        const newNames = Array.from({ length: count }, (_, i) => currentNames[i] || `Button ${i + 1}`);
        const newValues = Array.from({ length: count }, (_, i) => currentValues[i] || 0);
        const newSlots = [...slots];
        newSlots[index] = { ...newSlots[index], buttonCount: count, buttonNames: newNames, buttonValues: newValues };
        setSlots(newSlots);
    };

    const handleSlotButtonIndexChange = (index: number, buttonIndex: number) => {
        setSlotButtonIndices(prev => ({ ...prev, [index]: buttonIndex }));
    };

    const handleSlotChange = (index: number, field: keyof Slot, value: string | number | boolean | string[] | number[]) => {
        const newSlots = [...slots];
        newSlots[index] = { ...newSlots[index], [field]: value };
        setSlots(newSlots);
    };

    // Validate slots for errors
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

    // Reset currentButtonIndex when slot changes or button count changes
    useEffect(() => {
        setCurrentButtonIndex(0);
    }, [currentSlotIndex, slots]);

    return {
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
        setEventType,
        setEventName,
        setEventDays,
        setPassPoints,
        setSlotsPerDay,
        setWelcomeMessage,
        setKickResponse,
        setUndesignatedSlotResponse,
        setLeaderboardTime,
        setCurrentSlotIndex,
        setCurrentButtonIndex,
        handleSlotTypeChange,
        handleSlotButtonCountChange,
        handleSlotButtonIndexChange,
        handleSlotChange
    };
};