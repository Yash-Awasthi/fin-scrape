# Gmail App Password Setup Guide

This guide helps you set up Gmail for sending alerts from the Household Resilience Monitoring System.

## Why App Passwords?

Google requires app-specific passwords for third-party applications to enhance security. Your regular Gmail password won't work.

## Step-by-Step Setup

### 1. Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on "2-Step Verification"
3. Follow the setup process (phone number verification)
4. Complete 2FA setup

### 2. Generate App Password

1. After enabling 2FA, go back to [Security Settings](https://myaccount.google.com/security)
2. Search for "App passwords" or find it under "2-Step Verification"
3. Click "App passwords"
4. Select app: "Mail"
5. Select device: "Other (custom name)"
6. Enter name: "Household Resilience Monitor"
7. Click "Generate"
8. **Copy the 16-character password** (spaces don't matter)

### 3. Configure the System

Run the configuration helper:
```bash
cd household-resilience-monitor
source venv/bin/activate
python scripts/configure_credentials.py
```

Enter:
- Your Gmail address: `yourname@gmail.com`
- App password: The 16-character password from step 2
- Alert recipients: Email addresses for family members

### 4. Test Configuration

The script will offer to send a test email. If it fails:

1. Check the app password is correct
2. Ensure 2FA is enabled
3. Try generating a new app password
4. Check Gmail isn't blocking the connection

## Security Best Practices

1. **Never share your app password**
2. **Don't commit secrets.yaml to git** (it's already in .gitignore)
3. **Use unique app passwords** for different applications
4. **Revoke unused app passwords** from Google Account settings

## Alternative Email Providers

If you prefer not to use Gmail:

### Outlook/Hotmail
- SMTP Server: `smtp-mail.outlook.com`
- Port: `587`
- Requires app password from Microsoft account settings

### Yahoo Mail
- SMTP Server: `smtp.mail.yahoo.com`
- Port: `587`
- Generate app password from Yahoo account security

### ProtonMail
- Requires ProtonMail Bridge application
- SMTP Server: `127.0.0.1`
- Port: `1025`

## Troubleshooting

### "Authentication failed"
- Regenerate app password
- Check for typos in email/password
- Ensure 2FA is active

### "Connection timeout"
- Check firewall settings
- Try different network
- Verify SMTP settings in config.yaml

### "Less secure app blocked"
- This means you're using regular password instead of app password
- Follow steps above to generate app password

## Next Steps

After email is configured:
1. Test the monitoring system: `python src/main.py --check-status`
2. Set alert thresholds in `config/config.yaml`
3. Schedule automated monitoring
4. Configure SMS alerts (optional) with Twilio