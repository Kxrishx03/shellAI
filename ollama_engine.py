import requests
import json
import threading
import itertools
import time
import sys
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
      "explanation": "one short sentence explaining what this does"
    }
  ],
  "summary": "one sentence describing what these commands accomplish overall"
}

IMPORTANT rules:
- When a command needs a value personal to the user (name, email, project name,
  database name, branch name, port, password, server address etc) use a placeholder
  written in ALLCAPS inside double curly braces like {{YOUR_NAME}} or {{PROJECT_NAME}}
- Never invent fake values — always use placeholders for personal information
- If a command could cause data loss or is irreversible, add a "warning" field to that command
- Generate commands appropriate for the system info provided
- If git is already initialized (shown in environment context), never include git init

Example of a correct response:
{
  "commands": [
    {"command": "git init", "explanation": "Creates a new empty git repository"},
    {"command": "git add .", "explanation": "Stages all files"},
    {"command": "git commit -m \\"{{COMMIT_MESSAGE}}\\"", "explanation": "Makes the first commit"}
  ],
  "summary": "Initialize a new git repository and make the first commit"
}"""


def is_ollama_running() -> bool:
    """Check if Ollama server is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def get_available_models() -> list:
    """Return list of downloaded model names."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def clean_json_response(raw: str) -> str:
    """
    Strip markdown fences and extract just the JSON object.
    Local models sometimes wrap JSON in code blocks even when
    told not to. This handles all those cases.
    """
    raw = raw.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]).strip()

    start = raw.find("{")
    end = raw.rfind("}")

    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    return raw


def _spinner(label: str, stop_event: threading.Event):
    """Animated spinner shown while waiting for first token."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for f in itertools.cycle(frames):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r  {f}  {label}...")
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write(f"\r{' ' * 40}\r")
    sys.stdout.flush()


def get_commands_ollama(
    user_intent: str,
    os_context: str = "Ubuntu Linux",
    model: str = "phi3:mini",
    extra_context: str = ""
) -> dict:
    """
    Send a task to Ollama and stream the response back.
    Raises ConnectionError, ValueError, or RuntimeError with
    clear messages the user can act on.
    """
    if not is_ollama_running():
        raise ConnectionError(
            "Ollama is not running.\n"
            "  Start it with:  ollama serve &"
        )

    available = get_available_models()
    if available and model not in available:
        suggestion = available[0] if available else "phi3:mini"
        raise ValueError(
            f"Model '{model}' is not downloaded.\n"
            f"  Pull it with:  ollama pull {model}\n"
            f"  Or switch:     shellai --set-model {suggestion}"
        )

    full_prompt = SYSTEM_PROMPT
    if extra_context:
        full_prompt += f"\n\nCurrent environment:\n{extra_context}"
    full_prompt += f"\n\nSystem info: {os_context}"
    full_prompt += f"\n\nUser task: {user_intent}"

    request_body = {
        "model":   model,
        "prompt":  full_prompt,
        "stream":  True,
        "options": {
            "temperature": 0.1,
            "num_predict": 512
        }
    }

    # Start spinner while connection is being established
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(
        target=_spinner,
        args=("Thinking", stop_spinner),
        daemon=True
    )
    spinner_thread.start()

    full_response = ""
    first_token = True

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=request_body,
            stream=True,
            timeout=90
        )

        for line in response.iter_lines():
            if not line:
                continue

            chunk = json.loads(line)
            token = chunk.get("response", "")

            if token:
                if first_token:
                    # Stop spinner on first token so output is clean
                    stop_spinner.set()
                    spinner_thread.join()
                    first_token = False

                print(token, end="", flush=True)
                full_response += token

            if chunk.get("done", False):
                break

    except requests.exceptions.Timeout:
        stop_spinner.set()
        raise ConnectionError("Ollama timed out. The model may still be loading — try again.")
    except requests.exceptions.ConnectionError:
        stop_spinner.set()
        raise ConnectionError("Lost connection to Ollama.\n  Check it is running: ollama serve &")
    except Exception as e:
        stop_spinner.set()
        raise RuntimeError(f"Unexpected error: {e}")
    finally:
        stop_spinner.set()
        spinner_thread.join()

    print("\n")

    raw = clean_json_response(full_response)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model returned malformed JSON.\n"
            f"  Try a larger model: shellai --set-model mistral:7b\n"
            f"  Raw output: {raw[:150]}"
        )

    if "commands" not in result:
        raise ValueError(
            "Model did not return commands.\n"
            "  Try rephrasing your request or use: shellai --set-model mistral:7b"
        )

    result["commands"] = result["commands"][:MAX_COMMANDS]
    result["source"] = f"ollama:{model}"
    return result