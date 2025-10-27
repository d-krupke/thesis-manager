# Deployment Guide

This guide explains how to deploy the Thesis Manager application behind an nginx reverse proxy on a subdomain.

## Overview

The application is designed to run as a Docker Compose stack behind an external nginx reverse proxy. This setup allows you to:
- Host multiple applications on the same server
- Use a single nginx instance for SSL termination
- Serve the application on a subdomain (e.g., `theses.example.com`)

## Architecture

```
Internet → nginx (reverse proxy) → Docker Compose (thesis-manager)
           ↓                           ↓
       SSL/HTTPS                   web (Django+Gunicorn)
       Port 80/443                 db (PostgreSQL)
```

## Step 1: Configure Environment Variables

Update your `docker-compose.yml` to include the necessary environment variables for reverse proxy operation:

```yaml
environment:
  - DEBUG=0  # Set to 0 for production
  - SECRET_KEY=your-very-secret-key-here  # Generate a secure key!
  - ALLOWED_HOSTS=theses.example.com,thesis-manager.example.com
  - CSRF_TRUSTED_ORIGINS=https://theses.example.com,https://thesis-manager.example.com
  - USE_X_FORWARDED_HOST=True
  - USE_X_FORWARDED_PORT=True
  - SECURE_PROXY_SSL_HEADER=True
  # Database settings
  - POSTGRES_NAME=thesis_manager
  - POSTGRES_USER=thesis_user
  - POSTGRES_PASSWORD=secure-db-password-here
  - POSTGRES_HOST=db
  - POSTGRES_PORT=5432
  # Email settings (optional)
  - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  - EMAIL_HOST=smtp.gmail.com
  - EMAIL_PORT=587
  - EMAIL_USE_TLS=True
  - EMAIL_HOST_USER=your-email@gmail.com
  - EMAIL_HOST_PASSWORD=your-app-password
  - DEFAULT_FROM_EMAIL=thesis-manager@example.com
```

### Environment Variable Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DEBUG` | Yes | Set to `0` in production | `0` |
| `SECRET_KEY` | Yes | Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) | `django-insecure-...` |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hostnames | `theses.example.com` |
| `CSRF_TRUSTED_ORIGINS` | Yes* | Comma-separated list of trusted origins (include https://) | `https://theses.example.com` |
| `USE_X_FORWARDED_HOST` | Yes* | Trust X-Forwarded-Host header from proxy | `True` |
| `USE_X_FORWARDED_PORT` | Yes* | Trust X-Forwarded-Port header from proxy | `True` |
| `SECURE_PROXY_SSL_HEADER` | Yes* | Trust X-Forwarded-Proto header for HTTPS | `True` |

*Required when running behind a reverse proxy

## Step 2: Update Docker Compose Configuration

Modify your `docker-compose.yml` to expose the web service on a specific port (instead of mapping to host):

```yaml
services:
  web:
    expose:
      - "8000"  # Only expose to Docker networks, not to host
    # Remove any "ports:" section to prevent direct access
```

If you want to access the service directly (for testing), you can temporarily add:

```yaml
    ports:
      - "127.0.0.1:8001:8000"  # Only accessible from localhost
```

## Step 3: Configure nginx Reverse Proxy

Create an nginx configuration file for your subdomain. Place this in your main nginx configuration directory (e.g., `/etc/nginx/sites-available/theses.example.com.conf`):

### Basic Configuration (HTTP only - for testing)

```nginx
server {
    listen 80;
    server_name theses.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8001;  # Adjust to your Docker container's exposed port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Optional: Static files (if you want nginx to serve them directly for better performance)
    location /static/ {
        alias /path/to/thesis-manager/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/thesis-manager/media/;
        expires 7d;
    }
}
```

### Production Configuration (with HTTPS)

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name theses.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name theses.example.com;

    # SSL Configuration (adjust paths to your certificates)
    ssl_certificate /etc/letsencrypt/live/theses.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/theses.example.com/privkey.pem;

    # SSL Settings (Mozilla Intermediate configuration)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8001;  # Adjust to your Docker container's exposed port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Optional: Static files served by nginx
    location /static/ {
        alias /path/to/thesis-manager/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/thesis-manager/media/;
        expires 7d;
    }
}
```

### Using Docker Network (Alternative)

If you want nginx to communicate with the Django container via Docker networks instead of localhost:

1. Create a shared Docker network:
```bash
docker network create web-proxy
```

2. Update your `docker-compose.yml`:
```yaml
services:
  web:
    networks:
      - default
      - web-proxy

networks:
  web-proxy:
    external: true
```

3. Update nginx configuration:
```nginx
location / {
    proxy_pass http://thesis-manager-web-1:8000;  # Use container name
    # ... rest of proxy settings
}
```

## Step 4: Enable the Site

```bash
# Create symlink (if using sites-enabled pattern)
sudo ln -s /etc/nginx/sites-available/theses.example.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Step 5: Set Up SSL with Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (nginx method)
sudo certbot --nginx -d theses.example.com

# Certbot will automatically modify your nginx configuration for HTTPS
# Certificates auto-renew via systemd timer
```

## Step 6: Start the Application

```bash
cd /path/to/thesis-manager
docker-compose up -d
```

## Step 7: Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## Verification Checklist

- [ ] Application accessible at `https://theses.example.com`
- [ ] Login/logout works correctly
- [ ] Static files (CSS/JS) load properly
- [ ] CSRF tokens work (forms submit without CSRF errors)
- [ ] Password reset emails work (if email configured)
- [ ] Admin interface accessible and functional
- [ ] All links use correct domain/protocol

## Troubleshooting

### CSRF Verification Failed

**Problem**: Forms show "CSRF verification failed" error.

**Solution**: Ensure `CSRF_TRUSTED_ORIGINS` includes your full domain with protocol:
```yaml
- CSRF_TRUSTED_ORIGINS=https://theses.example.com
```

### Redirect Loop

**Problem**: Browser gets stuck in redirect loop.

**Solution**: Check that `SECURE_PROXY_SSL_HEADER=True` and nginx is setting `X-Forwarded-Proto: https`.

### Static Files Not Loading

**Problem**: CSS/JS files return 404.

**Solution**:
1. Run `docker-compose exec web python manage.py collectstatic --noinput`
2. Ensure nginx has read access to the staticfiles directory
3. Check the `alias` path in nginx configuration

### Database Connection Errors

**Problem**: Django can't connect to PostgreSQL.

**Solution**:
1. Verify database credentials in environment variables
2. Check that `POSTGRES_HOST=db` (the service name in docker-compose.yml)
3. Wait for database to be ready: `docker-compose logs db`

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Just web service
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web
```

### Check Container Status

```bash
docker-compose ps
```

## Backup

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U thesis_user thesis_manager < backup_20241027.sql
```

### Full Application Backup

```bash
# Backup everything (database + media files)
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup.sql
tar -czf thesis-manager-backup-$(date +%Y%m%d).tar.gz backup.sql media/ .env docker-compose.yml
```

## Updates

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Security Recommendations

1. **Use strong passwords**: Generate secure passwords for database and Django secret key
2. **Enable HTTPS**: Always use SSL certificates in production
3. **Set DEBUG=0**: Never run with DEBUG=True in production
4. **Regular updates**: Keep Docker images and dependencies updated
5. **Firewall**: Only expose necessary ports (80, 443) to the internet
6. **Backups**: Set up automated database backups
7. **Monitoring**: Set up log monitoring and alerts

## Example Production docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=thesis_manager
      - POSTGRES_USER=thesis_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}  # Use env file or secrets
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U thesis_user -d thesis_manager"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn thesis_manager.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 60"
    volumes:
      - ./media:/app/media
      - static_volume:/app/staticfiles
    expose:
      - "8000"
    environment:
      - DEBUG=0
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}
      - USE_X_FORWARDED_HOST=True
      - USE_X_FORWARDED_PORT=True
      - SECURE_PROXY_SSL_HEADER=True
      - POSTGRES_NAME=thesis_manager
      - POSTGRES_USER=thesis_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_HOST=db
      - POSTGRES_PORT=5432
      - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_USE_TLS=True
      - EMAIL_HOST_USER=${EMAIL_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_PASSWORD}
      - DEFAULT_FROM_EMAIL=${FROM_EMAIL}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
```

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
