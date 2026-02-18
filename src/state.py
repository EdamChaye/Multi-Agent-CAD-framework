from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages

class CADState(TypedDict):
    messages: Annotated[list, add_messages]
    specs: str
    active_requirements: str 
    current_code: str
    retry_count: int
    last_error: Optional[str]
    human_review: Optional[str] 
    metadata: dict