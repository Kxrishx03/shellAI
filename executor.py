import subprocess
import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)


def run_command(command: str, working_dir: str = None) -> tuple:
    """
    Run a single shell command.

    Returns a tuple of (success, output, error):
      success  — True if command exited with code 0
      output   — the text the command printed to stdout
      error    — the text the command printed to stderr
    """
    try:
        result = subprocess.run(
            command,
            shell=True,           # run through bash so cd, &&, etc. work
            cwd=working_dir,      # which directory to run in
            text=True,            # return strings instead of bytes
            capture_output=True   # capture both stdout and stderr
        )

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except Exception as e:
        return False, "", str(e)


def get_new_directory(command: str, current_dir: str) -> str:
    """
    If a command contains 'cd something', return the new directory.
    We need this because each subprocess call starts fresh —
    a 'cd' command in one call doesn't affect the next call.
    So we track directory changes ourselves.
    """
    # Split on && and ; to handle compound commands
    parts = command.replace("&&", ";").split(";")

    for part in parts:
        part = part.strip()
        if part.startswith("cd "):
            target = part[3:].strip()

            # Handle cd ~ (go home)
            if target == "~" or target == "":
                return os.path.expanduser("~")

            # Handle absolute paths
            if os.path.isabs(target):
                return target

            # Handle relative paths
            new_dir = os.path.join(current_dir, target)
            if os.path.isdir(new_dir):
                return os.path.realpath(new_dir)

    return current_dir


def run_all(commands: list, careful: bool = False) -> bool:
    """
    Run a list of commands one by one.

    If careful=True, ask for confirmation before each command.
    Returns True if all commands succeeded, False if any failed.

    The 'working_dir' concept:
    When you run 'cd my-app', the next command needs to run
    inside my-app/. We track this with the working_dir variable.
    """
    from confirm import ask_single_confirmation

    # Start in the current directory
    working_dir = os.getcwd()
    total       = len(commands)
    all_passed  = True

    print()

    for i, cmd_obj in enumerate(commands, 1):
        command     = cmd_obj.get("command", "")
        explanation = cmd_obj.get("explanation", "")

        if not command:
            continue

        # In careful mode, ask before each command
        if careful:
            if not ask_single_confirmation(command):
                print(f"  {Fore.YELLOW}skipped{Style.RESET_ALL}")
                continue

        # Print what we're about to run
        print(
            f"[{i}/{total}] "
            f"{Fore.CYAN}running:{Style.RESET_ALL} "
            f"{Style.BRIGHT}{command}{Style.RESET_ALL}"
        )

        # Run the command
        success, output, error = run_command(command, working_dir)

        # Print output if there is any
        if output.strip():
            # Indent each line of output for readability
            for line in output.strip().split("\n"):
                print(f"        {Style.DIM}{line}{Style.RESET_ALL}")

        if success:
            print(f"        {Fore.GREEN}✓ done{Style.RESET_ALL}")

            # Update working directory if this was a cd command
            working_dir = get_new_directory(command, working_dir)

        else:
            # Command failed — print the error
            print(f"        {Fore.RED}✗ failed{Style.RESET_ALL}")

            if error.strip():
                for line in error.strip().split("\n"):
                    print(f"        {Fore.RED}{line}{Style.RESET_ALL}")

            all_passed = False

            # Ask whether to continue after a failure
            answer = input(
                f"\n  Command failed. "
                f"Continue anyway? [{Fore.GREEN}y{Style.RESET_ALL}/{Fore.RED}n{Style.RESET_ALL}]: "
            ).strip().lower()

            if answer not in ("y", "yes"):
                print(f"\n{Fore.RED}Stopped.{Style.RESET_ALL}")
                return False

        print()

    return all_passed