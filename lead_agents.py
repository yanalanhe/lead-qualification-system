"""
Agent system for the Lead Qualification System.
"""
import asyncio
import streamlit as st
from agents import (
    Agent, Runner, function_tool, handoff, RunContextWrapper,
    ModelSettings, input_guardrail, output_guardrail, SQLiteSession,
    GuardrailFunctionOutput
)
from email_service import route_lead_email, force_lead_email
from database import save_lead_to_database
from utils import log_system_message, extract_lead_details
from config import OPENAI_API_KEY


# Guardrail functions for input validation
@input_guardrail
def validate_lead_input(ctx: RunContextWrapper, agent: Agent, input_data) -> GuardrailFunctionOutput:
    """Validate that the input contains meaningful lead information."""
    input_text = str(input_data) if input_data else ""
    
    # Only block truly problematic content
    # Check for completely empty input
    if not input_text.strip():
        return GuardrailFunctionOutput(
            output_info="Empty input provided",
            tripwire_triggered=True
        )
    
    # Only block obvious spam patterns (not individual words)
    obvious_spam_patterns = [
        "asdfasdf", "qwertyqwerty", "testtesttest", 
        "spamspamspam", "fakefakefake", "nonsensenonsense"
    ]
    
    input_lower = input_text.lower()
    for pattern in obvious_spam_patterns:
        if pattern in input_lower:
            return GuardrailFunctionOutput(
                output_info="Input appears to be spam content",
                tripwire_triggered=True
            )
    
    # Allow all other input - let the agent handle it
    return GuardrailFunctionOutput(
        output_info="Input validation passed",
        tripwire_triggered=False
    )

@output_guardrail
def validate_response_quality(ctx: RunContextWrapper, agent: Agent, response: str) -> GuardrailFunctionOutput:
    """Ensure responses are professional and helpful."""
    # Check for appropriate tone
    inappropriate_words = ["damn", "hell", "crap", "stupid", "idiot"]
    if any(word in response.lower() for word in inappropriate_words):
        return GuardrailFunctionOutput(
            output_info="Response contains inappropriate language",
            tripwire_triggered=True
        )
    
    # Only block completely empty responses
    if not response.strip():
        return GuardrailFunctionOutput(
            output_info="Empty response generated",
            tripwire_triggered=True
        )
    
    # Allow short responses - the agent should be able to generate appropriate responses
    # of any length for lead qualification
    return GuardrailFunctionOutput(
        output_info="Response quality validation passed",
        tripwire_triggered=False
    )


# Enhanced model settings
def get_model_settings() -> ModelSettings:
    """Get optimized model settings for lead qualification."""
    return ModelSettings(
        temperature=0.7,  # Balanced creativity and consistency
        max_tokens=1000,  # Sufficient for detailed responses
        top_p=0.9,        # Good balance for diverse responses
        frequency_penalty=0.1,  # Slight penalty to avoid repetition
        presence_penalty=0.1    # Encourage new topics
    )


# Session management
def get_session() -> SQLiteSession:
    """Get or create a database session for conversation persistence."""
    return SQLiteSession("conversations.db")


# Agent tool functions
@function_tool
def send_email(to_email: str, subject: str, body: str, cc: str = None) -> str:
    """Send email tool for agents with enhanced error handling."""
    try:
        from email_service import send_email_message
        result = send_email_message(to_email, subject, body, cc)
        log_system_message(f"EMAIL SENT: {to_email} - {subject}")
        return f"Email sent successfully to {to_email}: {result}"
    except Exception as e:
        error_msg = f"Failed to send email to {to_email}: {str(e)}"
        log_system_message(f"EMAIL ERROR: {error_msg}")
        return error_msg


@function_tool
def route_lead_to_email(lead_type: str, lead_name: str, company: str = None, email: str = None, phone: str = None, details: str = None, priority: str = "normal") -> str:
    """Route lead to appropriate email tool for agents with validation."""
    try:
        # Validate required fields
        if not lead_name or not lead_type:
            return "Error: Lead name and type are required for routing."
        
        if lead_type not in ["enterprise", "smb", "individual"]:
            return f"Error: Invalid lead type '{lead_type}'. Must be enterprise, smb, or individual."
        
        result = route_lead_email(lead_type, lead_name, company=company, email=email, phone=phone, details=details, priority=priority)
        log_system_message(f"LEAD ROUTED: {lead_type} - {lead_name}")
        return f"Lead routed successfully: {result}"
    except Exception as e:
        error_msg = f"Failed to route {lead_type} lead '{lead_name}': {str(e)}"
        log_system_message(f"ROUTING ERROR: {error_msg}")
        return error_msg


@function_tool
def store_lead_in_database(lead_type: str, lead_name: str, company: str = None, email: str = None, phone: str = None, details: str = None, priority: str = "normal") -> str:
    """Store lead in database tool for agents with validation."""
    try:
        # Validate required fields
        if not lead_name or not lead_type:
            return "Error: Lead name and type are required for storage."
        
        if lead_type not in ["enterprise", "smb", "individual"]:
            return f"Error: Invalid lead type '{lead_type}'. Must be enterprise, smb, or individual."
        
        result = save_lead_to_database(lead_type, lead_name, company, email, phone, details, priority)
        log_system_message(f"LEAD STORED: {lead_type} - {lead_name}")
        return f"Lead stored successfully: {result}"
    except Exception as e:
        error_msg = f"Failed to store {lead_type} lead '{lead_name}': {str(e)}"
        log_system_message(f"STORAGE ERROR: {error_msg}")
        return error_msg


def create_handoff_callback(lead_type):
    """Create a handoff callback function for a specific lead type."""
    def on_handoff(ctx: RunContextWrapper):
        log_system_message(f"HANDOFF: {lead_type.title()} lead detected")
        try:
            # Extract conversation history from Streamlit session state
            conversation = ""
            if 'conversation_history' in st.session_state:
                conversation = st.session_state['conversation_history']
            
            # Also try to get messages from session state if available
            if 'messages' in st.session_state and st.session_state['messages']:
                message_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in st.session_state['messages']
                ])
                if conversation:
                    conversation = f"{conversation}\n{message_text}"
                else:
                    conversation = message_text
            
            # Extract lead details and force email
            lead_details = extract_lead_details(conversation)
            log_system_message(f"HANDOFF: Extracted {lead_type} lead details: {lead_details}")
            
            # Schedule email sending
            asyncio.create_task(force_lead_email(lead_type, lead_details["name"], lead_details))
            
        except Exception as e:
            log_system_message(f"HANDOFF ERROR: Failed to process {lead_type} handoff: {str(e)}")
    
    return on_handoff


def create_agent_system():
    """Create and configure all agents."""
    
    # Specialized agent instructions
    agent_instructions = {
        "enterprise": """
        You are an enterprise sales specialist handling high-value enterprise leads.
        
        Focus on:
        - Professional, consultative tone
        - Business challenges and strategic needs
        - Company size, industry, current systems, pain points
        - Budget range, decision timeline, stakeholders
        - ROI, scalability, enterprise-grade features
        - Next steps: demos, technical consultations
        
        Enterprise clients value expertise, reliability, and strategic partnership.
        """,
        
        "smb": """
        You are an SMB sales specialist helping growing businesses find solutions.
        
        Focus on:
        - Friendly, helpful, solutions-oriented approach
        - Immediate needs and growth plans
        - Business size, type, current stage, challenges
        - Budget constraints, timeline, growth projections
        - Value, quick implementation, ROI for small businesses
        - Appropriate packages fitting their budget
        
        SMB clients need cost-effective, easy-to-implement, scalable solutions.
        """,
        
        "individual": """
        You are a customer success specialist for individual users.
        
        Focus on:
        - Conversational, friendly, approachable tone
        - Personal use cases and goals
        - Experience level, budget expectations
        - Features that matter most to them
        - Ease of use, personal value, affordability
        - Personal or freemium plans
        
        Individual clients value simplicity, affordability, and personal relevance.
        """
    }
    
    # Create specialized agents with enhanced settings
    agents = {}
    for agent_type, instruction in agent_instructions.items():
        agents[agent_type] = Agent(
            name=f"{agent_type.title()}LeadAgent",
            instructions=instruction,
            model_settings=get_model_settings(),
            input_guardrails=[validate_lead_input],
            output_guardrails=[validate_response_quality],
            tools=[route_lead_to_email, store_lead_in_database, send_email]
        )
    
    # Create lead qualifier with handoffs and enhanced settings
    lead_qualifier = Agent(
        name="LeadQualifier",
        instructions="""
        You are a lead qualification assistant. Your job is to:
        
        1. Greet leads professionally and collect basic information
        2. Analyze responses to determine lead type:
           - Enterprise: 1000+ employees, $500k+ budget, enterprise needs
           - SMB: <1000 employees, limited budget, growing business needs
           - Individual: Personal use, single users, non-business applications
        
        3. Hand off to appropriate specialist agent
        
        Always collect: contact name/role, company (if applicable), email/phone, basic requirements
        
        IMPORTANT: For EVERY lead, use these tools:
        - route_lead_to_email: Notify appropriate sales team
        - store_lead_in_database: Save lead information
        
        Ask clarifying questions if lead type is unclear.
        """,
        handoffs=[
            handoff(agents["enterprise"], on_handoff=create_handoff_callback("enterprise")),
            handoff(agents["smb"], on_handoff=create_handoff_callback("smb")),
            handoff(agents["individual"], on_handoff=create_handoff_callback("individual"))
        ],
        tools=[route_lead_to_email, store_lead_in_database, send_email],
        model_settings=get_model_settings(),
        input_guardrails=[validate_lead_input],
        output_guardrails=[validate_response_quality]
    )
    
    return lead_qualifier


# Process user input message
async def process_user_message(user_input):
    """Process user message through the agent system."""
    # Initialize conversation history
    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = ""
    
    # Update conversation history
    if st.session_state['conversation_history']:
        st.session_state['conversation_history'] += f"\nUser: {user_input}"
    else:
        st.session_state['conversation_history'] = user_input
    
    log_system_message(f"PROCESSING: New message: {user_input[:50]}...")
    
    try:
        # Create lead qualifier if needed
        if 'lead_qualifier' not in st.session_state:
            log_system_message("PROCESSING: Creating lead qualifier agent")
            st.session_state['lead_qualifier'] = create_agent_system()
        
        # Process through agent system with session management
        log_system_message("PROCESSING: Running through lead qualifier")
        with st.spinner('Processing your message...'):
            session = get_session()
            result = await Runner.run(
                st.session_state['lead_qualifier'], 
                user_input,
                context=session
            )
        
        # Get and store response
        response = result.final_output
        log_system_message(f"PROCESSING: Generated response: {response[:50]}...")
        
        # Update conversation and message history
        st.session_state['conversation_history'] += f"\nAssistant: {response}"
        st.session_state['messages'].append({"role": "user", "content": user_input})
        st.session_state['messages'].append({"role": "assistant", "content": response})
        
        return response
        
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        log_system_message(f"PROCESSING ERROR: {error_msg}")
        return "I apologize, but there was an error processing your message. Please try again."


