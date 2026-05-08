import re
from colorama import Fore, Style, init

init(autoreset=True)

# Matches anything like {{SOME_NAME}} — uppercase letters, digits, underscores
PLACEHOLDER_RE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')


def find_placeholders(commands: list) -> list:
    """
    Scan all commands and return a list of unique placeholder names.
    Preserves the order they were first seen.

    Example:
      Input commands contain {{YOUR_NAME}} and {{YOUR_EMAIL}}
      Returns: ["YOUR_NAME", "YOUR_EMAIL"]
    """
    seen   = set()
    result = []

    for cmd_obj in commands:
        command = cmd_obj.get("command", "")
        for match in PLACEHOLDER_RE.findall(command):
            if match not in seen:
                seen.add(match)
                result.append(match)

    return result


def friendly_label(name: str) -> str:
    """
    Convert a placeholder name to a readable prompt label.
    YOUR_NAME    → "Your name"
    DATABASE_NAME → "Database name"
    """
    return name.replace("_", " ").capitalize()


def get_hint(name: str, commands: list) -> str:
    """
    Find the explanation of the command that uses this placeholder.
    This gives the user context about what the value is used for.
    """
    token = f"{{{{{name}}}}}"
    for cmd_obj in commands:
        if token in cmd_obj.get("command", ""):
            return cmd_obj.get("explanation", "")
    return ""


def collect_values(placeholders: list, commands: list) -> dict:
    """
    Ask the user to enter a value for each placeholder.
    Shows a hint so the user understands what each value is for.
    Returns a dict mapping placeholder names to user-entered values.
    """
    if not placeholders:
        return {}

    print(f"\n{Fore.YELLOW}This plan needs some information from you:{Style.RESET_ALL}\n")

    # Show all placeholders with hints first so user can see what's needed
    for name in placeholders:
        hint = get_hint(name, commands)
        if hint:
            print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}  {Style.DIM}→ {hint}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}")

    print()

    # Now collect each value
    values = {}
    for name in placeholders:
        label = friendly_label(name)
        while True:
            value = input(f"  {Fore.CYAN}{label}:{Style.RESET_ALL} ").strip()
            if value:
                values[name] = value
                break
            print(f"    {Fore.RED}Cannot be empty. Please enter a value.{Style.RESET_ALL}")

    return values


def substitute(commands: list, values: dict) -> list:
    """
    Replace all {{PLACEHOLDER}} tokens in every command
    with the real values the user provided.

    Returns a new list — does not modify the original.
    """
    if not values:
        return commands

    result = []
    for cmd_obj in commands:
        new_cmd = dict(cmd_obj)
        command = new_cmd.get("command", "")

        for name, value in values.items():
            command = command.replace(f"{{{{{name}}}}}", value)

        new_cmd["command"] = command
        result.append(new_cmd)

    return result


def process_placeholders(commands: list) -> list:
    """
    Main entry point. Call this after getting commands and
    before showing the confirmation screen.

    Returns commands with all placeholders filled in.
    If no placeholders found, returns the original list unchanged.
    """
    placeholders = find_placeholders(commands)

    if not placeholders:
        return commands

    values = collect_values(placeholders, commands)
    return substitute(commands, values)