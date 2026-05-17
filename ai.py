import db
from ollama_engine import get_commands_ollama, is_ollama_running
from colorama import Fore, Style, init

init(autoreset=True)


def get_commands(
    user_intent: str,
    os_context: str = "Ubuntu Linux",
    os_id: str = "ubuntu",
    ollama_model: str = "phi3:mini"
) -> dict:
    """
    Find commands for a task.
    Returns a dict with 'commands', 'summary', and 'source'.
    Raises ConnectionError, ValueError, or RuntimeError with
    actionable messages on failure.
    """

    # Levels 1 and 2: memory cache then SQLite
    # db.search() checks cache first, falls through to SQLite on miss
    result = db.search(user_intent, os_id)

    if result:
        confidence = result.get("confidence", 0)
        if confidence >= 0.8:
            print(f"\n  {Fore.GREEN}✓{Style.RESET_ALL}", end="  ", flush=True)
        return result

    # Level 3: Ollama
    if not is_ollama_running():
        raise ConnectionError(
            "No answer found in local database and Ollama is not running.\n\n"
            "  Start Ollama:  ollama serve &\n"
            "  Then retry your command."
        )

    ollama_result = get_commands_ollama(
        user_intent=user_intent,
        os_context=os_context,
        model=ollama_model
    )

    # Save to pending automatically — silent, no user action needed
    saved = db.save_to_pending(user_intent, ollama_result, os_id)
    if saved:
        pending_count = db.count_pending()
        print(
            f"\n  {Style.DIM}Answer saved for review. "
            f"Run 'shellai --review' to add it to your database. "
            f"({pending_count} pending){Style.RESET_ALL}"
        )

    return ollama_result