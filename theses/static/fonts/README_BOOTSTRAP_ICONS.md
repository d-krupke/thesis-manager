# Bootstrap Icons Setup

Bootstrap Icons are required by this application but not included in the repository.

## Installation

Download Bootstrap Icons from the official source:
https://github.com/twbs/icons/releases/latest

### Option 1: Quick Install (Recommended)

```bash
# Download and extract Bootstrap Icons fonts
cd theses/static/fonts
curl -L https://github.com/twbs/icons/releases/download/v1.11.3/bootstrap-icons-1.11.3.zip -o bootstrap-icons.zip
unzip bootstrap-icons.zip
mv bootstrap-icons-1.11.3/font/fonts/* .
cd ../css
mv ../fonts/bootstrap-icons-1.11.3/font/bootstrap-icons.min.css bootstrap-icons.min.css
cd ../fonts
rm -rf bootstrap-icons-1.11.3 bootstrap-icons.zip
```

### Option 2: Manual Install

1. Download from: https://github.com/twbs/icons/releases
2. Extract the archive
3. Copy `font/fonts/*` files to `theses/static/fonts/`
4. Copy `font/bootstrap-icons.min.css` to `theses/static/css/`
5. Edit `bootstrap-icons.min.css` and update the font paths:
   - Change `url("./fonts/bootstrap-icons.woff2")`
   - To `url("../fonts/bootstrap-icons.woff2")`

### What You Need

After installation, you should have:
- `theses/static/fonts/bootstrap-icons.woff`
- `theses/static/fonts/bootstrap-icons.woff2`
- `theses/static/css/bootstrap-icons.min.css`

### Verify Installation

After running collectstatic, check that these files exist:
```bash
docker-compose exec web python manage.py collectstatic --noinput
ls staticfiles/fonts/ | grep bootstrap-icons
ls staticfiles/css/ | grep bootstrap-icons
```

## Security Note

We use local copies instead of CDN to:
- Prevent external requests that could leak information
- Ensure availability in air-gapped environments
- Comply with data protection requirements
- Avoid dependency on external services
