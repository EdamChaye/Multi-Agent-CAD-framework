import os
from langchain_groq import ChatGroq
from src.state import CADState
from src.utils.logger import get_logger

from src.config import PYTHONOCC_TEMPLATE
from src.prompts import CODER_SYSTEM_MSG

from dotenv import load_dotenv
load_dotenv()

log = get_logger("coder")

#Define the llm to work with
llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0.3,
    reasoning_effort="none"
)

def coder_node(state: CADState):
    """Generates PythonOCC code from specs."""
    log.info("Coder node triggered: Consolidating all feedback sources.")
    
   
    active_reqs = state.get("active_requirements", "")
    last_error = state.get("last_error", "")
    
    # We also pass the previous code if we are fixing an error
    current_code = state.get("current_code", "")
    
    # Adding the template to context in order to avoid hardcoding structural hints in the system prompt. This allows for easier updates to the template without changing code.
    template_path = str(PYTHONOCC_TEMPLATE)
    template_content = ""
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            template_content = f.read()

    system_msg = CODER_SYSTEM_MSG.format(template_content=template_content)
 
    # Construct the prompt based on whether we are starting fresh or repairing
    prompt = f"ACTIVE REQUIREMENTS:\n{active_reqs}\n\n"
    
    if last_error:
        prompt += f"--- CRITICAL: FIX THIS ERROR ---\n{last_error}\n\n"
        prompt += f"--- PREVIOUS CODE FOR REFERENCE ---\n{current_code}"

    messages = [
        ("system", system_msg),
        ("user", prompt)
    ]

    response = llm.invoke(messages)
    
    # Robust code extraction logic
    content = response.content
    if "```python" in content:
        code = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        code = content.split("```")[1].split("```")[0].strip()
    else:
        code = content.strip()
    
    return {
        "current_code": code,
        "last_error": None, # Clear error after attempt
        "human_review": None # Clear feedback after consumption
    }

 