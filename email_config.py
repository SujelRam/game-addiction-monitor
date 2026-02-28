"""
Email Configuration for Game Addiction Monitor
==============================================

This file stores Gmail SMTP configuration for sending email alerts.

SECURITY WARNING: Never commit this file to version control!
Add this file to .gitignore if you use git.

HOW TO SET UP GMAIL APP PASSWORD:
---------------------------------
1. Go to your Google Account (https://myaccount.google.com)
2. Navigate to Security > 2-Step Verification (enable it if not already)
3. Go to https://myaccount.google.com/apppasswords
4. Create a new app password for "Mail"
5. Use that 16-character password as your GMAIL_APP_PASSWORD

SET YOUR CREDENTIALS:
---------------------
Option 1 (Recommended - Environment Variables):
   Set environment variables:
   - GMAIL_EMAIL: your Gmail address
   - GMAIL_APP_PASSWORD: your 16-character app password

Option 2 (Config File - Less Secure):
   Edit the values below:
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_email_config():
    """
    Get email configuration from environment variables or config file.
    
    Returns:
        dict: Email configuration with 'email' and 'app_password' keys
    """
    # Try to get from environment variables first (more secure)
    gmail_email = os.environ.get('GMAIL_EMAIL')
    gmail_app_password = os.environ.get('GMAIL_APP_PASSWORD')
    
    if gmail_email and gmail_app_password:
        logger.info("Email configuration loaded from environment variables")
        return {
            'email': gmail_email,
            'app_password': gmail_app_password
        }
    
    # Fall back to config file values (less secure)
    # ============================================================
    # EDIT THESE VALUES - Set your Gmail and App Password here
    # ============================================================
    # Replace 'your_gmail@gmail.com' with your actual Gmail address
    # Replace 'your_app_password' with your 16-character Gmail App Password
    gmail_email = "updatestosujel@gmail.com"
    gmail_app_password = "elvnfrqfomxdltch"
    # ============================================================
    
    if gmail_email == "your_gmail@gmail.com" or gmail_app_password == "your_app_password":
        logger.warning("Email not configured! Please set your Gmail credentials.")
        logger.warning("Edit email_config.py or set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables")
        return None
    
    logger.info("Email configuration loaded from email_config.py")
    return {
        'email': gmail_email,
        'app_password': gmail_app_password
    }


def is_email_configured():
    """Check if email is properly configured."""
    config = get_email_config()
    return config is not None


# For backward compatibility - export the config values
EMAIL_CONFIG = get_email_config()
GMAIL_EMAIL = EMAIL_CONFIG['email'] if EMAIL_CONFIG else "your_gmail@gmail.com"
GMAIL_APP_PASSWORD = EMAIL_CONFIG['app_password'] if EMAIL_CONFIG else "your_app_password"
