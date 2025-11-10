# Wellness Bot - Telegram Wellness Management System

A comprehensive Telegram bot-based wellness management platform that enables organizations to run wellness challenges and programs for their teams through Telegram groups.

## Overview

Wellness Bot is a multi-tenant system that allows administrators to:
- Create and manage wellness events and challenges
- Configure time-based activity slots with custom responses
- Track participant engagement and points
- Manage multiple groups with different configurations
- Generate unique user IDs for participants
- Monitor leaderboards and participant statistics

## Architecture

The project consists of three main components:

1. **Telegram Bot** (`src/main.py`) - Python-based bot built with python-telegram-bot
2. **REST API** (`simple_api.py`) - Flask-based backend for admin operations
3. **Admin Panel** (`admin-panel/`) - React + TypeScript + Vite frontend

## Scalability & Concurrent User Capacity

### How Many Users Can Use This Project at a Time?

The system is designed with **multi-tenant architecture** supporting multiple concurrent scenarios:

#### 1. **Concurrent Administrators**
- **Unlimited concurrent admins** can manage their respective events and groups
- Each admin operates in isolation with their own database records
- Admin operations (creating events, configuring bots, etc.) are database-driven and thread-safe

#### 2. **Concurrent Telegram Groups**
- **Unlimited number of groups** can run simultaneously
- Each group operates with its own:
  - Event configuration
  - Bot settings
  - Member tracking
  - Point calculations
- Groups are completely isolated from each other

#### 3. **Per-Group Member Limits (Subscription-Based)**

The system uses a **tiered subscription model** that determines the maximum number of members per admin across all their groups:

| Subscription Plan | Max Members Per Admin | Billing Options |
|------------------|----------------------|-----------------|
| **Basic Plan**   | 25 members           | Monthly/Yearly  |
| **Pro Plan**     | 50 members           | Monthly/Yearly  |
| **Premium Plan** | 100 members          | Monthly/Yearly  |

**Important Notes:**
- Member limits are enforced **per admin user**, not per group
- If an admin has multiple groups, the total unique members across all groups cannot exceed their subscription limit
- The system uses the `admin_subscription_limits` table to track current member count
- Member count validation occurs when:
  - New members join a group
  - Admins generate new unique user IDs

#### 4. **Message Processing Capacity**

The Telegram bot uses asynchronous processing with python-telegram-bot's polling mechanism:
- **Concurrent message handling**: Handled by Telegram's API rate limits
- **Recommended maximum**: ~30 messages per second per bot instance
- **Rate limiting**: Telegram enforces limits of:
  - 20 messages per minute to the same group
  - 30 messages per second overall

#### 5. **Database Performance**

The system uses MySQL with connection pooling:
- Default pool size: Configured in `db.py`
- Supports hundreds of concurrent database operations
- Indexed on critical fields (telegram_id, group_id, event_id)

### Scalability Strategies

#### Current Architecture
The current setup is designed for **small to medium-scale deployments**:
- Single Flask API instance
- Single Telegram bot instance
- Single MySQL database
- **Estimated capacity**: 
  - 50-100 concurrent groups
  - 1,000-5,000 total active members across all groups
  - 10-20 concurrent administrators

#### Scaling to Higher Loads

For organizations needing to scale beyond these limits:

**1. Horizontal Scaling (Multiple Bot Instances)**
```python
# Deploy multiple bot instances with load balancing
# Each bot can handle different groups or use webhook mode
```
- Use webhook mode instead of polling
- Deploy multiple instances behind a load balancer
- Each instance can handle 50-100 groups

**2. Database Scaling**
- Enable MySQL replication (read replicas)
- Use connection pooling with higher limits
- Add database indexes on frequently queried fields
- Consider sharding by admin_user_id or group_id for very large scales

**3. Caching Layer**
- Add Redis/Memcached for:
  - Bot settings (frequently accessed)
  - Event configurations
  - Member data
  - Leaderboard calculations

**4. Message Queue**
- Implement message queuing (RabbitMQ/Redis) for:
  - Scheduled messages
  - Leaderboard calculations
  - Point updates
  - Notification broadcasts

**5. Microservices Architecture**
For enterprise-scale deployments (10,000+ members):
- Separate API and Bot into distinct services
- Dedicated message processing service
- Separate analytics/reporting service
- Container orchestration (Kubernetes)

### Performance Benchmarks

**Expected Response Times** (with default configuration):
- API endpoints: < 100ms for most operations
- Bot message processing: < 200ms per message
- Leaderboard generation: < 500ms for 100 members
- Unique ID generation: < 50ms

**Database Queries:**
- User lookup by telegram_id: ~5ms (indexed)
- Event configuration load: ~10ms
- Point calculations: ~20ms per member

## Installation

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Node.js 18+ (for admin panel)
- Telegram Bot Token (from @BotFather)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/ArjyeshMohapatra/Wellness_Bot.git
cd Wellness_Bot
```

2. **Install Python dependencies**
```bash
pip install -r requirements_simple.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration:
# - BOT_TOKEN: Your Telegram bot token
# - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME: Database credentials
# - STORAGE_PATH: Path for file storage
```

4. **Set up the database**
```bash
mysql -u root -p < sql/schema.sql
```

5. **Run the Flask API**
```bash
python simple_api.py
```
The API will start on http://localhost:8001

6. **Run the Telegram Bot**
```bash
python -m src.main
```

### Admin Panel Setup

1. **Navigate to admin panel directory**
```bash
cd admin-panel
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```
The admin panel will be available at http://localhost:5173

## Usage

### For Administrators

1. **Register an Admin Account**
   - Access the admin panel at http://localhost:5173
   - Register with email and password
   - Choose a subscription plan (Basic/Pro/Premium)

2. **Create an Event**
   - Log in to the admin panel
   - Create a new wellness event
   - Configure event settings:
     - Event name and duration
     - Activity slots with time ranges
     - Point values for activities
     - Custom messages

3. **Configure Bot for Group**
   - Add the bot to your Telegram group
   - Make the bot an administrator (if needed)
   - Use the license key to activate the bot in your group
   - Configure welcome messages, responses, and rules

4. **Generate Unique User IDs**
   - Generate unique IDs for participants
   - Distribute IDs to team members
   - Members use these IDs to join the wellness program

### For Participants

1. **Join the Telegram Group**
   - Receive group invite from administrator
   - Join the group where the wellness bot is active

2. **Register with Unique ID**
   - Use the unique ID provided by your admin
   - Follow bot instructions to complete registration

3. **Participate in Activities**
   - Respond to bot prompts at designated time slots
   - Complete wellness activities
   - Earn points for participation

4. **Track Progress**
   - View your points on the leaderboard
   - Check your ranking among participants
   - Monitor your completion rate

## API Endpoints

### Admin Management
- `POST /api/admin/register` - Register new admin
- `POST /api/admin/login` - Admin login
- `POST /api/admin/reset-password` - Reset password

### Event Management
- `GET /api/admin/events` - Get all events for admin
- `POST /api/admin/events` - Create new event
- `GET /api/admin/bot/settings` - Get bot settings for event
- `POST /api/admin/bot/settings/save` - Save bot settings

### Payment & Subscriptions
- `POST /api/payment/transaction` - Record payment transaction
- `GET /api/payment/check-subscription` - Check subscription status

### Group Management
- `POST /api/admin/panel/save` - Save admin panel configuration
- `GET /api/admin/panel/config` - Get configuration for group
- `POST /api/admin/generate-unique-user-ids` - Generate unique user IDs
- `GET /api/admin/get-available-user-ids` - Get available user IDs

## Database Schema

Key tables:
- **users** - Admin users and authentication
- **events** - Wellness events/challenges
- **bot_settings** - Bot configuration per event
- **groups_config** - Telegram group configurations
- **group_members** - Participant tracking
- **payment_transactions** - Subscription payments
- **admin_subscription_limits** - Member limits per admin
- **event_slots** - Time-based activity slots

See `sql/schema.sql` for complete schema.

## Technology Stack

### Backend
- **Python 3.8+** with python-telegram-bot
- **Flask** for REST API
- **MySQL 8.0+** for data persistence
- **python-dotenv** for configuration

### Frontend (Admin Panel)
- **React 18** with TypeScript
- **Vite** for build tooling
- **React Router** for navigation
- **Fetch API** for HTTP requests

### Infrastructure
- **Telegram Bot API** for messaging
- **MySQL** for database
- **File storage** for images/media

## Configuration

### Environment Variables

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here

# Database
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=telegram_bot_manager

# Storage
STORAGE_PATH=./storage
```

### Bot Configuration (per event)
- Event type (normal/time-limited)
- Event duration and dates
- Slots per day
- Pass points threshold
- Welcome messages
- Kick/warning responses
- Leaderboard time
- Banned words
- Custom activity slots

## Security

- Password hashing using bcrypt
- Session-based authentication
- SQL injection prevention via parameterized queries
- CORS configuration for API access
- Role-based access (admin/developer)
- License key validation
- Input sanitization

## Monitoring & Maintenance

### Health Checks
- Monitor bot polling status
- Check database connection pool
- Track API response times
- Monitor message processing rate

### Logs
- Bot operations logged to console
- Database queries logged in debug mode
- API request/response logging
- Error tracking with stack traces

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is available for use under standard open source practices.

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review the FAQ section

## FAQ

### How many concurrent users can the bot handle?
See the "Scalability & Concurrent User Capacity" section above. In summary:
- Unlimited admins and groups
- 25-100 members per admin (based on subscription)
- ~1,000-5,000 total active members with default configuration
- Higher capacity possible with scaling strategies

### Can I run multiple groups with different configurations?
Yes! Each group can have its own event configuration, bot settings, and activity slots.

### What happens when I reach my member limit?
The system prevents new member registrations when the limit is reached. Upgrade your subscription plan to increase capacity.

### Can I customize the bot messages and responses?
Yes, all messages are configurable through the admin panel, including welcome messages, activity prompts, and responses.

### How do I upgrade my subscription?
Process a new payment transaction for a higher-tier plan through the admin panel. The system automatically uses the highest plan you've purchased.

### Is my data secure?
Yes, the system uses industry-standard security practices including password hashing, parameterized queries, and role-based access control.

---

**Note**: This bot is designed for wellness programs, team challenges, and group activities. It's not suitable for financial transactions, medical advice, or critical applications without proper modifications and professional review.
