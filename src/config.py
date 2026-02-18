import os
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file from the root directory
load_dotenv()

# --- PROJECT ROOT ---
# This calculates the absolute path to your project folder
# so that it works on any computer without modification.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY & DATABASE ---
DB_URI = os.getenv("DB_URI")

# --- EXECUTION CONFIGURATION ---
PYTHON_EXE = os.getenv("CAD_PYTHON_EXE")

# --- DIRECTORY STRUCTURE ---
# We use Path objects for better cross-platform (Windows/Linux) support
TEMP_DIR = BASE_DIR / "temp"
DOCS_DIR = BASE_DIR / "docs"
OUTPUT_FOLDER = DOCS_DIR / "visual_qa"
TEMPLATES_DIR = DOCS_DIR / "templates"

# Specific File Outputs
STL_OUTPUT = OUTPUT_FOLDER / "latest_model.stl"
PYTHONOCC_TEMPLATE = TEMPLATES_DIR / "pythonocc_template.md"

# --- ENSURE DIRECTORIES EXIST ---
# Automatically creates the folders if they don't exist yet
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)