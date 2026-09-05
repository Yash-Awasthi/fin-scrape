"""
Email notifier for sending alerts via SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging
from datetime import datetime


class EmailNotifier:
    """Email notification handler."""
    
    def __init__(self, config):
        """
        Initialize email notifier.
        
        Args:
            config: Configuration object with email settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get email configuration from secrets
        secrets = config.get_secrets()
        self.email_config = secrets.get('email', {})
        
        if not self.email_config.get('from_email'):
            self.logger.warning("Email configuration not found in secrets")
    
    def send(self, alert_data: Dict[str, Any]):
        """Send alert via email."""
        if not self.email_config.get('from_email'):
            self.logger.debug("Email not configured, skipping notification")
            return
            
        alert_type = alert_data['type']
        
        if alert_type == 'TIGHTEN_UP':
            self._send_tightenup_alert(alert_data)
        elif alert_type == 'ERROR':
            self._send_error_alert(alert_data)
        # Status updates are not sent via email to avoid spam
    
    def _send_tightenup_alert(self, alert_data: Dict[str, Any]):
        """Send TIGHTEN-UP alert email."""
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_primary']
        msg['Subject'] = f"🚨 HOUSEHOLD RESILIENCE ALERT: {alert_data['red_count']} Red Conditions - TIGHTEN-UP REQUIRED"
        
        # Build the email body
        body = self._build_tightenup_body(alert_data)
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_config['from_email'], self.email_config['password'])
            server.sendmail(
                self.email_config['from_email'], 
                self.email_config['to_primary'], 
                msg.as_string()
            )
            server.quit()
            self.logger.info(f"TIGHTEN-UP alert email sent to {self.email_config['to_primary']}")
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def _send_error_alert(self, alert_data: Dict[str, Any]):
        """Send error alert email."""
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_primary']
        msg['Subject'] = f"⚠️ Household Resilience Monitor Error: {alert_data.get('collector', 'System')}"
        
        body = f"""HOUSEHOLD RESILIENCE MONITOR - ERROR ALERT

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Component: {alert_data.get('collector', 'System')}
Error: {alert_data['error']}

The monitoring system encountered an error but will continue checking other indicators.

--
Automated monitoring system
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_config['from_email'], self.email_config['password'])
            server.sendmail(
                self.email_config['from_email'], 
                self.email_config['to_primary'], 
                msg.as_string()
            )
            server.quit()
            self.logger.info(f"Error alert email sent to {self.email_config['to_primary']}")
        except Exception as e:
            self.logger.error(f"Failed to send error email: {e}")
    
    def _build_tightenup_body(self, alert_data: Dict[str, Any]) -> str:
        """Build the TIGHTEN-UP alert email body."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format red indicators
        red_indicators = []
        for name, _ in alert_data['red_indicators']:
            reading = alert_data['readings'].get(name, {})
            value = reading.get('formatted', 'N/A')
            red_indicators.append(f"🚨 {name}: {value}")
        
        # Format other indicators
        other_indicators = []
        for name, level in alert_data['threat_levels'].items():
            if level != "red":
                reading = alert_data['readings'].get(name, {})
                value = reading.get('formatted', 'N/A')
                symbol = "✅" if level == "green" else "⚠️" if level == "amber" else "❓"
                other_indicators.append(f"{symbol} {name}: {value} ({level.upper()})")
        
        body = f"""🚨 HOUSEHOLD RESILIENCE TIGHTEN-UP ALERT 🚨

IMMEDIATE ACTION REQUIRED: {alert_data['red_count']} Red Alert Conditions Detected

Generated: {timestamp}

CRITICAL TRIP-WIRES IN RED STATUS:
{chr(10).join(red_indicators)}

OTHER INDICATORS:
{chr(10).join(other_indicators)}

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

Multiple red indicators suggest potential for cascading effects.
This is NOT a drill. The confluence of these indicators
warrants immediate preparedness actions.

============================================
NEXT SYSTEM ACTIONS
============================================

• Monitoring continues hourly
• Next alert only if conditions change significantly
• Daily summary at 8 AM unless urgent changes

Stay prepared, stay calm, stay informed.

--
Household Resilience Monitoring System
Based on H1-H6 Risk Analysis Framework

This is an automated alert. Do not reply to this email.
For system issues, check logs at: logs/monitor.log"""
        
        return body