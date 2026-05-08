import os
import json
from colorama import Fore, Style, init

init(autoreset=True)

from config import SHELLAI_DIR, PROFILE_PATH

OS_OPTIONS = {
    "1": {"id": "ubuntu",  "name": "Ubuntu / Debian",     "pkg_manager": "apt",    "shell": "bash"},
    "2": {"id": "macos",   "name": "macOS (Homebrew)",     "pkg_manager": "brew",   "shell": "zsh"},
    "3": {"id": "windows", "name": "Windows WSL2",         "pkg_manager": "apt",    "shell": "bash"},
    "4": {"id": "arch",    "name": "Arch / Manjaro",       "pkg_manager": "pacman", "shell": "bash"},
    "5": {"id": "fedora",  "name": "Fedora / RHEL",        "pkg_manager": "dnf",    "shell": "bash"},
}


KNOWN_MODELS = [
    ("phi3:mini",       "2-4 GB RAM  — fast, works on most machines (recommended)"),
    ("llama3.2:3b",     "3-5 GB RAM  — good quality, strong instruction following"),
    ("mistral:7b",      "6-8 GB RAM  — better quality, needs 8GB+ RAM"),
    ("codellama:7b",    "6-8 GB RAM  — code focused, needs 8GB+ RAM"),
]


def profile_exists() -> bool:
    """Returns True if the user has already completed setup."""
    return os.path.exists(PROFILE_PATH)


def load_profile() -> dict:
    """
    Load saved profile from disk.
    Returns empty dict if profile does not exist yet.
    We never crash on a missing file — we just use defaults.
    """
    if not os.path.exists(PROFILE_PATH):
        return {}
    try:
        with open(PROFILE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_profile(profile: dict) -> None:
    """
    Save profile to disk.
    os.makedirs with exist_ok=True creates the folder
    if it doesn't exist yet, without crashing if it does.
    """
    os.makedirs(SHELLAI_DIR, exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def run_setup_wizard() -> dict:
    """
    Show the first-run wizard.
    Asks for OS and preferred Ollama model.
    Returns the completed profile dict.
    """
    print(f"\n{Fore.CYAN}{'─' * 52}")
    print(f"  Welcome to ShellAI!")
    print(f"  Quick one-time setup — takes about 30 seconds.")
    print(f"{'─' * 52}{Style.RESET_ALL}\n")

    # Step 1: Ask for OS
    print("Which operating system are you using?\n")
    for key, opt in OS_OPTIONS.items():
        print(f"  {Fore.CYAN}{key}{Style.RESET_ALL}.  {opt['name']}")
    print()

    while True:
        choice = input("Enter a number (1-5): ").strip()
        if choice in OS_OPTIONS:
            os_choice = OS_OPTIONS[choice]
            break
        print(f"  {Fore.RED}Please enter a number between 1 and 5{Style.RESET_ALL}")

    # Step 2: Ask for Ollama model
    print(f"\nWhich Ollama model do you want to use?\n")
    for i, (model_name, description) in enumerate(KNOWN_MODELS, 1):
        print(f"  {Fore.CYAN}{i}{Style.RESET_ALL}.  {model_name:<20} {Style.DIM}{description}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}5{Style.RESET_ALL}.  Other  {Style.DIM}(type your own model name){Style.RESET_ALL}")
    print()

    while True:
        model_choice = input("Enter a number (1-5): ").strip()
        if model_choice in ("1", "2", "3", "4"):
            selected_model = KNOWN_MODELS[int(model_choice) - 1][0]
            break
        elif model_choice == "5":
            selected_model = input("Enter model name: ").strip()
            if selected_model:
                break
            print(f"  {Fore.RED}Model name cannot be empty{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}Please enter a number between 1 and 5{Style.RESET_ALL}")

    # Build and save the profile
    profile = {
        "os_id":        os_choice["id"],
        "os_name":      os_choice["name"],
        "pkg_manager":  os_choice["pkg_manager"],
        "shell":        os_choice["shell"],
        "ollama_model": selected_model,
    }

    save_profile(profile)

    print(f"\n{Fore.GREEN}Profile saved!{Style.RESET_ALL}")
    print(f"  OS    : {Fore.CYAN}{os_choice['name']}{Style.RESET_ALL}")
    print(f"  Model : {Fore.CYAN}{selected_model}{Style.RESET_ALL}")
    print()
    print(f"{Style.DIM}Make sure Ollama is running before using ShellAI:")
    print(f"  ollama serve &")
    print(f"  ollama pull {selected_model}{Style.RESET_ALL}\n")

    return profile


def get_profile() -> dict:
    """
    Get the current profile, running setup wizard if needed.
    This is the main function other modules call.
    Every run goes through here.
    """
    if not profile_exists():
        return run_setup_wizard()
    return load_profile()


def get_os_context(profile: dict) -> str:
    """
    Build a description string we inject into the AI prompt.
    This tells the model what OS to generate commands for.

    Example output:
      "Ubuntu / Debian, package manager: apt, shell: bash"
    """
    if not profile:
        return "Ubuntu Linux, package manager: apt, shell: bash"
    return (
        f"{profile.get('os_name', 'Ubuntu Linux')}, "
        f"package manager: {profile.get('pkg_manager', 'apt')}, "
        f"shell: {profile.get('shell', 'bash')}"
    )