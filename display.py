import os
from colorama import Fore, Style, init

init(autoreset=True)

try:
    WIDTH = min(os.get_terminal_size().columns, 72)
except OSError:
    WIDTH = 72


def _line(char="─"):
    return char * WIDTH


def show_answer(result: dict) -> None:
    """
    Display the command plan in a clean bordered box.
    Users never see source attribution or confidence scores.
    They just see the summary and numbered commands.
    """
    commands = result.get("commands", [])
    summary = result.get("summary", "")

    print()
    print(f"  {Fore.CYAN}{_line()}{Style.RESET_ALL}")

    if summary:
        print(f"  {summary}")
        print(f"  {Fore.CYAN}{_line('·')}{Style.RESET_ALL}")

    for i, cmd in enumerate(commands, 1):
        command = cmd.get("command", "")
        explanation = cmd.get("explanation", "")
        warning = cmd.get("warning", "")

        print(f"\n  {i}.  {Style.BRIGHT}{command}{Style.RESET_ALL}")
        print(f"      {Style.DIM}{explanation}{Style.RESET_ALL}")

        if warning:
            print(f"      {Fore.YELLOW}⚠  {warning}{Style.RESET_ALL}")

    print(f"\n  {Fore.CYAN}{_line()}{Style.RESET_ALL}\n")


def ask_confirmation(num_commands: int) -> str:
    """
    Ask whether to run the commands.
    Returns 'yes', 'no', or 'edit'.
    """
    label = f"{num_commands} command" + ("s" if num_commands != 1 else "")
    while True:
        answer = input(
            f"  Run {label}?  "
            f"[{Fore.GREEN}y{Style.RESET_ALL}es  "
            f"{Fore.RED}n{Style.RESET_ALL}o  "
            f"{Fore.YELLOW}e{Style.RESET_ALL}dit]:  "
        ).strip().lower()

        if answer in ("y", "yes"):   return "yes"
        if answer in ("n", "no"):    return "no"
        if answer in ("e", "edit"):  return "edit"
        print("  Please type y, n, or e")


def ask_edit(commands: list) -> list:
    """Let user pick which commands to keep."""
    print(f"\n  Which commands do you want to run?\n")
    for i, cmd in enumerate(commands, 1):
        print(f"  {i}.  {cmd.get('command', '')}")
    print(f"\n  Enter numbers separated by spaces (e.g. 1 3), or 'all':\n")

    while True:
        answer = input("  > ").strip().lower()
        if answer == "all":
            return commands
        try:
            nums = [int(x) for x in answer.replace(",", " ").split()]
            selected = [commands[n - 1] for n in nums if 1 <= n <= len(commands)]
            if selected:
                return selected
            print("  No valid numbers. Try again.")
        except ValueError:
            print("  Enter numbers like: 1 3 4")


def show_running(index: int, total: int, command: str) -> None:
    print(f"\n  [{index}/{total}]  {Style.BRIGHT}{command}{Style.RESET_ALL}")


def show_command_ok() -> None:
    print(f"         {Fore.GREEN}✓{Style.RESET_ALL}")


def show_command_fail(stderr: str) -> None:
    print(f"         {Fore.RED}✗{Style.RESET_ALL}")
    if stderr.strip():
        for line in stderr.strip().split("\n"):
            print(f"         {Fore.RED}{line}{Style.RESET_ALL}")


def show_command_output(stdout: str) -> None:
    if stdout.strip():
        for line in stdout.strip().split("\n"):
            print(f"         {Style.DIM}{line}{Style.RESET_ALL}")


def ask_continue_after_failure() -> bool:
    answer = input(
        f"\n  Command failed. Continue anyway? "
        f"[{Fore.GREEN}y{Style.RESET_ALL}/{Fore.RED}n{Style.RESET_ALL}]:  "
    ).strip().lower()
    return answer in ("y", "yes")


def show_error(message: str) -> None:
    print(f"\n  {Fore.RED}Error:{Style.RESET_ALL} {message}\n")


def show_success() -> None:
    print(f"\n  {Fore.GREEN}Done.{Style.RESET_ALL}\n")


def show_cancelled() -> None:
    print(f"\n  Cancelled.\n")


def show_thinking() -> None:
    print(f"\n  {Style.DIM}Working on it...{Style.RESET_ALL}", flush=True)


def show_pending_hint(count: int) -> None:
    if count > 0:
        print(
            f"  {Style.DIM}{count} pending "
            f"entr{'y' if count == 1 else 'ies'} — "
            f"run 'shellai --review' to add to database{Style.RESET_ALL}"
        )