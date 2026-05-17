import os
import json
from colorama import Fore, Style, init
from config import SHELLAI_DIR, PROFILE_PATH

init(autoreset=True)

OS_OPTIONS = {
    "1": {"id": "ubuntu",  "name": "Ubuntu / Debian",      "pkg_manager": "apt",    "shell": "bash"},
    "2": {"id": "macos",   "name": "macOS (Homebrew)",      "pkg_manager": "brew",   "shell": "zsh"},
    "3": {"id": "windows", "name": "Windows WSL2",          "pkg_manager": "apt",    "shell": "bash"},
    "4": {"id": "arch",    "name": "Arch / Manjaro",        "pkg_manager": "pacman", "shell": "bash"},
    "5": {"id": "fedora",  "name": "Fedora / RHEL / CentOS","pkg_manager": "dnf",    "shell": "bash"},
}

KNOWN_MODELS = [
    ("phi3:mini",    "2-4 GB RAM — fast, recommended for most machines"),
    ("llama3.2:3b",  "3-5 GB RAM — good quality, strong instruction following"),
    ("mistral:7b",   "6-8 GB RAM — better quality, needs 8GB+ RAM"),
    ("codellama:7b", "6-8 GB RAM — focused on code tasks"),
]


def profile_exists() -> bool:
    return os.path.exists(PROFILE_PATH)


def load_profile() -> dict:
    if not os.path.exists(PROFILE_PATH):
        return {}
    try:
        with open(PROFILE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_profile(profile: dict) -> None:
    os.makedirs(SHELLAI_DIR, exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def run_setup_wizard() -> dict:
    """Show first-run setup wizard. Returns completed profile dict."""
    print(f"\n  {Fore.CYAN}Welcome to ShellAI!{Style.RESET_ALL}")
    print(f"  Quick one-time setup.\n")

    # OS selection
    print("  Which operating system are you using?\n")
    for key, opt in OS_OPTIONS.items():
        print(f"  {Fore.CYAN}{key}{Style.RESET_ALL}.  {opt['name']}")
    print()

    while True:
        choice = input("  Enter a number (1-5): ").strip()
        if choice in OS_OPTIONS:
            os_choice = OS_OPTIONS[choice]
            break
        print(f"  {Fore.RED}Please enter a number between 1 and 5{Style.RESET_ALL}")

    # Model selection
    print(f"\n  Which Ollama model do you want to use?\n")
    for i, (model_name, description) in enumerate(KNOWN_MODELS, 1):
        print(f"  {Fore.CYAN}{i}{Style.RESET_ALL}.  {model_name:<20} {Style.DIM}{description}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}5{Style.RESET_ALL}.  Other  {Style.DIM}(enter your own model name){Style.RESET_ALL}")
    print()

    while True:
        model_choice = input("  Enter a number (1-5): ").strip()
        if model_choice in ("1", "2", "3", "4"):
            selected_model = KNOWN_MODELS[int(model_choice) - 1][0]
            break
        elif model_choice == "5":
            selected_model = input("  Model name: ").strip()
            if selected_model:
                break
            print(f"  {Fore.RED}Model name cannot be empty{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}Please enter a number between 1 and 5{Style.RESET_ALL}")

    profile = {
        "os_id":        os_choice["id"],
        "os_name":      os_choice["name"],
        "pkg_manager":  os_choice["pkg_manager"],
        "shell":        os_choice["shell"],
        "ollama_model": selected_model,
    }

    save_profile(profile)

    print(f"\n  {Fore.GREEN}Profile saved!{Style.RESET_ALL}")
    print(f"  OS:    {Fore.CYAN}{os_choice['name']}{Style.RESET_ALL}")
    print(f"  Model: {Fore.CYAN}{selected_model}{Style.RESET_ALL}\n")

    return profile


def get_profile() -> dict:
    """Get profile, running setup wizard if this is the first launch."""
    if not profile_exists():
        return run_setup_wizard()
    return load_profile()


def get_os_context(profile: dict) -> str:
    """Build OS description string for injection into AI prompt."""
    if not profile:
        return "Ubuntu Linux, package manager: apt, shell: bash"
    return (
        f"{profile.get('os_name', 'Ubuntu Linux')}, "
        f"package manager: {profile.get('pkg_manager', 'apt')}, "
        f"shell: {profile.get('shell', 'bash')}"
    )