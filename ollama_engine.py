import requests
import json
from colorama import Fore, Style, init
from config import OLLAMA_BASE_URL, MAX_COMMANDS

init(autoreset=True)


SYSTEM_PROMPT = """You are an expert shell command assistant embedded in a terminal.
The user will describe a developer task in plain English.
Respond with ONLY a valid JSON object. No markdown. No backticks. No explanation outside the JSON.

The JSON must have exactly this structure:
{
  "commands": [
    {
      "command": "the exact shell command to run",
      "explanation": "one short sentence explaining what this command does"
    }
  ],
  "summary": "one sentence describing what these commands accomplish overall"
}

IMPORTANT — placeholders:
When a command needs a value personal to the user (name, email, project name,
database name, branch name, port, password, server address etc) use a placeholder
written in ALLCAPS inside double curly braces.

Correct placeholder examples:
  git config --global user.name "{{YOUR_NAME}}"
  createdb {{DATABASE_NAME}}
  git checkout -b {{BRANCH_NAME}}
  docker build -t {{IMAGE_NAME}} .

Never invent fake values like "myproject" or "johndoe". Always use placeholders.
If a command could cause data loss or is irreversible, add a "warning" field.

Example of a complete correct response:
{
  "commands": [
    {"command": "git init", "explanation": "Creates a new empty git repository"},
    {"command": "git add .", "explanation": "Stages all files"},
    {"command": "git commit -m \\"{{COMMIT_MESSAGE}}\\"", "explanation": "Makes the first commit"}
  ],
  "summary": "Initialize a new git repository and make the first commit"
}"""


def is_ollama_running() -> bool:
    """
    Check if the Ollama server is running.
    We do this before making any model requests so we can give
    a clear error message instead of a cryptic connection error.
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def get_available_models() -> list:
    """
    Ask Ollama which models are downloaded and ready to use.
    Returns a list of model name strings like ["phi3:mini", "mistral:7b"]
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return [m["name"] for m in models]
    except Exception:
        pass
    return []


def clean_json_response(raw: str) -> str:
    """
    Extract clean JSON from a model response that may contain
    extra text, markdown fences, or other noise.

    Strategy:
    1. Strip whitespace
    2. Remove markdown code fences if present (```json ... ```)
    3. Find the first { and last } to extract just the JSON object
       This handles cases where the model adds text before or after
    """
    raw = raw.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (```json or ```) and last line (```)
        raw = "\n".join(lines[1:-1]).strip()

    
    start = raw.find("{")
    end   = raw.rfind("}")

    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]

    return raw


def get_commands_ollama(
    user_intent: str,
    os_context:  str = "Ubuntu Linux",
    model:       str = "phi3:mini"
) -> dict:
    """
    Send a task description to the local Ollama model and return
    structured commands.

    Returns a dict with 'commands', 'summary', and 'source' fields.
    The 'source' field tells the caller where the answer came from.
    Raises exceptions with helpful messages if anything goes wrong.
    """

    if not is_ollama_running():
        raise ConnectionError(
            "Ollama is not running.\n"
            "Start it with:  ollama serve\n"
            "Or in the background:  ollama serve &"
        )

    available = get_available_models()
    if available and model not in available:
        # Model not found — suggest the first available one
        suggestion = available[0] if available else "phi3:mini"
        raise ValueError(
            f"Model '{model}' is not downloaded.\n"
            f"Pull it with:  ollama pull {model}\n"
            f"Or switch to an available model:  shellai --set-model {suggestion}"
        )

   
    full_prompt = (
        SYSTEM_PROMPT
        + f"\n\nSystem info: {os_context}"
        + f"\n\nUser task: {user_intent}"
    )

    request_body = {
        "model":  model,
        "prompt": full_prompt,
        "stream": False,      
        "options": {
            "temperature": 0.1, # low = predictable, which we want for commands
            "num_predict": 512  # max tokens in response
        }
    }

    print(
        f"\n{Fore.CYAN}⚡ Asking {model}...{Style.RESET_ALL}",
        end="",
        flush=True
    )

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=request_body,
            timeout=90  
        )
    except requests.exceptions.Timeout:
        raise ConnectionError(
            "Ollama timed out. The model may still be loading.\n"
            "Wait a few seconds and try again."
        )
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Lost connection to Ollama.\n"
            "Make sure it is still running:  ollama serve"
        )

    print(f"\r{' ' * 50}\r", end="")

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned error {response.status_code}:\n{response.text[:200]}"
        )

    raw_text = response.json().get("response", "")
    raw_text = clean_json_response(raw_text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model returned invalid JSON: {e}\n"
            f"Raw response:\n{raw_text[:300]}\n\n"
            f"Tip: larger models follow JSON format more reliably.\n"
            f"Try:  shellai --set-model mistral:7b"
        )

    # Validate the structure we expect
    if "commands" not in result:
        raise ValueError(
            "Model response is missing the 'commands' field.\n"
            "The model may not have followed the format.\n"
            "Try rephrasing your request or switching to a larger model."
        )

    result["commands"] = result["commands"][:MAX_COMMANDS]
    result["source"]   = f"ollama:{model}"

    return result