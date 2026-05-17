import subprocess
import os
from colorama import Fore, Style, init
from display import (
    show_running, show_command_ok, show_command_fail,
    show_command_output, ask_continue_after_failure
)

init(autoreset=True)


def run_command(command: str, working_dir: str = None) -> tuple:
    """
    Run a single shell command via bash.
    Returns (success, stdout, stderr).
    shell=True is required for cd, pipes, &&, env vars to work.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            text=True,
            capture_output=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def extract_new_directory(command: str, current_dir: str) -> str:
    """
    If the command contains a cd instruction, return the new directory.
    Handles compound commands like: mkdir foo && cd foo
    """
    parts = command.replace("&&", ";").split(";")

    for part in parts:
        part = part.strip()
        if part.startswith("cd "):
            target = part[3:].strip().strip('"').strip("'")

            if target in ("", "~"):
                return os.path.expanduser("~")

            if os.path.isabs(target):
                return target

            new_dir = os.path.join(current_dir, target)
            if os.path.isdir(new_dir):
                return os.path.realpath(new_dir)

    return current_dir


def run_all(commands: list, careful: bool = False) -> bool:
    """
    Run a list of commands sequentially.
    If careful=True, asks for confirmation before each command.
    Returns True if all commands succeeded.
    """
    working_dir = os.getcwd()
    total = len(commands)
    all_ok = True

    print()

    for i, cmd_obj in enumerate(commands, 1):
        command = cmd_obj.get("command", "")
        if not command:
            continue

        if careful:
            answer = input(
                f"  Run: {Style.BRIGHT}{command}{Style.RESET_ALL}  "
                f"[{Fore.GREEN}y{Style.RESET_ALL}/"
                f"{Fore.YELLOW}s{Style.RESET_ALL}kip/"
                f"{Fore.RED}n{Style.RESET_ALL}o]:  "
            ).strip().lower()

            if answer in ("n", "no"):
                print(f"\n  {Fore.RED}Stopped.{Style.RESET_ALL}\n")
                return False
            if answer in ("s", "skip"):
                print(f"  {Fore.YELLOW}Skipped{Style.RESET_ALL}\n")
                continue

        show_running(i, total, command)
        success, stdout, stderr = run_command(command, working_dir)
        show_command_output(stdout)

        if success:
            show_command_ok()
            working_dir = extract_new_directory(command, working_dir)
        else:
            show_command_fail(stderr)
            all_ok = False
            if not ask_continue_after_failure():
                return False

    return all_ok