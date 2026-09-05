#!/usr/bin/env python3
"""
Test notification credentials after manual configuration.
"""

import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import sys

def test_email():
    """Test email configuration."""
    print("🧪 Testing Email Configuration...")
    
    # Load secrets
    secrets_path = Path("config/secrets.yaml")
    if not secrets_path.exists():
        print("❌ Error: config/secrets.yaml not found!")
        print("Please copy config/secrets.yaml.example to config/secrets.yaml")
        print("and fill in your credentials.")
        return False
    
    try:
        with open(secrets_path, 'r') as f:
            secrets = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading secrets.yaml: {e}")
        return False
    
    email_config = secrets.get('email', {})
    
    # Check required fields
    required = ['from_email', 'password', 'to_primary']
    missing = [field for field in required if not email_config.get(field)]
    
    if missing:
        print(f"❌ Missing required email fields: {', '.join(missing)}")
        return False
    
    # Check for placeholder values
    if email_config['from_email'] == 'your.email@gmail.com':
        print("❌ Please replace example email with your actual Gmail address")
        return False
    
    if email_config['password'] == 'your-app-password-here':
        print("❌ Please replace example password with your Gmail App Password")
        print("   Get one from: https://myaccount.google.com/apppasswords")
        return False
    
    print(f"📧 From: {email_config['from_email']}")
    print(f"📧 To: {email_config['to_primary']}")
    
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_primary']
        msg['Subject'] = "✅ Household Resilience - Credentials Test Successful!"
        
        body = """Congratulations! Your email notifications are working correctly.

This test confirms that your Household Resilience Monitoring System can send alerts.

The system is monitoring these 6 trip-wire indicators:
• Treasury Reverse Repo (H1)
• ICE Detention Capacity (H4)
• Taiwan Strait Activity (H2)
• Hormuz War Risk Premium (H2)
• DoD Autonomous Systems (H2)
• mBridge CBDC Volume (H1)

When 2 or more indicators hit RED status, you'll receive a "TIGHTEN-UP" alert.

Stay prepared!
Your Resilience Monitoring System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print("📤 Sending test email...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_config['from_email'], email_config['password'])
        
        # Send to all configured recipients
        recipients = [email_config['to_primary']]
        if email_config.get('to_secondary') and email_config['to_secondary'] not in ['', 'family.member@gmail.com']:
            recipients.append(email_config['to_secondary'])
        
        for recipient in recipients:
            server.sendmail(email_config['from_email'], recipient, msg.as_string())
            print(f"✅ Email sent to: {recipient}")
        
        server.quit()
        
        print("\n✅ Email test PASSED! Check your inbox.")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication failed!")
        print("Common causes:")
        print("1. Using regular password instead of App Password")
        print("2. 2-Step Verification not enabled")
        print("3. Incorrect email or password")
        print("\nGet an App Password from: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"\n❌ Email test failed: {e}")
        return False

def test_system_ready():
    """Check if the system is ready to monitor."""
    print("\n🔍 Checking System Status...")
    
    # Check config files
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ config/config.yaml not found")
        return False
    
    # Check data directories
    data_dirs = ["data/raw", "data/processed", "data/historical", "logs"]
    for dir_path in data_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Directory missing: {dir_path}")
            return False
    
    print("✅ All directories present")
    print("✅ Configuration files loaded")
    
    # Check if we can import main modules
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from src.collectors import TreasuryCollector
        from src.processors import ThreatAnalyzer
        from src.notifications import AlertManager
        print("✅ All modules importable")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def main():
    """Run credential tests."""
    print("🏠 HOUSEHOLD RESILIENCE MONITORING - CREDENTIAL TEST")
    print("=" * 50)
    
    # Test email
    email_ok = test_email()
    
    # Test system
    system_ok = test_system_ready()
    
    if email_ok and system_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYour system is ready. You can now:")
        print("1. Run a status check: python src/main.py --check-status")
        print("2. Start monitoring: python src/main.py")
        print("3. Adjust thresholds: edit config/config.yaml")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
        if not email_ok:
            print("\n📧 Email Setup Help:")
            print("1. Copy config/secrets.yaml.example to config/secrets.yaml")
            print("2. Replace example values with your actual credentials")
            print("3. Use a Gmail App Password (not your regular password)")
            print("4. Get App Password from: https://myaccount.google.com/apppasswords")

if __name__ == "__main__":
    main()