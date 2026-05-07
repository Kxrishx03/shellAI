import sys
from colorama import Fore, Style, init

import config
import ai
import confirm
import executor

init(autoreset=True)

HELP_TEXT = """
shellai — run tasks by describing them in plain English

Usage:
  shellai <describe what you want to do>
  shellai --careful <describe what you want to do>

Flags:
  --careful    Ask for confirmation before each individual command
  --help       Show this help message
  --version    Show version

Examples:
  shellai initialize a react project with typescript and tailwind
  shellai merge branch feature/login into main with message "add login"
  shellai set up a PostgreSQL database called myapp
  shellai find all node_modules folders and delete them
  shellai --careful deploy to production using docker compose

Config:
  Add GEMINI_API_KEY=your_key to a .env file in the current directory
  or to ~/.shellai

  Get a free key at: https://aistudio.google.com
"""

VERSION = "0.1.0"


def main():
    args = sys.argv[1:]  # everything after "python3 main.py"

    # Handle flags
    if not args or "--help" in args or "-h" in args:
        print(HELP_TEXT)
        sys.exit(0)

    if "--version" in args or "-v" in args:
        print(f"shellai {VERSION}")
        sys.exit(0)

    # Check for --careful flag
    careful = "--careful" in args
    if careful:
        args = [a for a in args if a != "--careful"]

    # Everything remaining is the user's intent
    user_intent = " ".join(args)

    if not user_intent.strip():
        print(f"{Fore.RED}Error:{Style.RESET_ALL} Please describe what you want to do.")
        print('Example: shellai initialize a new git repository')
        sys.exit(1)

    # Step 1: Check API key exists before making any request
    if not config.get_api_key():
        print(f"\n{Fore.RED}Error:{Style.RESET_ALL} No API key found.")
        print("Add this to a .env file in your current directory:")
        print(f"  {Style.BRIGHT}GEMINI_API_KEY=your_key_here{Style.RESET_ALL}")
        print("\nGet a free key at: https://aistudio.google.com")
        sys.exit(1)

    # Step 2: Ask Gemini for commands
    print(f"\n{Fore.YELLOW}⚡ Thinking...{Style.RESET_ALL}", end="", flush=True)

    try:
        result = ai.get_commands(user_intent)
    except (ValueError, ConnectionError, RuntimeError) as e:
        print(f"\n{Fore.RED}Error:{Style.RESET_ALL} {e}")
        sys.exit(1)

    print(f"\r{' ' * 20}\r", end="")  # clear the "Thinking..." line

    commands = result.get("commands", [])

    if not commands:
        print(f"{Fore.RED}No commands returned.{Style.RESET_ALL} Try rephrasing your request.")
        sys.exit(1)

    # Step 3: Show the plan
    confirm.show_plan(result)

    # Step 4: Ask for confirmation
    decision = confirm.ask_confirmation(len(commands))

    if decision == "no":
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        sys.exit(0)

    if decision == "edit":
        commands = confirm.ask_edit(commands)
        if not commands:
            print(f"\n{Fore.YELLOW}Nothing selected. Cancelled.{Style.RESET_ALL}")
            sys.exit(0)
        # Update result with filtered commands
        result["commands"] = commands

    # Step 5: Run the commands
    success = executor.run_all(commands, careful=careful)

    # Step 6: Final summary
    if success:
        print(f"{Fore.GREEN}All done!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Finished with errors.{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()