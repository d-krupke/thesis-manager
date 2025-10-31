# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Thesis Manager is a Django-based web application for managing student theses at academic institutes. It tracks theses through multiple phases (from first contact to completion) with students, supervisors, dates, and comments. The application provides both a web interface and a comprehensive REST API.

**Tech Stack**: Django 5.0, PostgreSQL 16, Django REST Framework, Knox (API auth), drf-spectacular (OpenAPI docs), Bootstrap 5, Docker/Docker Compose, Nginx + Gunicorn

## Development Commands

### Docker Operations
```bash
# Start all services (PostgreSQL, Django web app, Nginx)
docker-compose up

# Start in background
docker-compose up -d

# Rebuild after dependency changes (requirements.txt)
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f web
docker-compose logs -f db
```

### Django Management Commands
All Django commands must be run inside the web container:
```bash
# Run any Django management command
docker-compose exec web python manage.py <command>

# Common commands:
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py collectstatic --noinput

# Test a single module
docker-compose exec web python manage.py test theses.tests.TestModelName
```

### Database Operations
```bash
# Backup database
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U thesis_user thesis_manager < backup.sql

# Reset everything (DELETES ALL DATA!)
docker-compose down -v
docker-compose up --build
```

## Architecture Overview

### Core Django Structure

**Django Project**: `thesis_manager/` - Project-level settings
- `settings.py`: All configuration (DB, REST framework, Knox, security, email)
- `urls.py`: Root URL routing (includes API routes, web routes, admin)

**Django App**: `theses/` - Main application logic
- `models.py`: Database schema (Student, Supervisor, Thesis, Comment)
- `views.py`: Web interface views (HTML responses)
- `forms.py`: Web forms for creating/editing objects
- `signals.py`: Automatic actions on model changes (auto-comments, email notifications)
- `warnings.py`: Warning system for thesis deadlines and issues
- `admin.py`: Django admin interface configuration

**API Package**: `theses/api/` - REST API implementation
- `serializers.py`: JSON serialization for all models
- `viewsets.py`: API endpoints (CRUD operations)
- `permissions.py`: Custom API permissions
- `urls.py`: API routing

### Key Architectural Patterns

#### 1. Dual Interface Architecture
The application provides two interfaces:
- **Web interface** (`views.py`): Traditional Django views with HTML templates
- **REST API** (`api/viewsets.py`): JSON API for programmatic access

Both interfaces share the same models and business logic (signals, warnings).

#### 2. Signal-Based Auto-Comments
**Location**: `signals.py`

The application automatically generates comments when thesis dates or phases change:
1. `pre_save` signal stores original thesis values
2. Second `pre_save` signal detects changes and prepares comment text
3. `post_save` signal creates Comment objects with detected changes
4. Another `post_save` signal on Comment sends email notifications to supervisors

**Important**: When updating Thesis objects in views, set `instance._current_user = request.user` before saving to track who made changes in auto-generated comments.

#### 3. Warning System
**Location**: `warnings.py`

Generates warnings for theses that need attention:
- Deadlines approaching/overdue
- Reviews overdue (>30 days after submission)
- Long time in early phases (>90 days)
- Missing supervisors or students

The `ThesisListView` displays warnings prominently in the web interface.

#### 4. Many-to-Many Relationships
- **Thesis ↔ Student**: Many-to-Many (rare cases of multiple students per thesis)
- **Thesis ↔ Supervisor**: Many-to-Many (allows backup supervisors)
- **Thesis → Comment**: One-to-Many with ForeignKey

Access relationships via:
- `thesis.students.all()`, `thesis.supervisors.all()`, `thesis.comments.all()`
- Reverse: `student.theses.all()`, `supervisor.supervised_theses.all()`

### REST API Design

**Authentication**: Knox token-based auth (multiple tokens per user, SHA512 hashing)
**Documentation**: Auto-generated OpenAPI/Swagger at `/api/docs/`

**API Endpoints**:
- `/api/theses/` - CRUD operations + filtering by phase, type, student, supervisor
- `/api/students/` - Student management
- `/api/supervisors/` - Supervisor management
- `/api/comments/` - Comment management
- `/api/theses/{id}/comments/` - Get comments for a thesis
- `/api/theses/{id}/add_comment/` - Add comment to a thesis

**Permissions**:
- All API endpoints require authentication
- Supervisors can edit their own theses (see `IsSupervisorOrReadOnly` in `api/permissions.py`)
- Users can only edit/delete their own comments (see `IsOwnerOrReadOnly`)
- Staff users have broader edit permissions

### Database Schema

**Models** (defined in `models.py`):

**Student**:
- first_name, last_name, email (unique), student_id
- comments (TextField for free text notes)

**Supervisor**:
- first_name, last_name, email (unique)
- comments (TextField for free text notes)

**Thesis**:
- title, thesis_type (bachelor/master/project/other), phase (10 phases from first_contact to completed)
- students (M2M), supervisors (M2M)
- 7 date fields: date_first_contact, date_topic_selected, date_registration, date_deadline, date_presentation, date_review, date_final_discussion
- git_repository (URL), description, task_description, review

**Comment**:
- thesis (FK), user (FK to Django User)
- text, is_auto_generated (bool)
- created_at, updated_at

### Email Notification System

**Configuration**: Set email backend and SMTP settings in `.env`
**Triggered by**: `post_save` signal on Comment model (in `signals.py`)
**Recipients**: All supervisors of the thesis (filtered by valid email addresses)
**Content**: Notifies about new comments (both manual and auto-generated)
**Graceful degradation**: Uses `fail_silently=True` so app continues if email fails

## Making Changes

### Adding a New Model Field

1. Edit the model in `theses/models.py`:
   ```python
   new_field = models.CharField(max_length=100, blank=True)
   ```

2. Create and apply migrations:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

3. Update related components:
   - Add to `forms.py` if it should appear in web forms
   - Add to `api/serializers.py` for API exposure
   - Update admin.py if needed for admin interface

### Adding a New API Endpoint

1. Create/update serializer in `theses/api/serializers.py`
2. Create/update viewset in `theses/api/viewsets.py`
3. Register viewset in `theses/api/urls.py` with router
4. Documentation auto-generates via drf-spectacular

### Adding a Custom Action to an Existing ViewSet

Use the `@action` decorator in `api/viewsets.py`:
```python
@action(detail=True, methods=['get'])
def custom_endpoint(self, request, pk=None):
    obj = self.get_object()
    # Your logic here
    return Response(data)
```

### Adding Auto-Comments for New Fields

Edit the `create_comment_on_date_change` function in `signals.py`:
1. Add field to the appropriate dictionary (e.g., `date_fields`)
2. The signal system will automatically detect changes and create comments

### Adding New Warnings

Edit the `check_thesis_warnings` function in `warnings.py`:
1. Add your warning condition check
2. Create a `ThesisWarning` object with appropriate urgency (INFO/WARNING/URGENT)
3. Append to the warnings list
4. Warnings automatically appear in the thesis list view

## Important Implementation Details

### Efficient Database Queries

The codebase uses `prefetch_related` and `select_related` to avoid N+1 query problems:
- `prefetch_related`: For Many-to-Many and reverse ForeignKey relationships
- `select_related`: For forward ForeignKey relationships

Example in `api/viewsets.py`:
```python
queryset = Thesis.objects.prefetch_related('students', 'supervisors', 'comments').all()
queryset = Comment.objects.select_related('user', 'thesis').all()
```

### Reverse Proxy Support

The application supports deployment behind nginx reverse proxy with HTTPS:
- Environment variables: `USE_X_FORWARDED_HOST`, `USE_X_FORWARDED_PORT`, `SECURE_PROXY_SSL_HEADER`
- CSRF protection: `CSRF_TRUSTED_ORIGINS` must include your domain(s)
- See `docs/deployment.md` for full production setup

### Static Files Handling

- Static files collected to `staticfiles/` directory
- Nginx serves static files directly (defined in `nginx.conf`)
- Run `collectstatic` after any static file changes:
  ```bash
  docker-compose exec web python manage.py collectstatic --noinput
  ```

### Template Context

Templates receive context from views. Common context variables:
- `thesis_list`/`theses`: List of Thesis objects
- `student`/`supervisor`: Individual model instances
- `form`: Form object for create/edit views
- `warnings`: List of ThesisWarning objects (in ThesisListView)

### Knox Token Authentication

Users can create multiple API tokens:
- Web interface: Navigate to API → My API Tokens
- Each token is independently revocable
- Tokens hashed with SHA512 (more secure than DRF's default)
- Use header: `Authorization: Token YOUR_TOKEN`

## Configuration Files

### `.env` (Environment Variables)
Copy from `.env.example` and configure:
- `DEBUG`: Set to 0 for production
- `SECRET_KEY`: Change for production (generate new random key)
- `POSTGRES_*`: Database credentials
- `EMAIL_*`: SMTP configuration for notifications
- `ALLOWED_HOSTS`: Comma-separated list of allowed domains
- `CSRF_TRUSTED_ORIGINS`: Required for reverse proxy with HTTPS

### `docker-compose.yml`
Defines three services:
- `db`: PostgreSQL 16 with health checks
- `web`: Django app (Gunicorn WSGI server)
- `nginx`: Reverse proxy serving static files

### `requirements.txt`
Python dependencies. After changes, rebuild:
```bash
docker-compose down
docker-compose up --build
```

## Common Pitfalls

1. **Forgetting to run migrations**: After model changes, always run `makemigrations` and `migrate`
2. **N+1 queries**: Use `prefetch_related`/`select_related` for relationships to avoid performance issues
3. **Signal ordering**: Signals run in registration order; `pre_save` must come before operations that depend on it
4. **Missing collectstatic**: Static files won't update without running `collectstatic`
5. **Permission classes**: Order matters - put most restrictive first
6. **API permissions**: Remember to set `permission_classes` on viewsets to prevent unauthorized access
7. **Auto-comment user tracking**: Set `instance._current_user = request.user` in views before saving Thesis objects

## Testing Notes

Access points:
- Main web interface: http://localhost
- Django admin: http://localhost/admin
- API docs (Swagger): http://localhost/api/docs/
- API docs (ReDoc): http://localhost/api/redoc/
- API root: http://localhost/api/

Default setup script (`setup.sh`) automates initial setup but you still need to run:
```bash
docker-compose exec web python manage.py createsuperuser
```
