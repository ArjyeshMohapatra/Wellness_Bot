-- Update existing slots with response_positive and response_clarify messages
USE telegram_bot_manager;

UPDATE group_slots SET 
    response_positive = 'Great start to your day! ✅ +10 points',
    response_clarify = 'Is this your morning routine message?'
WHERE slot_name = 'Good Morning';

UPDATE group_slots SET 
    response_positive = 'Amazing workout! 💪 +30 points',
    response_clarify = 'Is this your workout photo?'
WHERE slot_name = 'Workout';

UPDATE group_slots SET 
    response_positive = 'Healthy breakfast! 🍳 +25 points',
    response_clarify = 'Is this your breakfast photo?'
WHERE slot_name = 'Breakfast';

UPDATE group_slots SET 
    response_positive = 'Great hydration! 💧 +2 points',
    response_clarify = 'Did you drink water?'
WHERE slot_name = 'Water Intake 1';

UPDATE group_slots SET 
    response_positive = 'Nutritious lunch! 🍱 +25 points',
    response_clarify = 'Is this your lunch photo?'
WHERE slot_name = 'Lunch';

UPDATE group_slots SET 
    response_positive = 'Healthy snack! 🍎 +15 points',
    response_clarify = 'Is this your snack photo?'
WHERE slot_name = 'Evening Snacks';

UPDATE group_slots SET 
    response_positive = 'Great hydration! 💧 +2 points',
    response_clarify = 'Did you drink water?'
WHERE slot_name = 'Water Intake 2';

UPDATE group_slots SET 
    response_positive = 'Delicious dinner! 🍽️ +25 points',
    response_clarify = 'Is this your dinner photo?'
WHERE slot_name = 'Dinner';

-- Verify the updates
SELECT slot_name, response_positive, response_clarify FROM group_slots ORDER BY start_time;
