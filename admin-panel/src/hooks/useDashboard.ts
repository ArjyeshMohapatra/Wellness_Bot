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
    // Bot settings state - simplified to single group
    const [botSettings, setBotSettings] = useState<BotSettings | null>(null);
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

    // Function to load configuration - simplified for single group
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

            // Load bot settings from database for group 0
            const adminUserId = localStorage.getItem('userId');
            console.log('Loading dashboard for adminUserId:', adminUserId);

            if (!adminUserId) {
                console.error('No adminUserId found');
                return;
            }

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}&group_id=0`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                // For single group, we expect a single settings object, not an array
                const settings = dashboardResult.settings;
                setBotSettings(settings);
                loadSettingsForGroup(settings);
            } else {
                // If no settings exist, initialize with defaults for group 0
                const defaultSettings: BotSettings = {
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
                };
                setBotSettings(defaultSettings);
                loadSettingsForGroup(defaultSettings);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }, [loadSettingsForGroup]);

    // Function to handle group selection - removed for single group
    // Function to create new group settings - removed for single group

    // Function to refresh admin permissions
    const refreshAdminPermissions = useCallback(async () => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) return;

            const dashboardResponse = await fetch(`http://localhost:8001/api/admin/dashboard/settings?admin_user_id=${adminUserId}&group_id=0`);
            const dashboardResult = await dashboardResponse.json();
            if (dashboardResult.success && dashboardResult.settings) {
                const settings = dashboardResult.settings;
                setHasAdminPermissions(settings.has_admin_permissions || false);
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

    // Save selectedGroupId to localStorage whenever it changes - removed for single group

    return {
        // State
        botSettings,
        showConfigurationDialog,
        configurationDialogData,
        loadedSlots,
        botUsername,
        hasAdminPermissions,
        licenseKey,

        // Setters
        setBotSettings,
        setShowConfigurationDialog,
        setConfigurationDialogData,
        setLoadedSlots,
        setBotUsername,
        setHasAdminPermissions,
        setLicenseKey,

        // Functions
        loadSettingsForGroup,
        loadConfiguration,
        refreshAdminPermissions,
    };
};