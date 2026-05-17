import sys
from colorama import Fore, Style, init

# Initialize colorama at module level before any output
init(autoreset=True)

import db
import ai
import confirm
import executor
from display import show_error, show_success, show_cancelled
from profiles import get_profile, get_os_context, run_setup_wizard, save_profile
from placeholders import process_placeholders
from dataset_builder import run_review
from safety import check_pipeline, has_any_blocked, print_safety_report, require_explicit_confirmation
from intent import detect_intent, get_non_command_response, INTENT_COMMAND

VERSION = "0.1.0"

HELP_TEXT = """
  ShellAI — run developer tasks by describing them in plain English

  Usage:
    shellai <describe what you want to do>
    shellai --careful <describe what you want to do>

  Flags:
    --careful              Confirm each command individually before it runs
    --setup                Re-run the first-time setup wizard
    --review               Review and approve pending dataset entries
    --stats                Show database statistics
    --export-seed          Export database to seed.sql for sharing on GitHub
    --set-model <name>     Change the Ollama model (e.g. phi3:mini, mistral:7b)
    --help                 Show this help message
    --version              Show version number

  Examples:
    shellai initialize a react project with typescript
    shellai commit my current changes with message "add login"
    shellai find all files larger than 100mb
    shellai set up postgresql and create a database called myapp
    shellai --careful deploy using docker compose

  First time setup:
    shellai runs a short wizard on first launch.
    Make sure Ollama is installed and running:
      curl -fsSL https://ollama.com/install.sh | sh
      ollama pull phi3:mini
"""


def main():
    args = sys.argv[1:]

    # ── Flags that need no user_intent ────────────────────────────────────────

    if not args or "--help" in args or "-h" in args:
        print(HELP_TEXT)
        sys.exit(0)

    if "--version" in args or "-v" in args:
        print(f"  shellai {VERSION}")
        sys.exit(0)

    if "--setup" in args:
        run_setup_wizard()
        sys.exit(0)

    if "--review" in args:
        run_review()
        sys.exit(0)

    if "--stats" in args:
        stats = db.get_stats()
        print(f"\n  Database : {stats['total_commands']} commands")
        print(f"  Pending  : {stats['pending_review']} awaiting review")
        print(f"  Cached   : {stats['memory_cache']} in memory this session")
        if stats["top_commands"]:
            print(f"\n  Most used:")
            for intent, count in stats["top_commands"]:
                print(f"    {count:>4}×  {intent}")
        print()
        sys.exit(0)

    if "--export-seed" in args:
        print("\n  Exporting database to seed.sql...")
        path = db.export_seed_sql()
        print(f"  Written to: {path}")
        print(f"  Commit this to GitHub to share with other users.\n")
        sys.exit(0)

    if "--set-model" in args:
        idx = args.index("--set-model")
        if idx + 1 >= len(args):
            show_error("Usage: shellai --set-model phi3:mini")
            sys.exit(1)
        new_model = args[idx + 1]
        profile = get_profile()
        profile["ollama_model"] = new_model
        save_profile(profile)
        print(f"\n  {Fore.GREEN}Model set to: {new_model}{Style.RESET_ALL}")
        print(f"  {Style.DIM}Pull if not downloaded: ollama pull {new_model}{Style.RESET_ALL}\n")
        sys.exit(0)

    # ── Extract remaining args ─────────────────────────────────────────────────

    careful = "--careful" in args
    # Remove all flags — everything left is the user's intent
    args = [a for a in args if not a.startswith("--")]
    user_intent = " ".join(args).strip()

    if not user_intent:
        show_error(
            "Please describe what you want to do.\n"
            "  Example: shellai initialize a new git repository"
        )
        sys.exit(1)

    # ── Intent detection ───────────────────────────────────────────────────────
    # Must happen AFTER user_intent is built
    # Handles questions, greetings, and help requests gracefully

    intent_type, _ = detect_intent(user_intent)

    if intent_type != INTENT_COMMAND:
        print(f"\n  {get_non_command_response(intent_type)}\n")
        sys.exit(0)

    # ── Load profile ───────────────────────────────────────────────────────────
    # Runs setup wizard automatically on first launch
    # On every subsequent launch loads saved profile silently

    profile = get_profile()
    os_context = get_os_context(profile)
    os_id = profile.get("os_id", "ubuntu")
    ollama_model = profile.get("ollama_model", "phi3:mini")

    # ── Get commands ───────────────────────────────────────────────────────────
    # Checks: memory cache → SQLite database → Ollama

    try:
        result = ai.get_commands(
            user_intent=user_intent,
            os_context=os_context,
            os_id=os_id,
            ollama_model=ollama_model
        )
    except (ConnectionError, ValueError, RuntimeError) as e:
        show_error(str(e))
        sys.exit(1)

    commands = result.get("commands", [])

    if not commands:
        show_error("No commands found. Try rephrasing your request.")
        sys.exit(1)

    # ── Fill in placeholders ───────────────────────────────────────────────────
    # Must happen BEFORE showing the plan so users see real values

    commands = process_placeholders(commands)
    result["commands"] = commands

    # ── Safety checks ──────────────────────────────────────────────────────────

    safety_results = check_pipeline(commands)

    if has_any_blocked(safety_results):
        print_safety_report(safety_results)
        show_error("Execution blocked — one or more commands are too dangerous to run.")
        sys.exit(1)

    print_safety_report(safety_results)

    destructive = [(c, s) for c, s in safety_results if s.has_warnings]
    if destructive and not require_explicit_confirmation(destructive):
        show_cancelled()
        sys.exit(0)

    # ── Show plan and confirm ──────────────────────────────────────────────────

    confirm.show_plan(result)
    decision = confirm.ask_confirmation(len(commands))

    if decision == "no":
        show_cancelled()
        sys.exit(0)

    if decision == "edit":
        commands = confirm.ask_edit(commands)
        if not commands:
            show_cancelled()
            sys.exit(0)

    # ── Execute ────────────────────────────────────────────────────────────────

    success = executor.run_all(commands, careful=careful)

    if success:
        show_success()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()