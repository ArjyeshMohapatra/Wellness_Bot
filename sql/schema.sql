DROP DATABASE IF EXISTS telegram_bot_manager;
CREATE DATABASE IF NOT EXISTS telegram_bot_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;
USE telegram_bot_manager;

-- LICENSES TABLE
CREATE TABLE IF NOT EXISTS licenses (
    license_id INT AUTO_INCREMENT PRIMARY KEY,
    license_key VARCHAR(50) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    assigned_group_id BIGINT UNIQUE,
    assigned_admin_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GROUPS CONFIG TABLE
CREATE TABLE IF NOT EXISTS groups_config (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL UNIQUE,
    license_key VARCHAR(50) NOT NULL UNIQUE,
    admin_user_id BIGINT NOT NULL,
    max_members INT DEFAULT 0,
    welcome_message TEXT,
    kick_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (license_key) REFERENCES licenses(license_key) ON DELETE CASCADE
);

-- EVENTS TABLE
CREATE TABLE IF NOT EXISTS events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    event_name VARCHAR(255) NOT NULL DEFAULT 'Wellness Challenge',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    min_pass_points INT DEFAULT 250,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE
);

-- GROUP SLOTS TABLE
CREATE TABLE IF NOT EXISTS group_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    event_id INT,
    slot_name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    initial_message TEXT,
    response_positive TEXT,
    response_clarify TEXT,
    image_file_path TEXT,
    slot_type VARCHAR(50) DEFAULT 'default',
    slot_points INT DEFAULT 10,
    is_mandatory BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);

-- SLOT KEYWORDS TABLE
CREATE TABLE IF NOT EXISTS slot_keywords (
    keyword_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_id INT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    FOREIGN KEY (slot_id) REFERENCES group_slots(slot_id) ON DELETE CASCADE
);

-- GROUP MEMBERS TABLE
CREATE TABLE IF NOT EXISTS group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name  VARCHAR(255),
    is_admin TINYINT(1) DEFAULT 0,
    total_points INT DEFAULT 0,
    knockout_points INT DEFAULT 0,
    general_warnings INT DEFAULT 0,
    banned_word_count INT DEFAULT 0,
    user_day_number INT DEFAULT 1,
    cycle_start_date DATE,
    cycle_end_date DATE,
    is_restricted TINYINT(1) DEFAULT 0,
    restriction_until TIMESTAMP NULL DEFAULT NULL,
    last_active_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, group_id),
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE
);

-- MEMBER HISTORY TABLE
CREATE TABLE IF NOT EXISTS member_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    total_points INT,
    knockout_points INT,
    general_warnings INT,
    banned_word_count INT,
    user_day_number INT,
    cycle_start_date DATE,
    cycle_end_date DATE,
    joined_at TIMESTAMP NULL,
    last_active_timestamp TIMESTAMP NULL,
    action ENUM('joined', 'left', 'kicked', 'banned') NOT NULL,
    action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE
);

-- BANNED WORDS TABLE
CREATE TABLE IF NOT EXISTS banned_words (
    word_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT DEFAULT NULL,
    word VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci NOT NULL,
    UNIQUE (group_id, word),
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci;

-- USER ACTIVITY LOG TABLE
CREATE TABLE IF NOT EXISTS user_activity_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    activity_type ENUM('text', 'photo', 'video', 'document', 'sticker', 'animation', 'voice', 'video_note', 'button') NOT NULL,
    slot_name VARCHAR(255),
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    message_content TEXT,
    telegram_file_id VARCHAR(255),
    local_file_path TEXT,
    points_earned INT DEFAULT 0,
    is_valid BOOLEAN DEFAULT TRUE,
    activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE
);

-- DAILY SLOT TRACKER TABLE
CREATE TABLE IF NOT EXISTS daily_slot_tracker (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    slot_id INT NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    log_date DATE NOT NULL,
    status ENUM('completed', 'missed', 'invalid') NOT NULL,
    points_scored INT DEFAULT 0,
    completion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duplicate_submissions INT DEFAULT 0,
    UNIQUE(event_id, slot_id, user_id, log_date),
    FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES group_slots(slot_id) ON DELETE CASCADE
);

-- INACTIVITY WARNINGS TABLE
CREATE TABLE IF NOT EXISTS inactivity_warnings (
    warning_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    warning_date DATE NOT NULL,
    warning_type ENUM('3day', '4day') NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups_config(group_id) ON DELETE CASCADE,
    UNIQUE(group_id, user_id, warning_date, warning_type)
);

CREATE TABLE IF NOT EXISTS runtime_state (
    state_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    state_key VARCHAR(100) NOT NULL,
    state_value VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE(group_id,state_key)
);

INSERT IGNORE INTO banned_words (group_id, word) VALUES 
-- English
(NULL, 'fuck'),(NULL, 'fucking'),(NULL, 'fucked'),(NULL, 'fucker'),(NULL, 'fck'),(NULL, 'fuk'),(NULL, 'f**k'),(NULL, 'shit'),
(NULL, 'shit'),(NULL, 'bullshit'),(NULL, 'bitch'),(NULL, 'bitches'),(NULL, 'asshole'),(NULL, 'ass'),(NULL, 'bastard'),
(NULL, 'damn'),(NULL, 'damned'),(NULL, 'idiot'),(NULL, 'stupid'),(NULL, 'dumb'),(NULL, 'dumbass'),(NULL, 'moron'),
(NULL, 'retard'),(NULL, 'retarded'),(NULL, 'cunt'),(NULL, 'dick'),(NULL, 'cock'),(NULL, 'prick'),(NULL, 'pussy'),
(NULL, 'whore'),(NULL, 'slut'),(NULL, 'hoe'),(NULL, 'hell'),(NULL, 'piss'),(NULL, 'crap'),(NULL, 'screw'),(NULL, 'suck'),
(NULL, 'sucks'),(NULL, 'wtf'),(NULL, 'stfu'),(NULL, 'motherfucker'),(NULL, 'mf'),(NULL, 'son of a bitch'),(NULL, 'sob'),
(NULL, 'jerk'),(NULL, 'jackass'),(NULL, 'douchebag'),(NULL, 'douche'),(NULL, 'scumbag'),(NULL, 'loser'),(NULL, 'gay'),
(NULL, 'fag'),(NULL, 'faggot'),(NULL, 'nigger'),(NULL, 'nigga'),(NULL, 'negro'),(NULL, 'chink'),(NULL, 'spic'),(NULL, 'kike'),(NULL,'heck'),

-- Hindi
(NULL, 'मादरचोद'),(NULL, 'भोसड़ीके'),(NULL, 'भोसड़ी'),(NULL, 'चूतिया'),(NULL, 'चूतिये'),(NULL, 'चूत'),(NULL, 'लंड'),(NULL, 'लौड़ा'),
(NULL, 'लौड़े'),(NULL, 'गांड'),(NULL, 'गाण्ड'),(NULL, 'हरामी'),(NULL, 'हरामजादा'),(NULL, 'हरामजादे'),(NULL, 'कुत्ता'),(NULL, 'कुत्ते'),
(NULL, 'कुतिया'),(NULL, 'साला'),(NULL, 'साली'),(NULL, 'रंडी'),(NULL, 'रंडीबाज'),(NULL, 'चोद'),(NULL, 'चोदना'),(NULL, 'बकवास'),
(NULL, 'बेवकूफ'),(NULL, 'गधा'),(NULL, 'उल्लू'),(NULL, 'कमीना'),(NULL, 'कमीने'),(NULL, 'झाटू'),(NULL, 'झंटू'),(NULL, 'बहनचोद'),
(NULL, 'बेटीचोद'),(NULL, 'भड़वा'),(NULL, 'भड़वे'),(NULL, 'गंदा'),(NULL, 'घटिया'),(NULL, 'चूतड़'),

-- Hinglish
(NULL, 'madarchod'),(NULL, 'maderchod'),(NULL, 'mc'),(NULL, 'bhosadike'),(NULL, 'bhosdi ke'),(NULL, 'bhosdike'),(NULL, 'bhosda'),(NULL, 'bsdk'),
(NULL, 'chutiya'),(NULL, 'chutiye'),(NULL, 'chut'),(NULL, 'lund'),(NULL, 'lauda'),(NULL, 'loda'),(NULL, 'gaand'),(NULL, 'gand'),
(NULL, 'harami'),(NULL, 'haramzada'),(NULL, 'haraamzaada'),(NULL, 'kutta'),(NULL, 'kutte'),(NULL, 'kutiya'),(NULL, 'saala'),(NULL, 'sala'),
(NULL, 'saali'),(NULL, 'sali'),(NULL, 'randi'),(NULL, 'randwa'),(NULL, 'chod'),(NULL, 'chodna'),(NULL, 'bakwaas'),(NULL, 'bevkoof'),
(NULL, 'bevakoof'),(NULL, 'gadha'),(NULL, 'gadhe'),(NULL, 'ullu'),(NULL, 'kamina'),(NULL, 'kamine'),(NULL, 'kamini'),(NULL, 'jhatu'),
(NULL, 'jhaat'),(NULL, 'bahenchod'),(NULL, 'behenchod'),(NULL, 'bc'),(NULL, 'betichod'),(NULL, 'bhadwa'),(NULL, 'bhadwe'),(NULL, 'ganda'),
(NULL, 'gandu'),(NULL, 'gandiya'),(NULL, 'chhakka'),(NULL, 'chakka'),(NULL, 'hijra'),

-- Odia
(NULL, 'ବେଶ୍ୟା'),(NULL, 'ଗଧ'),(NULL, 'ମୂର୍ଖ'),(NULL, 'ବୋକା'),(NULL, 'କୁକୁର'),(NULL, 'କୁତ୍ରୀ'),(NULL, 'ହରାମି'),(NULL, 'ଖାଇବା'),
(NULL, 'ଗାଣ୍ଡ'),(NULL, 'ଚୁତ'),(NULL, 'ଲଉଡ଼ା'),

-- Romanian Odia
(NULL, 'beshya'),(NULL, 'besia'),(NULL, 'gadha'),(NULL, 'murkha'),(NULL, 'boka'),(NULL, 'kukura'),(NULL, 'kutri'),(NULL, 'harami'),
(NULL, 'ganda'),(NULL, 'gaand'),(NULL, 'chut'),(NULL, 'lauda'),(NULL, 'sala'),(NULL, 'jhia'),(NULL, 'pagala'),(NULL, 'paagal'),

-- Bengali
(NULL, 'চোদা'),(NULL, 'চুদা'),(NULL, 'মাগি'),(NULL, 'মাগীর'),(NULL, 'বেশ্যা'),(NULL, 'হারামি'),(NULL, 'কুত্তা'),(NULL, 'শুয়োরের'),
(NULL, 'গাধা'),(NULL, 'বোকা'),(NULL, 'চোদনা'),

-- Romanian Bengali
(NULL, 'choda'),(NULL, 'chuda'),(NULL, 'magir'),(NULL, 'magi'),(NULL, 'beshya'),(NULL, 'harami'),(NULL, 'kutta'),(NULL, 'shuorer'),
(NULL, 'gadha'),(NULL, 'boka'),(NULL, 'chodna'),

-- Common variations
(NULL, 'f*ck'),(NULL, 'fu*k'),(NULL, 'f u c k'),(NULL, 'f.u.c.k'),(NULL, 'sh*t'),(NULL, 'sh!t'),(NULL, 's h i t'),(NULL, 'b*tch'),
(NULL, 'b!tch'),(NULL, 'a**hole'),(NULL, 'a$$hole'),(NULL, 'd*ck'),(NULL, 'd!ck'),(NULL, 'p*ssy'),(NULL, 'pu$$y'),(NULL, 'wh0re'),
(NULL, 'sl*t'),(NULL, 's1ut'),

-- Additional offensive terms
(NULL, 'rape'),(NULL, 'rapist'),(NULL, 'kill yourself'),(NULL, 'kys'),(NULL, 'die'),(NULL, 'suicide'),(NULL, 'terrorist'),(NULL, 'bomb'),
(NULL, 'murder'),(NULL, 'killer'),(NULL, 'hate you'),(NULL, 'disgusting'),(NULL, 'ugly'),(NULL, 'fatass'),(NULL, 'fatty'),(NULL, 'pig'),
(NULL, 'piggy'),(NULL, 'trash'),(NULL, 'garbage'),(NULL, 'worthless'),(NULL, 'pathetic'),(NULL, 'useless'),(NULL, 'noob'),(NULL, 'newbie'),
(NULL, 'suck my'),(NULL, 'eat shit'),(NULL, 'go to hell'),(NULL, 'fuck off'),(NULL, 'piss off'),(NULL, 'shut up'),(NULL, 'stfu'),
(NULL, 'get lost'),(NULL, 'bugger off'),

-- Hinglish variations
(NULL, 'teri maa'),(NULL, 'teri ma'),(NULL, 'teri behen'),(NULL, 'maa ki'),(NULL, 'maa ka'),(NULL, 'bhen ki'),(NULL, 'behen ki'),(NULL, 'baap ka'),
(NULL, 'baap ki'),(NULL, 'lund choosle'),(NULL, 'gand mara'),(NULL, 'gandu'),(NULL, 'chodu'),(NULL, 'chodumal'),(NULL, 'land ka'),(NULL, 'lund ka'),
(NULL, 'chutad'),(NULL, 'choot'),(NULL, 'bhenchod'),(NULL, 'madarchod'),(NULL, 'mkc'),(NULL, 'mlc'),(NULL, 'bkl'),(NULL, 'bhikari'),
(NULL, 'bhikhari'),(NULL, 'kanjoos'),(NULL, 'thulla'),(NULL, 'fuddu'),(NULL, 'phuddu'),(NULL, 'tatti'),(NULL, 'mut'),(NULL, 'peshaab'),
(NULL, 'hagna'),(NULL, 'haggu'),

-- Sexual/inappropriate content
(NULL, 'sex'),(NULL, 'sexy'),(NULL, 'porn'),(NULL, 'porno'),(NULL, 'nude'),(NULL, 'naked'),(NULL, 'breast'),(NULL, 'boobs'),
(NULL, 'tits'),(NULL, 'nipple'),(NULL, 'penis'),(NULL, 'vagina'),(NULL, 'blowjob'),(NULL, 'handjob'),(NULL, 'masturbate'),(NULL, 'orgasm'),
(NULL, 'horny'),(NULL, 'stripper'),(NULL, 'prostitute'),(NULL, 'pimp'),(NULL, 'escort'),

-- Drug references
(NULL, 'weed'),(NULL, 'marijuana'),(NULL, 'ganja'),(NULL, 'charas'),(NULL, 'cocaine'),(NULL, 'heroin'),(NULL, 'meth'),(NULL, 'drugs'),
(NULL, 'addict'),(NULL, 'junkie'),(NULL, 'drunk'),(NULL, 'alcoholic'),

-- Offensive gestures/actions
(NULL, 'middle finger'),(NULL, 'flip off'),(NULL, 'bird'),(NULL, 'giving the finger'),

-- More variations and misspellings
(NULL, 'phuck'),(NULL, 'phuk'),(NULL, 'fook'),(NULL, 'fuc'),(NULL, 'fk'),(NULL, 'phek'),(NULL, 'shyt'),(NULL, 'shiit'),
(NULL, 'shiet'),(NULL, 'beatch'),(NULL, 'biatch'),(NULL, 'biotch'),(NULL, 'azz'),(NULL, 'asz'),(NULL, 'butthole'),(NULL, 'asswhole'),
(NULL, 'dumass'),(NULL, 'dumas'),(NULL, 'dumbfuck'),(NULL, 'mofo'),(NULL, 'mutha'),(NULL, 'cracka'),(NULL, 'cracker'),(NULL, 'honky'),
(NULL, 'whitey'),(NULL, 'brownie'),(NULL, 'paki'),(NULL, 'chinki'),(NULL, 'negro'),(NULL, 'darkie'),

-- Additional Hindi/Hinglish
(NULL, 'teri'),(NULL, 'tera'),(NULL, 'tere'),(NULL, 'maa chod'),(NULL, 'bhen chod'),(NULL, 'bap chod'),(NULL, 'chod de'),(NULL, 'mar jaa'),
(NULL, 'mar ja'),(NULL, 'jaa mar'),(NULL, 'ja mar'),(NULL, 'kamine'),(NULL, 'nalayak'),(NULL, 'nalayak'),(NULL, 'nikamma'),(NULL, 'faaltu'),
(NULL, 'faltu'),(NULL, 'bewda'),(NULL, 'sharaabi'),(NULL, 'sharabi'),(NULL, 'chutiya pan'),(NULL, 'chutiyapa'),(NULL, 'bakchodi'),(NULL, 'haggu'),
(NULL, 'peshaabi'),

-- Body shaming terms
(NULL, 'fat'),(NULL, 'fatso'),(NULL, 'obese'),(NULL, 'chubby'),(NULL, 'skinny'),(NULL, 'anorexic'),(NULL, 'midget'),(NULL, 'dwarf'),
(NULL, 'short'),(NULL, 'tall freak'),(NULL, 'giant'),(NULL, 'hairy'),(NULL, 'bald'),(NULL, 'baldhead'),(NULL, 'four eyes'),

-- Additional insults
(NULL, 'screw you'),(NULL, 'damn you'),(NULL, 'curse you'),(NULL, 'to hell with'),(NULL, 'bloody'),(NULL, 'bloody hell'),(NULL, 'bloody fool'),
(NULL, 'son of bitch'),(NULL, 'piece of shit'),(NULL, 'full of shit'),(NULL, 'eat my'),(NULL, 'kiss my'),(NULL, 'bite me'),(NULL, 'blow me'),
(NULL, 'screw off'),(NULL, 'get stuffed'),(NULL, 'up yours'),(NULL, 'your mom'),(NULL, 'your mother'),(NULL, 'yo mama'),(NULL, 'yo momma');
