#!/usr/bin/env python3
"""
Interactive credential configuration helper for household resilience monitoring.
Helps set up email and SMS notifications with proper validation.
"""

import yaml
import os
import re
import getpass
from pathlib import Path

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format."""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits including country code)
    return len(digits) >= 10 and len(digits) <= 15

def configure_email():
    """Configure email notification settings."""
    print("\n📧 EMAIL NOTIFICATION SETUP")
    print("-" * 40)
    print("For Gmail, you'll need an App Password:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-factor authentication")
    print("3. Search for 'App passwords'")
    print("4. Create a new app password for 'Mail'")
    print("-" * 40)
    
    email_config = {}
    
    # From email
    while True:
        from_email = input("\nYour email address (e.g., yourname@gmail.com): ").strip()
        if validate_email(from_email):
            email_config['from_email'] = from_email
            break
        else:
            print("❌ Invalid email format. Please try again.")
    
    # Password
    print("\nEnter your email app password (will be hidden):")
    email_config['password'] = getpass.getpass("App password: ")
    
    # Primary recipient
    while True:
        to_primary = input("\nPrimary alert recipient email: ").strip()
        if validate_email(to_primary):
            email_config['to_primary'] = to_primary
            break
        else:
            print("❌ Invalid email format. Please try again.")
    
    # Secondary recipient (optional)
    to_secondary = input("\nSecondary alert recipient (optional, press Enter to skip): ").strip()
    if to_secondary and validate_email(to_secondary):
        email_config['to_secondary'] = to_secondary
    else:
        email_config['to_secondary'] = ""
    
    return email_config

def configure_sms():
    """Configure SMS notification settings."""
    print("\n📱 SMS NOTIFICATION SETUP (Optional)")
    print("-" * 40)
    print("For SMS alerts, you'll need a Twilio account:")
    print("1. Sign up at https://www.twilio.com")
    print("2. Get your Account SID and Auth Token")
    print("3. Get a Twilio phone number")
    print("-" * 40)
    
    use_sms = input("\nDo you want to set up SMS notifications? (y/N): ").strip().lower()
    
    if use_sms != 'y':
        return {
            'twilio_sid': '',
            'twilio_token': '',
            'twilio_from': '',
            'sms_to_primary': ''
        }
    
    sms_config = {}
    
    # Twilio credentials
    sms_config['twilio_sid'] = input("\nTwilio Account SID: ").strip()
    sms_config['twilio_token'] = getpass.getpass("Twilio Auth Token: ")
    
    # From number
    while True:
        from_number = input("\nTwilio phone number (e.g., +1234567890): ").strip()
        if validate_phone(from_number):
            sms_config['twilio_from'] = from_number
            break
        else:
            print("❌ Invalid phone number. Include country code (e.g., +1234567890)")
    
    # To number
    while True:
        to_number = input("\nYour phone number for alerts (e.g., +1234567890): ").strip()
        if validate_phone(to_number):
            sms_config['sms_to_primary'] = to_number
            break
        else:
            print("❌ Invalid phone number. Include country code (e.g., +1234567890)")
    
    return sms_config

def test_email_config(email_config):
    """Test email configuration by sending a test message."""
    print("\n🧪 Testing email configuration...")
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_primary']
        msg['Subject'] = "✅ Household Resilience System - Test Email"
        
        body = """This is a test email from your Household Resilience Monitoring System.

If you're receiving this, your email notifications are configured correctly!

The system will send alerts when trip-wire indicators reach critical levels.

Stay prepared,
Your Resilience Monitoring System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_config['from_email'], email_config['password'])
        
        recipients = [email_config['to_primary']]
        if email_config.get('to_secondary'):
            recipients.append(email_config['to_secondary'])
        
        for recipient in recipients:
            server.sendmail(email_config['from_email'], recipient, msg.as_string())
        
        server.quit()
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print("\nCommon issues:")
        print("- Wrong app password (not your regular Gmail password)")
        print("- 2-factor authentication not enabled")
        print("- Less secure app access blocked")
        return False

def main():
    """Main configuration workflow."""
    print("🏠 HOUSEHOLD RESILIENCE MONITORING - CREDENTIAL SETUP")
    print("=" * 50)
    
    # Check if secrets.yaml exists
    secrets_path = Path("config/secrets.yaml")
    
    if secrets_path.exists():
        overwrite = input("\n⚠️  Secrets file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Configuration cancelled.")
            return
    
    # Configure email
    email_config = configure_email()
    
    # Configure SMS
    sms_config = configure_sms()
    
    # Prepare final configuration
    secrets = {
        'email': email_config,
        'sms': sms_config,
        'api_keys': {
            'treasury_api_key': '',
            'news_api_key': ''
        }
    }
    
    # Save configuration
    print("\n💾 Saving configuration...")
    with open(secrets_path, 'w') as f:
        yaml.dump(secrets, f, default_flow_style=False)
    
    print("✅ Configuration saved to config/secrets.yaml")
    
    # Test email
    test_email = input("\n📧 Would you like to send a test email? (Y/n): ").strip().lower()
    if test_email != 'n':
        test_email_config(email_config)
    
    print("\n✅ CONFIGURATION COMPLETE!")
    print("\nNext steps:")
    print("1. Run: python src/main.py --check-status")
    print("2. Modify thresholds in config/config.yaml if needed")
    print("3. Set up automated monitoring with cron or task scheduler")
    
    print("\n🔒 Security reminder:")
    print("- config/secrets.yaml is git-ignored for security")
    print("- Never commit credentials to version control")
    print("- Use app-specific passwords, not your main password")

if __name__ == "__main__":
    main()