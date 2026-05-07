import os

def load_env_file():
   
    locations = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.expanduser("~"), ".shellai")
    ]

    for path in locations:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    # Split on the first = sign
                    if "=" in line:
                        key, value = line.split("=", 1)
                        # Only set it if not already in environment
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip()
            return True

    return False


load_env_file()

def get_api_key():
    """Returns the Gemini API key, or None if not set."""
    return os.environ.get("GEMINI_API_KEY")

def get_model():
    """Returns which Gemini model to use. Can be overridden in .env"""
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def get_max_commands():
    """Max number of commands AI can suggest in one response."""
    return int(os.environ.get("SHELLAI_MAX_COMMANDS", "10"))