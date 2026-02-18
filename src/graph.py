import sys
from pathlib import Path

# Add parent directory to path so imports work when running this script directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from src.state import CADState
from src.nodes.architect import architect_node
from src.nodes.coder import coder_node
from src.nodes.executor import executor_node
from src.nodes.inspector import inspector_node
from src.utils.throttler import quota_cooldown
from src.utils.logger import get_logger

log = get_logger("graph")

# --- ROUTING LOGIC ---

def route_after_architect(state: CADState):
    messages = state.get("messages", [])
    last_user_msg = ""
    for msg in reversed(messages):
        # Handle both object and tuple formats
        content = msg.content.lower() if hasattr(msg, 'content') else (msg[1].lower() if isinstance(msg, tuple) else "")
        role = msg.type if hasattr(msg, 'type') else (msg[0] if isinstance(msg, tuple) else "")
        if role in ["user", "human"]:
            last_user_msg = content
            break
            
    if "confirm" in last_user_msg:
        return "coder"
    return "human_gate"

def route_after_executor(state: CADState):
    error = state.get("last_error")
    retries = state.get("metadata", {}).get("retry_count", 0)
    if error and retries < 7: #change this number based on how many times you want to allow the system to retry.
        log.error(f"Technical Error: {error}. Routing to Coder (Retry {retries+1}/7)")
        return "coder"
    return "human_gate"

def route_after_inspector(state: CADState):
    metadata = state.get("metadata", {})
    critique = metadata.get("inspector_critique", "")
    if "**MATCH**" in critique:
        return "human_gate"
    return "repair_bucket"

def review_router(state: CADState):
    # This reads the input provided by the UI
    user_input = (state.get("human_review") or "").lower()
    if user_input == "exit": return END
    if "inspector" in user_input: return "inspector"
    if "feedback" in user_input: return "update_bucket"
    if "refine" in user_input: return "architect"
    if "confirm" in user_input: return "coder"
    return "architect"

# --- NODES ---

def human_gate_node(state: CADState):
    if "metadata" not in state: state["metadata"] = {}
    state["metadata"]["retry_count"] = 0
    
    # The interrupt tells the graph to SAVE and STOP here.
    # Streamlit will resume this by passing the user's next message.
    decision = interrupt("WAITING_FOR_USER")
    return {"human_review": decision, "messages": [("user", decision)]}

def update_bucket_node(state: CADState):
    user_input = (state.get("human_review") or "").lower()
    clean_feedback = user_input.replace("feedback", "").strip(": ").strip()
    current_reqs = state.get("active_requirements", "")
    return {"active_requirements": f"{current_reqs}\n- UPDATE: {clean_feedback}"}

def repair_bucket_node(state: CADState):
    metadata = state.get("metadata", {})
    critique = metadata.get("inspector_critique", "")
    current_reqs = state.get("active_requirements", "")
    return {"active_requirements": f"{current_reqs}\n- FIX: {critique}"}

async def throttle_node(state: CADState):
    await quota_cooldown()
    return state

# --- GRAPH CONSTRUCTION ---

def create_cad_graph(checkpointer=None):
    workflow = StateGraph(CADState)

    workflow.add_node("architect", architect_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("inspector", inspector_node)
    workflow.add_node("human_gate", human_gate_node)
    workflow.add_node("update_bucket", update_bucket_node)
    workflow.add_node("repair_bucket", repair_bucket_node)
    workflow.add_node("throttle", throttle_node)

    workflow.add_edge(START, "architect")
    
    workflow.add_conditional_edges("architect", route_after_architect, {"coder": "coder", "human_gate": "human_gate"})
    workflow.add_edge("coder", "executor")
    workflow.add_conditional_edges("executor", route_after_executor, {"coder": "coder", "human_gate": "human_gate"})
    workflow.add_conditional_edges("human_gate", review_router, {"inspector": "inspector", "update_bucket": "update_bucket", "architect": "architect", "coder": "coder", END: END})
    workflow.add_edge("update_bucket", "coder")
    workflow.add_conditional_edges("inspector", route_after_inspector, {"human_gate": "human_gate", "repair_bucket": "repair_bucket"})
    workflow.add_edge("repair_bucket", "throttle")
    workflow.add_edge("throttle", "coder")

    return workflow.compile(checkpointer=checkpointer)
if __name__ == "__main__":
    import os
    graph = create_cad_graph()
    #visualize graph
    image_data = graph.get_graph().draw_mermaid_png()
    image_path = "graph_visualization.png"
    with open(image_path, "wb") as f:
        f.write(image_data)
    print(f"Graph visualization saved to: {image_path}")
    os.startfile(image_path)  # Opens the image with default viewer on Windows