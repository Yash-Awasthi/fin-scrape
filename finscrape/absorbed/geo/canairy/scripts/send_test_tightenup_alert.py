#!/usr/bin/env python3
"""
Send a test TIGHTEN-UP alert email to demonstrate the alert system.
"""

import smtplib
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

def send_tightenup_alert():
    """Send a test TIGHTEN-UP alert email."""
    
    # Load secrets
    secrets_path = Path("config/secrets.yaml")
    with open(secrets_path, 'r') as f:
        secrets = yaml.safe_load(f)
    
    email_config = secrets.get('email', {})
    
    # Create the TIGHTEN-UP alert message
    msg = MIMEMultipart()
    msg['From'] = email_config['from_email']
    msg['To'] = email_config['to_primary']
    msg['Subject'] = "🚨 HOUSEHOLD RESILIENCE ALERT: 3 Red Conditions - TIGHTEN-UP REQUIRED"
    
    # Create the alert body
    body = f"""🚨 HOUSEHOLD RESILIENCE TIGHTEN-UP ALERT 🚨

IMMEDIATE ACTION REQUIRED: 3 Red Alert Conditions Detected

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CRITICAL TRIP-WIRES IN RED STATUS:
🚨 Treasury Tail: 2.5 basis points (Threshold: 2.0)
🚨 ICE Detention: 75.0% capacity (Threshold: 70%)
🚨 mBridge Settlement: $15.5B (Threshold: $15B)

OTHER INDICATORS:
✅ Hormuz Risk: 0.8% (GREEN - below 0.7% threshold)
❓ Taiwan Zone: 8 incursions/week (Status unknown)
❓ DoD Autonomy: 350 systems (Status unknown)

============================================
IMMEDIATE ACTIONS (Complete within 48 hours):
============================================

✅ FUEL & CASH
   □ Top off all vehicle fuel tanks
   □ Fill any backup fuel containers
   □ Withdraw cash reserves ($500-1000 minimum)
   □ Ensure small bills available

✅ POWER & COMMUNICATIONS
   □ Charge ALL power banks to 100%
   □ Charge all devices (phones, tablets, radios)
   □ Test backup communication methods
   □ Verify emergency contact list is current

✅ FAMILY COORDINATION
   □ Conduct family briefing within 24 hours
   □ Review emergency meeting locations
   □ Confirm out-of-state contact person
   □ Test communication plan with all members

✅ INFORMATION AWARENESS
   □ Monitor trusted OSINT feeds more frequently
   □ Check local emergency management updates
   □ Review weather and regional alerts
   □ Avoid social media panic/rumors

✅ SUPPLIES CHECK
   □ Verify 72-hour kit completeness
   □ Check water supplies (1 gal/person/day)
   □ Inventory non-perishable food
   □ Confirm medications are current

✅ HOME READINESS
   □ Test flashlights and emergency lighting
   □ Locate important documents
   □ Review shelter-in-place supplies
   □ Clear any trip hazards/obstacles

============================================
PHASE RECOMMENDATIONS
============================================

Based on current threat levels, review preparedness phases:

Phase 0-3: IMMEDIATE PRIORITY
- Foundations and 72-hour readiness
- Communications and digital resilience
- Health and mobile communications

Phase 4-6: NEXT 7 DAYS (if conditions persist)
- Basement/shelter preparations
- Generator readiness
- Enhanced physical security

Phase 7-9: EVALUATE NEED
- Based on threat evolution
- Consult local conditions
- Community coordination

============================================
WHY THIS MATTERS
============================================

Multiple red indicators suggest:
• Financial system stress (Treasury, mBridge)
• Social/migration pressures (ICE capacity)
• Potential for cascading effects

This is NOT a drill. The confluence of these indicators
warrants immediate preparedness actions.

============================================
NEXT SYSTEM ACTIONS
============================================

• Monitoring frequency increased to every 15 minutes
• Next alert only if conditions change significantly
• Daily summary at 8 AM unless urgent changes

Stay prepared, stay calm, stay informed.

--
Household Resilience Monitoring System
Based on H1-H6 Risk Analysis Framework

This is an automated alert. Do not reply to this email.
For system issues, check logs at: logs/monitor.log"""
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    print("📤 Sending TIGHTEN-UP alert email...")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_config['from_email'], email_config['password'])
        server.sendmail(email_config['from_email'], email_config['to_primary'], msg.as_string())
        server.quit()
        
        print("✅ TIGHTEN-UP alert email sent successfully!")
        print(f"   To: {email_config['to_primary']}")
        print(f"   Subject: {msg['Subject']}")
        
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

if __name__ == "__main__":
    send_tightenup_alert()