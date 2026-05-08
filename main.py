import sys
from colorama import Fore, Style, init
import ai
import confirm
import executor
from profiles import get_profile, get_os_context, run_setup_wizard, save_profile
from placeholders import process_placeholders
from dataset_builder import run_review, count_pending

init(autoreset=True)

VERSION = "0.1.0"

HELP_TEXT = """
shellai — run developer tasks by describing them in plain English

Usage:
  shellai <describe what you want to do>
  shellai --careful <describe what you want to do>

Flags:
  --careful              Confirm each command individually before it runs
  --setup                Re-run the first-time setup wizard
  --review               Review and approve pending dataset entries
  --set-model <name>     Change the Ollama model  (e.g. phi3:mini, mistral:7b)
  --help                 Show this help message
  --version              Show version number

Examples:
  shellai initialize a react project with typescript
  shellai merge branch feature/login into main with message "add auth"
  shellai set up postgresql and create a database called myapp
  shellai --careful deploy using docker compose

How the local database grows automatically:
  When shellai asks Ollama for an answer, it saves the response
  to a pending queue. Run 'shellai --review' to approve good entries.
  Approved entries join your local database — next time the same
  task is asked, it is answered instantly with no model call needed.

First time setup:
  shellai will run a short wizard on first launch.
  Make sure Ollama is installed and running:
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull phi3:mini
    ollama serve &
"""

def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(HELP_TEXT)
        sys.exit(0)

    if "--version" in args or "-v" in args:
        print(f"shellai {VERSION}")
        sys.exit(0)

    if "--setup" in args:
        run_setup_wizard()
        sys.exit(0)

    if "--review" in args:
        run_review()
        sys.exit(0)

    if "--set-model" in args:
        idx = args.index("--set-model")
        if idx + 1 >= len(args):
            print(f"{Fore.RED}Usage: shellai --set-model phi3:mini{Style.RESET_ALL}")
            sys.exit(1)
        new_model = args[idx + 1]
        profile   = get_profile()
        profile["ollama_model"] = new_model
        save_profile(profile)
        print(f"{Fore.GREEN}Model set to: {new_model}{Style.RESET_ALL}")
        print(f"{Style.DIM}Make sure it is downloaded:  ollama pull {new_model}{Style.RESET_ALL}")
        sys.exit(0)


    careful = "--careful" in args
    args    = [a for a in args if not a.startswith("--")]

    user_intent = " ".join(args).strip()

    if not user_intent:
        print(f"{Fore.RED}Please describe what you want to do.{Style.RESET_ALL}")
        print("Example:  shellai initialize a new git repository")
        sys.exit(1)

   
    profile      = get_profile()
    os_context   = get_os_context(profile)
    os_id        = profile.get("os_id", "ubuntu")
    ollama_model = profile.get("ollama_model", "phi3:mini")

    try:
        result = ai.get_commands(
            user_intent  = user_intent,
            os_context   = os_context,
            os_id        = os_id,
            ollama_model = ollama_model
        )
    except (ConnectionError, ValueError, RuntimeError) as e:
        print(f"\n{Fore.RED}Error:{Style.RESET_ALL} {e}")
        sys.exit(1)

    commands = result.get("commands", [])

    if not commands:
        print(f"{Fore.RED}No commands returned.{Style.RESET_ALL} Try rephrasing your request.")
        sys.exit(1)

  
    commands         = process_placeholders(commands)
    result["commands"] = commands

    confirm.show_plan(result)
    decision = confirm.ask_confirmation(len(commands))

    if decision == "no":
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        sys.exit(0)

    if decision == "edit":
        commands = confirm.ask_edit(commands)
        if not commands:
            print(f"\n{Fore.YELLOW}Nothing selected. Cancelled.{Style.RESET_ALL}")
            sys.exit(0)

    success = executor.run_all(commands, careful=careful)

    if success:
        print(f"{Fore.GREEN}All done!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Finished with errors.{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()