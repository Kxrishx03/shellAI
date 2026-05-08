import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import COMMANDS_PATH, SIMILARITY_THRESHOLD


def load_dataset() -> list:
    """
    Load commands.json from disk.
    Returns an empty list if the file doesn't exist.
    We never crash on a missing file.
    """
    if not os.path.exists(COMMANDS_PATH):
        return []
    try:
        with open(COMMANDS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def build_searchable_text(entry: dict) -> str:
    """
    Convert a dataset entry into a single string that TF-IDF can search.
    We combine the intent, all tags, and the first word of each command.

    Why include command names?
    Because "git init" in the commands helps match queries like "git init"
    even if the intent description doesn't use those exact words.

    Example output for the git init entry:
    "initialize a new git repository git init setup version control
     new project git add git commit"
    """
    parts = [entry.get("intent", "")]
    parts += entry.get("tags", [])

    for cmd in entry.get("commands", []):
        command = cmd.get("command", "")
        if command:
            # Take just the program name (first word)
            parts.append(command.split()[0])

    return " ".join(parts).lower()


def filter_by_os(dataset: list, os_id: str) -> list:
    """
    Keep only entries that match the user's OS.
    Entries with os="all" are always included.
    Entries with os="ubuntu" are only included for Ubuntu users.
    """
    if not os_id:
        return dataset
    return [
        entry for entry in dataset
        if entry.get("os", "all") in ("all", os_id)
    ]


class LocalEngine:
    """
    Wraps the TF-IDF vectorizer and dataset.

    Why a class instead of just functions?
    Because we build the vectorizer once when the engine is created,
    then reuse it for every query. Building it is the slow part (~50ms).
    Each query after that is just a vector comparison (~1ms).

    If we rebuilt the vectorizer on every query it would be 50x slower.
    """

    def __init__(self, os_id: str = "ubuntu"):
        self.os_id      = os_id
        self.dataset    = []
        self.texts      = []
        self.vectorizer = None
        self.matrix     = None
        self._load()

    def _load(self):
        """Load dataset and build the TF-IDF index."""
        all_data     = load_dataset()
        self.dataset = filter_by_os(all_data, self.os_id)

        if not self.dataset:
            return

        # Build searchable text for each entry
        self.texts = [build_searchable_text(e) for e in self.dataset]

        # TfidfVectorizer learns the vocabulary from our texts
        # ngram_range=(1,2) means we consider both single words AND
        # two-word phrases. "git init" as a phrase is more meaningful
        # than "git" and "init" separately.
        # stop_words="english" removes words like "a", "the", "is"
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english"
        )

        # fit_transform does two things:
        # 1. Learns the vocabulary from all our texts (fit)
        # 2. Converts each text to a numerical vector (transform)
        # The result is a matrix with one row per dataset entry
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def find(self, query: str) -> tuple:
        """
        Find the best matching entry for a query string.

        Returns (entry, confidence) where:
          entry      = the matched dataset entry dict, or None
          confidence = float between 0.0 and 1.0

        If confidence is below SIMILARITY_THRESHOLD we return None
        because the match isn't reliable enough to act on.
        """
        if not self.dataset or self.vectorizer is None:
            return None, 0.0

        # Convert the query to a vector using the same vocabulary
        # we learned from the dataset
        query_vector = self.vectorizer.transform([query.lower()])

        # cosine_similarity returns a value between 0 and 1
        # 1.0 = vectors point in exactly the same direction (perfect match)
        # 0.0 = vectors are completely unrelated
        scores      = cosine_similarity(query_vector, self.matrix)[0]
        best_index  = scores.argmax()
        best_score  = float(scores[best_index])

        if best_score < SIMILARITY_THRESHOLD:
            return None, best_score

        return self.dataset[best_index], best_score

    def is_available(self) -> bool:
        """Returns True if the dataset loaded and has entries."""
        return len(self.dataset) > 0


def get_commands_local(query: str, os_id: str = "ubuntu") -> dict | None:
    """
    Main entry point for other modules.

    Try to find a match in the local dataset.
    Returns a result dict in the same format as ollama_engine.py,
    or None if no confident match found.

    Returning the same format as ollama_engine is intentional.
    The caller (ai.py) doesn't need to know where the answer came from.
    """
    engine = LocalEngine(os_id)

    if not engine.is_available():
        return None

    entry, confidence = engine.find(query)

    if entry is None:
        return None

    return {
        "commands":   entry.get("commands", []),
        "summary":    entry.get("summary", ""),
        "source":     "local",
        "confidence": round(confidence, 2)
    }