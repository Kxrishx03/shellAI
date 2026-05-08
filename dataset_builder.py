import json
import os
import re
from datetime import datetime
from colorama import Fore, Style, init
from config import COMMANDS_PATH, PENDING_PATH, SHELLAI_DIR

init(autoreset=True)

DUPLICATE_THRESHOLD = 0.65  


def load_json(path: str, default):
    """Load a JSON file. Return default if file missing or broken."""
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_json(path: str, data) -> None:
    """Save data to JSON file, creating parent directories if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def extract_tags(intent: str) -> list:
    """
    Auto-generate tags from an intent string.
    We just pull out meaningful words — anything not in our stop list.

    Why generate tags automatically?
    Because the TF-IDF engine uses tags during matching.
    More tags = better match coverage = fewer Ollama calls.
    """
    stop_words = {
        "a", "an", "the", "and", "or", "for", "to", "in", "with",
        "of", "on", "at", "by", "from", "into", "how", "what",
        "my", "new", "all", "set", "up", "i", "want", "need"
    }
    words  = re.findall(r'[a-z0-9]+', intent.lower())
    tags   = [w for w in words if w not in stop_words and len(w) > 2]

    # Remove duplicates while preserving order
    seen, unique = set(), []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return unique


def word_overlap(text_a: str, text_b: str) -> float:
    """
    Calculate similarity between two strings based on shared words.
    Uses Jaccard similarity: size of intersection / size of union.

    Returns 0.0 (completely different) to 1.0 (identical words).
    We use this only for duplicate detection — it is fast and simple.
    """
    words_a = set(re.findall(r'[a-z0-9]+', text_a.lower()))
    words_b = set(re.findall(r'[a-z0-9]+', text_b.lower()))

    if not words_a or not words_b:
        return 0.0

    return len(words_a & words_b) / len(words_a | words_b)


def is_duplicate(intent: str, os_id: str) -> bool:
    """
    Check if a very similar entry already exists in commands.json
    or in pending.json. We check both so we don't accumulate
    ten near-identical pending entries for the same task.
    """
    existing = load_json(COMMANDS_PATH, [])
    pending  = load_json(PENDING_PATH, [])

    for entry in existing + pending:
        entry_os = entry.get("os", "all")
        if entry_os not in ("all", os_id) and os_id not in ("all", entry_os):
            continue
        if word_overlap(intent, entry.get("intent", "")) >= DUPLICATE_THRESHOLD:
            return True

    return False


def build_entry(query: str, result: dict, os_id: str) -> dict:
    """
    Convert a raw Ollama result into a structured dataset entry
    ready for commands.json.

    We add os, tags, and metadata fields that the raw result lacks.
    The _meta field is stripped before saving to commands.json —
    it is only for tracking purposes in pending.json.
    """
    intent   = query.strip().lower()
    commands = []

    for cmd in result.get("commands", []):
        clean = {
            "command":     cmd.get("command", ""),
            "explanation": cmd.get("explanation", "")
        }
        if "warning" in cmd:
            clean["warning"] = cmd["warning"]
        commands.append(clean)

    return {
        "intent":   intent,
        "tags":     extract_tags(intent),
        "os":       os_id,
        "commands": commands,
        "summary":  result.get("summary", ""),
        "_meta": {
            "added_at":       datetime.now().isoformat(),
            "source":         result.get("source", "ollama"),
            "original_query": query
        }
    }


def save_pending(query: str, result: dict, os_id: str) -> bool:
    """
    Save an Ollama response to the pending review queue.
    Called automatically after every Ollama response.
    The user sees nothing — this happens silently in the background.

    Returns True if saved, False if skipped (duplicate or empty).
    """
    if not result.get("commands"):
        return False

    if is_duplicate(query, os_id):
        return False

    entry   = build_entry(query, result, os_id)
    pending = load_json(PENDING_PATH, [])
    pending.append(entry)
    save_json(PENDING_PATH, pending)
    return True


def count_pending() -> int:
    """How many entries are waiting for review."""
    return len(load_json(PENDING_PATH, []))


def show_entry(entry: dict, index: int, total: int) -> None:
    """Print one pending entry in a readable format."""
    intent   = entry.get("intent", "")
    os_id    = entry.get("os", "all")
    commands = entry.get("commands", [])
    added    = entry.get("_meta", {}).get("added_at", "")[:10]

    print(f"\n{Fore.CYAN}Entry {index} of {total}{Style.RESET_ALL}  {Style.DIM}(added {added}){Style.RESET_ALL}")
    print(f"  Intent  : {Style.BRIGHT}{intent}{Style.RESET_ALL}")
    print(f"  OS      : {os_id}")
    print(f"  Commands:")

    for i, cmd in enumerate(commands, 1):
        print(f"\n    {i}. {Style.BRIGHT}{cmd.get('command', '')}{Style.RESET_ALL}")
        print(f"       {Style.DIM}→ {cmd.get('explanation', '')}{Style.RESET_ALL}")
        if "warning" in cmd:
            print(f"       {Fore.RED}⚠  {cmd['warning']}{Style.RESET_ALL}")


def ask_decision() -> str:
    """Ask what to do with a pending entry. Returns 'approve', 'reject', 'skip', or 'quit'."""
    while True:
        answer = input(
            f"\n  [{Fore.GREEN}a{Style.RESET_ALL}]pprove  "
            f"[{Fore.RED}r{Style.RESET_ALL}]eject  "
            f"[{Fore.YELLOW}s{Style.RESET_ALL}]kip  "
            f"[{Fore.CYAN}q{Style.RESET_ALL}]uit: "
        ).strip().lower()

        if answer in ("a", "approve"):   return "approve"
        if answer in ("r", "reject"):    return "reject"
        if answer in ("s", "skip"):      return "skip"
        if answer in ("q", "quit"):      return "quit"
        print("  Please type a, r, s, or q")


def run_review() -> None:
    """
    Interactive review session for pending entries.
    Approved entries are added to commands.json.
    Rejected entries are deleted.
    Skipped entries stay in pending for later.
    """
    pending = load_json(PENDING_PATH, [])

    if not pending:
        print(f"\n{Fore.GREEN}No pending entries to review.{Style.RESET_ALL}")
        print(f"{Style.DIM}Entries appear here automatically when Ollama answers queries.{Style.RESET_ALL}\n")
        return

    total    = len(pending)
    approved = []
    skipped  = []

    print(f"\n{Fore.CYAN}{'─' * 52}")
    print(f"  Reviewing {total} pending entr{'y' if total == 1 else 'ies'}")
    print(f"  Approve good ones to grow your local database.")
    print(f"{'─' * 52}{Style.RESET_ALL}")

    for i, entry in enumerate(pending, 1):
        show_entry(entry, i, total)
        decision = ask_decision()

        if decision == "approve":
            approved.append(entry)
            print(f"  {Fore.GREEN}✓ Approved{Style.RESET_ALL}")
        elif decision == "reject":
            print(f"  {Fore.RED}✗ Rejected{Style.RESET_ALL}")
        elif decision == "skip":
            skipped.append(entry)
            print(f"  {Fore.YELLOW}→ Skipped (stays in pending){Style.RESET_ALL}")
        elif decision == "quit":
            # Everything not yet reviewed stays in pending
            skipped.extend(pending[i:])
            print(f"\n{Fore.YELLOW}Review paused.{Style.RESET_ALL}")
            break

    # Merge approved entries into commands.json
    if approved:
        # Strip _meta before saving — it is not part of the dataset format
        def strip_meta(e):
            c = dict(e)
            c.pop("_meta", None)
            return c

        dataset = load_json(COMMANDS_PATH, [])
        dataset.extend([strip_meta(e) for e in approved])
        save_json(COMMANDS_PATH, dataset)

    # Write skipped entries back to pending
    save_json(PENDING_PATH, skipped)

    print(f"\n  Approved : {Fore.GREEN}{len(approved)}{Style.RESET_ALL}")
    print(f"  Skipped  : {Fore.YELLOW}{len(skipped)}{Style.RESET_ALL} (still in pending)\n")