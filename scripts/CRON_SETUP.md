# Cron Setup for Automated Weekly Reports

This guide explains how to set up automated weekly thesis progress reports using cron and `uv`.

## Prerequisites

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Verify uv installation**:
   ```bash
   uv --version
   ```

3. **Test the script manually**:
   ```bash
   cd /path/to/thesis-manager/scripts
   ./gitlab_reporter.py --dry-run --ai
   ```

## How It Works

The `gitlab_reporter.py` script uses **inline dependencies** (PEP 723):

```python
#!/usr/bin/env -S uv run --quiet
# /// script
# dependencies = [
#   "python-gitlab>=4.0.0",
#   "requests>=2.31.0",
#   ...
# ]
# ///
```

When you run `./gitlab_reporter.py`, `uv` automatically:
1. Creates an isolated environment
2. Installs all dependencies
3. Runs the script
4. Caches everything for fast subsequent runs

**No virtual environment or pyproject.toml needed!**

## Cron Configuration

### Option 1: Weekly Reports (Recommended)

Run every Monday at 9 AM:

```cron
# Weekly thesis progress reports
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai >> /path/to/thesis-manager/scripts/logs/cron.log 2>&1
```

### Option 2: Multiple Times Per Week

Run every Monday and Thursday at 9 AM:

```cron
# Bi-weekly thesis progress reports
0 9 * * 1,4 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai >> /path/to/thesis-manager/scripts/logs/cron.log 2>&1
```

### Option 3: Daily Reports (for active development phase)

Run Monday-Friday at 9 AM:

```cron
# Daily thesis progress reports (weekdays only)
0 9 * * 1-5 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai >> /path/to/thesis-manager/scripts/logs/cron.log 2>&1
```

### Option 4: Monthly Summary

Run on the 1st of each month at 9 AM with a longer analysis period:

```cron
# Monthly thesis progress reports (30-day period)
0 9 1 * * cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai --days 30 >> /path/to/thesis-manager/scripts/logs/cron.log 2>&1
```

## Step-by-Step Setup

### 1. Edit Crontab

```bash
crontab -e
```

### 2. Add Your Chosen Schedule

Copy one of the cron lines above, replacing `/path/to/thesis-manager` with your actual path:

```cron
# Example: Weekly reports every Monday at 9 AM
0 9 * * 1 cd /home/youruser/thesis-manager/scripts && ./gitlab_reporter.py --ai >> /home/youruser/thesis-manager/scripts/logs/cron.log 2>&1
```

### 3. Save and Exit

- **vim/vi**: Press `ESC`, type `:wq`, press `ENTER`
- **nano**: Press `CTRL+O`, `ENTER`, then `CTRL+X`

### 4. Verify Crontab

```bash
crontab -l
```

You should see your new cron job listed.

## Environment Variables

Cron runs with a minimal environment, so you need to ensure environment variables are available.

### Option A: Source .env in the script (Recommended)

The reporter script already loads `.env` via `python-dotenv`, so as long as `scripts/.env` exists with:

```bash
GITLAB_URL=https://gitlab.ibr.cs.tu-bs.de/
GITLAB_TOKEN=your-token
THESIS_MANAGER_URL=https://your-thesis-manager.com/
THESIS_MANAGER_API_TOKEN=your-token
OPENAI_API_KEY=sk-...
```

It will work automatically.

### Option B: Set environment in crontab

If you need to override variables, add them in crontab:

```cron
# Environment variables
OPENAI_API_KEY=sk-your-key-here

# Weekly reports
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai
```

## Logging

### Cron Output Log

The cron command redirects output to a log file:

```bash
>> /path/to/thesis-manager/scripts/logs/cron.log 2>&1
```

- `>>` appends to the log file
- `2>&1` redirects stderr to stdout (captures all output)

### View Recent Cron Runs

```bash
tail -n 100 /path/to/thesis-manager/scripts/logs/cron.log
```

### View AI Audit Log

```bash
tail -n 100 /path/to/thesis-manager/scripts/logs/ai_audit.log
```

### Log Rotation

To prevent logs from growing too large, set up log rotation:

Create `/etc/logrotate.d/thesis-reporter`:

```
/path/to/thesis-manager/scripts/logs/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
}
```

## Troubleshooting

### Cron job not running?

1. **Check cron service is running**:
   ```bash
   sudo systemctl status cron     # Ubuntu/Debian
   sudo systemctl status crond    # CentOS/RHEL
   ```

2. **Check system logs**:
   ```bash
   sudo grep CRON /var/log/syslog        # Ubuntu/Debian
   sudo journalctl -u cron -n 50         # Systemd
   ```

3. **Verify script permissions**:
   ```bash
   ls -l /path/to/thesis-manager/scripts/gitlab_reporter.py
   # Should show: -rwxr-xr-x (executable)
   ```

4. **Test manually with same environment**:
   ```bash
   # Run as cron would (minimal environment)
   env -i HOME=$HOME SHELL=/bin/bash /path/to/thesis-manager/scripts/gitlab_reporter.py --dry-run
   ```

### Dependencies not found?

Ensure `uv` is in the PATH for cron. Add to crontab:

```cron
PATH=/usr/local/bin:/usr/bin:/bin:/home/youruser/.local/bin
```

### Environment variables not working?

Check that `scripts/.env` exists and has correct permissions:

```bash
ls -la /path/to/thesis-manager/scripts/.env
# Should be readable: -rw-r--r--
```

### Script fails silently?

Check the cron log:

```bash
cat /path/to/thesis-manager/scripts/logs/cron.log
```

Add `--verbose` flag for more detailed output:

```cron
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai --verbose >> logs/cron.log 2>&1
```

## Email Notifications

### Enable Cron Email Alerts

Set MAILTO at the top of your crontab:

```cron
MAILTO=your-email@example.com

0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai
```

Cron will email you if there are any errors.

### Disable Email (if getting too many)

```cron
MAILTO=""
```

## Testing Before Deployment

### Dry Run Test

```bash
cd /path/to/thesis-manager/scripts
./gitlab_reporter.py --ai --dry-run
```

This will:
- Fetch theses and commits
- Generate reports (including AI analysis)
- Print reports to console
- **NOT** post comments to the system

### Test Single Thesis

```bash
./gitlab_reporter.py --thesis-id 1 --ai --dry-run
```

### Test Without AI

```bash
./gitlab_reporter.py --dry-run
```

## Advanced Options

### Custom Analysis Period

```cron
# Last 14 days instead of 7
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai --days 14 >> logs/cron.log 2>&1
```

### Specific AI Model

```cron
# Use GPT-4o instead of gpt-4o-mini
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai --ai-model gpt-4o >> logs/cron.log 2>&1
```

### Multiple Jobs with Different Schedules

```cron
# Weekly AI reports
0 9 * * 1 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py --ai >> logs/weekly.log 2>&1

# Daily basic reports (no AI) - cheaper, faster
0 9 * * 2-5 cd /path/to/thesis-manager/scripts && ./gitlab_reporter.py >> logs/daily.log 2>&1
```

## Monitoring

### Create a Health Check Script

Create `scripts/check_reports.sh`:

```bash
#!/bin/bash
# Check if reports were generated today

LOG_FILE="/path/to/thesis-manager/scripts/logs/cron.log"
TODAY=$(date +%Y-%m-%d)

if grep -q "$TODAY" "$LOG_FILE"; then
    echo "Reports generated successfully today"
    exit 0
else
    echo "ERROR: No reports found for $TODAY"
    exit 1
fi
```

Run this from a monitoring system or another cron job.

### Systemd Timer Alternative

If you prefer systemd over cron:

Create `/etc/systemd/system/thesis-reporter.service`:

```ini
[Unit]
Description=Thesis Progress Reporter
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/thesis-manager/scripts
ExecStart=/path/to/thesis-manager/scripts/gitlab_reporter.py --ai
StandardOutput=append:/path/to/thesis-manager/scripts/logs/cron.log
StandardError=append:/path/to/thesis-manager/scripts/logs/cron.log
```

Create `/etc/systemd/system/thesis-reporter.timer`:

```ini
[Unit]
Description=Weekly Thesis Progress Reports
Requires=thesis-reporter.service

[Timer]
OnCalendar=Mon *-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl enable thesis-reporter.timer
sudo systemctl start thesis-reporter.timer
sudo systemctl status thesis-reporter.timer
```

## Summary

**Recommended Setup:**

1. Install uv
2. Test manually: `./gitlab_reporter.py --dry-run --ai`
3. Add to crontab: `0 9 * * 1 cd /path/to/scripts && ./gitlab_reporter.py --ai >> logs/cron.log 2>&1`
4. Monitor logs: `tail -f logs/cron.log`

The beauty of using `uv` with inline dependencies is:
- ✅ No virtual environment to manage
- ✅ No manual dependency installation
- ✅ Automatic caching for fast runs
- ✅ Everything in one file
- ✅ Perfect for cron jobs
