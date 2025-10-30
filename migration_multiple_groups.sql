-- Migration script to support multiple groups per admin
-- Run this after backing up your database

USE telegram_bot_manager;

-- Step 1: Create new bot_settings table for per-admin per-group settings
CREATE TABLE IF NOT EXISTS bot_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NOT NULL,
    group_id BIGINT NOT NULL DEFAULT 0,
    license_key VARCHAR(50) COLLATE utf8mb4_unicode_520_ci,
    bot_username VARCHAR(255) COLLATE utf8mb4_unicode_520_ci DEFAULT 'WellnessBot',
    has_admin_permissions BOOLEAN DEFAULT FALSE,
    event_type ENUM('normal', 'time-limited') DEFAULT 'normal',
    event_name VARCHAR(255) COLLATE utf8mb4_unicode_520_ci,
    event_days INT DEFAULT 7,
    pass_points INT DEFAULT 250,
    slots_per_day INT DEFAULT 2,
    welcome_message TEXT COLLATE utf8mb4_unicode_520_ci,
    kick_response TEXT COLLATE utf8mb4_unicode_520_ci,
    undesignated_slot_response TEXT COLLATE utf8mb4_unicode_520_ci,
    leaderboard_time VARCHAR(10) COLLATE utf8mb4_unicode_520_ci DEFAULT '11:00',
    banned_words JSON,
    loaded_slots JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE KEY unique_admin_group_setting (admin_user_id, group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Step 2: Remove UNIQUE constraint on assigned_group_id in licenses
-- Check if index exists before dropping
SET @index_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = 'telegram_bot_manager' AND TABLE_NAME = 'licenses' AND INDEX_NAME = 'assigned_group_id');
SET @sql = IF(@index_exists > 0, 'ALTER TABLE licenses DROP INDEX assigned_group_id', 'SELECT "Index assigned_group_id does not exist, skipping"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 3: Remove UNIQUE constraint on license_key in groups_config
-- Check if index exists before dropping
SET @index_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA = 'telegram_bot_manager' AND TABLE_NAME = 'groups_config' AND INDEX_NAME = 'license_key');
SET @sql = IF(@index_exists > 0, 'ALTER TABLE groups_config DROP INDEX license_key', 'SELECT "Index license_key does not exist, skipping"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 4: Add a new table to track admin subscription limits and usage
CREATE TABLE IF NOT EXISTS admin_subscription_limits (
    admin_user_id INT PRIMARY KEY,
    max_members INT NOT NULL DEFAULT 0,
    current_total_members INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- Step 5: Migrate existing data from admin_dashboard_settings to bot_settings
-- For existing admins, create a default group setting
INSERT INTO bot_settings (
    admin_user_id,
    group_id,
    license_key,
    bot_username,
    has_admin_permissions,
    event_type,
    event_name,
    event_days,
    pass_points,
    slots_per_day,
    welcome_message,
    kick_response,
    undesignated_slot_response,
    leaderboard_time,
    banned_words,
    loaded_slots
)
SELECT
    ads.admin_user_id,
    COALESCE(g.group_id, 0) as group_id, -- Use 0 for default/null group
    ads.license_key,
    ads.bot_username,
    ads.has_admin_permissions,
    ads.event_type,
    ads.event_name,
    ads.event_days,
    ads.pass_points,
    ads.slots_per_day,
    ads.welcome_message,
    ads.kick_response,
    ads.undesignated_slot_response,
    ads.leaderboard_time,
    ads.banned_words,
    ads.loaded_slots
FROM admin_dashboard_settings ads
LEFT JOIN groups_config g ON g.license_key = ads.license_key AND g.admin_user_id = ads.admin_user_id;

-- Step 6: Update admin_subscription_limits with current subscription data
INSERT INTO admin_subscription_limits (admin_user_id, max_members, current_total_members)
SELECT
    u.id,
    CASE
        WHEN MAX(pt.plan_name) = 'Basic' THEN 25
        WHEN MAX(pt.plan_name) = 'Pro' THEN 50
        WHEN MAX(pt.plan_name) = 'Enterprise' THEN 100
        ELSE 0
    END as max_members,
    COALESCE(gm_total.total_members, 0) as current_total_members
FROM users u
LEFT JOIN payment_transactions pt ON pt.user_id = u.id AND pt.status = 'completed'
LEFT JOIN (
    SELECT gc.admin_user_id, COUNT(gm.member_id) as total_members
    FROM groups_config gc
    LEFT JOIN group_members gm ON gm.group_id = gc.group_id
    GROUP BY gc.admin_user_id
) gm_total ON gm_total.admin_user_id = u.id
WHERE u.role = 'admin' AND u.is_active = TRUE
GROUP BY u.id, gm_total.total_members;

-- Step 7: Add triggers to automatically update member counts
DELIMITER //

CREATE TRIGGER update_member_count_on_insert
AFTER INSERT ON group_members
FOR EACH ROW
BEGIN
    UPDATE admin_subscription_limits
    SET current_total_members = current_total_members + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE admin_user_id = (
        SELECT admin_user_id FROM groups_config WHERE group_id = NEW.group_id
    );
END//

CREATE TRIGGER update_member_count_on_delete
AFTER DELETE ON group_members
FOR EACH ROW
BEGIN
    UPDATE admin_subscription_limits
    SET current_total_members = GREATEST(current_total_members - 1, 0),
        updated_at = CURRENT_TIMESTAMP
    WHERE admin_user_id = (
        SELECT admin_user_id FROM groups_config WHERE group_id = OLD.group_id
    );
END//

DELIMITER ;

-- Step 8: Update groups_config to include setting_id reference
ALTER TABLE groups_config ADD COLUMN setting_id INT NULL;
ALTER TABLE groups_config ADD FOREIGN KEY (setting_id) REFERENCES bot_settings (setting_id) ON DELETE SET NULL;

-- Update existing groups_config with setting_id
UPDATE groups_config gc
JOIN bot_settings bs ON bs.admin_user_id = gc.admin_user_id AND bs.group_id = gc.group_id
SET gc.setting_id = bs.setting_id;