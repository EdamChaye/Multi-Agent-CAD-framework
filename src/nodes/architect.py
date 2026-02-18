from langchain_groq import ChatGroq
from src.state import CADState
from src.utils.logger import get_logger

from src.prompts import ARCHITECT_SYSTEM_MSG

from dotenv import load_dotenv
load_dotenv()
log = get_logger("architect")

#Define the llm to work with
llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.3, 
    reasoning_effort="none"
)

def architect_node(state: CADState):
    """Handles conversational requirement gathering."""
    log.info("Architect node triggered.")
    
    messages = state.get("messages", [])
    # Get current history of requirements if they exist
    current_active = state.get("active_requirements", "No requirements defined yet.")

    full_prompt = [("system", ARCHITECT_SYSTEM_MSG)]
    
    for msg in messages:
        # Convert stored messages back into a format the LLM understands
        role = "user" if (hasattr(msg, 'type') and msg.type in ['human', 'user']) or (isinstance(msg, tuple) and msg[0] in ['human', 'user']) else "assistant"
        content = msg.content if hasattr(msg, 'content') else (msg[1] if isinstance(msg, tuple) else str(msg))
        full_prompt.append((role, content))

    # 3. EXECUTION
    response = llm.invoke(full_prompt)
    new_specs = response.content

    # Only update specs if the AI actually output requirements
    updated_active = new_specs if "***USER TECHNICAL REQUIREMENTS***" in new_specs else current_active

    return {
        "specs": new_specs,
        "active_requirements": updated_active,
        "messages": [("assistant", new_specs)]
    }
    
   