# Deployment Guide

This guide covers deploying the Thesis Manager application in a production multi-app environment with a top-level nginx reverse proxy handling SSL/TLS termination.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Deployment Approach Evaluation](#deployment-approach-evaluation)
3. [Production Configuration](#production-configuration)
4. [Top-Level Nginx Configuration](#top-level-nginx-configuration)
5. [Security Considerations](#security-considerations)
6. [Deployment Steps](#deployment-steps)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Current Development Setup

The application uses a three-container architecture:

```
┌─────────────────────────────────────────┐
│  nginx (port 80)                        │
│  - Serves static files                  │
│  - Proxies to Gunicorn                  │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  web (Django + Gunicorn port 8000)      │
│  - Application logic                    │
│  - Not exposed externally               │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  db (PostgreSQL)                        │
│  - Database                             │
│  - Not exposed externally               │
└─────────────────────────────────────────┘
```

**Volumes:**
- `postgres_data`: Database persistence
- `static_volume`: Django static files (CSS, JS, images)
- `media_volume`: User-uploaded files

---

## Deployment Approach Evaluation

For production deployment in a multi-app environment, you have two main options:

### Option A: Keep App-Level Nginx (Recommended for Most Cases)

**Architecture:**
```
Top-Level Nginx (SSL) → App Nginx → Gunicorn → Django
```

**Pros:**
- ✅ Self-contained application - can be deployed anywhere
- ✅ Simpler local development (matches production)
- ✅ Static files are handled at the app level (less top-level nginx config)
- ✅ Easier to move between environments
- ✅ App-specific nginx tuning (timeouts, client_max_body_size, etc.)
- ✅ Buffer and caching can be done at app level

**Cons:**
- ❌ Extra nginx container per app (~10MB memory per instance)
- ❌ One additional network hop (negligible performance impact)
- ❌ Slightly more complex architecture

**Best for:** Multi-app environments, teams that want self-contained apps, flexibility in deployment

### Option B: Direct to Gunicorn

**Architecture:**
```
Top-Level Nginx (SSL) → Gunicorn → Django
```

**Pros:**
- ✅ Simpler architecture (fewer containers)
- ✅ Slightly less memory usage (~10MB saved per app)
- ✅ One fewer network hop
- ✅ Centralized nginx configuration

**Cons:**
- ❌ Top-level nginx must handle all static files from all apps
- ❌ Top-level nginx config becomes complex with many apps
- ❌ Less portable (requires specific top-level nginx configuration)
- ❌ Development environment differs from production
- ❌ All app-specific nginx settings must be in top-level config

**Best for:** Single app deployments, resource-constrained environments, simple setups

### Recommendation

**Use Option A (Keep App-Level Nginx)** for the following reasons:

1. **Separation of Concerns**: Each app manages its own static files and nginx configuration
2. **Portability**: The app can be deployed to different environments without changing the top-level nginx
3. **Development/Production Parity**: Local development matches production setup
4. **Scalability**: Easy to add/remove apps without touching top-level nginx
5. **Memory Overhead is Minimal**: ~10MB per nginx instance is negligible on modern servers

The only scenario where Option B makes sense is if you're extremely resource-constrained (embedded devices, minimal VPS) or have a single application.

---

## Production Configuration

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - .env.prod
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # No networks specified - uses default network

  web:
    build: .
    restart: unless-stopped
    command: sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn thesis_manager.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - "8000"
    env_file:
      - .env.prod
    depends_on:
      db:
        condition: service_healthy
    # No networks specified - uses default network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    expose:
      - "80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    depends_on:
      - web
    networks:
      - default  # Internal communication with web
      - nginx_proxy_network  # External access from top-level nginx

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  # Only define external network - Docker Compose creates 'default' automatically
  nginx_proxy_network:
    external: true
```

**Key Changes from Development:**

1. **No `--reload` flag**: Production Gunicorn doesn't auto-reload
2. **Multiple workers**: `--workers 4` for better performance
3. **Restart policy**: `unless-stopped` ensures containers restart after crashes
4. **No volume mount for code**: Production uses code baked into image
5. **Simplified networking**:
   - Docker Compose default network for internal communication (db ↔ web ↔ nginx)
   - Only nginx joins the external `nginx_proxy_network` for top-level nginx access
   - Database remains isolated on internal network only
6. **Environment configuration**: Uses `env_file: .env.prod` for all configuration

### 2. Production Environment File

Create `.env.prod` (or copy from `.env.prod.example`):

```bash
# PostgreSQL
POSTGRES_DB=thesis_manager
POSTGRES_USER=thesis_user
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD

# Django
SECRET_KEY=CHANGE_THIS_TO_RANDOM_50_CHAR_STRING
DEBUG=False

# Domain configuration (subdomain deployment example)
ALLOWED_HOSTS=theses.example.com
CSRF_TRUSTED_ORIGINS=https://theses.example.com

# Reverse proxy settings
USE_X_FORWARDED_HOST=True
USE_X_FORWARDED_PORT=True
SECURE_PROXY_SSL_HEADER=True

# Security settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=SAMEORIGIN
```

**Generate strong credentials:**
```bash
# Generate SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generate database password
openssl rand -base64 32
```

**For complete configuration with comments and examples, see `.env.prod.example`.**

---

## Top-Level Nginx Configuration

The top-level nginx handles SSL/TLS termination and routes requests to individual applications.

### Prerequisites

1. **Create external network (once, shared by all apps):**
```bash
docker network create nginx_proxy_network
```

2. **Install Certbot for Let's Encrypt SSL:**
```bash
# Ubuntu/Debian
apt-get update && apt-get install -y certbot python3-certbot-nginx

# RHEL/CentOS
yum install -y certbot python3-certbot-nginx
```

### Option 1: Subdomain Deployment (Recommended)

Deploy at `theses.example.com`

**Top-level nginx config (`/etc/nginx/sites-available/theses.example.com`):**

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name theses.example.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name theses.example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/theses.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/theses.example.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # HSTS (optional but recommended)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client upload size limit
    client_max_body_size 100M;

    # Proxy to app's nginx container
    location / {
        proxy_pass http://thesis_nginx;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Upstream definition for the thesis app
# Note: Replace 'thesis-manager-nginx-1' with your actual container name
# You can find it with: docker ps | grep nginx
upstream thesis_nginx {
    server thesis-manager-nginx-1:80;
}
```

**Enable the site:**
```bash
ln -s /etc/nginx/sites-available/theses.example.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

**Obtain SSL certificate:**
```bash
certbot --nginx -d theses.example.com
```

**Update `.env.prod`:**
```bash
ALLOWED_HOSTS=theses.example.com
CSRF_TRUSTED_ORIGINS=https://theses.example.com
```

### Option 2: Subpath Deployment

Deploy at `example.com/theses/`

**Challenges with subpath deployment:**
- Django must know it's running under a subpath
- All URLs must include the prefix
- Static files must be served with prefix
- More complex nginx configuration

**Top-level nginx config (add to `/etc/nginx/sites-available/example.com`):**

```nginx
# Existing example.com server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com;

    # ... existing SSL configuration ...

    # Thesis Manager app under /theses/
    location /theses/ {
        # Remove /theses prefix before passing to app
        rewrite ^/theses/(.*)$ /$1 break;

        proxy_pass http://thesis_nginx;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /theses;  # Tell Django about prefix
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

upstream thesis_nginx {
    server thesis-manager-nginx-1:80;
}
```

**Update `.env.prod` for subpath:**
```bash
ALLOWED_HOSTS=example.com
CSRF_TRUSTED_ORIGINS=https://example.com
FORCE_SCRIPT_NAME=/theses
STATIC_URL=/theses/static/
MEDIA_URL=/theses/media/
```

**Note:** Subdomain deployment is **significantly simpler** and less error-prone than subpath deployment. Recommend using subdomain unless you have a specific requirement for subpath.

---

## Security Considerations

### 1. Environment Variables

**Never commit secrets to git:**
```bash
# Add to .gitignore
.env.prod
.env.local
*.key
*.pem
```

**Use strong passwords:**
```bash
# Generate strong PostgreSQL password
openssl rand -base64 32

# Generate Django SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 2. Django Settings

**All production settings are configured via environment variables in `.env.prod`.**

No changes to `settings.py` are required! The following settings are already supported via environment variables:

- `DEBUG` - Set to False in production
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Comma-separated list of allowed domains
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins with https://
- `USE_X_FORWARDED_HOST` - Enable for reverse proxy (True/False)
- `USE_X_FORWARDED_PORT` - Enable for reverse proxy (True/False)
- `SECURE_PROXY_SSL_HEADER` - Enable for HTTPS behind proxy (True/False)
- `SECURE_SSL_REDIRECT` - Redirect HTTP to HTTPS (True/False)
- `SESSION_COOKIE_SECURE` - Secure session cookies (True/False)
- `CSRF_COOKIE_SECURE` - Secure CSRF cookies (True/False)
- `SECURE_BROWSER_XSS_FILTER` - Browser XSS protection (True/False)
- `SECURE_CONTENT_TYPE_NOSNIFF` - Content type sniffing protection (True/False)
- `X_FRAME_OPTIONS` - Clickjacking protection (SAMEORIGIN/DENY)
- `SECURE_HSTS_SECONDS` - HSTS max age in seconds (0 to disable)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` - Include subdomains in HSTS (True/False)
- `SECURE_HSTS_PRELOAD` - HSTS preload (True/False)

For subpath deployments, also configure:
- `FORCE_SCRIPT_NAME` - URL prefix (e.g., /theses)
- `STATIC_URL` - Static files URL (e.g., /theses/static/)
- `MEDIA_URL` - Media files URL (e.g., /theses/media/)

See `.env.prod.example` for complete configuration examples.

### 3. Database Security

- Never expose PostgreSQL port externally
- Use strong passwords (32+ characters)
- Keep database in internal Docker network
- Regular backups (see below)

### 4. Firewall Configuration

```bash
# Allow only SSH, HTTP, and HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 5. Regular Updates

```bash
# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Update system packages
apt-get update && apt-get upgrade -y
```

---

## Deployment Steps

### Initial Setup

1. **Prepare the server:**
```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Install nginx and certbot
apt-get install -y nginx certbot python3-certbot-nginx
```

2. **Create external network:**
```bash
docker network create nginx_proxy_network
```

3. **Clone and configure application:**
```bash
cd /opt
git clone <your-repo-url> thesis-manager
cd thesis-manager

# Copy and configure production environment
cp .env.example .env.prod
nano .env.prod  # Edit with production values
```

4. **Build and start application:**
```bash
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

5. **Find the nginx container name:**
```bash
docker ps | grep thesis
# Look for container name like: thesis-manager-nginx-1
```

6. **Configure top-level nginx:**
```bash
# Create config file
nano /etc/nginx/sites-available/theses.example.com
# Paste subdomain configuration from above
# Update the upstream server name with your actual container name

# Enable site
ln -s /etc/nginx/sites-available/theses.example.com /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

7. **Obtain SSL certificate:**
```bash
certbot --nginx -d theses.example.com
```

8. **Create Django superuser:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

9. **Verify deployment:**
```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Check application
curl https://theses.example.com
```

### Updates and Maintenance

**Deploy code updates:**
```bash
cd /opt/thesis-manager
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

**Database backups:**
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U thesis_user thesis_manager > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U thesis_user thesis_manager < backup_20241028_120000.sql
```

**View logs:**
```bash
# All containers
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f db
```

---

## Troubleshooting

### Application not accessible

**Check container status:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

**Check logs:**
```bash
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs nginx
```

**Check network connectivity:**
```bash
# Verify nginx container is on the external network
docker network inspect nginx_proxy_network

# Test connection from host to app nginx (should work via external network)
docker exec thesis-manager-nginx-1 wget -O- http://localhost

# Test internal communication (web -> db)
docker-compose -f docker-compose.prod.yml exec web nc -zv db 5432
```

**Check container name is correct:**
```bash
# Find actual container name
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Update upstream in /etc/nginx/sites-available/theses.example.com if needed
```

### Static files not loading

**Collect static files:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

**Check volume mounts:**
```bash
docker-compose -f docker-compose.prod.yml exec nginx ls -la /app/staticfiles
```

**Check nginx configuration:**
```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
docker-compose -f docker-compose.prod.yml exec nginx cat /etc/nginx/conf.d/default.conf
```

### CSRF verification failed

**Update Django settings:**
```python
# In .env.prod
CSRF_TRUSTED_ORIGINS=https://theses.example.com

# For subpath deployment
CSRF_TRUSTED_ORIGINS=https://example.com
```

**Restart application:**
```bash
docker-compose -f docker-compose.prod.yml restart web
```

### Database connection errors

**Check database is running:**
```bash
docker-compose -f docker-compose.prod.yml exec db pg_isready -U thesis_user
```

**Check database credentials:**
```bash
# Verify .env.prod matches docker-compose.prod.yml
cat .env.prod
```

**Check database logs:**
```bash
docker-compose -f docker-compose.prod.yml logs db
```

### Performance issues

**Increase Gunicorn workers:**
```yaml
# In docker-compose.prod.yml
command: gunicorn thesis_manager.wsgi:application --bind 0.0.0.0:8000 --workers 8 --timeout 120
```

**Rule of thumb:** `workers = (2 * CPU_cores) + 1`

**Add database connection pooling** (for high-traffic sites)

**Enable nginx caching** (for static content)

---

## Multi-App Example

If you have multiple applications on the same server:

```
/etc/nginx/sites-available/
├── app1.example.com
├── app2.example.com
└── theses.example.com

/opt/
├── app1/
│   └── docker-compose.prod.yml
├── app2/
│   └── docker-compose.prod.yml
└── thesis-manager/
    └── docker-compose.prod.yml
```

All apps connect to the same `nginx_proxy_network` and each has its own nginx container for static file serving and app-specific configuration.

**Benefits of this approach:**
- Each app is self-contained
- Easy to add/remove apps
- Simple nginx configuration per app
- No conflicts between apps
- Easy to test locally (matches production)

---

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Deployment](https://docs.gunicorn.org/en/stable/deploy.html)
- [Nginx Best Practices](https://www.nginx.com/blog/nginx-best-practices/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
