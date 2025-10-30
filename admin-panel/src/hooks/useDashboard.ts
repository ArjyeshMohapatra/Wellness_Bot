import { useState, useEffect, useCallback } from 'react';
import type { Slot } from './useSlotConfiguration';

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

export const useDashboardState = () => {
    // Bot settings state
    const [botSettings, setBotSettings] = useState<BotSettings[]>([]);
    const [selectedGroupId, setSelectedGroupId] = useState<number>(0);
    const [showCreateGroupDialog, setShowCreateGroupDialog] = useState(false);
    const [newGroupName, setNewGroupName] = useState('');

    // Configuration dialog state
    const [showConfigurationDialog, setShowConfigurationDialog] = useState(false);
    const [configurationDialogData, setConfigurationDialogData] = useState<{
        botUsername: string;
        licenseKey: string | null;
    } | null>(null);

    // Basic bot state
    const [loadedSlots, setLoadedSlots] = useState<Slot[]>([]);
    const [botUsername, setBotUsername] = useState('BeHumanAgainBot');
    const [hasAdminPermissions, setHasAdminPermissions] = useState(false);
    const [licenseKey, setLicenseKey] = useState<string | null>(null);

    // Function to load settings for a specific group
    const loadSettingsForGroup = useCallback((settings: BotSettings) => {
        setBotUsername(settings.bot_username || 'BeHumanAgainBot');
        setHasAdminPermissions(settings.has_admin_permissions || false);
        setLicenseKey(settings.license_key || null);
        setLoadedSlots(settings.loaded_slots || []);
    }, []);

    // Function to load configuration
    const loadConfiguration = useCallback(async () => {
        try {
            // Load dashboard state from localStorage first
            const savedDashboardState = localStorage.getItem('dashboardState');
            if (savedDashboardState) {
                const state = JSON.parse(savedDashboardState);
                setBotUsername(state.botUsername || 'BeHumanAgainBot');
                setHasAdminPermissions(state.hasAdminPermissions || false);
                setLicenseKey(state.licenseKey || null);
                setLoadedSlots(state.loadedSlots || []);
            }

            // Load all bot settings from database
            const adminUserId = localStorage.getItem('userId');
            console.log('Loading dashboard for adminUserId:', adminUserId);

            if (!adminUserId) {
                console.error('No adminUserId found');
                return;
            }

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                const settingsList = Array.isArray(dashboardResult.settings) ? dashboardResult.settings : [dashboardResult.settings];
                setBotSettings(settingsList);

                // If no settings exist yet, initialize with default
                if (settingsList.length === 0) {
                    setBotSettings([{
                        setting_id: 0,
                        admin_user_id: parseInt(adminUserId),
                        group_id: 0,
                        license_key: null,
                        bot_username: 'BeHumanAgainBot',
                        has_admin_permissions: false,
                        event_type: 'normal',
                        event_name: '',
                        event_days: 7,
                        pass_points: 250,
                        slots_per_day: 2,
                        welcome_message: '',
                        kick_response: '',
                        undesignated_slot_response: '',
                        leaderboard_time: '11:00',
                        banned_words: [],
                        loaded_slots: [],
                        is_active: true
                    }]);
                    setSelectedGroupId(0);
                } else {
                    // Load the selected group's settings, defaulting to the first group
                    const savedGroupId = localStorage.getItem('selectedGroupId');
                    let selectedSettings = settingsList[0];
                    if (savedGroupId) {
                        const saved = settingsList.find((s: BotSettings) => s.group_id === parseInt(savedGroupId));
                        if (saved) selectedSettings = saved;
                    }
                    setSelectedGroupId(selectedSettings.group_id);
                    loadSettingsForGroup(selectedSettings);
                }
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }, [loadSettingsForGroup]);

    // Function to handle group selection
    const handleGroupSelect = (groupId: number) => {
        setSelectedGroupId(groupId);
        const settings = botSettings.find(s => s.group_id === groupId);
        if (settings) {
            loadSettingsForGroup(settings);
        }
    };

    // Function to create new group settings
    const handleCreateGroup = async () => {
        if (!newGroupName.trim()) {
            alert('Please enter a group name');
            return;
        }

        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) {
                alert('User not logged in');
                return;
            }

            // Create new group settings with default values
            const newSettings: BotSettings = {
                admin_user_id: parseInt(adminUserId),
                group_id: Date.now(), // Use timestamp as temporary group_id until bot joins
                group_name: newGroupName.trim(),
                license_key: null,
                bot_username: 'BeHumanAgainBot',
                has_admin_permissions: false,
                event_type: 'normal',
                event_name: '',
                event_days: 7,
                pass_points: 250,
                slots_per_day: 2,
                welcome_message: '',
                kick_response: '',
                undesignated_slot_response: '',
                leaderboard_time: '11:00',
                banned_words: [],
                loaded_slots: [],
                is_active: true
            };

            const response = await fetch('http://localhost:8001/api/admin/dashboard/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    group_id: newSettings.group_id,
                    settings: newSettings
                })
            });

            const result = await response.json();
            if (result.success) {
                // Add to local state
                setBotSettings(prev => [...prev, newSettings]);
                setSelectedGroupId(newSettings.group_id);
                loadSettingsForGroup(newSettings);
                setShowCreateGroupDialog(false);
                setNewGroupName('');
                alert('New group created successfully! Add the bot to your Telegram group and it will automatically detect the group ID.');
            } else {
                alert(`Failed to create group: ${result.message}`);
            }
        } catch (error) {
            console.error('Error creating group:', error);
            alert('Error creating group. Please try again.');
        }
    };

    // Function to refresh admin permissions
    const refreshAdminPermissions = useCallback(async () => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) return;

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                // Note: dbSettings is an array, so we can't directly access has_admin_permissions
                // For now, we'll skip updating permissions from here since it's not correctly implemented
                // The permissions should be loaded in loadConfiguration
            }
        } catch (error) {
            console.error('Error refreshing admin permissions:', error);
        }
    }, []);

    // Load saved configuration on component mount
    useEffect(() => {
        loadConfiguration();

        // Set up periodic refresh of admin permissions (every 30 seconds)
        const interval = setInterval(() => {
            refreshAdminPermissions();
        }, 30000);

        return () => clearInterval(interval);
    }, [loadConfiguration, refreshAdminPermissions]);

    // Save selectedGroupId to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('selectedGroupId', selectedGroupId.toString());
    }, [selectedGroupId]);

    return {
        // State
        botSettings,
        selectedGroupId,
        showCreateGroupDialog,
        newGroupName,
        showConfigurationDialog,
        configurationDialogData,
        loadedSlots,
        botUsername,
        hasAdminPermissions,
        licenseKey,

        // Setters
        setBotSettings,
        setSelectedGroupId,
        setShowCreateGroupDialog,
        setNewGroupName,
        setShowConfigurationDialog,
        setConfigurationDialogData,
        setLoadedSlots,
        setBotUsername,
        setHasAdminPermissions,
        setLicenseKey,

        // Functions
        loadSettingsForGroup,
        loadConfiguration,
        handleGroupSelect,
        handleCreateGroup,
        refreshAdminPermissions,
    };
};