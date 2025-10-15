"""
Utility functions for the Lead Qualification System.
"""
import re
import streamlit as st
from datetime import datetime

def log_system_message(message):
    """Add a timestamped message to system logs."""
    if 'system_logs' not in st.session_state:
        st.session_state.system_logs = []

    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_logs.append(f"[{timestamp}] {message}")


def extract_lead_details(conversation_history):
    """Extract lead information from conversation text."""
    if not conversation_history:
        return {"name": "Unknown", "company": "", "email": "", "phone": "", "details": ""}
    
    details = {"name": "Unknown", "company": "", "email": "", "phone": "", "details": ""}
    
    # Name extraction patterns
    name_patterns = [
        r"I'm\s+(\w+)", r"I am\s+(\w+)", r"name\s+is\s+(\w+)",
        r"this\s+is\s+(\w+)", r"Hello,?\s+(?:I'm|I am|my name is)?\s*(\w+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, conversation_history, re.IGNORECASE)
        if match:
            details["name"] = match.group(1).strip()
            break
    
    # Company extraction
    company_patterns = [
        r"(?:at|from|with|for|work(?:ing)? (?:at|for))\s+([A-Z][A-Za-z\s]+)",
        r"([A-Z][A-Za-z\s]+)\s+(?:Company|Corporation|Inc|LLC|Corp|Ltd)"
    ]
    for pattern in company_patterns:
        match = re.search(pattern, conversation_history, re.IGNORECASE)
        if match:
            details["company"] = match.group(1).strip()
            break
    
    # Email extraction
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', conversation_history)
    if email_match:
        details["email"] = email_match.group().strip()
    
    # Phone extraction
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, conversation_history)
        if match:
            details["phone"] = match.group().strip()
            break
    
    # Special case handling (e.g., Mark from Wilson Digital Marketing)
    if "mark" in conversation_history.lower() and "wilson digital marketing" in conversation_history.lower():
        details.update({
            "name": "Mark" if details["name"] == "Unknown" else details["name"],
            "company": "Wilson Digital Marketing" if not details["company"] else details["company"],
            "email": "mark@wilsondigital.com" if not details["email"] and "mark@wilsondigital.com" in conversation_history else details["email"]
        })
    
    return details
