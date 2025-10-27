# Thesis Manager

A Django-based web application for managing student theses at academic institutes. Track theses from first contact through completion, including all important dates, student and supervisor information, and repository links.

## Quick Links

- **[Installation & Setup](#installation--setup)** - Get started quickly
- **[API Documentation](API.md)** - REST API usage guide
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment with nginx
- **[Email Setup](EMAIL_SETUP_GUIDE.md)** - Configure email notifications
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

## Features

- **Thesis Tracking**: Manage theses through multiple phases (first contact, topic discussion, literature research, registration, working, defense, review, completion)
- **Student Management**: Track students and their associated theses (bachelor, master, project work)
- **Supervisor Management**: Assign multiple supervisors to theses for redundancy
- **Supervisor Overview**: Dashboard showing workload distribution across all supervisors and phases
- **Timeline Tracking**: Record important dates (first contact, registration, deadline, presentation, review, final discussion)
- **Advanced Comment System**:
  - Add, edit, and delete comments on theses
  - Automatic comment generation when dates or phases change
  - User attribution and timestamps for all comments
  - Visual distinction between manual and auto-generated comments
  - Email notifications to supervisors when comments are added (optional)
- **User Management**:
  - Password change functionality for all users
  - Password reset via email (when email is configured)
  - Secure authentication with Django's built-in system
- **REST API**:
  - Full programmatic access to all thesis management functionality
  - Secure token-based authentication (Knox)
  - Automatic OpenAPI/Swagger documentation
  - Support for filtering, search, and pagination
  - Multiple tokens per user for different applications
  - See [API.md](API.md) for complete documentation
- **Git Repository Links**: Track student repository URLs
- **Filtering & Search**: Filter by phase, thesis type, and search by title or student name
- **Django Admin Interface**: Full administrative access for advanced management

## Technology Stack

- **Backend**: Django 5.0+
- **API**: Django REST Framework 3.14+
- **Authentication**: Django REST Knox (token-based API auth)
- **Database**: PostgreSQL 16
- **Container**: Docker & Docker Compose
- **Web Server**: Nginx (reverse proxy) + Gunicorn (WSGI server)
- **Frontend**: Bootstrap 5.3
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)

## Prerequisites

- Docker
- Docker Compose

## Installation & Setup

1. **Clone the repository**:
   ```bash
   cd /path/to/thesis-manager
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update the values as needed:
   - `SECRET_KEY` - Generate a secure key for production
   - `DEBUG` - Set to `0` for production
   - `POSTGRES_PASSWORD` - Change from default
   - Configure email settings if needed

3. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the Django application container with all dependencies
   - Start PostgreSQL database
   - Start Nginx web server
   - Run database migrations (including Knox token tables)
   - Collect static files
   - Start Gunicorn WSGI server

   **Note**: The `--build` flag is important for the first run to install all dependencies including the API packages (Django REST Framework, Knox, drf-spectacular, etc.).

4. **Create a superuser** (in a new terminal):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

   Follow the prompts to create an admin account.

5. **Access the application**:
   - Main interface: http://localhost
   - Django admin: http://localhost/admin
   - API documentation: http://localhost/api/docs/
   - API endpoints: http://localhost/api/

## Configuration

### Environment Variables

All configuration is managed through the `.env` file (created from `.env.example`). Key variables:

**Django Settings:**
- `DEBUG` - Enable debug mode (1) or production mode (0)
- `SECRET_KEY` - Django secret key (generate a new one for production!)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hostnames

**Database:**
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Database credentials
- `POSTGRES_HOST`, `POSTGRES_PORT` - Database connection details

**Reverse Proxy (for production with HTTPS):**
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins
- `USE_X_FORWARDED_HOST`, `USE_X_FORWARDED_PORT` - Enable proxy headers
- `SECURE_PROXY_SSL_HEADER` - Enable HTTPS detection through proxy

**Email (optional):**
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT` - SMTP configuration
- `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - SMTP auth
- `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL` - From addresses

### Email Configuration (Optional)

The system supports email notifications and password reset via email. Email configuration is optional but recommended for production use.

#### Features Requiring Email

1. **Password Reset**: Users can reset forgotten passwords via email
2. **Comment Notifications**: Supervisors receive email notifications when comments are added to their theses

#### Setting Up Email

1. **Edit `.env`** and uncomment/configure the email variables:

```bash
# Email configuration (uncomment and configure to enable email features)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=thesis-manager@yourdomain.com
```

2. **For Gmail** (recommended for testing):
   - Enable 2-factor authentication on your Google account
   - Generate an App Password: https://myaccount.google.com/apppasswords
   - Use the app password (not your regular password) in `EMAIL_HOST_PASSWORD`

3. **For Other SMTP Providers**:
   - **Office 365**: `EMAIL_HOST=smtp.office365.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`
   - **SendGrid**: `EMAIL_HOST=smtp.sendgrid.net`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`
   - **Mailgun**: `EMAIL_HOST=smtp.mailgun.org`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`
   - **Custom SMTP**: Configure according to your provider's documentation

4. **Restart the application**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Testing Email Configuration

To test if email is working:

1. Try the password reset feature at http://localhost/accounts/password_reset/
2. Add a comment to a thesis with supervisors - they should receive an email notification
3. Check the container logs for any email errors:
   ```bash
   docker-compose logs -f web
   ```

### Without Email Configuration

If you don't configure email, the system will still work but:
- Password reset will not be available (users must contact admin)
- Comment notifications will not be sent
- Emails will be printed to console logs instead (in DEBUG mode)

## User Management

### Password Management

Users can manage their passwords through the web interface:

1. **Change Password**: Click on your username in the top-right corner → "Change Password"
2. **Reset Forgotten Password**: Click "Forgot your password?" on the login page (requires email configuration)

### Creating User Accounts

User accounts must be created by administrators:

1. Go to Django Admin (http://localhost/admin)
2. Click "Users" → "Add User"
3. Set username and password
4. Edit the user to add:
   - First name and last name
   - Email address (required for password reset and notifications)
   - Staff status (if they should access admin panel)
   - Superuser status (if they should have full permissions)

### Supervisor Accounts

To create accounts for supervisors:

1. Create a User account (as above) with their email
2. Create a Supervisor record in the thesis manager with the same email
3. The supervisor can now:
   - Log in to view and manage theses
   - Change their password
   - Receive email notifications (if configured)

## Usage

### First Time Setup

1. Log in to the Django admin at http://localhost/admin
2. Create some supervisors (staff members)
3. Create students as they contact you
4. Create thesis entries

### Managing Theses

#### Creating a New Thesis

1. Click "New Thesis" in the navigation
2. Start with minimal information:
   - Select thesis type (Bachelor, Master, Project)
   - Set phase to "First Contact"
   - Add the date of first contact
   - Assign student(s) and supervisor(s)
   - Add any initial comments

3. As the thesis progresses, edit the entry to add:
   - Thesis title (once decided)
   - Update the phase
   - Add dates (registration, deadline, presentation, etc.)
   - Add git repository URL
   - Update comments

#### Phases

Theses go through these phases:
1. **First Contact**: Initial inquiry
2. **Topic Discussion**: Exploring potential topics
3. **Literature Research**: Student researching before formal start
4. **Registered**: Officially registered with the university
5. **Working**: Active thesis work
6. **Submitted**: Thesis submitted
7. **Defended**: Presentation/defense completed
8. **Reviewed**: Review completed
9. **Completed**: All done
10. **Abandoned**: Thesis was not completed

### Main Views

- **Thesis List** (`/`): Overview table of all theses with filtering and search
- **Thesis Detail** (`/thesis/<id>/`): Complete information about a thesis
- **Student Detail** (`/student/<id>/`): Student information and their theses
- **Student List** (`/students/`): Overview of all students
- **Supervisor List** (`/supervisors/`): Overview of all supervisors
- **Supervisor Detail** (`/supervisor/<id>/`): Supervisor information and supervised theses
- **Edit Forms**: Update thesis, student, or supervisor information

## API Access

The Thesis Manager provides a comprehensive REST API for programmatic access.

### Using the API

1. **Create an API Token**:
   - Log in to the web interface
   - Navigate to **API** → **My API Tokens**
   - Click **Create New Token**
   - Copy and save the token securely

2. **Make API Requests**:
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/theses/
   ```

3. **View Documentation**:
   - Interactive Swagger UI: http://localhost/api/docs/
   - ReDoc: http://localhost/api/redoc/
   - See [API.md](API.md) for complete usage guide

### API Endpoints

- `/api/theses/` - Manage theses
- `/api/students/` - Manage students
- `/api/supervisors/` - Manage supervisors
- `/api/comments/` - Manage comments

For detailed API documentation, examples, and best practices, see **[API.md](API.md)**.

## Docker Commands

### Start the application
```bash
docker-compose up
```

### Start in detached mode (background)
```bash
docker-compose up -d
```

### Rebuild and start (after dependency changes)
```bash
docker-compose up --build
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Run Django management commands
```bash
docker-compose exec web python manage.py <command>

# Examples:
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
```

### Run migrations (if you modify models)
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Collect static files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Access Django shell
```bash
docker-compose exec web python manage.py shell
```

### Backup database
```bash
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup_$(date +%Y%m%d).sql
```

### Restore database
```bash
docker-compose exec -T db psql -U thesis_user thesis_manager < backup.sql
```

### Reset everything (careful - deletes all data!)
```bash
docker-compose down -v  # -v removes volumes (database data)
docker-compose up --build
```

## Production Deployment

For production deployment behind an nginx reverse proxy on a subdomain, please refer to the comprehensive **[DEPLOYMENT.md](DEPLOYMENT.md)** guide.

The deployment guide covers:
- Setting up nginx as a reverse proxy
- Configuring environment variables for reverse proxy operation
- SSL/TLS setup with Let's Encrypt
- Security best practices
- Backup and monitoring procedures
- Troubleshooting common issues

### Quick Start for Production

1. **Update environment variables** in `docker-compose.yml`:
   ```yaml
   - DEBUG=0
   - SECRET_KEY=<generate-secure-key>
   - ALLOWED_HOSTS=theses.example.com
   - CSRF_TRUSTED_ORIGINS=https://theses.example.com
   - USE_X_FORWARDED_HOST=True
   - USE_X_FORWARDED_PORT=True
   - SECURE_PROXY_SSL_HEADER=True
   ```

2. **Configure nginx** as a reverse proxy (see [DEPLOYMENT.md](DEPLOYMENT.md))

3. **Set up SSL** with Let's Encrypt:
   ```bash
   sudo certbot --nginx -d theses.example.com
   ```

4. **Start the application**:
   ```bash
   docker-compose up -d
   ```

## Database Schema

### Models

- **Student**: first_name, last_name, email, student_id, comments, created_at, updated_at
- **Supervisor**: first_name, last_name, email, comments, created_at, updated_at
- **Thesis**: title, thesis_type, phase, dates (7 different date fields), git_repository, description, created_at, updated_at, many-to-many relations with Student and Supervisor
- **Comment**: thesis (ForeignKey), user (ForeignKey), text, is_auto_generated, created_at, updated_at

### Relationships

- Thesis ↔ Student: Many-to-Many (rare cases of multiple students per thesis)
- Thesis ↔ Supervisor: Many-to-Many (backup supervisors)
- Thesis → Comment: One-to-Many (each thesis can have multiple comments)
- User → Comment: One-to-Many (each user can make multiple comments)

## Development

### Project Structure

```
thesis-manager/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Django container image
├── nginx.conf                  # Nginx configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── manage.py                   # Django management script
├── README.md                   # This file
├── API.md                      # API documentation
├── DEPLOYMENT.md               # Production deployment guide
├── EMAIL_SETUP_GUIDE.md        # Email configuration guide
├── CHANGELOG.md                # Version history
│
├── thesis_manager/             # Django project settings
│   ├── settings.py             # Main settings (DB, API, Knox, etc.)
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application
│
└── theses/                     # Main Django app
    ├── models.py               # Data models (Student, Supervisor, Thesis, Comment)
    ├── views.py                # Web views and API token management
    ├── forms.py                # Form definitions
    ├── urls.py                 # App URL routing
    ├── admin.py                # Django admin configuration
    ├── signals.py              # Signal handlers for auto-comments and emails
    │
    ├── api/                    # REST API package
    │   ├── __init__.py
    │   ├── serializers.py      # API serializers for all models
    │   ├── viewsets.py         # API viewsets with filtering
    │   ├── permissions.py      # Custom API permissions
    │   └── urls.py             # API URL routing
    │
    ├── migrations/             # Database migrations
    │   ├── 0001_initial.py
    │   └── 0002_remove_thesis_comments_thesis_description_comment.py
    │
    └── templates/              # HTML templates
        ├── base.html           # Base template with navigation
        ├── registration/       # Authentication templates
        │   ├── login.html
        │   ├── password_*.html
        │   └── ...
        ├── emails/             # Email templates
        │   └── comment_notification.txt
        └── theses/             # App-specific templates
            ├── thesis_list.html
            ├── thesis_detail.html
            ├── thesis_form.html
            ├── student_list.html
            ├── student_detail.html
            ├── student_form.html
            ├── supervisor_list.html
            ├── supervisor_detail.html
            ├── supervisor_form.html
            ├── api_tokens.html
            └── comment_edit.html
```

### Python Dependencies

The application uses the following key dependencies (see `requirements.txt`):

#### Core Framework
- **Django (>=5.0,<5.1)**: Web framework providing ORM, admin interface, authentication, and more
- **psycopg2-binary (>=2.9.9)**: PostgreSQL database adapter for Python
- **gunicorn (>=21.2.0)**: Production WSGI server for running Django

#### REST API
- **djangorestframework (>=3.14.0)**: Toolkit for building RESTful APIs in Django
  - Provides serializers, viewsets, authentication, and API browsing
- **django-rest-knox (>=4.2.0)**: Token-based authentication for Django REST Framework
  - Allows users to create multiple API tokens
  - More secure than DRF's built-in token auth (uses SHA512 hashing)
  - Supports token expiry and per-user token limits
- **drf-spectacular (>=0.27.0)**: OpenAPI 3.0 schema generation for Django REST Framework
  - Auto-generates API documentation from code
  - Provides Swagger UI and ReDoc interfaces
  - Makes API testing and exploration easier
- **django-filter (>=23.5)**: Reusable Django app for filtering querysets
  - Enables filtering API endpoints by multiple fields
  - Used for phase, type, student, and supervisor filtering
- **cryptography (>=41.0.0)**: Cryptographic recipes and primitives
  - Required by django-rest-knox for secure token hashing
  - Provides SHA512 and other hashing algorithms

#### Why These Dependencies?

1. **Django REST Framework**: Industry standard for building APIs in Django. Well-maintained, extensively documented, and feature-rich.

2. **Knox**: Chosen over DRF's built-in token auth because it:
   - Supports multiple tokens per user (different apps/devices)
   - Uses more secure hashing (SHA512 vs SHA1)
   - Allows setting token expiry
   - Enables token rotation without password changes

3. **drf-spectacular**: Best-in-class OpenAPI documentation generator for DRF:
   - More actively maintained than alternatives
   - Better OpenAPI 3.0 support
   - Cleaner, more modern Swagger UI

4. **django-filter**: Simplifies adding filtering to API endpoints:
   - Reduces boilerplate code
   - Provides consistent filtering interface
   - Well-integrated with DRF

### Adding New Features

1. Modify models in `theses/models.py`
2. Create and run migrations:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```
3. Update forms, views, and templates as needed
4. For API changes:
   - Update serializers in `theses/api/serializers.py`
   - Update viewsets in `theses/api/viewsets.py`
   - API documentation auto-updates via drf-spectacular

## Troubleshooting

### Port 80 already in use
```bash
# Check what's using port 80
sudo lsof -i :80
# Stop other services or change the port in docker-compose.yml
docker-compose down
docker ps -a  # Check for other containers
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps
docker-compose logs db

# Check database environment variables in .env
cat .env | grep POSTGRES
```

### Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check nginx is serving static files
docker-compose logs nginx
```

### API returns 401 Unauthorized
- Ensure you're including the `Authorization: Token YOUR_TOKEN` header
- Check if token is valid: Go to API → My API Tokens in the web interface
- Create a new token if needed

### API documentation not loading
```bash
# Ensure drf-spectacular is installed
docker-compose exec web python manage.py shell -c "import drf_spectacular"

# Check logs for errors
docker-compose logs web

# Rebuild if needed
docker-compose up --build
```

### Migrations fail with "no module named cryptography"
```bash
# Rebuild the Docker image to install new dependencies
docker-compose down
docker-compose up --build
```

### Email notifications not working
- Check email settings in `.env`
- Verify SMTP credentials are correct
- Check logs: `docker-compose logs web | grep -i email`
- Test with console backend first: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`

## License

This project is created for academic thesis management. Modify and use as needed for your institution.

## Support

For issues or questions, please check the Django documentation at https://docs.djangoproject.com/
