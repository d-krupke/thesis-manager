# Changelog

## Version 2.1 - Password Management and Email Notifications

### New Features

#### 1. Password Management
- **Password Change**: Users can change their password from the web interface
  - Access via user dropdown menu in top-right corner
  - Requires current password verification
  - Password strength validation
- **Password Reset via Email**: Users can reset forgotten passwords
  - Request reset link via email
  - Secure token-based reset process
  - 24-hour expiration on reset links
  - Requires email configuration

#### 2. Email Notifications
- **Comment Notifications**: Supervisors automatically receive emails when:
  - A new comment is added to a thesis they supervise
  - An auto-generated comment is created (e.g., date changes)
- **Configurable**: Email can be enabled/disabled via environment variables
- **Graceful Degradation**: System works without email (notifications just won't be sent)

#### 3. Enhanced Authentication
- **Login Page**: Clean, professional login interface
- **User Dropdown**: Easy access to password change and logout
- **Email Requirement**: Users need email addresses for password reset and notifications

### Technical Changes

#### Settings (`thesis_manager/settings.py`)
- Added email configuration via environment variables
- Added `EMAIL_NOTIFICATIONS_ENABLED` flag
- Updated `LOGIN_URL` to use new authentication URLs
- Added `LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL`

#### URLs (`thesis_manager/urls.py`)
- Added Django authentication URLs:
  - `/accounts/login/` - Login page
  - `/accounts/logout/` - Logout
  - `/accounts/password_change/` - Change password
  - `/accounts/password_reset/` - Request password reset
  - `/accounts/reset/<uidb64>/<token>/` - Reset password with token

#### Templates
- **Login & Password Management**:
  - `registration/login.html` - Login page
  - `registration/password_change_form.html` - Change password form
  - `registration/password_change_done.html` - Success message
  - `registration/password_reset_form.html` - Request reset form
  - `registration/password_reset_done.html` - Email sent confirmation
  - `registration/password_reset_confirm.html` - Set new password
  - `registration/password_reset_complete.html` - Reset complete
  - `registration/password_reset_email.html` - Reset email template
  - `registration/password_reset_subject.txt` - Email subject
- **Email Notifications**:
  - `emails/comment_notification.txt` - Comment notification email template
- **Updated**:
  - `base.html` - Added user dropdown menu with password change and logout

#### Signals (`theses/signals.py`)
- Added `send_comment_notification_email` signal
- Sends email to all supervisors when a comment is created
- Includes thesis details, student info, and comment text
- Only sends when email is configured
- Fails silently if email sending fails

#### Docker Configuration
- Updated `docker-compose.yml` with email environment variables (commented by default)
- Updated `.env.example` with email configuration examples

### Configuration

#### Email Setup

Add to `docker-compose.yml` (uncomment and configure):
```yaml
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=your-email@gmail.com
- EMAIL_HOST_PASSWORD=your-app-password
- DEFAULT_FROM_EMAIL=thesis-manager@yourdomain.com
```

#### Supported Email Providers

- Gmail (with App Password)
- Office 365
- SendGrid
- Mailgun
- Any SMTP server

### Usage Notes

1. **Without Email**: System works fully, but password reset and notifications are disabled
2. **With Email**: All features enabled, supervisors get notified of thesis updates
3. **User Accounts**: Must be created via Django admin with valid email addresses
4. **Testing**: Use password reset feature to test email configuration

### Breaking Changes

None - fully backward compatible. Email features are optional.

## Version 2.0 - Enhanced Comment System and Supervisor Overview

### New Features

#### 1. Comment System for Theses
- **Replaced** simple `comments` field with a full-featured comment system
- **Renamed** `comments` to `description` in the Thesis model for general thesis description
- **Added** new `Comment` model with the following features:
  - User tracking (which user wrote the comment)
  - Timestamps (created_at, updated_at)
  - Auto-generated flag for system comments
  - Edit and delete functionality
  - Permission checks (users can only edit/delete their own comments, or staff can manage all)

#### 2. Automatic Comment Generation
- **Implemented** signals that automatically create comments when:
  - Any date field is added or changed (first contact, registration, deadline, presentation, review, final discussion)
  - The thesis phase changes
- Auto-generated comments are marked with a badge and cannot be deleted by regular users
- Comments include the username of the person who made the change

#### 3. Supervisor Overview Dashboard
- **Added** supervisor statistics table on the main thesis list page
- Shows breakdown of theses per supervisor by phase
- Displays total count per supervisor
- Only shows supervisors with active theses
- Compact, easy-to-read table format

### Technical Changes

#### Models (`theses/models.py`)
- Added `Comment` model with fields:
  - `thesis` (ForeignKey to Thesis)
  - `user` (ForeignKey to User, nullable for system comments)
  - `text` (TextField)
  - `is_auto_generated` (BooleanField)
  - `created_at`, `updated_at` (DateTimeField)
- Renamed `Thesis.comments` to `Thesis.description`

#### Views (`theses/views.py`)
- Updated `ThesisListView` to include supervisor statistics in context
- Updated `ThesisDetailView` to include comments and comment form
- Updated `ThesisUpdateView` to set current user for signal tracking
- Added `add_comment()` function view for creating comments
- Added `edit_comment()` function view for editing comments
- Added `delete_comment()` function view for deleting comments

#### Signals (`theses/signals.py`)
- New file with Django signals for automatic comment generation
- `pre_save` signal to detect date and phase changes
- `post_save` signal to create comments after thesis is saved
- Tracks changes to all 7 date fields and phase field

#### Forms (`theses/forms.py`)
- Updated `ThesisForm` to use `description` instead of `comments`
- Added `CommentForm` for creating/editing comments

#### Templates
- **thesis_detail.html**: Complete redesign of comments section
  - Shows all comments in chronological order
  - Comment form for adding new comments
  - Edit/Delete buttons for own comments
  - Visual distinction for auto-generated comments
  - Shows comment author and timestamps
- **thesis_list.html**: Added supervisor overview table at top
- **thesis_form.html**: Updated to use `description` field
- **comment_edit.html**: New template for editing comments

#### Admin (`theses/admin.py`)
- Added `CommentAdmin` for managing comments
- Added `CommentInline` for viewing comments within thesis admin
- Updated `ThesisAdmin` to use `description` instead of `comments`

#### URLs (`theses/urls.py`)
- Added routes for comment operations:
  - `/thesis/<id>/comment/add/` - Add comment
  - `/comment/<id>/edit/` - Edit comment
  - `/comment/<id>/delete/` - Delete comment

### Database Migration
- Migration `0002_remove_thesis_comments_thesis_description_comment.py`:
  - Removes `comments` field from Thesis
  - Adds `description` field to Thesis
  - Creates Comment table

### Usage

#### Adding Comments
1. Navigate to any thesis detail page
2. Type comment in the text box at the bottom
3. Click "Add Comment"

#### Automatic Comments
When you edit a thesis and change dates or phase:
1. Save the thesis
2. System automatically creates a comment describing the change
3. Comment is attributed to the logged-in user
4. Auto-generated comments are marked with an "Auto" badge

#### Viewing Supervisor Overview
- The supervisor overview appears at the top of the main thesis list page
- Shows a table with supervisors in rows and phases in columns
- Numbers indicate how many theses each supervisor has in each phase
- Total column shows overall workload per supervisor

### Breaking Changes
- The `comments` field on Thesis model has been renamed to `description`
- Existing comments data will be removed during migration (as it's being replaced with the new Comment system)
- If you have existing data in the `comments` field that you want to keep:
  1. Export it before running migrations
  2. Run migrations
  3. Create manual comments with the exported data

### Migration Instructions

#### Development
```bash
# Apply migrations
docker-compose exec web python manage.py migrate

# Or if starting fresh
docker-compose down -v
docker-compose up --build
docker-compose exec web python manage.py createsuperuser
```

#### Production
```bash
# Backup database first!
docker-compose exec db pg_dump -U thesis_user thesis_manager > backup_before_v2.sql

# Apply migrations
docker-compose exec web python manage.py migrate

# Verify everything works
# If issues occur, restore from backup:
# docker-compose exec -T db psql -U thesis_user thesis_manager < backup_before_v2.sql
```

## Version 1.0 - Initial Release
- Basic thesis management system
- Student, Supervisor, and Thesis models
- Timeline tracking with multiple date fields
- Django admin interface
- Docker Compose setup
- Bootstrap UI
