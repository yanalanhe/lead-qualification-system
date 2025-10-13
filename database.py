"""
Database operations for the Lead Qualification System.
"""
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
from config import DB_FILE


def init_database():
    """Initialize SQLite database and create tables."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            lead_type TEXT NOT NULL,
            name TEXT NOT NULL,
            company TEXT,
            email TEXT,
            phone TEXT,
            details TEXT,
            priority TEXT NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
        st.sidebar.success(f"✅ Connected to SQLite database: {DB_FILE}")
        return True
    except Exception as e:
        st.sidebar.error(f"❌ Failed to initialize database: {e}")
        return False


def save_lead_to_database(lead_type, lead_name, company=None, email=None, phone=None, details=None, priority="normal"):
    """Save lead information to database."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Import here to avoid circular imports
    from utils import log_system_message
    
    log_system_message(f"DATABASE: Storing lead for {lead_name}")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO leads (timestamp, lead_type, name, company, email, phone, details, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, lead_type, lead_name, company or "", email or "", phone or "", details or "", priority))
        conn.commit()
        conn.close()
        log_system_message(f"DATABASE: Lead successfully stored for {lead_name}")
        return f"Lead for {lead_name} successfully stored in database"
    except Exception as e:
        error_msg = f"Failed to store lead: {str(e)}"
        log_system_message(f"DATABASE ERROR: {error_msg}")
        return error_msg


def get_all_leads():
    """Retrieve all leads from database."""
    try:
        # Import here to avoid circular imports
        from utils import log_system_message
        
        log_system_message("DATABASE: Retrieving all leads")
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM leads ORDER BY timestamp DESC", conn)
        conn.close()
        log_system_message(f"DATABASE: Retrieved {len(df)} leads")
        return df
    except Exception as e:
        error_msg = f"Error retrieving leads: {str(e)}"
        log_system_message(f"DATABASE ERROR: {error_msg}")
        st.error(error_msg)
        return pd.DataFrame()


def clear_all_leads():
    """Clear all leads from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("DELETE FROM leads")
        conn.commit()
        conn.close()
        
        # Import here to avoid circular imports
        from utils import log_system_message
        log_system_message("DATABASE: All leads cleared")
        return True
    except Exception as e:
        st.error(f"Error clearing leads: {e}")
        return False
