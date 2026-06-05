# services/email_service.py
import secrets
import aiosmtplib
from email.mime.text import MIMEText
import os

async def dispatch_production_mfa_token(recipient_email: str) -> str:
    """
    Generates a cryptographically secure 6-digit OTP token and transfers 
    it via an asynchronous network socket route directly to AWS SES / SendGrid.
    """
    # 1. Cryptographically sound numeric generation
    secret_otp = f"{secrets.randbelow(900000) + 100000}"
    
    # 2. Build the corporate notification envelope
    message = MIMEText(
        f"FinAdvisorGPT Terminal Access Validation Challenge Token.\n\n"
        f"Token Key: {secret_otp}\n\n"
        f"This security string is valid for 10 minutes. If you did not trigger "
        f"this access query, notify your network operations center immediately.",
        "plain"
    )
    message["From"] = os.getenv("MFA_SENDER_IDENTITY", "security@institution.com")
    message["To"] = recipient_email
    message["Subject"] = "🔒 TERMINAL SECURITY: 6-Digit Verification Token"
    
    # 3. Asynchronous SMTP Transport Handshake with AWS SES endpoint
    # These configurations run on non-blocking loops so your app doesn't freeze.
    await aiosmtplib.send(
        message,
        hostname=os.getenv("SMTP_GATEWAY_HOST", "email-smtp.us-east-1.amazonaws.com"),
        port=int(os.getenv("SMTP_GATEWAY_PORT", 587)),
        username=os.getenv("SMTP_GATEWAY_USER"),
        password=os.getenv("SMTP_GATEWAY_SECRET"),
        use_tls=True
    )
    
    # Return the generated OTP string back to the state manager for local database verification
    return secret_otp