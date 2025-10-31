import { useState, useEffect, useCallback } from 'react';
import type { Slot } from './useSlotConfiguration';

interface Event {
    event_id: number;
    admin_user_id: number;
    event_name: string;
    event_type: 'normal' | 'time-limited';
    event_days: number;
    slots_per_day: number;
    start_date: string;
    end_date: string;
    min_pass_points: number;
    license_key: string;
    is_active: boolean;
    created_at: string;
    groups: Array<{
        group_id: number;
        group_name: string;
        is_active: boolean;
    }>;
}

interface BotSettings {
    setting_id: number;
    event_id: number;
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
    // Events state
    const [events, setEvents] = useState<Event[]>([]);
    const [currentEvent, setCurrentEvent] = useState<Event | null>(null);

    // Bot settings state - now per event
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

    // Function to load settings for an event
    const loadSettingsForEvent = useCallback((settings: BotSettings) => {
        setBotUsername(settings.bot_username || 'BeHumanAgainBot');
        setHasAdminPermissions(settings.has_admin_permissions || false);
        setLoadedSlots(settings.loaded_slots || []);
    }, []);

    // Function to load events for admin
    const loadEvents = useCallback(async () => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) return;

            const response = await fetch(`http://localhost:8001/api/admin/events?admin_user_id=${adminUserId}`);
            const result = await response.json();
            if (result.success) {
                setEvents(result.events);
                if (result.events.length > 0 && !currentEvent) {
                    setCurrentEvent(result.events[0]);
                    loadSettingsForEvent(result.events[0]); // Assuming settings are included
                }
            }
        } catch (error) {
            console.error('Error loading events:', error);
        }
    }, [currentEvent, loadSettingsForEvent]);

    // Function to load configuration - loads events and current event settings
    const loadConfiguration = useCallback(async () => {
        try {
            // Load events first
            await loadEvents();

            // If we have a current event, load its settings
            if (currentEvent) {
                const settingsResponse = await fetch(`http://localhost:8001/api/admin/bot/settings?event_id=${currentEvent.event_id}`);
                const settingsResult = await settingsResponse.json();
                if (settingsResult.success && settingsResult.settings) {
                    setBotSettings(settingsResult.settings);
                    loadSettingsForEvent(settingsResult.settings);
                    setLicenseKey(currentEvent.license_key);
                }
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
        }
    }, [currentEvent, loadEvents, loadSettingsForEvent]);

    // Function to select an event
    const selectEvent = useCallback(async (event: Event) => {
        setCurrentEvent(event);
        setLicenseKey(event.license_key);
        // Load settings for this event
        try {
            const settingsResponse = await fetch(`http://localhost:8001/api/admin/bot/settings?event_id=${event.event_id}`);
            const settingsResult = await settingsResponse.json();
            if (settingsResult.success && settingsResult.settings) {
                setBotSettings(settingsResult.settings);
                loadSettingsForEvent(settingsResult.settings);
            } else {
                // If no settings found, create default settings
                setBotSettings(null);
            }
        } catch (error) {
            console.error('Error loading bot settings for event:', error);
            setBotSettings(null);
        }
    }, [loadSettingsForEvent]);

    // Function to add new event
    const addEvent = useCallback(async (eventName: string) => {
        try {
            const adminUserId = localStorage.getItem('userId');
            if (!adminUserId) return false;

            const response = await fetch('http://localhost:8001/api/admin/events', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    admin_user_id: parseInt(adminUserId),
                    event_name: eventName
                })
            });
            const result = await response.json();
            if (result.success) {
                await loadEvents(); // Reload events
                // Find and select the newly created event
                const newEvent = {
                    event_id: result.event_id,
                    admin_user_id: parseInt(adminUserId),
                    event_name: eventName,
                    event_type: 'normal' as const,
                    event_days: 7,
                    slots_per_day: 2,
                    start_date: new Date().toISOString().split('T')[0],
                    end_date: new Date(Date.now() + 3650 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                    min_pass_points: 250,
                    license_key: result.license_key,
                    is_active: true,
                    created_at: new Date().toISOString(),
                    groups: []
                };
                selectEvent(newEvent);
                return true;
            }
        } catch (error) {
            console.error('Error adding event:', error);
        }
        return false;
    }, [loadEvents, selectEvent]);

    // Function to refresh admin permissions
    const refreshAdminPermissions = useCallback(async () => {
        if (currentEvent) {
            const settingsResponse = await fetch(`http://localhost:8001/api/admin/bot/settings?event_id=${currentEvent.event_id}`);
            const settingsResult = await settingsResponse.json();
            if (settingsResult.success && settingsResult.settings) {
                setHasAdminPermissions(settingsResult.settings.has_admin_permissions || false);
            }
        }
    }, [currentEvent]);

    // Load saved configuration on component mount
    useEffect(() => {
        loadConfiguration();

        // Set up periodic refresh of admin permissions (every 30 seconds)
        const interval = setInterval(() => {
            refreshAdminPermissions();
        }, 30000);

        return () => clearInterval(interval);
    }, [loadConfiguration, refreshAdminPermissions]);

    return {
        // Events
        events,
        currentEvent,

        // State
        botSettings,
        showConfigurationDialog,
        configurationDialogData,
        loadedSlots,
        botUsername,
        hasAdminPermissions,
        licenseKey,

        // Setters
        setShowConfigurationDialog,
        setConfigurationDialogData,
        setLoadedSlots,
        setBotUsername,
        setHasAdminPermissions,
        setLicenseKey,

        // Functions
        loadConfiguration,
        selectEvent,
        addEvent,
        refreshAdminPermissions,
    };
};