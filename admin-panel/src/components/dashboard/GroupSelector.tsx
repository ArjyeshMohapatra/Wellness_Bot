import React from 'react';
import {
    Box,
    Typography,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
} from '@mui/material';
import {
    PersonAdd as PersonAddIcon,
} from '@mui/icons-material';
import type { Slot } from '../../hooks/useSlotConfiguration';

interface BotSettings {
    setting_id?: number;
    admin_user_id: number;
    group_id: number;
    group_name?: string;
    license_key: string | null;
    bot_username: string;
    has_admin_permissions: boolean;
    event_type: 'normal' | 'time-limited';
    event_name: string;
    event_days: number;
    pass_points: number;
    slots_per_day: number;
    welcome_message: string;
    kick_response: string;
    undesignated_slot_response: string;
    leaderboard_time: string;
    banned_words: string[];
    loaded_slots: Slot[];
    is_active: boolean;
}

interface GroupSelectorProps {
    botSettings: BotSettings[];
    selectedGroupId: number;
    onGroupSelect: (groupId: number) => void;
    onCreateGroup: () => void;
}

const GroupSelector: React.FC<GroupSelectorProps> = ({
    botSettings,
    selectedGroupId,
    onGroupSelect,
    onCreateGroup
}) => {
    return (
        <Box sx={{ mt: 3, mb: 2 }}>
            <Box sx={{
                bgcolor: 'background.paper',
                p: 3,
                borderRadius: 2,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                border: '1px solid',
                borderColor: 'divider'
            }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                    📋 Group Configuration
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <FormControl sx={{ minWidth: 200 }}>
                        <InputLabel>Select Group</InputLabel>
                        <Select
                            value={selectedGroupId}
                            label="Select Group"
                            onChange={(e) => onGroupSelect(Number(e.target.value))}
                        >
                            {botSettings.map((setting) => (
                                <MenuItem key={setting.group_id} value={setting.group_id}>
                                    {setting.group_name || `Group ${setting.group_id}`}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <Button
                        variant="outlined"
                        color="primary"
                        onClick={onCreateGroup}
                        startIcon={<PersonAddIcon />}
                    >
                        Add New Group
                    </Button>
                </Box>

                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    Configure different bot settings for each Telegram group. Add the bot to your groups and it will automatically detect them.
                </Typography>
            </Box>
        </Box>
    );
};

export default GroupSelector;