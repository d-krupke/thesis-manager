# Thesis Manager

A Django-based web application for managing student theses at academic institutes. Track theses from first contact through completion, including all important dates, student and supervisor information, and repository links.

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
- **Git Repository Links**: Track student repository URLs
- **Filtering & Search**: Filter by phase, thesis type, and search by title or student name
- **Django Admin Interface**: Full administrative access for advanced management

## Technology Stack

- **Backend**: Django 5.0+
- **Database**: PostgreSQL 16
- **Container**: Docker & Docker Compose
- **Web Server**: Nginx (reverse proxy) + Gunicorn (WSGI server)
- **Frontend**: Bootstrap 5.3

## Prerequisites

- Docker
- Docker Compose

## Installation & Setup

1. **Clone the repository**:
   ```bash
   cd /path/to/thesis-manager
   ```

2. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build the Django application container
   - Start PostgreSQL database
   - Start Nginx web server
   - Run database migrations
   - Collect static files
   - Start Gunicorn WSGI server

3. **Create a superuser** (in a new terminal):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

   Follow the prompts to create an admin account.

4. **Access the application**:
   - Main interface: http://localhost
   - Django admin: http://localhost/admin

## Email Configuration (Optional)

The system supports email notifications and password reset via email. Email configuration is optional but recommended for production use.

### Features Requiring Email

1. **Password Reset**: Users can reset forgotten passwords via email
2. **Comment Notifications**: Supervisors receive email notifications when comments are added to their theses

### Setting Up Email

1. **Edit `docker-compose.yml`** and uncomment the email environment variables:

```yaml
environment:
  # ... other variables ...
  # Email configuration (uncomment and configure to enable email features)
  - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  - EMAIL_HOST=smtp.gmail.com  # Your SMTP server
  - EMAIL_PORT=587
  - EMAIL_USE_TLS=True
  - EMAIL_HOST_USER=your-email@gmail.com
  - EMAIL_HOST_PASSWORD=your-app-password
  - DEFAULT_FROM_EMAIL=thesis-manager@yourdomain.com
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
- **Edit Forms**: Update thesis, student, or supervisor information

## Docker Commands

### Start the application
```bash
docker-compose up
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f web
```

### Run Django management commands
```bash
docker-compose exec web python manage.py <command>
```

### Access Django shell
```bash
docker-compose exec web python manage.py shell
```

### Run migrations (if you modify models)
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Backup database
```bash
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup.sql
```

### Restore database
```bash
docker-compose exec -T db psql -U thesis_user thesis_manager < backup.sql
```

## Production Deployment

For production deployment:

1. **Update environment variables**:
   - Set `DEBUG=0` in docker-compose.yml
   - Generate a new `SECRET_KEY`
   - Set `ALLOWED_HOSTS` to your domain

2. **Set up SSL/TLS** with Let's Encrypt or your certificate provider by updating the nginx configuration

3. **Update nginx.conf** to listen on port 443 for HTTPS and add SSL certificate paths

The application already includes nginx for serving static files efficiently. Static files are served directly by nginx from the `/app/staticfiles/` volume, while application requests are proxied to the Gunicorn WSGI server.

## Database Schema

### Models

- **Student**: first_name, last_name, email, student_id, comments
- **Supervisor**: first_name, last_name, email, comments
- **Thesis**: title, thesis_type, phase, dates (7 different date fields), git_repository, comments, many-to-many relations with Student and Supervisor

### Relationships

- Thesis ↔ Student: Many-to-Many (rare cases of multiple students per thesis)
- Thesis ↔ Supervisor: Many-to-Many (backup supervisors)

## Development

### Project Structure

```
thesis-manager/
├── docker-compose.yml      # Docker services configuration
├── Dockerfile              # Django container image
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── thesis_manager/        # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── theses/               # Main Django app
    ├── models.py         # Data models
    ├── views.py          # View logic
    ├── forms.py          # Form definitions
    ├── urls.py           # URL routing
    ├── admin.py          # Django admin configuration
    └── templates/        # HTML templates
        ├── base.html
        └── theses/
            ├── thesis_list.html
            ├── thesis_detail.html
            ├── thesis_form.html
            ├── student_detail.html
            ├── student_form.html
            └── supervisor_form.html
```

### Adding New Features

1. Modify models in `theses/models.py`
2. Create and run migrations:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```
3. Update forms, views, and templates as needed

## Troubleshooting

### Port 8000 already in use
```bash
# Stop other services using port 8000 or change the port in docker-compose.yml
docker-compose down
docker ps -a  # Check for other containers
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps
docker-compose logs db
```

### Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## License

This project is created for academic thesis management. Modify and use as needed for your institution.

## Support

For issues or questions, please check the Django documentation at https://docs.djangoproject.com/
