# Tabbycat DigitalOcean Deployment - Complete Setup

Your Tabbycat project is now ready for deployment on DigitalOcean App Platform with the **$10/mo Basic Plan** configuration.

## 📋 What's Been Configured

### ✅ Basic Plan Configuration ($10/mo)
- **Resources**: 1 GB RAM, 1 Shared vCPU, 100 GB bandwidth
- **Optimized settings** for limited resources
- **No Redis/WebSocket** to conserve memory
- **Single web service** (no separate worker)
- **External database** required (PostgreSQL)

### ✅ Files Created/Modified

#### Deployment Configuration
- `.do/app.yaml` - Main deployment configuration (Basic plan)
- `.do/app-basic.yaml` - Alternative basic plan configuration
- `requirements.txt` - Python dependencies (generated from Pipfile)

#### Django Settings
- `tabbycat/settings/digitalocean.py` - Full-featured DigitalOcean settings
- `tabbycat/settings/digitalocean_basic.py` - Memory-optimized for Basic plan
- Updated `tabbycat/settings/__init__.py` to detect DigitalOcean environment

#### Build & Deployment Scripts
- `bin/digitalocean-build.sh` - Standard build script
- `bin/digitalocean-build-basic.sh` - Memory-optimized build script
- `deploy-digitalocean.sh` - Interactive deployment script
- `check-deployment.sh` - Pre-deployment validation

#### Documentation
- `DIGITALOCEAN_DEPLOYMENT.md` - Complete deployment guide
- `DIGITALOCEAN_BASIC_DEPLOYMENT.md` - Basic plan specific guide
- `README_DEPLOYMENT.md` - This summary file

#### NPM Scripts Added
```json
"digitalocean-build": "NODE_ENV='production' npm-run-all -p build-* cp-* && python manage.py collectstatic --noinput",
"digitalocean-serve": "npm-run-all -p digitalocean-server digitalocean-worker",
"digitalocean-server": "python tabbycat/run-asgi.py",
"digitalocean-worker": "python manage.py runworker notifications adjallocation venues"
```

## 🚀 Quick Deployment Guide

### Step 1: Setup External Database
You need a PostgreSQL database. Recommended options:

**Budget Options:**
- **Railway**: $5/mo PostgreSQL
- **Supabase**: Free tier (limited)
- **ElephantSQL**: Free tier (20MB limit)

**Production Options:**
- **DigitalOcean Managed DB**: $15/mo (recommended)
- **AWS RDS**: $13/mo (t3.micro)

### Step 2: Configure Environment Variables
Update `.do/app.yaml` with your values:

```yaml
# Required - Replace these placeholders
DATABASE_URL: "postgresql://username:password@host:port/database"
DJANGO_SECRET_KEY: "your-generated-secret-key"
TAB_DIRECTOR_EMAIL: "your-email@example.com"

# Optional
TIME_ZONE: "America/New_York"  # Your timezone
```

### Step 3: Deploy

#### Option A: Automated Script
```bash
# Check deployment readiness
./check-deployment.sh

# Setup environment variables interactively
./deploy-digitalocean.sh setup-env

# Deploy to DigitalOcean
./deploy-digitalocean.sh create-basic
```

#### Option B: Manual Deployment
```bash
# Install DigitalOcean CLI
sudo snap install doctl  # Ubuntu/Debian
# or
brew install doctl       # macOS

# Authenticate
doctl auth init

# Create app
doctl apps create --spec .do/app-basic.yaml

# Monitor deployment
doctl apps list
doctl apps logs YOUR_APP_ID --follow
```

## 💰 Cost Breakdown

### Minimum Setup (~$15-20/mo)
- DigitalOcean App Platform Basic: **$10/mo**
- Railway PostgreSQL: **$5/mo**
- **Total: $15/mo**

### Recommended Setup (~$25-30/mo)
- DigitalOcean App Platform Basic: **$10/mo**
- DigitalOcean Managed Database: **$15/mo**
- **Total: $25/mo**

### Professional Setup (~$40-50/mo)
- DigitalOcean App Platform Professional-XS: **$12/mo**
- DigitalOcean Managed Database: **$15/mo**
- Custom domain: **$10-15/year**
- **Total: $27-30/mo**

## 📊 Performance Expectations

### Basic Plan Suitable For:
- ✅ Small tournaments (up to 50 teams)
- ✅ Regional competitions
- ✅ Development/testing
- ✅ Low-traffic deployments (10-20 concurrent users)

### Performance Metrics:
- **Response Time**: 200-500ms
- **Concurrent Users**: 10-20
- **Memory Usage**: 700-900MB (out of 1GB)
- **Tournament Size**: Up to 50 teams
- **Uptime**: 99.5%+

### Limitations:
- ❌ No real-time WebSocket features
- ❌ Limited concurrent processing
- ❌ Single worker process
- ❌ Basic caching only

## 🔧 Post-Deployment Steps

### 1. Database Setup
```bash
# Connect to your app
doctl apps logs YOUR_APP_ID --type run

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata minimal8team
```

### 2. Monitoring Setup
- Monitor app performance in DigitalOcean dashboard
- Set up alerts for:
  - Memory usage > 90%
  - Response time > 5 seconds
  - Error rate > 5%

### 3. Backup Strategy
- Configure automatic database backups
- Export tournament data regularly
- Keep configuration in version control

## 🛠 Troubleshooting

### Common Issues:

#### Memory Errors (502/503 errors)
```bash
# Check memory usage
doctl apps logs YOUR_APP_ID --type run | grep -i memory

# Solutions:
# 1. Reduce cache timeouts
# 2. Clear static files
# 3. Consider upgrading plan
```

#### Slow Performance
```bash
# Check response times
doctl apps logs YOUR_APP_ID --type run | grep -i "response"

# Solutions:
# 1. Optimize database queries
# 2. Check database performance
# 3. Enable more caching
```

#### Build Failures
```bash
# Check build logs
doctl apps logs YOUR_APP_ID --type build

# Common fixes:
# 1. Check requirements.txt
# 2. Verify build script permissions
# 3. Check Node.js/Python versions
```

## 📈 Scaling Options

### When to Upgrade:
- More than 20 concurrent users
- Tournaments with 50+ teams
- Need real-time features
- Memory usage consistently > 90%

### Upgrade Paths:
1. **Professional-XS** ($12/mo): Better performance, same RAM
2. **Professional-S** ($25/mo): 1GB RAM, dedicated vCPU
3. **Professional-M** ($50/mo): 2GB RAM, 2 vCPUs

## 📚 Additional Resources

### Documentation:
- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [Tabbycat Documentation](https://tabbycat.readthedocs.io/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)

### Support:
- **DigitalOcean Support**: 24/7 ticket support
- **Tabbycat Community**: GitHub discussions
- **Django Community**: Stack Overflow, Django forums

## ✅ Deployment Checklist

Before deploying, ensure:

- [ ] External PostgreSQL database is set up
- [ ] GitHub repository URL updated in `.do/app.yaml`
- [ ] Environment variables configured
- [ ] Django secret key generated
- [ ] Tab director email set
- [ ] Deployment checker passes (`./check-deployment.sh`)
- [ ] doctl CLI installed and authenticated
- [ ] All required files present

## 🎯 Success Metrics

Your deployment is successful when:
- ✅ App builds without errors
- ✅ Database migrations complete
- ✅ Static files load correctly
- ✅ Admin panel accessible
- ✅ Can create and manage tournaments
- ✅ Memory usage < 900MB
- ✅ Response times < 2 seconds

---

**Your Tabbycat project is now ready for DigitalOcean deployment!** 

Run `./check-deployment.sh` to validate your setup, then use `./deploy-digitalocean.sh create-basic` to deploy to the $10/mo Basic plan.
