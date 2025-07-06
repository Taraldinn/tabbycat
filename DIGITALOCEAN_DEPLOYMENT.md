# DigitalOcean App Platform Deployment Guide for Tabbycat

This guide helps you deploy Tabbycat on DigitalOcean App Platform with external database support.

## Prerequisites

1. DigitalOcean account
2. GitHub account with your Tabbycat repository
3. Basic knowledge of environment variables
4. PostgreSQL database (external or DigitalOcean Managed Database)

## Deployment Methods

### Method 1: Automatic Deployment (Recommended)

1. **Fork/Clone this repository** to your GitHub account

2. **Configure external database connection:**
   - Create a PostgreSQL database (DigitalOcean Managed Database, AWS RDS, etc.)
   - Note the connection string format: `postgresql://username:password@host:port/database`

3. **Deploy using App Platform:**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Choose "GitHub" as source and select your repository
   - DigitalOcean will auto-detect the `.do/app.yaml` configuration

4. **Set environment variables** in the App Platform dashboard:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   REDIS_URL=redis://username:password@host:port/database
   DJANGO_SECRET_KEY=your-super-secret-key-here
   TAB_DIRECTOR_EMAIL=your-email@example.com
   TIME_ZONE=Your/Timezone
   ```

5. **Deploy and monitor:**
   - Click "Create Resources"
   - Monitor the build and deployment logs
   - The application will be available at the provided URL

### Method 2: Manual Deployment with CLI

1. **Install DigitalOcean CLI (doctl):**
   ```bash
   # On Ubuntu/Debian
   sudo snap install doctl
   
   # On macOS
   brew install doctl
   
   # On other systems, download from:
   # https://github.com/digitalocean/doctl/releases
   ```

2. **Authenticate with DigitalOcean:**
   ```bash
   doctl auth init
   ```

3. **Create the app:**
   ```bash
   doctl apps create --spec .do/app.yaml
   ```

4. **Update environment variables:**
   ```bash
   # Get your app ID
   doctl apps list
   
   # Update environment variables
   doctl apps update YOUR_APP_ID --spec .do/app.yaml
   ```

## Configuration Files

### 1. Django Settings for DigitalOcean

The project includes a new settings file for DigitalOcean deployment:
- `tabbycat/settings/digitalocean.py` - Production settings optimized for DigitalOcean

### 2. Package.json Scripts

New scripts added for DigitalOcean deployment:
- `digitalocean-serve` - Start the web server
- `digitalocean-worker` - Start the background worker
- `digitalocean-build` - Build static assets for production

### 3. App Specification

The `.do/app.yaml` file contains:
- Web service configuration
- Worker service configuration  
- Environment variables
- Database specifications
- Redis configuration

## External Database Setup

### Using DigitalOcean Managed Database

1. **Create a PostgreSQL database:**
   ```bash
   doctl databases create tabbycat-db --engine pg --region nyc1 --size db-s-1vcpu-1gb
   ```

2. **Get connection details:**
   ```bash
   doctl databases connection tabbycat-db
   ```

3. **Configure connection string:**
   ```
   DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
   ```

### Using External PostgreSQL (AWS RDS, Google Cloud SQL, etc.)

1. **Create database instance** in your cloud provider
2. **Configure security groups/firewall** to allow DigitalOcean IPs
3. **Get connection string** from your cloud provider
4. **Set DATABASE_URL** environment variable

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://user:pass@host:6379/0` |
| `DJANGO_SECRET_KEY` | Django secret key | `your-super-secret-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TAB_DIRECTOR_EMAIL` | Contact email for notifications | None |
| `TIME_ZONE` | Application timezone | `UTC` |
| `DEBUG` | Enable debug mode | `0` |
| `WEB_CONCURRENCY` | Number of web workers | `2` |

## Post-Deployment Steps

1. **Run database migrations:**
   ```bash
   # Access your app's console
   doctl apps logs YOUR_APP_ID --type run
   
   # Or connect via SSH if available
   python manage.py migrate
   ```

2. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

3. **Load initial data (optional):**
   ```bash
   python manage.py loaddata fixtures/initial_data.json
   ```

4. **Test the application:**
   - Visit your app URL
   - Login with created superuser
   - Create a test tournament

## Monitoring and Logs

### View Application Logs
```bash
# View build logs
doctl apps logs YOUR_APP_ID --type build

# View runtime logs
doctl apps logs YOUR_APP_ID --type run

# View all logs
doctl apps logs YOUR_APP_ID --follow
```

### Monitor Performance
- Use DigitalOcean App Platform metrics dashboard
- Set up alerts for high CPU/memory usage
- Monitor database performance

## Scaling

### Vertical Scaling
- Increase instance size in `.do/app.yaml`
- Update using: `doctl apps update YOUR_APP_ID --spec .do/app.yaml`

### Horizontal Scaling
- Increase `instance_count` in web/worker services
- Consider database connection limits

## Security Considerations

1. **Environment Variables:** Store sensitive data in DO's encrypted environment variables
2. **HTTPS:** Automatically handled by DigitalOcean App Platform
3. **Database Security:** Use strong passwords and restrict network access
4. **Secret Key:** Generate a strong Django secret key
5. **CORS:** Configure CORS settings for API access

## Troubleshooting

### Common Issues

1. **Build Failures:**
   - Check Python/Node versions in logs
   - Verify dependencies in Pipfile/package.json
   - Review build command output

2. **Database Connection:**
   - Verify DATABASE_URL format
   - Check database firewall settings
   - Ensure database is accessible from DigitalOcean

3. **Static Files:**
   - Verify static files are built during build process
   - Check STATIC_ROOT and STATIC_URL settings
   - Ensure WhiteNoise is configured

4. **WebSocket Issues:**
   - Verify Redis connection
   - Check worker service logs
   - Ensure Redis is accessible

### Getting Help

1. **DigitalOcean Support:** https://www.digitalocean.com/support/
2. **Tabbycat Documentation:** https://tabbycat.readthedocs.io/
3. **Community Forum:** https://github.com/TabbycatDebate/tabbycat/discussions

## Cost Optimization

1. **Development:** Use `professional-xs` instances
2. **Production:** Scale based on usage patterns  
3. **Database:** Start with smaller instances, scale as needed
4. **Redis:** Use managed Redis or smaller instances for development

## Backup Strategy

1. **Database Backups:** Configure automatic backups in your database provider
2. **Application Data:** Regular exports of tournament data
3. **Configuration:** Keep `.do/app.yaml` and settings in version control

This deployment configuration provides a robust foundation for running Tabbycat on DigitalOcean App Platform with external database support.
