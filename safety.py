import re
from colorama import Fore, Style, init

init(autoreset=True)

BLOCKED_PATTERNS = [
    (r"rm\s+-[a-z]*r[a-z]*f\s+/\s*$",            "rm -rf / destroys the entire operating system"),
    (r"rm\s+-[a-z]*f[a-z]*r\s+/\s*$",            "rm -rf / destroys the entire operating system"),
    (r"rm\s+-rf\s+/etc\b",                         "Deleting /etc removes all system configuration"),
    (r"rm\s+-rf\s+/boot\b",                        "Deleting /boot makes the system unbootable"),
    (r"rm\s+-rf\s+/usr\b",                         "Deleting /usr removes all system programs"),
    (r"rm\s+-rf\s+/bin\b",                         "Deleting /bin removes essential system binaries"),
    (r"rm\s+-rf\s+/lib\b",                         "Deleting /lib removes system libraries"),
    (r":\(\)\{.*\|.*:.*\}.*:.*",                   "Fork bomb — will crash the system"),
    (r"dd\s+if=.*of=/dev/sd[a-z]\b",              "Writing to a disk device can wipe your entire drive"),
    (r"dd\s+if=.*of=/dev/nvme",                   "Writing to a disk device can wipe your entire drive"),
    (r"curl\s+.*\|\s*(bash|sh|zsh|fish)",          "Piping internet content to a shell is a security risk"),
    (r"wget\s+.*-O\s*-\s*\|\s*(bash|sh|zsh)",     "Piping internet content to a shell is a security risk"),
    (r"chmod\s+777\s+/\s*$",                       "chmod 777 / makes every file world-writable"),
    (r"chmod\s+-R\s+777\s+/\s*$",                 "chmod -R 777 / makes every file world-writable"),
]

DESTRUCTIVE_PATTERNS = [
    (r"\brm\s+-[a-z]*r[a-z]*f\b",                "Recursive force delete — permanently removes files"),
    (r"\brm\s+-[a-z]*f[a-z]*r\b",                "Recursive force delete — permanently removes files"),
    (r"\bdrop\s+database\b",                       "Drops the entire database permanently"),
    (r"\bdrop\s+table\b",                          "Drops a database table permanently"),
    (r"\btruncate\s+table\b",                      "Removes all rows from a table permanently"),
    (r"\bmkfs\.",                                   "Formats a filesystem — destroys all data on target"),
    (r"\bshred\b",                                  "Permanently overwrites files — not recoverable"),
    (r">\s*/etc/",                                  "Writing to /etc/ can break system configuration"),
    (r"\buserdel\b",                               "Deletes a user account permanently"),
]

FLAGGED_PATTERNS = [
    (r"\bsudo\b",                                   "Runs with administrator privileges"),
    (r"\bchmod\b",                                  "Changes file permissions"),
    (r"\bchown\b",                                  "Changes file ownership"),
    (r"\bcrontab\b",                                "Modifies scheduled tasks"),
    (r"\bsystemctl\s+(stop|disable|mask)\b",        "Stopping or disabling a system service"),
    (r"\bapt\s+(remove|purge)\b",                  "Removing system packages"),
]

SENSITIVE_PATHS = [
    "/etc", "/boot", "/usr", "/bin", "/sbin", "/lib",
    "/proc", "/sys", "/dev", "/root", "~/.ssh",
    "~/.bashrc", "~/.zshrc", "~/.profile"
]


class SafetyResult:
    def __init__(self):
        self.blocked     = None
        self.destructive = None
        self.flagged     = None
        self.path_warn   = None

    @property
    def is_blocked(self) -> bool:
        return self.blocked is not None

    @property
    def has_warnings(self) -> bool:
        return self.destructive is not None or self.path_warn is not None

    @property
    def has_notices(self) -> bool:
        return self.flagged is not None


def check_command(command: str) -> SafetyResult:
    """Run all safety checks on a single command."""
    result = SafetyResult()
    cmd_lower = command.lower().strip()

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            result.blocked = reason
            return result

    for pattern, warning in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            result.destructive = warning
            break

    for path in SENSITIVE_PATHS:
        if path in command:
            result.path_warn = f"Operates on sensitive path: {path}"
            break

    for pattern, notice in FLAGGED_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            result.flagged = notice
            break

    return result


def check_pipeline(commands: list) -> list:
    """Check all commands. Returns list of (command_dict, SafetyResult)."""
    return [(cmd, check_command(cmd.get("command", ""))) for cmd in commands]


def has_any_blocked(results: list) -> bool:
    return any(s.is_blocked for _, s in results)


def print_safety_report(results: list) -> None:
    """Print safety findings. Only prints if there is something to report."""
    has_anything = any(
        s.is_blocked or s.has_warnings or s.has_notices
        for _, s in results
    )
    if not has_anything:
        return

    print(f"\n  {Fore.YELLOW}Safety check:{Style.RESET_ALL}")

    for cmd_obj, safety in results:
        command = cmd_obj.get("command", "")
        short = command[:55] + "..." if len(command) > 55 else command

        if safety.is_blocked:
            print(f"  {Fore.RED}✗ BLOCKED:{Style.RESET_ALL} {short}")
            print(f"    {Fore.RED}{safety.blocked}{Style.RESET_ALL}")
        elif safety.has_warnings:
            print(f"  {Fore.YELLOW}⚠ WARNING:{Style.RESET_ALL} {short}")
            if safety.destructive:
                print(f"    {Fore.YELLOW}{safety.destructive}{Style.RESET_ALL}")
            if safety.path_warn:
                print(f"    {Fore.YELLOW}{safety.path_warn}{Style.RESET_ALL}")
        elif safety.has_notices:
            print(f"  {Style.DIM}ℹ {short}{Style.RESET_ALL}")

    print()


def require_explicit_confirmation(commands_with_warnings: list) -> bool:
    """
    For destructive commands require the user to type 'yes' in full.
    Typing just 'y' is not enough — this forces a conscious decision.
    """
    print(f"  {Fore.RED}The following commands are destructive:{Style.RESET_ALL}")
    for cmd_obj, safety in commands_with_warnings:
        if safety.has_warnings:
            print(f"  • {cmd_obj.get('command', '')}")
    print()

    answer = input(
        f"  Type {Fore.RED}yes{Style.RESET_ALL} to confirm, "
        f"or anything else to cancel: "
    ).strip()

    return answer.lower() == "yes"