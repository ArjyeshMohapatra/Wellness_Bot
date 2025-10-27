import React, { useState } from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    TextField,
    Select,
    MenuItem,
    FormControl,
    Checkbox,
    IconButton,
    Collapse,
    Box,
    Typography,
    Card,
    CardContent,
    useMediaQuery,
    useTheme,
} from '@mui/material';
import {
    KeyboardArrowDown as ExpandMoreIcon,
    KeyboardArrowUp as ExpandLessIcon,
} from '@mui/icons-material';

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
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const toggleRowExpansion = (index: number) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedRows(newExpanded);
    };

    if (isMobile) {
        // Mobile card layout
        return (
            <Box sx={{ mt: 3 }}>
                {slots.map((slot, index) => (
                    <Card key={index} sx={{ mb: 2, boxShadow: 2 }}>
                        <CardContent sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    {slot.name || `Slot ${index + 1}`}
                                </Typography>
                                <IconButton
                                    size="small"
                                    onClick={() => toggleRowExpansion(index)}
                                >
                                    {expandedRows.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                </IconButton>
                            </Box>

                            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                <FormControl size="small" sx={{ minWidth: 80 }}>
                                    <Select
                                        value={slot.type}
                                        onChange={(e) => onSlotTypeChange(index, e.target.value as 'media' | 'button')}
                                    >
                                        <MenuItem value="media">📷 Media</MenuItem>
                                        <MenuItem value="button">🔘 Button</MenuItem>
                                    </Select>
                                </FormControl>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Checkbox
                                        checked={slot.compulsory}
                                        onChange={() => onSlotChange(index, 'compulsory', !slot.compulsory)}
                                        size="small"
                                    />
                                    <Typography variant="caption">Required</Typography>
                                </Box>
                            </Box>

                            <Collapse in={expandedRows.has(index)}>
                                <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                        <TextField
                                            label="Start Time"
                                            type="time"
                                            value={slot.startTime}
                                            onChange={(e) => onSlotChange(index, 'startTime', e.target.value)}
                                            size="small"
                                            sx={{ flex: 1 }}
                                        />
                                        <TextField
                                            label="End Time"
                                            type="time"
                                            value={slot.endTime}
                                            onChange={(e) => onSlotChange(index, 'endTime', e.target.value)}
                                            size="small"
                                            sx={{ flex: 1 }}
                                        />
                                        <TextField
                                            label="Points"
                                            type="number"
                                            value={slot.points}
                                            onChange={(e) => onSlotChange(index, 'points', Number(e.target.value))}
                                            size="small"
                                            sx={{ width: 80 }}
                                            inputProps={{ min: 0, max: 100 }}
                                        />
                                    </Box>

                                    {slot.type === 'button' && (
                                        <Box sx={{ mb: 2 }}>
                                            <TextField
                                                label="Button Count"
                                                type="number"
                                                value={slot.buttonCount || 2}
                                                onChange={(e) => onSlotButtonCountChange(index, Math.max(1, Number(e.target.value)))}
                                                size="small"
                                                sx={{ width: 120, mb: 1 }}
                                                inputProps={{ min: 1, max: 10 }}
                                            />
                                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                                <TextField
                                                    label={`Button ${(slotButtonIndices[index] || 0) + 1} Name`}
                                                    value={slot.buttonNames?.[slotButtonIndices[index] || 0] ?? `Button ${(slotButtonIndices[index] || 0) + 1}`}
                                                    onChange={(e) => {
                                                        const newNames = [...(slot.buttonNames || [])];
                                                        newNames[slotButtonIndices[index] || 0] = e.target.value;
                                                        onSlotChange(index, 'buttonNames', newNames);
                                                    }}
                                                    size="small"
                                                    sx={{ flex: 1 }}
                                                />
                                                <TextField
                                                    label="Value"
                                                    type="number"
                                                    value={slot.buttonValues?.[slotButtonIndices[index] || 0] ?? 0}
                                                    onChange={(e) => {
                                                        const newValues = [...(slot.buttonValues || [])];
                                                        newValues[slotButtonIndices[index] || 0] = Number(e.target.value) || 0;
                                                        onSlotChange(index, 'buttonValues', newValues);
                                                    }}
                                                    size="small"
                                                    sx={{ width: 80 }}
                                                />
                                                <IconButton
                                                    size="small"
                                                    onClick={() => {
                                                        const currentIndex = slotButtonIndices[index] || 0;
                                                        const maxIndex = (slot.buttonCount || 2) - 1;
                                                        const nextIndex = currentIndex < maxIndex ? currentIndex + 1 : 0;
                                                        onSlotButtonIndexChange(index, nextIndex);
                                                    }}
                                                >
                                                    →
                                                </IconButton>
                                            </Box>
                                        </Box>
                                    )}

                                    <TextField
                                        label="Bot Response"
                                        value={slot.botResponse || ''}
                                        onChange={(e) => onSlotChange(index, 'botResponse', e.target.value)}
                                        size="small"
                                        fullWidth
                                        sx={{ mb: 1 }}
                                        placeholder="Bot response message"
                                    />
                                    <TextField
                                        label="Post Response"
                                        value={slot.postResponse || ''}
                                        onChange={(e) => onSlotChange(index, 'postResponse', e.target.value)}
                                        size="small"
                                        fullWidth
                                        placeholder="Post-response message"
                                    />
                                </Box>
                            </Collapse>
                        </CardContent>
                    </Card>
                ))}
            </Box>
        );
    }

    // Desktop table layout - compact version
    return (
        <Box sx={{ mt: 3 }}>
            <TableContainer component={Paper} sx={{ boxShadow: 2 }}>
                <Table size="small">
                    <TableHead>
                        <TableRow sx={{ backgroundColor: 'primary.main' }}>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '25%' }}>Slot Name</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '10%' }}>Type</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '10%' }}>Required</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '15%' }}>Time Range</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '10%' }}>Points</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '15%' }}>Button Config</TableCell>
                            <TableCell sx={{ color: 'white', fontWeight: 'bold', width: '15%' }}>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {slots.map((slot, index) => (
                            <React.Fragment key={index}>
                                <TableRow hover>
                                    <TableCell>
                                        <TextField
                                            value={slot.name}
                                            onChange={(e) => onSlotChange(index, 'name', e.target.value)}
                                            size="small"
                                            placeholder="Enter slot name"
                                            fullWidth
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <FormControl size="small" fullWidth>
                                            <Select
                                                value={slot.type}
                                                onChange={(e) => onSlotTypeChange(index, e.target.value as 'media' | 'button')}
                                            >
                                                <MenuItem value="media">📷 Media</MenuItem>
                                                <MenuItem value="button">🔘 Button</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </TableCell>
                                    <TableCell>
                                        <Checkbox
                                            checked={slot.compulsory}
                                            onChange={() => onSlotChange(index, 'compulsory', !slot.compulsory)}
                                            size="small"
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                            <TextField
                                                type="time"
                                                value={slot.startTime}
                                                onChange={(e) => onSlotChange(index, 'startTime', e.target.value)}
                                                size="small"
                                                sx={{ width: 100 }}
                                            />
                                            <TextField
                                                type="time"
                                                value={slot.endTime}
                                                onChange={(e) => onSlotChange(index, 'endTime', e.target.value)}
                                                size="small"
                                                sx={{ width: 100 }}
                                            />
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            value={slot.points}
                                            onChange={(e) => onSlotChange(index, 'points', Number(e.target.value))}
                                            size="small"
                                            sx={{ width: 70 }}
                                            inputProps={{ min: 0, max: 100 }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        {slot.type === 'button' ? (
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <TextField
                                                    type="number"
                                                    value={slot.buttonCount || 2}
                                                    onChange={(e) => onSlotButtonCountChange(index, Math.max(1, Number(e.target.value)))}
                                                    size="small"
                                                    sx={{ width: 60 }}
                                                    inputProps={{ min: 1, max: 10 }}
                                                />
                                                <Typography variant="caption">
                                                    {slotButtonIndices[index] !== undefined ? `Btn ${(slotButtonIndices[index] || 0) + 1}` : 'Btn 1'}
                                                </Typography>
                                            </Box>
                                        ) : (
                                            <Typography variant="caption" color="text.secondary">-</Typography>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <IconButton
                                            size="small"
                                            onClick={() => toggleRowExpansion(index)}
                                            color="primary"
                                        >
                                            {expandedRows.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                                <TableRow>
                                    <TableCell colSpan={7} sx={{ py: 0 }}>
                                        <Collapse in={expandedRows.has(index)}>
                                            <Box sx={{ p: 2, backgroundColor: 'grey.50' }}>
                                                {slot.type === 'button' && (
                                                    <Box sx={{ mb: 2 }}>
                                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Button Configuration</Typography>
                                                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                                            <TextField
                                                                label={`Button ${(slotButtonIndices[index] || 0) + 1} Name`}
                                                                value={slot.buttonNames?.[slotButtonIndices[index] || 0] ?? `Button ${(slotButtonIndices[index] || 0) + 1}`}
                                                                onChange={(e) => {
                                                                    const newNames = [...(slot.buttonNames || [])];
                                                                    newNames[slotButtonIndices[index] || 0] = e.target.value;
                                                                    onSlotChange(index, 'buttonNames', newNames);
                                                                }}
                                                                size="small"
                                                                sx={{ flex: 1 }}
                                                            />
                                                            <TextField
                                                                label="Value"
                                                                type="number"
                                                                value={slot.buttonValues?.[slotButtonIndices[index] || 0] ?? 0}
                                                                onChange={(e) => {
                                                                    const newValues = [...(slot.buttonValues || [])];
                                                                    newValues[slotButtonIndices[index] || 0] = Number(e.target.value) || 0;
                                                                    onSlotChange(index, 'buttonValues', newValues);
                                                                }}
                                                                size="small"
                                                                sx={{ width: 80 }}
                                                            />
                                                            <IconButton
                                                                size="small"
                                                                onClick={() => {
                                                                    const currentIndex = slotButtonIndices[index] || 0;
                                                                    const maxIndex = (slot.buttonCount || 2) - 1;
                                                                    const nextIndex = currentIndex < maxIndex ? currentIndex + 1 : 0;
                                                                    onSlotButtonIndexChange(index, nextIndex);
                                                                }}
                                                            >
                                                                →
                                                            </IconButton>
                                                        </Box>
                                                    </Box>
                                                )}
                                                <Box sx={{ display: 'flex', gap: 2 }}>
                                                    <TextField
                                                        label="Bot Response"
                                                        value={slot.botResponse || ''}
                                                        onChange={(e) => onSlotChange(index, 'botResponse', e.target.value)}
                                                        size="small"
                                                        sx={{ flex: 1 }}
                                                        placeholder="Bot response message"
                                                    />
                                                    <TextField
                                                        label="Post Response"
                                                        value={slot.postResponse || ''}
                                                        onChange={(e) => onSlotChange(index, 'postResponse', e.target.value)}
                                                        size="small"
                                                        sx={{ flex: 1 }}
                                                        placeholder="Post-response message"
                                                    />
                                                </Box>
                                            </Box>
                                        </Collapse>
                                    </TableCell>
                                </TableRow>
                            </React.Fragment>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default SlotTable;