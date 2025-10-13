"""
Streamlit UI components for the Lead Qualification System.
"""
import json
import streamlit as st
from config import OPENAI_API_KEY, EMAIL_USER, EMAIL_ENABLED
from database import init_database, get_all_leads, clear_all_leads
from email_service import send_test_email, route_lead_email
from utils import log_system_message


def render_sidebar():
    """Render the sidebar with configuration and controls."""
    st.sidebar.title("System Configuration")
    
    # API Key status
    if OPENAI_API_KEY:
        st.sidebar.success("✅ OpenAI API Key configured")
    else:
        st.sidebar.error("❌ OpenAI API Key not configured")
    
    # Email status and controls
    if EMAIL_ENABLED:
        st.sidebar.success(f"✅ Email enabled ({EMAIL_USER})")
        
        if st.sidebar.button("📧 Send Test Email"):
            send_test_email()
        
        if st.sidebar.button("📤 Test Email Routing"):
            results = []
            for lead_type in ["enterprise", "smb", "individual"]:
                result = route_lead_email(lead_type, f"Test {lead_type.title()} Lead")
                results.append("successfully" in result)
            
            if all(results):
                st.sidebar.success("✅ Test emails sent successfully!")
            else:
                st.sidebar.error("❌ Some test emails failed. Check logs.")
    else:
        st.sidebar.warning("⚠️ Email sending disabled")
        st.sidebar.info("Add EMAIL_USER and EMAIL_APP_PASSWORD to .env file")
    
    # Control buttons
    if st.sidebar.button("🔄 Reset Conversation"):
        st.session_state['messages'] = []
        st.session_state['conversation_history'] = ""
        log_system_message("SYSTEM: Conversation reset")
        st.rerun()
    
    # Database management
    st.sidebar.subheader("Database Management")
    
    if st.sidebar.button("👥 View Stored Leads"):
        df = get_all_leads()
        if not df.empty:
            st.sidebar.dataframe(df, use_container_width=True)
        else:
            st.sidebar.info("No leads found in database.")
    
    if st.sidebar.button("📤 Export Leads to JSON"):
        df = get_all_leads()
        if not df.empty:
            json_data = df.to_json(orient="records", indent=4)
            st.sidebar.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name="leads_export.json",
                mime="application/json"
            )
        else:
            st.sidebar.info("No leads to export.")
    
    # Clear leads with confirmation
    if st.sidebar.checkbox("I understand this will permanently delete all leads"):
        if st.sidebar.button("🗑️ Clear All Leads"):
            if clear_all_leads():
                st.sidebar.success("All leads cleared from database.")
            else:
                st.sidebar.error("Failed to clear leads.")


def render_main_content():
    """Render the main content area with chat interface."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display chat messages
        for message in st.session_state['messages']:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            # Import here to avoid circular imports and avoid conflict with installed package 'agents'
            from lead_agents import process_user_message
            import asyncio
            asyncio.run(process_user_message(user_input))
            st.rerun()
    
    with col2:
        # System logs
        st.subheader("System Logs")
        log_container = st.container(height=500)
        with log_container:
            for log in st.session_state['system_logs']:
                st.text(log)


def render_header():
    """Render the application header."""
    st.title("🤖 Lead Qualification System")
    st.markdown("Welcome to our automated lead qualification system. This chat will help us understand your needs and connect you with the right team.")


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'system_logs' not in st.session_state:
        st.session_state['system_logs'] = []


def setup_page_config():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Lead Qualification System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
