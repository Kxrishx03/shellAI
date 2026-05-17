import os

# Where all user data lives
SHELLAI_DIR = os.path.join(os.path.expanduser("~"), ".shellai")

# SQLite database path
DB_PATH = os.path.join(SHELLAI_DIR, "commands.db")

# Pending entries path (now in SQLite, this is just for reference)
PENDING_PATH = os.path.join(SHELLAI_DIR, "pending.json")

# Where the seed SQL file lives (committed to GitHub)
SEED_PATH = os.path.join(os.path.dirname(__file__), "data", "seed.sql")

# Where commands.json lives (used as fallback seed source)
COMMANDS_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "commands.json")

# Ollama server address — never changes unless manually configured
OLLAMA_BASE_URL = "http://localhost:11434"

# Maximum commands returned in one response
MAX_COMMANDS = 10

# Minimum keyword match score to count as a hit (0.0 to 1.0)
SIMILARITY_THRESHOLD = 0.35

# Profile file path
PROFILE_PATH = os.path.join(SHELLAI_DIR, "profile.json")