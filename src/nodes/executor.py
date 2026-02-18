import subprocess
import os
import sys
from src.state import CADState
from src.utils.logger import get_logger
from src.config import PYTHON_EXE, TEMP_DIR, OUTPUT_FOLDER, STL_OUTPUT 

log = get_logger("executor")

RUNNER_PY = os.path.join(TEMP_DIR, "runner.py")
PHOTO_PY = os.path.join(TEMP_DIR, "photographer.py")

def executor_node(state: CADState):
    log.info("Executor node: Starting Render & Export...")
    metadata = state.get("metadata", {})
    if "retry_count" not in metadata:
        metadata["retry_count"] = 0

    code = state.get("current_code")
    if not code:
        log.error("No code found in state!")
        return {"last_error": "No code to execute."}

    # --- DYNAMIC ABSOLUTE PATHS ---
    # We resolve these here to ensure the subprocess has the full D:/... path
    abs_stl_path = os.path.abspath(str(STL_OUTPUT)).replace("\\", "/")
    abs_output_folder = os.path.abspath(str(OUTPUT_FOLDER)).replace("\\", "/")
    abs_temp_dir = os.path.abspath(str(TEMP_DIR))

    # Ensure directories exist
    os.makedirs(abs_temp_dir, exist_ok=True)
    os.makedirs(abs_output_folder, exist_ok=True)
    
    # 1. Write the runner script
    with open(RUNNER_PY, "w") as f:
        f.write(code)

    # 2. Write the photographer script (NO DELETIONS, JUST STL ADDED)
    photographer_code = f"""
import os
import time
import sys
from OCC.Display.SimpleGui import init_display
from OCC.Core.Quantity import (Quantity_Color, Quantity_NOC_GOLDENROD, Quantity_NOC_BROWN,
                               Quantity_NOC_GRAY20, Quantity_TOC_RGB)
import runner

def capture_empire_views(shape, output_dir):
    try:
        display, start_display, add_menu, add_function_to_menu = init_display(backend_str="tk")
        white = Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB)
        display.View.SetBackgroundColor(white)
        display.View.SetBgGradientColors(white, white, 0, False)
        display.DisplayShape(shape, update=True)
    
        
        views = [
            ("view_front.png", lambda: display.View.SetProj(0, -1, 0)),
            ("view_top.png",   lambda: display.View.SetProj(0, 0, 1)),
            ("view_right.png", lambda: display.View.SetProj(1, 0, 0)),
            ("view_iso.png",   lambda: display.View.SetProj(1, -1, 1))
        ]
        
        for filename, set_view_func in views:
            set_view_func()
            display.FitAll()
            display.View.Redraw()
            time.sleep(0.5)
            display.View.Dump(os.path.join(output_dir, filename))
        display.EraseAll()
    except Exception as e:
        print(f"SUBPROCESS_LOG: Render Error - {{e}}")

if __name__ == "__main__":
    if hasattr(runner, 'shape'):
        # --- ATOMIC EXPORT LOGIC (Indented 8 spaces to match the 'if') ---
        try:
            from OCC.Extend.DataExchange import write_stl_file
            write_stl_file(
                runner.shape,
                r"{abs_stl_path}",
                mode="binary",
                linear_deflection=0.1,
                angular_deflection=0.1
            )
            print("SUBPROCESS_LOG: STL Export Successful via write_stl_file")
        except Exception as e:
            print(f"SUBPROCESS_LOG: STL Export Failed - {{str(e)}}")
        
        # --- CAPTURE VIEWS ---
        capture_empire_views(runner.shape, r"{abs_output_folder}")
    else:
        print("SUBPROCESS_LOG: No shape found")
        sys.exit(1)
"""
    with open(PHOTO_PY, "w") as f:
        f.write(photographer_code)

    try:
        # Setup environment to find runner.py
        env = os.environ.copy()
        env["PYTHONPATH"] = str(TEMP_DIR)
        
        # Run subprocess and CAPTURE everything
        result = subprocess.run(
            [str(PYTHON_EXE), PHOTO_PY], 
            capture_output=True, 
            text=True, 
            timeout=40, 
            env=env
        )
        
        # Log exactly what the subprocess said to terminal
        if result.stdout:
            print(f"--- SUBPROCESS STDOUT ---\\n{result.stdout}")
        if result.stderr:
            print(f"--- SUBPROCESS STDERR ---\\n{result.stderr}")

        if result.returncode != 0:
            metadata["retry_count"] += 1
            return {"last_error": result.stderr or "Subprocess failed", "metadata": metadata}

    except Exception as e:
        log.error(f"Executor crashed: {e}")
        metadata["retry_count"] += 1
        return {"last_error": str(e), "metadata": metadata}

    log.info("Render successful.")
    metadata["retry_count"] = 0
    return {"last_error": None, "metadata": metadata}