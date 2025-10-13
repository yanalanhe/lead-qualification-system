# Lead Qualification System - Modular Architecture

This project has been restructured into a modular architecture for better maintainability and organization.

## Project Structure

```
lead-qualification-system/
├── app.py                 # Main application entry point
├── config.py             # Configuration and environment variables
├── database.py           # Database operations and SQLite functions
├── email_service.py      # Email functionality and routing
├── agents.py             # Agent system, handoffs, and processing logic
├── utils.py              # Utility functions (logging, lead extraction)
├── ui.py                 # Streamlit UI components
├── leads.db              # SQLite database file
└── venv/                 # Virtual environment
```

## Module Descriptions

### `app.py`
- **Purpose**: Main application entry point
- **Responsibilities**: Orchestrates all modules and runs the Streamlit application
- **Key Functions**: `main()`

### `config.py`
- **Purpose**: Centralized configuration management
- **Responsibilities**: Environment variables, API keys, email settings, database configuration
- **Key Variables**: `OPENAI_API_KEY`, `EMAIL_USER`, `EMAIL_APP_PASSWORD`, `DB_FILE`, `EMAIL_ROUTING`

### `database.py`
- **Purpose**: Database operations and data persistence
- **Responsibilities**: SQLite database initialization, lead storage, data retrieval
- **Key Functions**: `init_database()`, `save_lead_to_database()`, `get_all_leads()`, `clear_all_leads()`

### `email_service.py`
- **Purpose**: Email functionality and notification system
- **Responsibilities**: Email sending, lead routing, deduplication, test emails
- **Key Functions**: `send_email_message()`, `route_lead_email()`, `force_lead_email()`, `send_test_email()`

### `agents.py`
- **Purpose**: AI agent system and conversation processing
- **Responsibilities**: Agent creation, handoffs, message processing, tool functions
- **Key Functions**: `create_agent_system()`, `process_user_message()`, `create_handoff_callback()`

### `utils.py`
- **Purpose**: Utility functions and helper methods
- **Responsibilities**: System logging, lead information extraction, text processing
- **Key Functions**: `log_system_message()`, `extract_lead_details()`

### `ui.py`
- **Purpose**: Streamlit user interface components
- **Responsibilities**: Page layout, sidebar controls, chat interface, system logs display
- **Key Functions**: `render_sidebar()`, `render_main_content()`, `render_header()`, `setup_page_config()`

## Benefits of Modular Architecture

1. **Separation of Concerns**: Each module has a single responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Testability**: Individual modules can be tested in isolation
4. **Reusability**: Modules can be imported and used in other projects
5. **Scalability**: New features can be added without affecting existing code
6. **Code Organization**: Related functionality is grouped together

## Running the Application

The application can be run using the same command as before:

```bash
streamlit run app.py
```

All functionality remains the same, but the code is now organized in a more maintainable structure.

## Dependencies

The modular structure maintains all original dependencies:
- `streamlit`
- `openai`
- `pandas`
- `sqlite3`
- `smtplib`
- `python-dotenv`
- `agents` (custom agent framework)

## Migration Notes

- All original functionality has been preserved
- No changes to the database schema or email configuration
- The user interface remains identical
- All agent behaviors and handoffs work as before
- Environment variables and configuration remain the same
