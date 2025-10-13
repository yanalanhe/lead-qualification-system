"""
Main application entry point for the Lead Qualification System.
"""
import streamlit as st
from database import init_database
from ui import setup_page_config, initialize_session_state, render_header, render_sidebar, render_main_content


def main():
    """Main Streamlit application."""
    # Page configuration
    setup_page_config()
    
    # Header
    render_header()
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize database
    if not init_database():
        st.warning("Failed to initialize database. Check system logs for details.")
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()
















