import os
from dotenv import load_dotenv

# Load relative to file, not CWD
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MAX_RETRIES = 5
    WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
    RESULTS_FILE = "results.json"

    # Ensure workspace exists
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
