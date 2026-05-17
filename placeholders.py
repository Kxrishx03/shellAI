import re
from colorama import Fore, Style, init

init(autoreset=True)

PLACEHOLDER_RE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')


def find_placeholders(commands: list) -> list:
    """Return a list of unique placeholder names in the order first seen."""
    seen = set()
    result = []

    for cmd_obj in commands:
        for match in PLACEHOLDER_RE.findall(cmd_obj.get("command", "")):
            if match not in seen:
                seen.add(match)
                result.append(match)

    return result


def friendly_label(name: str) -> str:
    """Convert BRANCH_NAME to 'Branch name'."""
    return name.replace("_", " ").capitalize()


def get_hint(name: str, commands: list) -> str:
    """Find the explanation of the command using this placeholder."""
    token = f"{{{{{name}}}}}"
    for cmd_obj in commands:
        if token in cmd_obj.get("command", ""):
            return cmd_obj.get("explanation", "")
    return ""


def validate_value(name: str, value: str) -> str | None:
    """
    Validate a placeholder value makes sense.
    Returns an error string if invalid, None if valid.
    """
    value = value.strip()

    if not value:
        return f"{name} cannot be empty"

    name_placeholders = {"YOUR_NAME", "USERNAME", "PROJECT_NAME", "DATABASE_NAME", "IMAGE_NAME"}
    if name in name_placeholders and ("/" in value or "\\" in value):
        return f"{name} looks like a path — expected a simple name like 'myproject'"

    if "EMAIL" in name and "@" not in value:
        return f"{name} does not look like a valid email address"

    if "PORT" in name:
        if not value.isdigit():
            return f"{name} must be a number"
        if not (1 <= int(value) <= 65535):
            return f"{name} must be between 1 and 65535"

    return None


def collect_values(placeholders: list, commands: list) -> dict:
    """Ask the user to enter a value for each placeholder."""
    if not placeholders:
        return {}

    print(f"\n  {Fore.YELLOW}This plan needs some information from you:{Style.RESET_ALL}\n")

    for name in placeholders:
        hint = get_hint(name, commands)
        if hint:
            print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}  {Style.DIM}→ {hint}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}")

    print()

    values = {}
    for name in placeholders:
        label = friendly_label(name)
        while True:
            value = input(f"  {Fore.CYAN}{label}:{Style.RESET_ALL} ").strip()
            error = validate_value(name, value)
            if error:
                print(f"    {Fore.RED}{error}{Style.RESET_ALL}")
                continue
            values[name] = value
            break

    return values


def substitute(commands: list, values: dict) -> list:
    """Replace all placeholder tokens with real values. Returns a new list."""
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
    Main entry point. Call with the commands list before confirmation.
    Returns commands with all placeholders substituted.
    If no placeholders found, returns the original list unchanged.
    """
    placeholders = find_placeholders(commands)

    if not placeholders:
        return commands

    values = collect_values(placeholders, commands)
    return substitute(commands, values)