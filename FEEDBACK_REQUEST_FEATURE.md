# Student Feedback Request Feature

## Overview

This feature allows supervisors to request structured feedback from students via email, without requiring students to log in. Students receive a secure link where they can provide and edit their responses, which are then stored as comments on the thesis.

## Feature Workflow

### For Supervisors

1. **Navigate to Thesis**: Go to the thesis detail page
2. **Click "Request Feedback"**: Button located in the Comments section header
3. **Select/Edit Template**: Choose a pre-made template or write a custom message
4. **Send Request**: Click "Send Feedback Request"
5. **Receive Notification**: Get an email when the student responds
6. **View Response**: Student's response appears as a specially marked comment

### For Students

1. **Receive Email**: Get an email with the feedback request and secure link
2. **Click Link**: No login required - the link contains a secure token
3. **Read Request**: See the supervisor's message/questions
4. **Provide Response**: Edit the text area with their feedback (Markdown supported)
5. **Submit**: Click submit - supervisors are notified
6. **Edit Later**: Can return to the same link to update their response

## Components

### Database Models

#### FeedbackTemplate
Stores reusable templates for feedback requests.

**Fields:**
- `name` - Template name (e.g., "Weekly Status Update")
- `message` - Template message text (supports Markdown)
- `description` - Optional description of when to use this template
- `is_active` - Whether the template is available for use
- `created_at`, `updated_at` - Timestamps

**Location:** `theses/models.py:295-313`

#### FeedbackRequest
Tracks individual feedback requests sent to students.

**Fields:**
- `thesis` - ForeignKey to Thesis
- `comment` - OneToOneField to Comment (stores the response)
- `request_message` - The message/prompt sent to the student
- `token` - Secure token (48 bytes, URL-safe) for student access
- `requested_by` - ForeignKey to User (who sent the request)
- `is_responded` - Boolean flag for response status
- `first_response_at` - Timestamp of first response
- `created_at`, `updated_at` - Timestamps

**Methods:**
- `save()` - Auto-generates secure token on creation
- `get_student_url()` - Returns the public URL for student access

**Location:** `theses/models.py:316-356`

### Forms

#### FeedbackRequestForm
Form for supervisors to create feedback requests.

**Fields:**
- `template` - ModelChoiceField for selecting a template (optional)
- `message` - CharField with Textarea for the request message

**Features:**
- Auto-fills message when template is selected (via JavaScript)
- Pre-fills with first active template on initial load

**Location:** `theses/forms.py:225-257`

#### FeedbackResponseForm
Form for students to respond to feedback requests.

**Fields:**
- `response` - CharField with large Textarea for student response

**Location:** `theses/forms.py:260-274`

### Views

#### feedback_request_create
View for supervisors to create and send feedback requests.

**URL:** `/thesis/<int:thesis_pk>/request-feedback/`
**Method:** GET (show form), POST (send request)
**Authentication:** Login required

**Process:**
1. Shows form with template selection and message editor
2. On submit, creates a Comment and FeedbackRequest
3. Sends email to students with secure link (supervisors CC'd)
4. Redirects to thesis detail page with success message

**Location:** `theses/views.py:846-949`

#### feedback_respond
Public view for students to respond to feedback requests.

**URL:** `/feedback/<str:token>/`
**Method:** GET (show form), POST (submit response)
**Authentication:** None (token-based access)

**Process:**
1. Validates token and retrieves FeedbackRequest
2. Shows form pre-filled with existing response (if any)
3. On submit, updates Comment with response
4. On first response, sends notification to supervisors
5. Shows success page

**Location:** `theses/views.py:952-1043`

### Templates

#### Web Templates

1. **feedback_request_form.html**
   - Form for supervisors to create requests
   - Includes JavaScript for template auto-fill
   - Location: `theses/templates/theses/feedback_request_form.html`

2. **feedback_response_form.html**
   - Public form for students (standalone page, not extending base.html)
   - Shows thesis info and supervisor's message
   - Location: `theses/templates/theses/feedback_response_form.html`

3. **feedback_response_success.html**
   - Success page after student submission
   - Standalone page with confirmation message
   - Location: `theses/templates/theses/feedback_response_success.html`

4. **thesis_detail.html** (modified)
   - Added "Request Feedback" button in Comments section header
   - Enhanced comment display with feedback request badges
   - Shows pending/responded status
   - Location: `theses/templates/theses/thesis_detail.html:273-327`

#### Email Templates

1. **feedback_request.txt / .html**
   - Email sent to students with request
   - Includes thesis info, supervisor message, and secure link
   - Supervisors are CC'd
   - Location: `theses/templates/emails/feedback_request.*`

2. **feedback_response_notification.txt / .html**
   - Email sent to supervisors when student responds
   - Includes student response and link to thesis
   - Location: `theses/templates/emails/feedback_response_notification.*`

### Admin Interface

#### FeedbackTemplateAdmin
Allows managing feedback request templates.

**Features:**
- List display: name, is_active, timestamps
- Searchable: name, description, message
- Filterable: is_active, created_at
- Grouped fields: Basic Info, Template Content

**Location:** `theses/admin.py:261-280`

#### FeedbackRequestAdmin
Shows feedback requests with status and links.

**Features:**
- List display: thesis, requested_by, is_responded, timestamps
- Searchable: thesis title, username, message
- Filterable: is_responded, created_at
- Read-only: token, timestamps, student_link
- Custom method: student_link (displays clickable URL)

**Location:** `theses/admin.py:283-322`

### Migrations

1. **0003_feedbacktemplate_feedbackrequest.py**
   - Creates FeedbackTemplate and FeedbackRequest models
   - Location: `theses/migrations/0003_feedbacktemplate_feedbackrequest.py`

2. **0004_initial_feedback_templates.py**
   - Data migration to create initial templates
   - Creates 6 default templates:
     - Weekly Status Update
     - Monthly Progress Report
     - Pre-Submission Check
     - Post-Meeting Follow-Up
     - Research Phase Update
     - Implementation Status
   - Location: `theses/migrations/0004_initial_feedback_templates.py`

## Setup Instructions

### 1. Run Migrations

```bash
# If using Docker:
docker-compose exec web python manage.py migrate

# If running directly:
python manage.py migrate
```

This will:
- Create the FeedbackTemplate and FeedbackRequest tables
- Populate initial feedback templates

### 2. Configure Email Settings

Ensure your `.env` file has email configured:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

### 3. Update Domain Settings

For production, update the domain in:
- `.env`: Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Views generate URLs using `get_current_site()` (auto-configured)

### 4. Test the Feature

1. Log in as a supervisor
2. Navigate to a thesis with assigned students
3. Click "Request Feedback"
4. Select a template and customize the message
5. Send the request
6. Check student email for the feedback link
7. Submit a response using the link
8. Verify supervisors receive the notification
9. Check that the response appears in thesis comments

## Usage Tips

### For Administrators

- **Managing Templates**: Go to Django Admin → Feedback Templates
- **Custom Templates**: Create new templates for specific use cases
- **Deactivate Templates**: Set `is_active=False` instead of deleting
- **Monitor Requests**: Use Django Admin → Feedback Requests to track all requests

### For Supervisors

- **When to Use**: Regular check-ins, milestone updates, pre-submission reviews
- **Template Selection**: Choose appropriate template based on thesis phase
- **Customization**: Always review and customize the template message
- **Multiple Students**: Email is sent to all students assigned to the thesis
- **Follow-up**: Students can edit their responses; subsequent edits don't notify supervisors

### For Students

- **Secure Link**: Keep the link private; anyone with the link can edit the response
- **Markdown Support**: Use Markdown for formatting (bold, lists, headings)
- **Edit Anytime**: Return to the link to update your response
- **No Notifications**: Updates don't send new emails to supervisors (only first submission)

## Security Considerations

### Token Security
- Tokens are 48 bytes (384 bits) URL-safe random strings
- Generated using `secrets.token_urlsafe(48)` (cryptographically secure)
- Stored hashed in database? No - stored as-is (consider hashing for production)
- Unique constraint ensures no token collisions

### Access Control
- Students don't need to log in (token provides access)
- Only the specific comment can be edited via the token
- Supervisors must be logged in to create requests
- Admin interface requires staff access

### Potential Improvements
1. **Token Expiration**: Add expiration date to FeedbackRequest
2. **Token Hashing**: Hash tokens in database, compare hashes
3. **Rate Limiting**: Limit submission attempts per token
4. **Access Logging**: Log all access to feedback response view

## Architecture Decisions

### Why OneToOneField for Comment?
- Each FeedbackRequest has exactly one Comment
- Comment stores the student's response text
- OneToOneField prevents multiple FeedbackRequests per Comment
- Allows easy reverse lookup: `comment.feedback_request`

### Why No Login Required?
- Reduces friction for students
- Students may not have accounts in the system
- Secure tokens provide adequate protection
- Supervisors need visibility, students just need to respond

### Why Store Request Message?
- Documents what was asked (even if template changes later)
- Allows showing the original request to students
- Useful for tracking and auditing

### Why Email Notifications?
- Students may not regularly check the system
- Email provides a direct channel to students
- Supervisors get timely updates on responses
- CC'ing supervisors keeps everyone informed

## Troubleshooting

### Emails Not Sending
1. Check email configuration in `.env`
2. Verify SMTP settings are correct
3. Check Django logs for email errors
4. Test with `python manage.py sendtestemail`

### Student Can't Access Link
1. Verify token in URL matches database
2. Check for copy-paste errors (extra spaces/characters)
3. Ensure FeedbackRequest wasn't deleted
4. Check if token is unique in database

### Templates Not Showing
1. Run migrations: `python manage.py migrate`
2. Check if templates are marked `is_active=True`
3. Verify data migration ran successfully
4. Check Django Admin → Feedback Templates

### Responses Not Appearing
1. Verify Comment was created/updated
2. Check FeedbackRequest.is_responded flag
3. Ensure thesis detail view prefetches feedback_request
4. Check template syntax in thesis_detail.html

## Future Enhancements

### Potential Features
1. **Response Reminders**: Automated reminders if no response after X days
2. **Template Variables**: Dynamic fields like `{student_name}`, `{deadline}`
3. **Response Analytics**: Track response times, completion rates
4. **Multi-Question Forms**: Structured questions with separate fields
5. **File Attachments**: Allow students to attach files with responses
6. **Version History**: Track all edits to student responses
7. **Anonymous Feedback**: Option for anonymous responses
8. **Bulk Requests**: Send same request to multiple theses at once

### Technical Improvements
1. **Token Hashing**: Hash tokens in database for security
2. **Token Expiration**: Add expiration dates to tokens
3. **Rate Limiting**: Prevent abuse of public endpoints
4. **Markdown Preview**: Live preview while editing responses
5. **Email Templates**: Move inline styles to separate CSS files
6. **Async Emails**: Use Celery for async email sending
7. **Notification Preferences**: Let supervisors choose notification settings

## Testing Checklist

- [ ] Create feedback request as supervisor
- [ ] Verify email is sent to students
- [ ] Verify supervisors are CC'd on request email
- [ ] Access feedback link without login
- [ ] Submit response as student
- [ ] Verify supervisor receives notification email
- [ ] Verify response appears in thesis comments
- [ ] Edit response and verify no additional notification
- [ ] Test with multiple students on one thesis
- [ ] Test with no students assigned (should show warning)
- [ ] Test template selection and auto-fill
- [ ] Test custom message without template
- [ ] Verify feedback request badge in comments
- [ ] Verify pending vs responded status display
- [ ] Test admin interface for templates
- [ ] Test admin interface for requests
- [ ] Verify token security (URL tampering)
- [ ] Test with email disabled (should fail gracefully)

## Support and Maintenance

### Files to Monitor
- `theses/models.py` - Model definitions
- `theses/views.py` - View logic
- `theses/forms.py` - Form definitions
- `theses/templates/` - All template files
- `theses/migrations/` - Database migrations

### Common Maintenance Tasks
1. **Adding New Templates**: Use Django Admin or create data migration
2. **Updating Email Templates**: Edit files in `theses/templates/emails/`
3. **Modifying Form Fields**: Update forms in `theses/forms.py`
4. **Changing Token Length**: Update `token` field in FeedbackRequest model
5. **Adding Notifications**: Extend view logic in `feedback_respond()`

### Version Information
- Feature implemented: 2025-11-11
- Django version: 5.0+
- Python version: 3.11+
- Dependencies: django-markdown-deux (for Markdown rendering)
