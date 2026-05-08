from colorama import Fore, Style, init

init(autoreset=True)

def show_plan(result: dict) -> None:
    """
    Print the full plan in a bordered box.
    Shows summary, each numbered command, its explanation,
    and any warnings for dangerous operations.
    """
    commands = result.get("commands", [])
    summary  = result.get("summary", "")
    source   = result.get("source", "")

    print()
    print(Fore.CYAN + "┌─ Plan " + "─" * 53)

    if summary:
        print(Fore.CYAN + "│ " + Style.RESET_ALL + summary)
        print(Fore.CYAN + "│")

    for i, cmd in enumerate(commands, 1):
        command     = cmd.get("command", "")
        explanation = cmd.get("explanation", "")
        warning     = cmd.get("warning", "")

        print(
            Fore.CYAN + f"│  {i}. " +
            Style.BRIGHT + Fore.WHITE + command + Style.RESET_ALL
        )
        print(
            Fore.CYAN + "│     " +
            Style.DIM + "→ " + explanation + Style.RESET_ALL
        )

        if warning:
            print(
                Fore.CYAN + "│     " +
                Fore.RED + "⚠  " + warning + Style.RESET_ALL
            )

        if i < len(commands):
            print(Fore.CYAN + "│")

    # Show source in bottom border so user knows where answer came from
    source_label = f" source: {source} " if source else ""
    print(Fore.CYAN + "└" + "─" * 53 + source_label)
    print()


def ask_confirmation(num_commands: int) -> str:
    """
    Ask the user whether to run the commands.
    Returns 'yes', 'no', or 'edit'.
    """
    count = f"{num_commands} command" + ("s" if num_commands != 1 else "")

    while True:
        answer = input(
            f"Run {count}? "
            f"[{Fore.GREEN}y{Style.RESET_ALL}es / "
            f"{Fore.RED}n{Style.RESET_ALL}o / "
            f"{Fore.YELLOW}e{Style.RESET_ALL}dit]: "
        ).strip().lower()

        if answer in ("y", "yes"):     return "yes"
        if answer in ("n", "no", "q"): return "no"
        if answer in ("e", "edit"):    return "edit"
        print("  Please type y, n, or e")


def ask_edit(commands: list) -> list:
    """
    Let the user choose which commands to keep.
    Returns a filtered list of commands.
    """
    print("\nEnter the numbers of commands to run (e.g. 1 3 4), or 'all':\n")

    for i, cmd in enumerate(commands, 1):
        print(f"  {i}. {cmd.get('command', '')}")

    while True:
        answer = input("\n> ").strip().lower()

        if answer == "all":
            return commands

        try:
            nums     = [int(x) for x in answer.replace(",", " ").split()]
            selected = [commands[n - 1] for n in nums if 1 <= n <= len(commands)]
            if selected:
                return selected
            print("  No valid numbers. Try again.")
        except ValueError:
            print("  Please enter numbers separated by spaces, e.g.: 1 3 4")