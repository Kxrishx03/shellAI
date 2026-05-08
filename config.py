import os

OLLAMA_BASE_URL = "http://localhost:11434"

SIMILARITY_THRESHOLD = 0.35

MAX_COMMANDS = 10

SHELLAI_DIR   = os.path.join(os.path.expanduser("~"), ".shellai")
PROFILE_PATH  = os.path.join(SHELLAI_DIR, "profile.json")
PENDING_PATH  = os.path.join(SHELLAI_DIR, "pending.json")


COMMANDS_PATH = os.path.join(os.path.dirname(__file__), "data", "commands.json")