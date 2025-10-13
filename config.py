"""
Configuration settings for the Lead Qualification System.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Email configuration
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_ENABLED = EMAIL_USER and EMAIL_APP_PASSWORD

# Database configuration
DB_FILE = os.getenv("DB_FILE", "leads.db")

# Email routing configuration
EMAIL_ROUTING = {
    "enterprise": EMAIL_USER,
    "smb": EMAIL_USER,
    "individual": EMAIL_USER
}

# Cache configuration for lead deduplication
EMAIL_DEPUPE_WINDOW = 300  # 5 minutes in seconds
