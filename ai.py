import requests
import json
import config
import time

SYSTEM_PROMPT = """
You are an expert shell command assistant.
The user will describe a task in plain English.
You must respond with ONLY a valid JSON object — no markdown, no explanation, no backticks.

The JSON must have this exact structure:
{
  "commands": [
    {
      "command": "the exact shell command to run",
      "explanation": "one short sentence explaining what this command does"
    }
  ],
  "summary": "one sentence describing what these commands will accomplish overall"
}

Rules:
- commands must be real, runnable shell commands
- each command should do one thing
- explanations must be short and plain English
- if the task is dangerous (rm -rf, format, delete), add a "warning" field to that command
- do not include commands that require sudo unless absolutely necessary
- assume the user is on Ubuntu Linux
"""


def get_commands(user_intent: str) -> dict:
    api_key = config.get_api_key()
    model   = config.get_model()

    if not api_key:
        raise ValueError(
            "No API key found. Add GEMINI_API_KEY=your_key to your .env file.\n"
            "Get a free key at: https://aistudio.google.com"
        )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT + "\n\nUser task: " + user_intent
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024
        }
    }

    # Retry up to 3 times on rate limit errors
    max_retries = 3
    wait_seconds = 10

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=20
            )
        except requests.exceptions.Timeout:
            raise ConnectionError("Request timed out. Check your internet connection.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Could not connect to Gemini. Check your internet.")

        # Success
        if response.status_code == 200:
            break

        # Rate limited — wait and retry
        if response.status_code == 429:
            if attempt < max_retries:
                print(f"\n  Rate limited. Waiting {wait_seconds}s before retry {attempt}/{max_retries - 1}...")
                time.sleep(wait_seconds)
                wait_seconds *= 2  # wait longer each time: 10s, 20s, 40s
                continue
            else:
                raise RuntimeError(
                    "Rate limit hit. You've exceeded Gemini's free tier quota.\n"
                    "Options:\n"
                    "  1. Wait a minute and try again\n"
                    "  2. Wait until tomorrow if you've hit the daily limit\n"
                    "  3. Check your quota at: https://ai.google.dev/gemini-api/docs/rate-limits"
                )

        # Any other error
        raise RuntimeError(
            f"Gemini API error {response.status_code}: {response.text[:200]}"
        )

    # Parse the response
    data     = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        lines    = raw_text.split("\n")
        raw_text = "\n".join(lines[1:-1])

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON: {e}\n"
            f"Raw response was:\n{raw_text[:300]}"
        )

    if "commands" not in result:
        raise ValueError("Gemini response missing 'commands' field")

    max_cmds = config.get_max_commands()
    result["commands"] = result["commands"][:max_cmds]

    return result