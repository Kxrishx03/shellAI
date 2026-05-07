from colorama import Fore, Style, init

init(autoreset=True)

def show_plan(result: dict) -> None:
    """
    Print the full plan of commands in a clear, readable format.
    Shows the summary, each numbered command, its explanation,
    and any warnings about dangerous operations.
    """
    commands = result.get("commands", [])
    summary  = result.get("summary", "")

    print()

    print(Fore.CYAN + "┌─ Plan " + "─" * 55)
    if summary:
        print(Fore.CYAN + "│ " + Style.RESET_ALL + summary)
        print(Fore.CYAN + "│")

    for i, cmd in enumerate(commands, 1):
        command     = cmd.get("command", "")
        explanation = cmd.get("explanation", "")
        warning     = cmd.get("warning", "")

        print(
            Fore.CYAN + f"│  {i}. " +
            Style.BRIGHT + Fore.WHITE + command
        )

        print(
            Fore.CYAN + "│     " +
            Style.DIM + "→ " + explanation
        )

        if warning:
            print(
                Fore.CYAN + "│     " +
                Fore.RED + "⚠  " + warning
            )

        if i < len(commands):
            print(Fore.CYAN + "│")

    print(Fore.CYAN + "└" + "─" * 62)
    print()


def ask_confirmation(num_commands: int) -> str:
    """
    Ask the user whether to run the commands.
    Returns:
      'yes'  — run all commands
      'no'   — cancel
      'edit' — let user pick which commands to run
    """
    count_word = f"{num_commands} command" + ("s" if num_commands != 1 else "")

    while True:
        answer = input(
            f"Run {count_word}? "
            f"[{Fore.GREEN}y{Style.RESET_ALL}es / "
            f"{Fore.RED}n{Style.RESET_ALL}o / "
            f"{Fore.YELLOW}e{Style.RESET_ALL}dit]: "
        ).strip().lower()

        if answer in ("y", "yes"):
            return "yes"
        elif answer in ("n", "no", "q", "quit"):
            return "no"
        elif answer in ("e", "edit"):
            return "edit"
        else:
            print("  Please type y, n, or e")


def ask_edit(commands: list) -> list:
    """
    Let the user pick which commands to keep.
    Returns a filtered list of commands.
    """
    print("\nEnter the numbers of commands to run (e.g. 1 3 4), or 'all':")

    for i, cmd in enumerate(commands, 1):
        print(f"  {i}. {cmd['command']}")

    while True:
        answer = input("> ").strip().lower()

        if answer == "all":
            return commands

        # Parse numbers like "1 3 4" or "1,3,4"
        try:
            nums    = [int(x) for x in answer.replace(",", " ").split()]
            selected = [commands[n - 1] for n in nums if 1 <= n <= len(commands)]
            if selected:
                return selected
            else:
                print("  No valid numbers entered. Try again.")
        except ValueError:
            print("  Please enter numbers separated by spaces, e.g.: 1 3 4")


def ask_single_confirmation(command: str) -> bool:
    """
    Ask for confirmation before each individual command.
    Used in careful mode.
    Returns True to run, False to skip.
    """
    answer = input(
        f"\n  Run: {Style.BRIGHT}{command}{Style.RESET_ALL}  "
        f"[{Fore.GREEN}y{Style.RESET_ALL}/{Fore.RED}n{Style.RESET_ALL}/skip]: "
    ).strip().lower()

    return answer in ("y", "yes", "")