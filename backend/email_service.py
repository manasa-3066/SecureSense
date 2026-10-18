import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")


# ============================================================
# SEND CRITICAL THREAT ALERT
# ============================================================

def send_critical_threat_email(incident):
    """
    Sends an email notification for a CRITICAL security incident.

    Returns:
        True  -> email sent successfully
        False -> email not sent / configuration missing
    """

    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL_TO:
        print("Email notification skipped: SMTP configuration incomplete.")
        return False

    incident_id = incident.get("incident_id", "N/A")
    prediction = incident.get("prediction", "N/A")
    confidence = incident.get("confidence", 0)
    risk_level = incident.get("risk_level", "N/A")
    timestamp = incident.get("timestamp", "N/A")

    subject = (
        f"[SecureSense] CRITICAL Threat Detected - {incident_id}"
    )

    body = f"""
SecureSense Security Alert
===========================

A critical security threat has been detected.

Incident ID : {incident_id}
Prediction  : {prediction}
Confidence  : {confidence}%
Risk Level  : {risk_level}
Timestamp   : {timestamp}

The incident has been recorded in the SecureSense
incident management system.

Please investigate the incident through the
SecureSense Security Operations Dashboard.

This notification was generated automatically by SecureSense.
"""

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = SMTP_USERNAME
    message["To"] = ALERT_EMAIL_TO

    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(message)

        print(
            f"Critical threat email sent successfully "
            f"for incident {incident_id}"
        )

        return True

    except Exception as error:

        print(
            f"Email notification failed: {error}"
        )

        return False