import subprocess
import os
from colorama import Fore, Style, init

init(autoreset=True)

def run_command(command: str, working_dir: str = None) -> tuple:
    """
    Run a single shell command.
    Returns (success, stdout_text, stderr_text).
    success is True if the command exited with code 0.
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
    We handle compound commands like: mkdir foo && cd foo

    Why is this needed?
    subprocess.run() is stateless. Running 'cd /tmp' in a subprocess
    changes the subprocess's directory, but that subprocess exits
    immediately and the change is lost. We simulate the effect by
    tracking the directory ourselves.
    """
    # Split on && and ; to handle compound commands
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

    If careful=True, ask for confirmation before each individual command.
    Prints clear output for each command including success/failure status.
    Returns True if all commands succeeded, False if any failed.
    """
    working_dir = os.getcwd()
    total       = len(commands)
    all_ok      = True

    print()

    for i, cmd_obj in enumerate(commands, 1):
        command     = cmd_obj.get("command", "")
        explanation = cmd_obj.get("explanation", "")

        if not command:
            continue

        # In careful mode, ask before each command
        if careful:
            answer = input(
                f"  Run: {Style.BRIGHT}{command}{Style.RESET_ALL}  "
                f"[{Fore.GREEN}y{Style.RESET_ALL}/{Fore.YELLOW}s{Style.RESET_ALL}kip/{Fore.RED}n{Style.RESET_ALL}o]: "
            ).strip().lower()

            if answer in ("n", "no"):
                print(f"\n{Fore.RED}Stopped.{Style.RESET_ALL}")
                return False
            if answer in ("s", "skip"):
                print(f"  {Fore.YELLOW}Skipped{Style.RESET_ALL}\n")
                continue

        print(
            f"[{i}/{total}] "
            f"{Fore.CYAN}running:{Style.RESET_ALL} "
            f"{Style.BRIGHT}{command}{Style.RESET_ALL}"
        )

        success, stdout, stderr = run_command(command, working_dir)

        # Print output with indentation for readability
        if stdout.strip():
            for line in stdout.strip().split("\n"):
                print(f"        {Style.DIM}{line}{Style.RESET_ALL}")

        if success:
            print(f"        {Fore.GREEN}✓ done{Style.RESET_ALL}")
            working_dir = extract_new_directory(command, working_dir)
        else:
            print(f"        {Fore.RED}✗ failed{Style.RESET_ALL}")
            if stderr.strip():
                for line in stderr.strip().split("\n"):
                    print(f"        {Fore.RED}{line}{Style.RESET_ALL}")

            all_ok = False
            answer = input(
                f"\n  Command failed. Continue anyway? "
                f"[{Fore.GREEN}y{Style.RESET_ALL}/{Fore.RED}n{Style.RESET_ALL}]: "
            ).strip().lower()

            if answer not in ("y", "yes"):
                print(f"\n{Fore.RED}Stopped.{Style.RESET_ALL}")
                return False

        print()

    return all_ok