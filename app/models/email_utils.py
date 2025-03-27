import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# These should be set in your .env file
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@dut.ac.za')

def send_email(recipient, subject, message, from_email=None):
    """
    Send an email notification
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Email subject
        message (str): Email message (HTML)
        from_email (str, optional): Sender email. Defaults to DEFAULT_FROM_EMAIL.
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # For development/testing, just print the email instead of sending
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print(f"\n----- EMAIL -----")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print(f"----- END EMAIL -----\n")
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email or DEFAULT_FROM_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'html'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_grievance_status_update(email, grievance_id, new_status, title):
    """Send email notification about grievance status update"""
    subject = f"Grievance Status Update - {title}"
    message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://www.dut.ac.za/wp-content/uploads/2022/03/DUT-NEW-LOGO.png" alt="DUT Logo" style="max-width: 150px;">
            </div>
            <h2 style="color: #004F9F;">Grievance Status Update</h2>
            <p>Dear Student,</p>
            <p>The status of your grievance <strong>#{grievance_id}</strong> with title "<strong>{title}</strong>" has been updated to: <strong style="color: #E31837;">{new_status}</strong>.</p>
            <p>You can login to the Student Grievance Portal to view more details and track the progress of your grievance.</p>
            <div style="margin-top: 30px; text-align: center;">
                <a href="#" style="background-color: #004F9F; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Grievance</a>
            </div>
            <p style="margin-top: 30px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 15px;">
                This is an automated message from the DUT Student Grievance Management System. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(email, subject, message)

def send_new_grievance_notification(email, grievance_id, title):
    """Send email notification about a new grievance submission"""
    subject = f"Grievance Submitted Successfully - {title}"
    message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://www.dut.ac.za/wp-content/uploads/2022/03/DUT-NEW-LOGO.png" alt="DUT Logo" style="max-width: 150px;">
            </div>
            <h2 style="color: #004F9F;">Grievance Submitted Successfully</h2>
            <p>Dear Student,</p>
            <p>Your grievance has been submitted successfully.</p>
            <p><strong>Grievance ID:</strong> #{grievance_id}<br>
            <strong>Title:</strong> {title}<br>
            <strong>Status:</strong> Pending</p>
            <p>Your grievance will be reviewed by the administration shortly. You will receive notifications as its status changes.</p>
            <div style="margin-top: 30px; text-align: center;">
                <a href="#" style="background-color: #004F9F; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Grievance</a>
            </div>
            <p style="margin-top: 30px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 15px;">
                This is an automated message from the DUT Student Grievance Management System. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(email, subject, message) 