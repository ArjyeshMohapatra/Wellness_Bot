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
    Button,
} from '@mui/material';
import {
    KeyboardArrowDown as ExpandMoreIcon,
    KeyboardArrowUp as ExpandLessIcon,
    PhotoCamera as PhotoIcon,
    Delete as DeleteIcon,
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
    image?: string; // Base64 encoded image or image URL
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

    // Removed debouncing from input fields for immediate responsiveness
    // Debouncing can be added back for expensive operations like API calls if needed

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
                                            value={slot.points ?? ''}
                                            onChange={(e) => onSlotChange(index, 'points', e.target.value === '' ? 0 : Number(e.target.value))}
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
                                                    sx={{ width: 80 }}
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

                                    {/* Image Upload Section */}
                                    <Box sx={{ mt: 2, p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                                            Slot Image (Optional)
                                        </Typography>

                                        {slot.image && (
                                            <Box sx={{ mb: 2, textAlign: 'center' }}>
                                                <Box
                                                    component="img"
                                                    src={slot.image}
                                                    alt={`Slot ${index + 1}`}
                                                    sx={{
                                                        maxWidth: '100%',
                                                        maxHeight: 150,
                                                        borderRadius: 1,
                                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                    }}
                                                />
                                                <Button
                                                    size="small"
                                                    color="error"
                                                    startIcon={<DeleteIcon />}
                                                    onClick={() => onSlotChange(index, 'image', '')}
                                                    sx={{ mt: 1 }}
                                                >
                                                    Remove Image
                                                </Button>
                                            </Box>
                                        )}

                                        <Button
                                            variant="outlined"
                                            component="label"
                                            size="small"
                                            startIcon={<PhotoIcon />}
                                            fullWidth
                                        >
                                            {slot.image ? 'Change Image' : 'Upload Image'}
                                            <input
                                                type="file"
                                                accept="image/*"
                                                hidden
                                                onChange={(e) => {
                                                    const file = e.target.files?.[0];
                                                    if (file) {
                                                        const reader = new FileReader();
                                                        reader.onload = (event) => {
                                                            const base64 = event.target?.result as string;
                                                            onSlotChange(index, 'image', base64);
                                                        };
                                                        reader.readAsDataURL(file);
                                                    }
                                                }}
                                            />
                                        </Button>
                                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                            Recommended: 500x300px, max 2MB
                                        </Typography>
                                    </Box>
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
                                                sx={{ width: 135 }}
                                            />
                                            <TextField
                                                type="time"
                                                value={slot.endTime}
                                                onChange={(e) => onSlotChange(index, 'endTime', e.target.value)}
                                                size="small"
                                                sx={{ width: 135 }}
                                            />
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            value={slot.points ?? ''}
                                            onChange={(e) => onSlotChange(index, 'points', e.target.value === '' ? '' : Number(e.target.value))}
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
                                                    <Box sx={{ mb: 2, border: '1px solid green', borderRadius: 1, p: 2 }}>
                                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Button Configuration</Typography>
                                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                            {Array.from({ length: slot.buttonCount || 2 }, (_, i) => (
                                                                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200, border: '1px solid green', borderRadius: 1, p: 1 }}>
                                                                    <TextField
                                                                        label={`Button ${i + 1} Name`}
                                                                        value={slot.buttonNames?.[i] ?? `Button ${i + 1}`}
                                                                        onChange={(e) => {
                                                                            const newNames = [...(slot.buttonNames || new Array(slot.buttonCount || 2).fill(''))];
                                                                            newNames[i] = e.target.value;
                                                                            onSlotChange(index, 'buttonNames', newNames);
                                                                        }}
                                                                        size="small"
                                                                        sx={{ width: 160 }}
                                                                    />
                                                                    <TextField
                                                                        label="Value"
                                                                        type="number"
                                                                        value={slot.buttonValues?.[i] ?? ''}
                                                                        onChange={(e) => {
                                                                            const newValues = [...(slot.buttonValues || new Array(slot.buttonCount || 2).fill(0))];
                                                                            newValues[i] = e.target.value === '' ? '' : Number(e.target.value);
                                                                            onSlotChange(index, 'buttonValues', newValues);
                                                                        }}
                                                                        size="small"
                                                                        sx={{ width: 80 }}
                                                                        inputProps={{ min: 0 }}
                                                                    />
                                                                </Box>
                                                            ))}
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
                                                {/* Image Upload Section for Desktop Table */}
                                                <Box sx={{ mt: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 1, backgroundColor: 'white' }}>
                                                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Slot Image (Optional)</Typography>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                                        <Button
                                                            variant="outlined"
                                                            component="label"
                                                            size="small"
                                                            sx={{ minWidth: 120 }}
                                                        >
                                                            Upload Image
                                                            <input
                                                                type="file"
                                                                accept="image/*"
                                                                hidden
                                                                onChange={(e) => {
                                                                    const file = e.target.files?.[0];
                                                                    if (file) {
                                                                        const reader = new FileReader();
                                                                        reader.onload = (event) => {
                                                                            const base64 = event.target?.result as string;
                                                                            onSlotChange(index, 'image', base64);
                                                                        };
                                                                        reader.readAsDataURL(file);
                                                                    }
                                                                }}
                                                            />
                                                        </Button>
                                                        {slot.image && (
                                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                                <Box
                                                                    component="img"
                                                                    src={slot.image}
                                                                    alt="Slot preview"
                                                                    sx={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 1 }}
                                                                />
                                                                <IconButton
                                                                    size="small"
                                                                    onClick={() => onSlotChange(index, 'image', '')}
                                                                    color="error"
                                                                >
                                                                    <DeleteIcon fontSize="small" />
                                                                </IconButton>
                                                            </Box>
                                                        )}
                                                    </Box>
                                                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                                        Recommended: 500x300px, max 2MB
                                                    </Typography>
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