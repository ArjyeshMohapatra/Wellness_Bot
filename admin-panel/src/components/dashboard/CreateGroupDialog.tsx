import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    TextField,
} from '@mui/material';

interface CreateGroupDialogProps {
    open: boolean;
    onClose: () => void;
    newGroupName: string;
    onNewGroupNameChange: (name: string) => void;
    onCreateGroup: () => void;
}

const CreateGroupDialog: React.FC<CreateGroupDialogProps> = ({
    open,
    onClose,
    newGroupName,
    onNewGroupNameChange,
    onCreateGroup
}) => {
    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="sm"
            fullWidth
        >
            <DialogTitle sx={{ textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    ➕ Create New Group Configuration
                </Typography>
            </DialogTitle>
            <DialogContent sx={{ p: 3 }}>
                <Typography variant="body1" sx={{ mb: 2, color: 'text.secondary' }}>
                    Create a new configuration for a different Telegram group. You can customize bot settings for each group independently.
                </Typography>
                <TextField
                    autoFocus
                    margin="dense"
                    label="Group Name"
                    fullWidth
                    variant="outlined"
                    value={newGroupName}
                    onChange={(e) => onNewGroupNameChange(e.target.value)}
                    placeholder="e.g., Wellness Group, Fitness Club"
                    helperText="Choose a descriptive name for this group configuration"
                />
            </DialogContent>
            <DialogActions sx={{ p: 3, justifyContent: 'center', gap: 2 }}>
                <Button
                    variant="outlined"
                    onClick={onClose}
                    sx={{ minWidth: 100 }}
                >
                    Cancel
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={onCreateGroup}
                    disabled={!newGroupName.trim()}
                    sx={{ minWidth: 100 }}
                >
                    Create Group
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default CreateGroupDialog;