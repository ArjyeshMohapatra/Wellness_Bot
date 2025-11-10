# Wellness Bot - Architecture & Scalability Guide

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Platform                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Bot API (Polling/Webhook)
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Wellness Bot Instance                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Handlers   │  │   Services   │  │  Bot Utils   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ MySQL Connector
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    MySQL Database                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │ Users  │  │Events  │  │Groups  │  │Members │           │
│  └────────┘  └────────┘  └────────┘  └────────┘           │
└─────────────────────────────────────────────────────────────┘
                        ▲
                        │
                        │ REST API Calls
                        │
┌─────────────────────────────────────────────────────────────┐
│                    Flask API Server                          │
│                   (simple_api.py)                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP/CORS
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Admin Panel (React + Vite)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Dashboard  │  │Event Config  │  │ User Mgmt    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Telegram Bot (`src/main.py`)

**Technology**: Python 3.8+, python-telegram-bot 22.5+

**Key Responsibilities**:
- Handle incoming messages from Telegram groups
- Process user commands and responses
- Validate user participation in time slots
- Calculate and update points
- Send leaderboards and notifications
- Enforce group rules and member limits

**Handlers** (`src/handlers/`):
- `join_handler.py` - New member onboarding
- Message processing handlers
- Callback query handlers
- Command handlers

**Services** (`src/services/`):
- `database_service.py` - Database operations
- `file_storage.py` - Media file management

**Scalability Considerations**:
- Uses async/await for non-blocking I/O
- Connection pooling for database
- Event-driven architecture
- Stateless design (all state in database)

### 2. Flask API (`simple_api.py`)

**Technology**: Flask 2.3+, Flask-CORS 4.0+

**Key Responsibilities**:
- Admin authentication and authorization
- Event and bot configuration management
- Payment transaction recording
- Unique user ID generation
- Group configuration API
- Real-time sync notifications

**API Architecture**:
- RESTful endpoints
- JSON request/response format
- CORS enabled for frontend access
- Error handling with appropriate HTTP status codes

**Key Endpoints**:

**Authentication**:
```
POST /api/admin/register
POST /api/admin/login
POST /api/admin/reset-password
```

**Event Management**:
```
GET  /api/admin/events
POST /api/admin/events
GET  /api/admin/bot/settings
POST /api/admin/bot/settings/save
```

**Subscription & Payments**:
```
POST /api/payment/transaction
GET  /api/payment/check-subscription
```

**Group Operations**:
```
POST /api/admin/panel/save
GET  /api/admin/panel/config
POST /api/admin/generate-unique-user-ids
GET  /api/admin/get-available-user-ids
```

### 3. Admin Panel (`admin-panel/`)

**Technology**: React 18, TypeScript, Vite

**Key Features**:
- Admin authentication UI
- Event creation and configuration
- Bot settings management
- Payment plan selection
- Unique ID generation interface
- Group management dashboard
- Real-time configuration sync

**Build Configuration**:
- Vite for fast development and optimized production builds
- TypeScript for type safety
- ESLint for code quality

### 4. Database Schema (`sql/schema.sql`)

**Technology**: MySQL 8.0+ with UTF-8MB4 support

**Core Tables**:

**users** - Admin accounts
```sql
- id (PK)
- telegram_id (unique)
- email (unique)
- password_hash
- role (admin/developer)
- subscription details
```

**events** - Wellness events/challenges
```sql
- event_id (PK)
- admin_user_id (FK)
- event_name
- event_type
- event_days
- license_key (unique)
- start_date, end_date
```

**groups_config** - Telegram group settings
```sql
- config_id (PK)
- group_id (unique)
- event_id (FK)
- admin_user_id (FK)
- max_members
- bot settings
```

**group_members** - Participant tracking
```sql
- member_id (PK)
- user_id (telegram_id)
- group_id (FK)
- unique_user_id (unique)
- total_points
- participation stats
```

**payment_transactions** - Subscription payments
```sql
- id (PK)
- user_id (FK)
- plan_name
- amount
- status
```

**admin_subscription_limits** - Member capacity
```sql
- admin_user_id (PK)
- max_members
- current_total_members
```

## Concurrency & Threading Model

### Telegram Bot
- **Async I/O**: Uses Python asyncio for non-blocking operations
- **Thread Pool**: python-telegram-bot manages internal thread pool
- **Message Queue**: Built-in message queuing by python-telegram-bot
- **Concurrent Handlers**: Multiple message handlers can run simultaneously

### Flask API
- **WSGI Server**: Runs with default Flask development server (single-threaded)
- **Production**: Should use Gunicorn/uWSGI with multiple workers
- **Database Connections**: Connection pooling prevents connection exhaustion

### Database
- **Connection Pool**: Configured in `db.py` with `init_db_pool()`
- **Concurrent Queries**: MySQL handles concurrent reads/writes
- **Transactions**: Used for critical operations (payments, member limits)
- **Indexes**: Optimized for common query patterns

## Scalability Analysis

### Current Capacity

**Single Instance Limits**:
- **Telegram Bot**: ~30 messages/second (Telegram API limit)
- **Flask API**: ~100 requests/second (single worker)
- **Database**: ~1000 queries/second (depends on hardware)
- **Total Groups**: 50-100 concurrent groups
- **Total Members**: 1,000-5,000 active members

### Bottlenecks & Solutions

#### 1. Telegram Rate Limits

**Problem**: Telegram enforces rate limits
- 20 messages/minute to same group
- 30 messages/second overall

**Solutions**:
- Implement message batching
- Use message queues with rate limiting
- Distribute across multiple bot instances with different tokens

#### 2. Database Connection Pool

**Problem**: Limited connection pool size

**Current**: Default pool size in `db.py`

**Solutions**:
```python
# Increase pool size
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="wellness_pool",
    pool_size=32,  # Increase from default
    pool_reset_session=True,
    host=config.DB_HOST,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    database=config.DB_NAME
)
```

#### 3. API Response Time

**Problem**: Slow API responses under load

**Solutions**:
- Deploy with Gunicorn: `gunicorn -w 4 -b 0.0.0.0:8001 simple_api:app`
- Add Redis caching for frequently accessed data
- Optimize database queries with proper indexes
- Use CDN for static admin panel assets

#### 4. Message Processing Latency

**Problem**: High latency during peak usage

**Solutions**:
- Implement background task queue (Celery + Redis)
- Process non-critical tasks asynchronously
- Cache bot settings in memory
- Pre-compute leaderboards

## Scaling Strategies

### Vertical Scaling (Scale Up)

**Increase server resources**:
- More CPU cores for concurrent processing
- More RAM for larger connection pools
- Faster SSD storage for database
- Better network bandwidth

**Expected Improvement**:
- 2x CPU cores → ~1.8x capacity
- 2x RAM → ~1.5x capacity
- SSD → 2-3x database performance

### Horizontal Scaling (Scale Out)

#### Option 1: Multiple Bot Instances

**Setup**:
```bash
# Instance 1 - Groups 1-50
BOT_TOKEN=token1 python -m src.main

# Instance 2 - Groups 51-100
BOT_TOKEN=token2 python -m src.main

# Instance 3 - Groups 101-150
BOT_TOKEN=token3 python -m src.main
```

**Load Distribution**:
- Round-robin by group_id
- Hash-based distribution
- Manual assignment

**Capacity**: Linear scaling (3x instances = ~3x capacity)

#### Option 2: API Server Cluster

**Setup**:
```bash
# Use Nginx load balancer
upstream api_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

# Gunicorn workers per instance
gunicorn -w 4 -b 0.0.0.0:8001 simple_api:app
gunicorn -w 4 -b 0.0.0.0:8002 simple_api:app
```

**Capacity**: 4 instances × 4 workers = 16x API capacity

#### Option 3: Database Replication

**Setup**:
```
Master Database (Writes)
    ├── Read Replica 1
    ├── Read Replica 2
    └── Read Replica 3
```

**Query Distribution**:
- All writes to master
- Read queries to replicas
- 80% of queries are reads

**Capacity**: ~4x read throughput

### Advanced Scaling Architecture

For enterprise deployments (10,000+ members):

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌───▼─────┐
    │ API     │         │ API     │         │ API     │
    │ Server 1│         │ Server 2│         │ Server 3│
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌───▼─────┐
    │ Bot     │         │ Bot     │         │ Bot     │
    │Instance1│         │Instance2│         │Instance3│
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Redis Cache    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌────▼────┐         ┌───▼─────┐
    │ MySQL   │         │ MySQL   │         │ MySQL   │
    │ Master  │─────────│ Replica1│─────────│ Replica2│
    └─────────┘         └─────────┘         └─────────┘
```

**Expected Capacity**:
- 50,000+ concurrent members
- 500+ concurrent groups
- 100+ administrators
- 500 messages/second processing

## Performance Optimization

### Database Optimization

**Indexes**:
```sql
-- Already indexed in schema
CREATE INDEX idx_telegram_id ON users(telegram_id);
CREATE INDEX idx_group_id ON groups_config(group_id);
CREATE INDEX idx_event_id ON bot_settings(event_id);
CREATE INDEX idx_user_group ON group_members(user_id, group_id);

-- Additional for performance
CREATE INDEX idx_member_points ON group_members(total_points DESC);
CREATE INDEX idx_transaction_user ON payment_transactions(user_id, status);
CREATE INDEX idx_event_admin ON events(admin_user_id, is_active);
```

**Query Optimization**:
```sql
-- Use prepared statements (already implemented)
-- Avoid SELECT * (use specific columns)
-- Use LIMIT for pagination
-- Use JOIN instead of subqueries where possible
```

### Caching Strategy

**Redis Implementation** (for future scaling):
```python
import redis

# Cache bot settings
r = redis.Redis(host='localhost', port=6379, db=0)

def get_bot_settings(event_id):
    cache_key = f"bot_settings:{event_id}"
    cached = r.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    settings = fetch_from_db(event_id)
    
    # Cache for 5 minutes
    r.setex(cache_key, 300, json.dumps(settings))
    
    return settings
```

**Cache Invalidation**:
- Time-based expiration (TTL)
- Event-based invalidation (when settings change)
- Manual purge via admin panel

### Message Queue Implementation

**Celery + Redis** (for async tasks):
```python
from celery import Celery

celery_app = Celery('wellness_bot', broker='redis://localhost:6379/0')

@celery_app.task
def send_leaderboard_async(group_id):
    # Generate and send leaderboard
    # Non-blocking operation
    pass

@celery_app.task
def calculate_daily_points(group_id):
    # Calculate points for all members
    # Run as scheduled task
    pass
```

**Benefits**:
- Non-blocking API responses
- Better resource utilization
- Scheduled task execution
- Retry logic for failed tasks

## Monitoring & Observability

### Key Metrics to Track

**Bot Metrics**:
- Messages processed per second
- Average response time
- Error rate
- Active connections

**API Metrics**:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active sessions

**Database Metrics**:
- Connection pool usage
- Query execution time
- Slow query count
- Replication lag (if using replicas)

**Business Metrics**:
- Active groups
- Total members
- Subscription distribution
- Event completion rate

### Logging Strategy

**Bot Logging**:
```python
import logging

# Already configured in main.py
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Add file handler for production
file_handler = logging.FileHandler('bot.log')
logger.addHandler(file_handler)
```

**API Logging**:
```python
# Add request logging middleware
@app.before_request
def log_request():
    app.logger.info(f"{request.method} {request.path}")

@app.after_request
def log_response(response):
    app.logger.info(f"Response: {response.status_code}")
    return response
```

### Health Checks

**API Health Endpoint**:
```python
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check database connection
        execute_query("SELECT 1", fetch=True)
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
```

**Bot Health Check**:
```python
# Monitor polling status
# Log last successful message
# Alert on connection failures
```

## Deployment Recommendations

### Development Environment
- Single instance for all components
- SQLite or local MySQL
- No caching layer needed
- Development Flask server

### Staging Environment
- Separate bot and API instances
- Shared MySQL database
- Test with production-like data
- Gunicorn with 2-4 workers

### Production Environment (Small Scale)
- Dedicated bot instance
- Gunicorn API server (4-8 workers)
- MySQL with regular backups
- SSL/TLS encryption
- Monitoring and logging

### Production Environment (Large Scale)
- Multiple bot instances with load balancing
- API cluster behind load balancer
- MySQL master-slave replication
- Redis caching layer
- Message queue for async tasks
- Container orchestration (Docker + Kubernetes)
- Auto-scaling policies
- Comprehensive monitoring (Prometheus + Grafana)

## Security Considerations

### Authentication & Authorization
- Password hashing with bcrypt
- Role-based access control (RBAC)
- License key validation
- Session management

### Data Protection
- Parameterized SQL queries (prevent SQL injection)
- Input validation and sanitization
- CORS configuration
- Environment variable protection

### Network Security
- HTTPS/TLS for API
- Telegram's encrypted channels
- Database firewall rules
- Rate limiting on API endpoints

### Monitoring & Auditing
- Login attempt tracking
- Admin action logging
- Unusual activity detection
- Regular security audits

## Cost Analysis

### Infrastructure Costs (Monthly Estimates)

**Small Deployment** (100 groups, 2,500 members):
- VPS/EC2 Instance (4GB RAM): $20-40
- MySQL Database (managed): $15-30
- Storage (50GB): $5-10
- **Total**: ~$40-80/month

**Medium Deployment** (500 groups, 12,500 members):
- API Servers (2x 8GB RAM): $80-160
- Bot Instances (2x 4GB RAM): $40-80
- MySQL (managed, replicated): $100-200
- Redis Cache (2GB): $20-40
- Storage (200GB): $20-40
- **Total**: ~$260-520/month

**Large Deployment** (2,000 groups, 50,000 members):
- Load Balancer: $20-40
- API Servers (4x 16GB RAM): $320-640
- Bot Instances (4x 8GB RAM): $160-320
- MySQL Cluster: $400-800
- Redis Cluster: $100-200
- Message Queue: $50-100
- Storage (1TB): $50-100
- Monitoring: $50-100
- **Total**: ~$1,150-2,300/month

## Conclusion

The Wellness Bot system is designed with scalability in mind, supporting:
- **Current capacity**: 1,000-5,000 members across 50-100 groups
- **Horizontal scaling**: Easy addition of more instances
- **Vertical scaling**: Better hardware → better performance
- **Cost-effective**: Start small, scale as needed

For most use cases, the default single-instance deployment is sufficient. As your organization grows, the architecture supports incremental scaling without major rewrites.

The subscription-based member limits provide a natural business model that aligns with infrastructure capacity, ensuring sustainable growth.
