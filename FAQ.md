# Wellness Bot - Frequently Asked Questions (FAQ)

## General Questions

### What is Wellness Bot?
Wellness Bot is a Telegram-based platform for running wellness challenges and programs within Telegram groups. It enables administrators to create events, track participant activities, award points, and maintain leaderboards.

### Who is this for?
- **Organizations**: Run wellness programs for employees
- **Communities**: Organize group challenges
- **Teams**: Track team activities and engagement
- **Fitness Groups**: Manage workout challenges
- **Educational Institutions**: Student wellness programs

### Is this free to use?
The software itself is open source, but it operates on a subscription model for member capacity:
- **Basic Plan**: 25 members - $X/month
- **Pro Plan**: 50 members - $Y/month
- **Premium Plan**: 100 members - $Z/month

(Pricing configured by deployment administrator)

## Capacity & Scalability

### How many users can use this at the same time?

The answer depends on what you mean by "users":

#### 1. **Administrators**
- **Unlimited** concurrent administrators can manage their events
- Each admin has their own dashboard and settings
- No limit on the number of admins in the system

#### 2. **Telegram Groups**
- **Unlimited** groups can run simultaneously
- Each group operates independently
- Groups can have different events and configurations

#### 3. **Members per Admin** (Subscription-Based)
This is where limits apply:
- **Basic Plan**: Up to 25 members total across all your groups
- **Pro Plan**: Up to 50 members total across all your groups
- **Premium Plan**: Up to 100 members total across all your groups

**Example**: If you have Premium Plan with 3 groups:
- Group A: 40 members
- Group B: 35 members  
- Group C: 25 members
- **Total: 100 members** ✅ (within limit)

#### 4. **System-Wide Capacity** (Technical Limits)

With default single-instance deployment:
- **Total active members**: 1,000-5,000 across all admins
- **Concurrent groups**: 50-100
- **Message processing**: ~30 messages per second
- **API requests**: ~100 requests per second

For higher capacity, see the ARCHITECTURE.md file for scaling strategies.

### What happens if I exceed my member limit?
- The system prevents new members from joining when you hit your subscription limit
- Existing members continue to function normally
- You'll need to upgrade your subscription plan to add more members
- You can also remove inactive members to free up slots

### Can I have multiple groups with different settings?
**Yes!** Each group can have:
- Different event configurations
- Different activity slots and schedules
- Different point systems
- Different welcome messages and responses
- Independent member tracking

All groups share the same member limit from your subscription.

### How do I scale beyond 100 members?
For organizations needing more than 100 members:

1. **Contact for Enterprise Plan**: Custom pricing for higher limits
2. **Deploy Your Own Instance**: Host your own version with custom limits
3. **Multiple Accounts**: Use multiple admin accounts (not recommended)
4. **Scale Infrastructure**: See ARCHITECTURE.md for technical scaling

## Technical Questions

### What technology stack does this use?
- **Backend**: Python 3.8+ with Flask
- **Bot Framework**: python-telegram-bot
- **Database**: MySQL 8.0+
- **Frontend**: React + TypeScript + Vite
- **APIs**: REST API for admin operations

### What are the server requirements?

**Minimum (Development)**:
- 2 GB RAM
- 1 CPU core
- 10 GB storage
- MySQL 8.0+
- Python 3.8+

**Recommended (Production - 100 groups)**:
- 4 GB RAM
- 2 CPU cores
- 50 GB storage
- Stable internet connection

**Enterprise (500+ groups)**:
- 16 GB RAM
- 4-8 CPU cores
- 200 GB storage
- Load balancer
- Database replication

### Can I self-host this?
**Yes!** The project is open source. You can:
- Deploy on your own server
- Customize member limits
- Modify features as needed
- Remove subscription restrictions
- Use your own Telegram bot token

See README.md for installation instructions.

### Does it work with private Telegram groups?
**Yes!** The bot works with:
- Public groups
- Private groups
- Channels (limited functionality)

The bot needs to be added as a member and optionally as an administrator.

### How is data stored?
- **Database**: MySQL stores all user data, events, and configurations
- **Files**: Images and media stored in local file system
- **Sessions**: No session data stored (stateless design)
- **Backups**: Regular database backups recommended

### Is my data secure?
Security measures include:
- Password hashing (bcrypt)
- Parameterized SQL queries (prevent SQL injection)
- Role-based access control
- HTTPS/TLS for API communication
- Telegram's encrypted messaging
- Environment variable protection

## Usage Questions

### How do I get started as an admin?

1. **Register**: Create an admin account via the admin panel
2. **Subscribe**: Choose a subscription plan (Basic/Pro/Premium)
3. **Create Event**: Set up your wellness event with activities
4. **Configure Bot**: Customize messages and settings
5. **Add to Group**: Add the bot to your Telegram group
6. **Generate IDs**: Create unique user IDs for participants
7. **Distribute**: Share IDs with your team members
8. **Monitor**: Track participation via the admin dashboard

### How do participants join?

1. **Receive ID**: Admin provides unique user ID
2. **Join Group**: Member joins the Telegram group
3. **Register**: Follow bot instructions to register with unique ID
4. **Participate**: Respond to activity prompts and earn points
5. **Track**: View leaderboard and personal progress

### What types of activities can I track?
The bot supports time-based activity slots where you can track:
- **Morning routines**: Exercise, meditation, etc.
- **Daily check-ins**: Water intake, meal logging
- **Scheduled activities**: Yoga sessions, walks
- **Custom prompts**: Any activity with a time window
- **Button responses**: Quick-response activities

Each activity has:
- Custom time slot (start/end time)
- Point value
- Bot prompt message
- Response confirmation
- Optional images
- Button-based or text-based responses

### Can I have different point values for activities?
**Yes!** You can customize:
- Points per activity slot
- Bonus points for streaks
- Penalty points for missed activities
- Pass/fail thresholds
- Warning system

### How does the leaderboard work?
- **Automatic generation**: Updated in real-time as points are earned
- **Scheduled posting**: Can be posted at specific times
- **Ranking**: Members ranked by total points
- **Visibility**: Shown to all group members
- **Privacy**: Members identified by names or unique IDs

### Can members join mid-challenge?
Yes, but:
- They start with 0 points
- Previous days' activities cannot be completed retroactively
- They compete from their join date forward
- Admins can manually adjust points if needed

## Configuration Questions

### Can I customize bot messages?
**Yes!** You can customize:
- Welcome messages
- Activity prompts
- Success responses
- Failure responses
- Warning messages
- Kick messages
- Leaderboard format
- Help text

All via the admin panel.

### Can I set different time zones?
Currently, the bot uses server time. For multi-timezone support:
- Set activity slots to accommodate all time zones
- Use UTC and inform participants to convert
- Future enhancement: per-member timezone settings

### Can I ban certain words or responses?
**Yes!** The admin panel allows you to:
- Configure banned words list
- Automatic warning for violations
- Kick after multiple violations
- Custom violation response messages

### How do I change my subscription plan?
1. **Upgrade**: Process payment for higher plan
2. **Automatic**: System automatically uses highest plan purchased
3. **Immediate**: New limits apply immediately
4. **No downgrade**: Current implementation keeps highest plan

### Can I run multiple events in the same group?
Currently, each group runs one event at a time. For multiple events:
- Use different groups for different events
- Create sequential events (one after another)
- Future enhancement: concurrent events per group

## Troubleshooting

### Bot not responding in group?
**Checklist**:
1. ✅ Bot added to group?
2. ✅ Bot has admin permissions (if required)?
3. ✅ Group configured with license key?
4. ✅ Event is active?
5. ✅ Bot server is running?
6. ✅ Database connection working?

### Members can't register?
**Common issues**:
- Member limit reached (check subscription)
- Invalid unique user ID
- ID already used by another member
- Group not properly configured
- Bot lacks permissions

### Leaderboard not posting?
**Check**:
- Leaderboard time configured correctly
- Bot has permission to post in group
- At least one member has points
- Event is active
- Server time matches expected time

### API errors in admin panel?
**Verify**:
- API server is running (port 8001)
- CORS settings allow admin panel origin
- Database connection is active
- Correct API endpoint configuration
- Network connectivity

### Points not updating?
**Reasons**:
- Response outside activity time slot
- Incorrect response format
- Banned word used
- Member not properly registered
- Database write failure

## Payment & Subscription

### What payment methods are accepted?
This depends on your deployment. The system records:
- Transaction ID
- Plan name
- Amount
- Duration
- Status

Payment processing is handled externally (integration required).

### Can I get a refund?
Refund policies depend on your service provider. The system supports:
- Transaction status tracking
- Refund status recording
- Subscription history

### Does my subscription auto-renew?
This depends on your payment integration. The system tracks:
- Subscription duration
- Expiration dates
- Payment history

### What happens if my subscription expires?
Implementation-dependent, but typically:
- Existing members continue to function
- Cannot add new members
- Warning notifications
- Grace period (configurable)
- Eventually restricted access

## Advanced Questions

### Can I integrate with other systems?
**Yes!** Via the REST API:
- Member data export
- Point tracking integration
- Event data access
- Custom reporting
- Third-party authentication

API documentation in README.md

### Can I customize the source code?
**Yes!** It's open source:
- Modify features
- Add integrations
- Change business logic
- Remove restrictions
- Contribute back to community

### Can I white-label this?
**Yes!** You can:
- Change bot name
- Customize all messages
- Update branding
- Modify admin panel theme
- Remove original branding

### Can I migrate from another system?
Possible with custom scripts:
- Export data from old system
- Format for MySQL import
- Import users, events, points
- Validate data integrity
- Test before production

### How do I backup my data?
**Database backup**:
```bash
mysqldump -u username -p telegram_bot_manager > backup.sql
```

**Restore**:
```bash
mysql -u username -p telegram_bot_manager < backup.sql
```

**Files**:
```bash
tar -czf storage_backup.tar.gz ./storage
```

**Automation**: Set up cron jobs for regular backups

### Can I contribute to the project?
**Yes!** Contributions welcome:
- Bug reports
- Feature requests
- Code contributions
- Documentation improvements
- Translation support

See GitHub repository for contribution guidelines.

## Support

### Where can I get help?
- **Documentation**: README.md and ARCHITECTURE.md
- **GitHub Issues**: Report bugs and feature requests
- **Code Review**: Check source code for details
- **Community**: Join discussion forums (if available)

### How do I report a bug?
1. Check existing GitHub issues
2. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Error messages/logs

### How do I request a feature?
1. Search existing feature requests
2. Create GitHub issue with:
   - Feature description
   - Use case
   - Expected benefits
   - Mockups/examples (if applicable)

### Is there professional support available?
Depends on deployment model:
- **Open source**: Community support via GitHub
- **Managed hosting**: Support from service provider
- **Enterprise**: Custom support agreements

---

## Quick Reference

### Subscription Limits
| Plan    | Members | Price      |
|---------|---------|------------|
| Basic   | 25      | $X/month   |
| Pro     | 50      | $Y/month   |
| Premium | 100     | $Z/month   |

### System Capacity (Default)
- **Groups**: 50-100 concurrent
- **Total Members**: 1,000-5,000
- **Message Rate**: 30/second
- **API Rate**: 100 requests/second

### Key Links
- **GitHub**: [Repository URL]
- **Documentation**: README.md, ARCHITECTURE.md
- **Admin Panel**: http://localhost:5173 (dev)
- **API**: http://localhost:8001 (dev)

---

**Last Updated**: 2025-11-10

For more detailed technical information, see ARCHITECTURE.md
For installation and setup, see README.md
