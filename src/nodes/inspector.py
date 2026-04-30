import os
import base64
import time 


from langchain_groq import ChatGroq
from src.state import CADState
from src.utils.logger import get_logger

from src.config import OUTPUT_FOLDER
from src.prompts import INSPECTOR_SYSTEM_MSG

log = get_logger("inspector")

#Define the llm to work with, must be a multimodal model with vision capabilities
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct", 
    temperature=0.3
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def inspector_node(state: CADState):
    log.info("Inspector node: Analyzing orthogonal views...")
    time.sleep(2)  # Simulate processing time
    # The inspector agent looks at the Bucket, not the original specs
    requirements = state.get("active_requirements", "")
    specs_data = state.get('specs')
    
   # Use centralized config path
    image_folder = str(OUTPUT_FOLDER)
    view_names = ["view_front.png", "view_top.png", "view_right.png", "view_iso.png"]
    image_paths = [os.path.join(image_folder, name) for name in view_names]
    
    valid_images = [p for p in image_paths if os.path.exists(p)]
    if not valid_images:
        return {"last_error": "Inspector Error: Geometric views missing."}

    system_msg = INSPECTOR_SYSTEM_MSG.format(user_specs=specs_data)
    prompt = f"REQUIREMENTS TO VERIFY:\n{requirements}"

    # Prepare vision messages
    content = [{"type": "text", "text": prompt}]
      

    for path in valid_images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encode_image(path)}"}
        })

    response = llm.invoke([
        ("system", system_msg),
        ("user", content)
    ])
    critique = response.content
  
    is_match="**MATCH**" in critique
    
    # We store the critique in metadata
    return {
        "metadata": {
            "inspector_critique": critique,
            "is_visual_match": is_match
        }
    }