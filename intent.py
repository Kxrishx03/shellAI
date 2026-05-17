import re
import random

INTENT_COMMAND  = "command"
INTENT_QUESTION = "question"
INTENT_GREETING = "greeting"
INTENT_HELP     = "help"

QUESTION_PATTERNS = [
    r"^what (are|is|do|does|can|should|will)\b",
    r"^who (are|is)\b",
    r"^why (is|are|do|does|did)\b",
    r"^how (do|does|did|can|should|would|is|are)\b",
    r"^where (is|are|do|does)\b",
    r"^when (is|are|do|does|did|will)\b",
    r"^can you (tell|explain|describe|help|show)\b",
    r"^do you (know|understand|support|have)\b",
    r"^tell me (about|what|how|why)\b",
    r"^explain\b",
    r"^describe\b",
    r"what do you do",
    r"what are you",
    r"who are you",
    r"what can you do",
    r"how do you work",
    r"are you an? (ai|bot|tool|assistant|program)",
]

GREETING_PATTERNS = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^thanks?\b",
    r"^thank you",
    r"^good (morning|afternoon|evening|night)",
    r"^howdy",
    r"^sup\b",
    r"^yo\b",
    r"^greetings",
]

HELP_PATTERNS = [
    r"^help\b",
    r"how (do i|to) use",
    r"what commands",
    r"show me (examples|how)",
    r"getting started",
    r"^usage\b",
    r"^tutorial\b",
]

COMMAND_SIGNALS = [
    r"^(create|make|build|set up|setup|install|run|start|stop|restart)\b",
    r"^(initialize|init|configure|config|deploy|delete|remove|add)\b",
    r"^(find|search|list|show|check|verify|test|push|pull|merge)\b",
    r"^(generate|compress|extract|move|copy|rename|update|upgrade)\b",
    r"^(commit|branch|clone|fork|rebase|reset|stash|tag)\b",
    r"^(npm|pip|apt|brew|docker|git|python|node|yarn)\b",
    r"\b(command|script|file|directory|folder|database|server|service)\b",
]

GREETING_RESPONSES = [
    "Hey! Describe a developer task and I will find the commands for you.",
    "Hello! Tell me what you want to do and I will handle the commands.",
    "Hi! What would you like to set up or run today?",
]

QUESTION_RESPONSE = """I am ShellAI — I turn plain English descriptions into shell commands.

  I work best when you describe a task rather than ask a question.

  Instead of:  what is docker
  Try:         run a docker container from an image

  Instead of:  how do I use git
  Try:         initialize a new git repository

  Instead of:  what does npm install do
  Try:         install all npm dependencies in this project

  What would you like to do?"""

HELP_RESPONSE = """ShellAI — run developer tasks by describing them.

  Usage:
    shellai <describe what you want to do>

  Examples:
    shellai initialize a react project with typescript
    shellai commit my current changes with message "add login"
    shellai find all files larger than 100mb
    shellai set up postgresql and create a database called myapp

  Flags:
    --careful    confirm each command individually before it runs
    --setup      re-run the first-time setup wizard
    --review     review pending dataset entries
    --stats      show database statistics
    --set-model  switch ollama model
    --version    show version"""


def detect_intent(text: str) -> tuple:
    """
    Classify user input into an intent category.
    Returns (intent_type, confidence) where confidence is 0.0-1.0.
    Checks patterns in order of specificity — first match wins.
    """
    text_lower = text.strip().lower()

    for pattern in GREETING_PATTERNS:
        if re.search(pattern, text_lower):
            return INTENT_GREETING, 0.95

    for pattern in HELP_PATTERNS:
        if re.search(pattern, text_lower):
            return INTENT_HELP, 0.90

    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, text_lower):
            return INTENT_QUESTION, 0.85

    for pattern in COMMAND_SIGNALS:
        if re.search(pattern, text_lower):
            return INTENT_COMMAND, 0.90

    # Default to command — most shellai inputs are commands
    return INTENT_COMMAND, 0.50


def get_non_command_response(intent: str) -> str:
    """Return an appropriate response for non-command intents."""
    if intent == INTENT_GREETING:
        return random.choice(GREETING_RESPONSES)
    if intent == INTENT_QUESTION:
        return QUESTION_RESPONSE
    if intent == INTENT_HELP:
        return HELP_RESPONSE
    return "Describe a developer task and I will find the commands for you."