# Deployment Guide - Household Resilience Monitor

## Cloud Deployment Options

### Option 1: Railway (Recommended - Easiest)
Railway is modern, simple, and has a generous free tier.

1. **Sign up at [Railway.app](https://railway.app)**

2. **Install Railway CLI**:
   ```bash
   brew install railway
   # or
   npm install -g @railway/cli
   ```

3. **Deploy**:
   ```bash
   cd household-resilience-monitor
   railway login
   railway init
   railway up
   ```

4. **Add Environment Variables**:
   ```bash
   railway variables set FRED_API_KEY=91c1cb50df4e3f061389ac2ecc335ead
   railway variables set NEWS_API_KEY=88dd145bb61d4aa0b9655edec04309f8
   railway variables set ALPHA_VANTAGE_KEY=H1UKYU1N148IZ94W
   ```

5. **Your app will be live at**: `https://your-app.railway.app`

### Option 2: Render (Also Easy)
Render offers free SSL and easy deploys.

1. **Sign up at [Render.com](https://render.com)**

2. **Create New Web Service**:
   - Connect GitHub repo
   - Build Command: `pip install -r requirements-prod.txt`
   - Start Command: `cd dashboard && gunicorn app:app`

3. **Add Environment Variables** in Render dashboard

4. **Your app will be live at**: `https://your-app.onrender.com`

### Option 3: Firebase (Google)
More complex but integrates well with other Google services.

1. **Install Firebase CLI**:
   ```bash
   npm install -g firebase-tools
   firebase login
   ```

2. **Initialize Firebase**:
   ```bash
   firebase init hosting
   firebase init functions
   ```

3. **Deploy**:
   ```bash
   firebase deploy
   ```

### Option 4: Self-Hosted (VPS)
For maximum control, use a VPS like DigitalOcean or Linode.

1. **Get a VPS** ($5-10/month)

2. **SSH and setup**:
   ```bash
   ssh root@your-server-ip
   apt update && apt upgrade
   apt install python3-pip nginx certbot
   ```

3. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/household-resilience-monitor
   cd household-resilience-monitor
   pip3 install -r requirements-prod.txt
   ```

4. **Configure Nginx**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:5555;
           proxy_set_header Host $host;
       }
   }
   ```

5. **Get SSL certificate**:
   ```bash
   certbot --nginx -d yourdomain.com
   ```

6. **Run with systemd**:
   ```bash
   # Create /etc/systemd/system/resilience.service
   [Unit]
   Description=Household Resilience Monitor
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/household-resilience-monitor
   ExecStart=/usr/bin/python3 dashboard/app.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

## Security Configuration

### 1. Add Authentication
```python
# In dashboard/app.py
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Set in environment variables
    return username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASS')

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

### 2. Environment Variables
Create `.env` file (never commit!):
```
FRED_API_KEY=your-key
NEWS_API_KEY=your-key
ALPHA_VANTAGE_KEY=your-key
ADMIN_USER=your-username
ADMIN_PASS=strong-password-here
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 3. HTTPS Only
Always use HTTPS in production. Railway and Render provide this automatically.

## Mobile Access

### PWA Setup
Add to `dashboard/templates/index.html`:
```html
<link rel="manifest" href="/manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
```

Create `dashboard/static/manifest.json`:
```json
{
  "name": "Household Resilience Monitor",
  "short_name": "Resilience",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#007bff",
  "background_color": "#ffffff",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

## Monitoring Your Deployment

### 1. Uptime Monitoring
- Use [UptimeRobot](https://uptimerobot.com) (free)
- Monitor `/api/status` endpoint
- Get alerts if site goes down

### 2. Error Tracking
- Add [Sentry](https://sentry.io) for error tracking:
```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### 3. Backup Data
```bash
# Backup script
#!/bin/bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/
# Upload to cloud storage
```

## Quick Start Commands

### Railway (Fastest)
```bash
# One-line deploy
railway login && railway init && railway up

# Add secrets
railway variables set FRED_API_KEY=your-key NEWS_API_KEY=your-key
```

### Local Testing
```bash
# Test production build locally
pip install -r requirements-prod.txt
gunicorn --chdir dashboard app:app --bind 0.0.0.0:5555
```

## Costs
- **Railway**: Free tier includes 500 hours/month
- **Render**: Free tier with spin-down after 15 min
- **Firebase**: Generous free tier
- **VPS**: $5-10/month for always-on

## Support
- Railway Discord: https://discord.gg/railway
- Render Community: https://community.render.com
- Firebase Support: https://firebase.google.com/support