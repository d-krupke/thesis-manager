# Email Setup Guide

This guide explains how to configure email functionality in the Thesis Manager system.

## Overview

The system supports two email-based features:
1. **Password Reset**: Allow users to reset their passwords via email
2. **Comment Notifications**: Automatically notify supervisors when comments are added to their theses

Email configuration is **optional**. The system works fully without email, but these features will be disabled.

## Quick Setup

### Step 1: Choose Your Email Provider

#### Option A: Gmail (Recommended for Testing)

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Thesis Manager"
   - Copy the 16-character password

3. Configure in `docker-compose.yml`:
   ```yaml
   - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   - EMAIL_HOST=smtp.gmail.com
   - EMAIL_PORT=587
   - EMAIL_USE_TLS=True
   - EMAIL_HOST_USER=your-email@gmail.com
   - EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # App password from step 2
   - DEFAULT_FROM_EMAIL=thesis-manager@yourdomain.com
   ```

#### Option B: Office 365 / Outlook

```yaml
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.office365.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=your-email@yourdomain.com
- EMAIL_HOST_PASSWORD=your-password
- DEFAULT_FROM_EMAIL=your-email@yourdomain.com
```

#### Option C: SendGrid

1. Create a SendGrid account and API key
2. Configure:
   ```yaml
   - EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   - EMAIL_HOST=smtp.sendgrid.net
   - EMAIL_PORT=587
   - EMAIL_USE_TLS=True
   - EMAIL_HOST_USER=apikey
   - EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxx  # Your SendGrid API key
   - DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

#### Option D: Mailgun

```yaml
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.mailgun.org
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=postmaster@yourdomain.mailgun.org
- EMAIL_HOST_PASSWORD=your-mailgun-password
- DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

#### Option E: Custom SMTP Server

```yaml
- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=mail.yourdomain.com
- EMAIL_PORT=587  # Or 465 for SSL, 25 for unencrypted
- EMAIL_USE_TLS=True  # False if using SSL or unencrypted
- EMAIL_USE_SSL=False  # True if using port 465
- EMAIL_HOST_USER=smtp-username
- EMAIL_HOST_PASSWORD=smtp-password
- DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Step 2: Update Configuration

1. Edit `docker-compose.yml`
2. Find the email configuration section under the `web` service
3. Uncomment the lines and fill in your SMTP details
4. Save the file

### Step 3: Restart Application

```bash
docker-compose down
docker-compose up -d
```

### Step 4: Test Email

#### Test Password Reset

1. Go to http://localhost/accounts/password_reset/
2. Enter a user's email address
3. Check if the email arrives

#### Test Comment Notifications

1. Create or edit a thesis with supervisors
2. Add a comment
3. Check if supervisors receive email notifications

#### Check Logs for Errors

```bash
docker-compose logs -f web | grep -i email
```

## Troubleshooting

### Emails Not Sending

1. **Check logs**:
   ```bash
   docker-compose logs web
   ```

2. **Verify environment variables are loaded**:
   ```bash
   docker-compose exec web python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.EMAIL_HOST)
   >>> print(settings.EMAIL_NOTIFICATIONS_ENABLED)
   ```

3. **Test SMTP connection**:
   ```bash
   docker-compose exec web python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

### Gmail "Less Secure App" Error

- Gmail no longer supports "less secure apps"
- You MUST use an App Password (see Gmail setup above)
- Regular password will not work

### Port 587 vs 465 vs 25

- **Port 587**: TLS (STARTTLS) - Most common, use `EMAIL_USE_TLS=True`
- **Port 465**: SSL - Use `EMAIL_USE_SSL=True`, `EMAIL_USE_TLS=False`
- **Port 25**: Unencrypted - Not recommended for production

### Authentication Errors

- Double-check username and password
- Some providers require full email as username, others just the username part
- Check if your provider requires app-specific passwords

### Firewall Issues

If running on a server, ensure outbound SMTP ports are not blocked:
```bash
telnet smtp.gmail.com 587
```

## Notification Behavior

### When Supervisors Receive Emails

Supervisors receive email notifications when:
1. A user adds a manual comment to a thesis they supervise
2. The system generates an automatic comment (date/phase change) on their thesis

### Email Contents

Emails include:
- Thesis title and type
- Student name(s)
- Current phase
- Comment text
- Comment author
- Important dates (deadline, presentation)

### Who Receives Notifications

- Only supervisors assigned to the thesis
- Only supervisors with valid email addresses
- All supervisors receive the same email (not BCC'd)

## Disabling Email

To disable email features:

1. Comment out email variables in `docker-compose.yml`
2. Or set `EMAIL_HOST=` (empty)
3. Restart: `docker-compose restart web`

The system will continue to work, but:
- Password reset will not be available
- Notifications will not be sent
- Emails will be logged to console in DEBUG mode

## Security Considerations

### Production Recommendations

1. **Use environment files**: Don't commit passwords to git
   ```bash
   # Create .env file (not in git)
   EMAIL_HOST_PASSWORD=secret123

   # Reference in docker-compose.yml
   env_file: .env
   ```

2. **Use app-specific passwords**: Don't use your main account password

3. **Use dedicated email account**: Create a separate email for the application

4. **Enable TLS/SSL**: Always use encrypted connections

5. **Restrict SMTP access**: Use firewall rules to limit outbound SMTP

### Email Privacy

- Supervisors on the same thesis all receive notification emails
- Email addresses are visible in the "To" field (not BCC)
- Consider using a mailing list service if privacy is a concern

## Advanced Configuration

### Custom Email Templates

Edit these files to customize email content:
- `theses/templates/emails/comment_notification.txt` - Comment notifications
- `theses/templates/registration/password_reset_email.html` - Password reset

After editing, restart:
```bash
docker-compose restart web
```

### Bulk Email Limits

Many providers have sending limits:
- Gmail: 500 emails/day
- SendGrid: Depends on plan
- Mailgun: Depends on plan

For high-volume use, consider a dedicated email service provider.

### HTML Email

The system currently sends plain text emails. To add HTML:

1. Create template: `theses/templates/emails/comment_notification.html`
2. Modify signal in `theses/signals.py` to use `EmailMultiAlternatives`

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs web`
2. Verify SMTP settings with your provider
3. Test with a simple email first
4. Check firewall/network restrictions
5. Consult provider's SMTP documentation

Common provider documentation:
- [Gmail SMTP](https://support.google.com/a/answer/176600)
- [Office 365 SMTP](https://learn.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-microsoft-365-or-office-365)
- [SendGrid SMTP](https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api)
- [Mailgun SMTP](https://documentation.mailgun.com/en/latest/user_manual.html#sending-via-smtp)
