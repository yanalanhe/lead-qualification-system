"""
Agent system for the Lead Qualification System.
"""
import asyncio
import streamlit as st
from agents import Agent, Runner, function_tool, handoff, RunContextWrapper
from email_service import route_lead_email, force_lead_email
from database import save_lead_to_database
from utils import log_system_message, extract_lead_details


# Agent tool functions
@function_tool
def send_email(to_email: str, subject: str, body: str, cc: str = None) -> str:
    """Send email tool for agents."""
    from email_service import send_email_message
    return send_email_message(to_email, subject, body, cc)


@function_tool
def route_lead_to_email(lead_type: str, lead_name: str, company: str = None, email: str = None, phone: str = None, details: str = None, priority: str = "normal") -> str:
    """Route lead to appropriate email tool for agents."""
    return route_lead_email(lead_type, lead_name, company=company, email=email, phone=phone, details=details, priority=priority)


@function_tool
def store_lead_in_database(lead_type: str, lead_name: str, company: str = None, email: str = None, phone: str = None, details: str = None, priority: str = "normal") -> str:
    """Store lead in database tool for agents."""
    return save_lead_to_database(lead_type, lead_name, company, email, phone, details, priority)


def create_handoff_callback(lead_type):
    """Create a handoff callback function for a specific lead type."""
    def on_handoff(ctx: RunContextWrapper):
        log_system_message(f"HANDOFF: {lead_type.title()} lead detected")
        try:
            # Extract conversation history
            conversation = ""
            if hasattr(ctx, 'conversation_history'):
                conversation = ctx.conversation_history
            elif hasattr(ctx, 'messages'):
                conversation = "\n".join(msg.content for msg in ctx.messages if hasattr(msg, 'content'))
            
            # Add session conversation history if available
            if 'conversation_history' in st.session_state:
                conversation = f"{conversation}\n{st.session_state['conversation_history']}" if conversation else st.session_state['conversation_history']
            
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
    
    # Create specialized agents
    agents = {}
    for agent_type, instruction in agent_instructions.items():
        agents[agent_type] = Agent(
            name=f"{agent_type.title()}LeadAgent",
            instructions=instruction
        )
    
    # Create lead qualifier with handoffs
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
        tools=[route_lead_to_email, store_lead_in_database, send_email]
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
        
        # Process through agent system
        log_system_message("PROCESSING: Running through lead qualifier")
        with st.spinner('Processing your message...'):
            result = await Runner.run(st.session_state['lead_qualifier'], user_input)
        
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


