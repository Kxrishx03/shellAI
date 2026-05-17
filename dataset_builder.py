import db
from colorama import Fore, Style, init

init(autoreset=True)


def save_pending(query: str, result: dict, os_id: str) -> bool:
    """Save Ollama result to pending table. Returns True if saved."""
    return db.save_to_pending(query, result, os_id)


def count_pending() -> int:
    """How many entries are waiting for review."""
    return db.count_pending()


def run_review() -> None:
    """
    Interactive review session for pending entries.
    Approved entries go into the live commands table immediately.
    Rejected entries are deleted permanently.
    Skipped entries stay in pending for next time.
    """
    entries = db.get_pending_entries()

    if not entries:
        print(f"\n  {Fore.GREEN}No pending entries to review.{Style.RESET_ALL}")
        print(
            f"  {Style.DIM}Entries appear here automatically when "
            f"Ollama answers a query not in the database.{Style.RESET_ALL}\n"
        )
        return

    total = len(entries)
    approved = 0
    rejected = 0
    skipped = 0

    print(f"\n  {Fore.CYAN}Reviewing {total} pending "
          f"entr{'y' if total == 1 else 'ies'}{Style.RESET_ALL}")
    print(f"  Approve good ones to add them to your database.\n")

    for i, entry in enumerate(entries, 1):
        print(f"  {Fore.CYAN}{i}/{total}{Style.RESET_ALL}  "
              f"{Style.BRIGHT}{entry['intent']}{Style.RESET_ALL}  "
              f"{Style.DIM}({entry['os']}){Style.RESET_ALL}")

        for j, cmd in enumerate(entry["commands"], 1):
            print(f"       {j}. {Style.BRIGHT}{cmd.get('command', '')}{Style.RESET_ALL}")
            print(f"          {Style.DIM}{cmd.get('explanation', '')}{Style.RESET_ALL}")
            if cmd.get("warning"):
                print(f"          {Fore.YELLOW}⚠  {cmd['warning']}{Style.RESET_ALL}")

        print()

        while True:
            choice = input(
                f"  [{Fore.GREEN}a{Style.RESET_ALL}]pprove  "
                f"[{Fore.RED}r{Style.RESET_ALL}]eject  "
                f"[{Fore.YELLOW}s{Style.RESET_ALL}]kip  "
                f"[{Fore.CYAN}q{Style.RESET_ALL}]uit: "
            ).strip().lower()

            if choice in ("a", "approve"):
                db.approve_pending(entry["id"])
                approved += 1
                print(f"  {Fore.GREEN}✓ Added to database{Style.RESET_ALL}\n")
                break
            elif choice in ("r", "reject"):
                db.reject_pending(entry["id"])
                rejected += 1
                print(f"  {Fore.RED}✗ Rejected{Style.RESET_ALL}\n")
                break
            elif choice in ("s", "skip"):
                skipped += 1
                print(f"  {Fore.YELLOW}→ Skipped (stays pending){Style.RESET_ALL}\n")
                break
            elif choice in ("q", "quit"):
                print(f"\n  Stopped early.\n")
                break
            else:
                print("  Please type a, r, s, or q")

        if choice in ("q", "quit"):
            break

    print(f"  Approved: {Fore.GREEN}{approved}{Style.RESET_ALL}  "
          f"Rejected: {Fore.RED}{rejected}{Style.RESET_ALL}  "
          f"Skipped: {Fore.YELLOW}{skipped}{Style.RESET_ALL}\n")