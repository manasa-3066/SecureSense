# import os
# import smtplib
# from email.message import EmailMessage
# from dotenv import load_dotenv

# load_dotenv()


# # ============================================================
# # EMAIL CONFIGURATION
# # ============================================================

# SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
# SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")


# # ============================================================
# # SEND CRITICAL THREAT ALERT
# # ============================================================

# def send_critical_threat_email(incident):
#     """
#     Sends an email notification for a CRITICAL security incident.

#     Returns:
#         True  -> email sent successfully
#         False -> email not sent / configuration missing
#     """

#     if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL_TO:
#         print("Email notification skipped: SMTP configuration incomplete.")
#         return False

#     incident_id = incident.get("incident_id", "N/A")
#     prediction = incident.get("prediction", "N/A")
#     confidence = incident.get("confidence", 0)
#     risk_level = incident.get("risk_level", "N/A")
#     timestamp = incident.get("timestamp", "N/A")

#     subject = (
#         f"[SecureSense] CRITICAL Threat Detected - {incident_id}"
#     )

#     body = f"""
# SecureSense Security Alert
# ===========================

# A critical security threat has been detected.

# Incident ID : {incident_id}
# Prediction  : {prediction}
# Confidence  : {confidence}%
# Risk Level  : {risk_level}
# Timestamp   : {timestamp}

# The incident has been recorded in the SecureSense
# incident management system.

# Please investigate the incident through the
# SecureSense Security Operations Dashboard.

# This notification was generated automatically by SecureSense.
# """

#     message = EmailMessage()

#     message["Subject"] = subject
#     message["From"] = SMTP_USERNAME
#     message["To"] = ALERT_EMAIL_TO

#     message.set_content(body)

#     try:
#         with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:

#             server.ehlo()

#             server.starttls()

#             server.ehlo()

#             server.login(
#                 SMTP_USERNAME,
#                 SMTP_PASSWORD
#             )

#             server.send_message(message)

#         print(
#             f"Critical threat email sent successfully "
#             f"for incident {incident_id}"
#         )

#         return True

#     except Exception as error:

#         print(
#             f"Email notification failed: {error}"
#         )

#         return False

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_critical_threat_email(incident):
    """
    Sends a critical-threat notification using the Resend API.
    Works on Render Free because it uses HTTPS instead of SMTP.
    """

    resend_api_key = os.getenv("RESEND_API_KEY")
    alert_email_to = os.getenv("ALERT_EMAIL_TO")

    if not resend_api_key:
        print("RESEND_API_KEY is not configured.")
        return False

    if not alert_email_to:
        print("ALERT_EMAIL_TO is not configured.")
        return False

    incident_id = incident.get("incident_id", "N/A")
    prediction = incident.get("prediction", "N/A")
    confidence = incident.get("confidence", "N/A")
    risk_level = incident.get("risk_level", "CRITICAL")
    timestamp = incident.get("timestamp", "N/A")

    subject = f"🚨 SecureSense Critical Threat Alert - {incident_id}"

    html_content = f"""
    <html>
        <body>
            <h2>🚨 SecureSense Critical Threat Alert</h2>

            <p>A critical security threat has been detected by SecureSense.</p>

            <table border="1" cellpadding="8" cellspacing="0">
                <tr>
                    <td><strong>Incident ID</strong></td>
                    <td>{incident_id}</td>
                </tr>
                <tr>
                    <td><strong>Prediction</strong></td>
                    <td>{prediction}</td>
                </tr>
                <tr>
                    <td><strong>Confidence</strong></td>
                    <td>{confidence}</td>
                </tr>
                <tr>
                    <td><strong>Risk Level</strong></td>
                    <td>{risk_level}</td>
                </tr>
                <tr>
                    <td><strong>Timestamp</strong></td>
                    <td>{timestamp}</td>
                </tr>
            </table>

            <br>

            <p>
                Please review the incident in the SecureSense dashboard.
            </p>

            <p>
                <strong>SecureSense</strong><br>
                AI-Based Cyber Threat Detection and Incident Analysis Platform
            </p>
        </body>
    </html>
    """

    payload = {
        "from": "SecureSense <onboarding@resend.dev>",
        "to": [alert_email_to],
        "subject": subject,
        "html": html_content
    }

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code in (200, 201):
            print("Critical threat email sent successfully.")
            return True

        print(
            f"Resend email failed: "
            f"{response.status_code} - {response.text}"
        )
        return False

    except Exception as e:
        print(f"Error sending Resend email: {e}")
        return False