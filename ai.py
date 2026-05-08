from colorama import Fore, Style, init
from local_engine import get_commands_local
from ollama_engine import get_commands_ollama, is_ollama_running
from dataset_builder import save_pending

init(autoreset=True)


def get_commands(
    user_intent: str,
    os_context:  str  = "Ubuntu Linux",
    os_id:       str  = "ubuntu",
    ollama_model: str = "phi3:mini"
) -> dict:
    """
    Find commands for a task. Returns a dict with:
      commands  — list of {command, explanation} dicts
      summary   — one sentence describing the overall task
      source    — where the answer came from: "local" or "ollama:modelname"

    Raises exceptions with clear messages if Ollama is not running
    or if no answer can be found.
    """

   
    print(
        f"\n{Fore.CYAN}Checking local database...{Style.RESET_ALL}",
        end="",
        flush=True
    )

    local_result = get_commands_local(user_intent, os_id)

    if local_result:
        confidence = local_result.get("confidence", 0)
        print(
            f"\r{Fore.GREEN}✓ Found in local database "
            f"{Style.DIM}(confidence: {confidence:.0%}){Style.RESET_ALL}"
            + " " * 10
        )
        return local_result

    print(f"\r{' ' * 50}\r", end="")

    if not is_ollama_running():
        raise ConnectionError(
            "No local database match found and Ollama is not running.\n\n"
            "Start Ollama with:\n"
            "  ollama serve\n\n"
            "Or run it in the background:\n"
            "  ollama serve &"
        )

    result = get_commands_ollama(user_intent, os_context, ollama_model)

  
    saved = save_pending(user_intent, result, os_id)

    if saved:
        pending_note = (
            f"\n{Style.DIM}  This response was saved to pending. "
            f"Run 'shellai --review' to add it to your local database.{Style.RESET_ALL}"
        )
        print(pending_note)

    return result