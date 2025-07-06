# DigitalOcean Basic Plan Deployment Guide ($10/mo)

This guide is specifically optimized for the DigitalOcean App Platform Basic plan:
- **$10.00/mo**
- **1 GB RAM**
- **1 Shared vCPU** 
- **100 GB bandwidth**

## Quick Start

### Prerequisites
1. DigitalOcean account
2. External PostgreSQL database (required)
3. GitHub repository with your Tabbycat code

### 1. Setup External Database

Since the Basic plan doesn't include a database, you'll need an external PostgreSQL database:

#### Option A: DigitalOcean Managed Database (Recommended)
```bash
# Create a PostgreSQL database (starts at $15/mo)
doctl databases create tabbycat-db --engine pg --region nyc1 --size db-s-1vcpu-1gb

# Get connection details
doctl databases connection tabbycat-db
```

#### Option B: External Providers (Cost-effective options)
- **Railway**: $5/mo for PostgreSQL
- **Supabase**: Free tier available
- **ElephantSQL**: Free tier available
- **AWS RDS**: Free tier for 12 months
- **Google Cloud SQL**: $7/mo minimum

### 2. Deploy Using Basic Configuration

Use the optimized configuration for the Basic plan:

```bash
# Deploy using the basic configuration
doctl apps create --spec .do/app-basic.yaml
```

Or manually through the DigitalOcean dashboard:
1. Go to Apps → Create App
2. Connect your GitHub repository
3. Use the settings below

### 3. Required Environment Variables

Set these in the DigitalOcean App Platform dashboard:

```env
# Database (Required)
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require

# Django (Required)
DJANGO_SECRET_KEY=your-generated-secret-key-here
ON_DIGITALOCEAN=1
DEBUG=0

# Optional but recommended
TAB_DIRECTOR_EMAIL=your-email@example.com
TIME_ZONE=Your/Timezone
```

### 4. Basic Plan Optimizations

The configuration includes several optimizations for the 1GB RAM / 1 vCPU limitation:

#### Memory Optimizations
- **Single worker process** (`WEB_CONCURRENCY=1`)
- **Reduced cache size** (1000 entries max)
- **Local memory cache** instead of Redis
- **Disabled WebSocket support** to save memory
- **Reduced database connections** (max 5)

#### Performance Optimizations
- **Shorter session timeouts** (1 hour)
- **Compressed static files**
- **Optimized middleware stack**
- **Limited file upload sizes** (2.5MB max)

#### Resource Conservation
- **Minimal logging** (warnings/errors only)
- **No separate worker service**
- **Cached template loading**
- **Connection pooling**

## Cost Breakdown

### Minimum Monthly Cost: ~$25-30
- **App Platform Basic**: $10/mo
- **External Database**: $5-15/mo (depending on provider)
- **Total**: $15-25/mo

### Recommended Setup for Production: ~$35-45
- **App Platform Basic**: $10/mo
- **DigitalOcean Managed DB**: $15/mo
- **Domain**: $10-20/year
- **Total**: $25-35/mo

## Performance Expectations

### Suitable For:
- **Small tournaments** (up to 50 teams)
- **Development/testing**
- **Regional competitions**
- **Low-traffic deployments**

### Limitations:
- **No real-time features** (WebSocket disabled)
- **Single concurrent worker**
- **Limited file upload sizes**
- **Basic caching only**

### Expected Performance:
- **Response time**: 200-500ms
- **Concurrent users**: 10-20
- **Tournament size**: Up to 50 teams
- **Uptime**: 99.5%+

## Scaling Options

### When to Upgrade:
- **More than 20 concurrent users**
- **Tournaments > 50 teams**
- **Need real-time features**
- **Higher traffic volume**

### Upgrade Paths:
1. **Professional XS** ($12/mo) - 512MB RAM, better performance
2. **Professional S** ($25/mo) - 1GB RAM, dedicated vCPU
3. **Professional M** ($50/mo) - 2GB RAM, 2 vCPUs

## Troubleshooting

### Common Issues on Basic Plan:

#### 1. Memory Errors
**Symptoms**: App crashes, 502 errors
**Solutions**: 
- Reduce cache timeout values
- Clear static files regularly
- Monitor memory usage in dashboard

#### 2. Slow Response Times
**Symptoms**: Pages load slowly (>5 seconds)
**Solutions**:
- Check database performance
- Optimize queries
- Consider upgrading plan

#### 3. Database Connection Errors
**Symptoms**: Connection timeouts, database errors
**Solutions**:
- Verify DATABASE_URL format
- Check database firewall settings
- Ensure SSL is enabled

#### 4. Build Failures
**Symptoms**: Deployment fails during build
**Solutions**:
- Check build logs
- Verify all dependencies are in requirements.txt
- Ensure build script has proper permissions

## Monitoring

### Key Metrics to Watch:
- **Memory usage** (should stay under 900MB)
- **CPU usage** (should stay under 80%)
- **Response times** (target under 2 seconds)
- **Error rates** (should be <1%)

### Alerts to Set Up:
- Memory usage > 90%
- Response time > 5 seconds
- Error rate > 5%
- Uptime < 99%

## Backup Strategy

### Database Backups:
- Configure automatic backups on your database provider
- Test restore process monthly
- Keep at least 7 days of backups

### Application Data:
- Export tournament data regularly
- Version control all configuration changes
- Document custom settings

## Security Considerations

### Basic Plan Security:
- HTTPS enabled by default
- Database connections encrypted
- Environment variables encrypted
- Regular security updates

### Additional Recommendations:
- Use strong database passwords
- Regularly update dependencies
- Monitor access logs
- Implement rate limiting if needed

## Support and Resources

### Getting Help:
1. **DigitalOcean Support**: Available 24/7 via tickets
2. **Community**: DigitalOcean Community Forums
3. **Documentation**: This guide and official DO docs
4. **Tabbycat Community**: GitHub discussions

### Useful Links:
- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [Tabbycat Documentation](https://tabbycat.readthedocs.io/)
- [Django Deployment Best Practices](https://docs.djangoproject.com/en/stable/howto/deployment/)

This configuration provides a solid foundation for running Tabbycat on a budget while maintaining good performance for small to medium tournaments.
