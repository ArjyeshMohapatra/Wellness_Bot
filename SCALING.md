# Wellness Bot - Scaling & Capacity Quick Reference

## TL;DR - How Many Users?

### Simple Answer
- **Admins**: Unlimited ✅
- **Groups**: Unlimited ✅
- **Members per Admin**: 25-100 (based on subscription plan) 📊
- **System Total**: 1,000-5,000 active members (single instance) 🖥️

### Subscription-Based Member Limits

| Subscription Plan | Max Members | Per Admin |
|------------------|-------------|-----------|
| Basic Plan       | **25**      | Total across all groups |
| Pro Plan         | **50**      | Total across all groups |
| Premium Plan     | **100**     | Total across all groups |

**Important**: Member limits are per administrator account, not per group.

**Example**: Premium plan admin with 100 member limit:
- ✅ Can have: 3 groups with 30, 40, and 30 members (total: 100)
- ❌ Cannot have: 3 groups with 40, 40, and 40 members (total: 120)

## Concurrent Usage Capacity

### What Can Run Simultaneously?

1. **Administrators**: 
   - ♾️ Unlimited concurrent admins
   - Each admin manages independently
   - No waiting or queuing

2. **Telegram Groups**:
   - ♾️ Unlimited groups (within system capacity)
   - 50-100 groups recommended per server instance
   - Each group runs its own event configuration

3. **Active Members**:
   - 1,000-5,000 total members (default single server)
   - Distributed across all groups and admins
   - Real-time message processing

4. **Message Processing**:
   - ~30 messages per second (Telegram API limit)
   - Asynchronous handling
   - Queue-based processing

## Technical Limits (Single Instance)

| Resource | Capacity | Bottleneck |
|----------|----------|------------|
| Concurrent Admins | Unlimited | Database connections |
| Concurrent Groups | 50-100 | Bot processing power |
| Total Members | 1,000-5,000 | Database + Bot processing |
| Messages/Second | ~30 | Telegram API rate limit |
| API Requests/Sec | ~100 | Flask single worker |
| Database Queries/Sec | ~1,000 | MySQL performance |

## When to Scale?

### Signs You Need to Scale

🔴 **Critical - Scale Now**:
- Response times > 5 seconds
- Bot frequently timing out
- Database connection errors
- Members reporting missed messages

🟡 **Warning - Plan to Scale**:
- > 70% of member capacity used
- > 40 groups active
- Response times > 2 seconds
- Peak usage causing slowdowns

🟢 **Healthy - No Action Needed**:
- < 50% member capacity
- < 30 groups active
- Response times < 1 second
- Smooth operation during peak hours

## Scaling Options

### Quick Wins (No Architecture Changes)

1. **Upgrade Server** ⬆️
   - More RAM: 4GB → 8GB
   - More CPU: 2 cores → 4 cores
   - Better storage: HDD → SSD
   - **Cost**: $20-50/month extra
   - **Capacity gain**: 1.5-2x

2. **Optimize Database** 🗄️
   - Add indexes on frequently queried fields
   - Increase connection pool size
   - Enable query caching
   - **Cost**: Free
   - **Capacity gain**: 1.3-1.5x

3. **Use Production Server** 🚀
   - Switch from Flask dev to Gunicorn
   - Multiple worker processes
   - **Cost**: Free
   - **Capacity gain**: 2-4x API performance

### Medium Effort Scaling

4. **Add Caching Layer** ⚡
   - Deploy Redis
   - Cache bot settings
   - Cache event configs
   - **Cost**: $20-40/month
   - **Capacity gain**: 2-3x

5. **Deploy Multiple Bot Instances** 🤖×3
   - Run 3 bot instances
   - Load balance across groups
   - **Cost**: $80-120/month
   - **Capacity gain**: ~3x

### Advanced Scaling

6. **Full Horizontal Scale** 🏗️
   - Multiple API servers
   - Multiple bot instances
   - Database replication
   - Load balancers
   - **Cost**: $500-1000/month
   - **Capacity gain**: 10-20x

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed scaling strategies.

## Capacity Planning

### Small Organization (1-50 people)
- **Plan**: Basic (25 members)
- **Groups**: 1-2
- **Server**: Shared hosting or small VPS (2GB RAM)
- **Cost**: ~$40/month total
- **Scaling**: Not needed

### Medium Organization (50-250 people)
- **Plan**: Premium (100 members) × 3 admins
- **Groups**: 5-10
- **Server**: Dedicated VPS (4GB RAM, 2 CPU)
- **Cost**: ~$150/month total
- **Scaling**: Consider caching

### Large Organization (250-1,000 people)
- **Plan**: Premium (100 members) × 10 admins
- **Groups**: 20-40
- **Server**: 2 VPS instances (8GB RAM, 4 CPU each)
- **Database**: Managed MySQL with replication
- **Caching**: Redis
- **Cost**: ~$500/month total
- **Scaling**: Multi-instance setup

### Enterprise (1,000+ people)
- **Plan**: Custom enterprise agreement
- **Groups**: 50-200
- **Server**: Kubernetes cluster (3-5 nodes)
- **Database**: MySQL cluster with read replicas
- **Caching**: Redis cluster
- **Queue**: RabbitMQ/Celery
- **Load Balancer**: Nginx/HAProxy
- **Cost**: $1,500-3,000/month
- **Scaling**: Full microservices

## Performance Targets

### Expected Response Times

| Operation | Target | Acceptable | Critical |
|-----------|--------|------------|----------|
| Bot message response | < 200ms | < 500ms | > 1s |
| API request | < 100ms | < 300ms | > 1s |
| Database query | < 50ms | < 100ms | > 500ms |
| Leaderboard generation | < 500ms | < 2s | > 5s |
| Member registration | < 200ms | < 500ms | > 2s |

### Monitoring Thresholds

Set alerts for:
- ⚠️ CPU usage > 70%
- ⚠️ RAM usage > 80%
- ⚠️ Database connections > 80% of pool
- ⚠️ Response time > 2 seconds
- ⚠️ Error rate > 1%
- ⚠️ Message queue backlog > 100

## Cost vs Capacity

### Infrastructure Cost Estimates

| Capacity | Members | Groups | Monthly Cost | Setup Effort |
|----------|---------|--------|--------------|--------------|
| Starter  | 100     | 5      | $40-60       | Low          |
| Small    | 500     | 20     | $100-150     | Low          |
| Medium   | 2,500   | 100    | $300-500     | Medium       |
| Large    | 10,000  | 400    | $1,000-1,500 | High         |
| Enterprise | 50,000 | 2,000  | $3,000-5,000 | Very High    |

**Costs include**: Server hosting, database, caching, storage, bandwidth

**Not included**: Staff time, support, backups, monitoring services

## Common Scenarios

### Scenario 1: Company Wellness Program
- **Company size**: 150 employees
- **Expected participation**: 80% (~120 people)
- **Solution**: 2 Premium admins (200 member capacity)
- **Groups**: 3-4 department groups
- **Cost**: ~$100/month
- **Scaling needed**: No

### Scenario 2: Multi-Client Consulting
- **Clients**: 10 companies
- **Members per client**: 20-50
- **Total members**: ~350
- **Solution**: 4 Premium admins (400 capacity)
- **Groups**: 10 (one per client)
- **Server**: Medium VPS with caching
- **Cost**: ~$300/month
- **Scaling needed**: Add caching layer

### Scenario 3: Educational Institution
- **Students**: 2,000 across multiple programs
- **Groups**: 30 (different cohorts/classes)
- **Solution**: Custom enterprise plan
- **Infrastructure**: Multi-instance with load balancing
- **Cost**: ~$1,500/month
- **Scaling needed**: Yes - full horizontal scaling

### Scenario 4: Fitness Community Platform
- **Total users**: 10,000+
- **Concurrent active**: 1,000-2,000
- **Groups**: 100+ challenge groups
- **Solution**: Enterprise deployment
- **Infrastructure**: Kubernetes cluster
- **Cost**: $3,000-5,000/month
- **Scaling needed**: Yes - microservices architecture

## Quick Decision Tree

```
How many total members?
├─ < 100 members
│  └─ ✅ Single instance, Basic/Premium plan
│     💰 $40-80/month
│
├─ 100-1,000 members
│  └─ ✅ Single instance + caching
│     💰 $150-300/month
│
├─ 1,000-5,000 members
│  └─ ⚠️ Multi-instance or upgrade server
│     💰 $500-1,000/month
│
└─ 5,000+ members
   └─ 🔴 Full horizontal scaling required
      💰 $1,500-5,000/month
```

## Action Items

### To Answer "How Many Users?"

When someone asks this question, clarify:

1. **"What type of users?"**
   - Admins managing events → Unlimited
   - Groups running concurrently → Unlimited (within system capacity)
   - Members participating → 25-100 per admin (subscription-based)

2. **"Concurrent or total?"**
   - Concurrent active users → ~1,000-5,000 (technical limit)
   - Total registered members → Based on subscription plans

3. **"Single instance or scalable?"**
   - Single server → 1,000-5,000 members
   - Scaled infrastructure → 50,000+ members possible

### Standard Response Template

> **"The Wellness Bot supports:**
> - **Unlimited** concurrent administrators
> - **Unlimited** Telegram groups
> - **25-100 members per admin** (based on subscription: Basic/Pro/Premium)
> - **1,000-5,000 total active members** on a single server instance
> 
> **For scaling beyond these limits:**
> - Deploy multiple bot instances → Linear scaling
> - Add database replication → 4x read capacity
> - Implement caching layer → 2-3x performance
> - Full horizontal scaling → 50,000+ members possible
>
> See our [Scaling Guide](SCALING.md) for details."

---

## Additional Resources

- **Full Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - Technical deep dive
- **Installation Guide**: [README.md](README.md) - Getting started
- **FAQ**: [FAQ.md](FAQ.md) - Common questions
- **Source Code**: Check database schema and API code for implementation details

---

**Quick Contact Guide**
- Need < 100 members? → Use default setup
- Need 100-1,000 members? → Plan for scaling  
- Need 1,000-5,000 members? → Multi-instance required
- Need 5,000+ members? → Contact for enterprise architecture
