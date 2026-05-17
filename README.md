<p align="center">
  <h1 align="center">🤖 ShellAI</h1>
  <p align="center">Run developer tasks by describing them in plain English — powered by local AI</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/powered_by-ollama-green.svg" alt="Ollama">
  <img src="https://img.shields.io/badge/works_offline-yes-brightgreen.svg" alt="Offline">
  <img src="https://img.shields.io/badge/no_api_key-required-orange.svg" alt="No API Key">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL2-lightblue.svg" alt="Platform">
</p>

---

```bash
shellai initialize a react project with typescript and tailwind
shellai merge branch feature/login into main with message "add authentication"
shellai find all files larger than 100mb in my home directory
shellai set up postgresql and create a database called myapp
```

---

## What is ShellAI

ShellAI is a local-first CLI tool that turns plain English descriptions into
shell commands and runs them — with your confirmation before anything executes.

You describe what you want. ShellAI figures out the exact commands, shows you
everything clearly, asks for confirmation, then runs them one by one with live output.

**Everything runs on your own machine.**
No API keys. No internet required after setup. No usage limits. No data sent anywhere.

---

## How it works

```
You type:   shellai initialize a react project with typescript

  Step 1 — Checks local SQLite database instantly
            ✓ Found in local database (confidence: 91%)

  Step 2 — Shows you the full plan

            ┌─ Plan ──────────────────────────────────────────────────
            │  Create a new React project with TypeScript configured
            │
            │  1. npx create-react-app my-app --template typescript
            │     → Creates a new React project with TypeScript
            │
            │  2. cd my-app
            │     → Enter the project directory
            │
            │  3. npm start
            │     → Start the development server on localhost:3000
            └─────────────────────────────────────────────────────────

  Step 3 — Fills in what it needs from you
            Project name: my-app

  Step 4 — Asks for confirmation
            Run 3 commands? [yes / no / edit]:

  Step 5 — Runs each command with live output
            [1/3] running: npx create-react-app my-app --template typescript
                  ✓ done
```

---

## What's new in this version

This release is a significant rewrite focused on speed, reliability, and simplicity:

- **Removed scikit-learn entirely** — replaced with pure Python keyword search. No heavy ML dependency, faster cold start, identical results for this use case.
- **SQLite replaces JSON files** — commands and pending entries now live in a proper database at `~/.shellai/commands.db`. Faster lookups, concurrent-safe, survives crashes cleanly.
- **Two-level cache** — memory cache (instant, lives for the current session) sits in front of SQLite (fast, persists forever). Most repeated queries never touch disk.
- **Intent detection** — questions, greetings, and non-command input are handled gracefully instead of being sent to Ollama.
- **Streaming output** — you see Ollama tokens arrive as they're generated with an animated spinner. No more staring at a blank screen.
- **Retry logic on timeout** — Ollama retries up to 3 times with a delay so a cold-starting model doesn't cause an immediate failure.
- **`display.py`** — all terminal output is now routed through a single module for consistent, clean formatting.
- **Rewritten install and uninstall scripts** — HTTPS clone (no GitHub login ever needed), automatic Ollama startup, PATH set correctly, full uninstall with optional model and Ollama removal.

---

## Features

- **Plain English input** — describe intent, not syntax
- **Instant local database** — common tasks answered in milliseconds from SQLite
- **Two-level cache** — memory cache + SQLite, same query never hits Ollama twice
- **Local AI fallback** — powered by Ollama, runs entirely on your machine
- **Streaming output** — watch tokens arrive in real time with a live spinner
- **Fully offline** — no internet needed after the one-time model download
- **No API keys** — ever
- **Intent detection** — questions and greetings handled gracefully, not sent to the model
- **Confirmation gate** — you see every command before anything runs
- **Placeholder detection** — asks for your name, email, project name before running
- **Edit mode** — pick exactly which commands from the plan to run
- **Three-level safety system** — blocks dangerous commands, warns on destructive ones
- **Self-improving** — learns from every Ollama response and grows smarter over time
- **OS-aware** — generates the right commands for Ubuntu, macOS, Arch, Fedora, WSL2

---

## Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.8 or higher |
| Ollama | Latest version |
| RAM | 4 GB available minimum |
| Platform | Linux, macOS, or Windows WSL2 |

No scikit-learn. No numpy. No heavy dependencies.

---

## Installation

### One-line install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/Kxrishx03/shellai/master/install.sh | bash
```

This single command will:
- Check your Python version
- Install Ollama if not already installed
- Clone ShellAI via HTTPS — **no GitHub account, password, or SSH key needed**
- Set up the Python virtual environment and install dependencies
- Create the `shellai` command so it works from anywhere in your terminal
- Pull the default AI model (phi3:mini, ~2.3 GB, one-time download)

After it finishes, open a new terminal and run:

```bash
shellai --help
```

ShellAI runs a one-time setup wizard on first launch to ask for your OS
and preferred model. After that, it remembers your preferences.

> **Prefer SSH?** If you already have GitHub SSH keys configured:
> ```bash
> curl -sSL https://raw.githubusercontent.com/Kxrishx03/shellai/master/install.sh | bash -s -- --ssh
> ```
> The installer will test your SSH connection first and give clear instructions if it fails.

---

### Manual installation

**Step 1 — Install Ollama**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

> **WSL2 users:** If you see a `zstd` error during install:
> ```bash
> sudo apt update && sudo apt install -y zstd
> curl -fsSL https://ollama.com/install.sh | sh
> ```

> **macOS users:**
> ```bash
> brew install ollama
> ```

**Step 2 — Pull a model**

Check available RAM first:
```bash
free -h   # look at the "available" column
```

Then pull the right model for your machine:

```bash
# 4 GB+ RAM — recommended for most machines
ollama pull phi3:mini

# 8 GB+ RAM — better response quality
ollama pull mistral:7b

# Under 4 GB RAM — lightest option
ollama pull tinyllama
```

**Step 3 — Clone and install ShellAI**

```bash
git clone https://github.com/Kxrishx03/shellai.git
cd shellai
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Step 4 — Start Ollama and run**

```bash
# Start Ollama if not already running
ollama serve &

shellai --help
```

---

### Install via pip

```bash
pip install git+https://github.com/Kxrishx03/shellai.git
```

---

## Uninstalling

```bash
curl -sSL https://raw.githubusercontent.com/Kxrishx03/shellai/master/uninstall.sh | bash
```

The uninstaller asks for confirmation before removing anything and lets you keep
your database and profile if you plan to reinstall later.

**Optional flags:**

```bash
# Also delete the AI model (~2.3 GB freed)
bash uninstall.sh --remove-model

# Also remove Ollama from your system entirely
bash uninstall.sh --remove-ollama

# Both at once
bash uninstall.sh --remove-model --remove-ollama
```

---

## Ollama is already running

If you see `address already in use` when starting Ollama, it is running as a
system service. This is normal — just verify and continue:

```bash
curl http://localhost:11434
# Expected: Ollama is running
```

---

## Usage

```bash
shellai <describe what you want to do>
shellai --careful <describe what you want to do>
```

### Examples

**Git workflows**
```bash
shellai initialize a new git repository
shellai configure git username and email
shellai create and switch to a new branch called feature/auth
shellai merge branch feature/login into main with message "add login"
shellai undo the last commit but keep the changes
shellai show all branches including remote
```

**Project setup**
```bash
shellai initialize a react project with typescript
shellai initialize a react project with typescript and tailwind
shellai set up a python virtual environment and install django
shellai create a new node project with express and nodemon
shellai scaffold a fastapi project with uvicorn
```

**File management**
```bash
shellai find all files larger than 100mb
shellai find all files containing the text TODO
shellai compress the dist folder into a tar.gz
shellai sync two directories with rsync
shellai find and delete all node_modules folders
shellai show disk usage of each folder in current directory
shellai watch a log file in real time
shellai compare two files and show differences
```

**Docker**
```bash
shellai build a docker image called myapp
shellai run docker compose in the background
shellai stop all running docker containers
shellai remove all unused docker images
shellai show logs for a running container
```

**Database**
```bash
shellai install postgresql
shellai create a postgresql database called myapp
shellai dump the myapp database to a backup file
shellai restore a postgresql database from backup
```

**System**
```bash
shellai check which process is using port 3000 and kill it
shellai check available disk space
shellai generate an ssh key pair for github
shellai show cpu and memory usage
```

---

## All flags

| Flag | Description |
|------|-------------|
| `--careful` | Confirm each individual command before it runs |
| `--setup` | Re-run the first-time setup wizard |
| `--review` | Review and approve pending dataset entries |
| `--stats` | Show database statistics and most-used commands |
| `--export-seed` | Export your database to `seed.sql` for sharing |
| `--set-model <name>` | Switch Ollama model (e.g. `mistral:7b`) |
| `--help` | Show help message |
| `--version` | Show version number |

---

## Confirmation options

When ShellAI shows you the plan, you have three choices:

| Input | What happens |
|-------|-------------|
| `y` or `yes` | Run all commands |
| `n` or `no` | Cancel everything |
| `e` or `edit` | Choose which commands to run |

**Edit mode:**
```
Run 4 commands? [yes / no / edit]: e

Enter the numbers of commands to run (e.g. 1 3 4), or 'all':
  1. npx create-react-app my-app --template typescript
  2. cd my-app
  3. npm install -D tailwindcss postcss autoprefixer
  4. npx tailwindcss init -p
> 1 2
```

---

## Changing models

```bash
ollama pull mistral:7b
shellai --set-model mistral:7b
```

| Model | RAM needed | Speed | Notes |
|-------|-----------|-------|-------|
| `tinyllama` | 1–2 GB | Very fast | Lower quality |
| `phi3:mini` | 2–4 GB | Fast | **Recommended default** |
| `llama3.2:3b` | 3–5 GB | Fast | Strong instruction following |
| `mistral:7b` | 6–8 GB | Medium | Better quality |
| `codellama:7b` | 6–8 GB | Medium | Better for code tasks |

> **First run is slow.** On cold start, phi3:mini can take 60–120 seconds to load
> into memory. ShellAI retries automatically up to 3 times — you will see a
> `Retrying (2/3)…` message rather than an immediate failure.
> Pre-warm if you're impatient: `ollama run phi3:mini 'hi'`

---

## Safety

ShellAI runs a three-level safety check on every command before you are asked to confirm.

**Level 1 — Blocked (never runs)**
Commands that could destroy your system or expose security risks are refused
regardless of confirmation. Examples: `rm -rf /`, fork bombs, writing directly
to disk devices, piping internet content to bash.

**Level 2 — Warning (requires typing `yes` in full)**
Destructive but legitimate commands get a red warning and require the full word
`yes` before running. Examples: `rm -rf ./old-project`, `DROP DATABASE`, `mkfs`.

**Level 3 — Notice (informational)**
Commands using `sudo` or touching sensitive paths show a dim notice.

**Placeholder validation**
When a command needs your email, port number, or project name, ShellAI validates
the value before proceeding so you can't accidentally pass the wrong type.

---

## How the local database grows

```
You ask something not in the local database
            ↓
Ollama generates the answer (streamed to your terminal)
            ↓
ShellAI saves it to a pending queue automatically
            ↓
You run: shellai --review
            ↓
You approve or reject each entry
            ↓
Approved entries join the SQLite database permanently
            ↓
Same task asked again — instant answer, no model needed
```

The more you use ShellAI, the more queries it answers from the local database
without needing the AI at all. Run `shellai --stats` to see how many commands
are stored and which ones get used most.

```bash
shellai --review    # review pending entries
shellai --stats     # database statistics
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'db'` (or any local module)**

The package was installed without all modules listed. Reinstall:
```bash
cd shellai
source venv/bin/activate
pip install -e .
```

**`Ollama is not running`**
```bash
ollama serve &
# or on Linux with systemd:
sudo systemctl start ollama
```

**`Ollama timed out` on first use**

The model is still loading into memory. ShellAI retries automatically.
If all retries fail, pre-warm the model and try again:
```bash
ollama run phi3:mini 'hi'
# wait for a response, then retry your command
```

**`Model not downloaded`**
```bash
ollama pull phi3:mini
```

**`command not found: shellai` after manual install**
```bash
source venv/bin/activate
pip install -e .
export PATH="$HOME/.local/bin:$PATH"
```

**`zstd` error during Ollama install on WSL2**
```bash
sudo apt update && sudo apt install -y zstd
curl -fsSL https://ollama.com/install.sh | sh
```

**Model returns invalid JSON**

Larger models follow format instructions more reliably:
```bash
shellai --set-model mistral:7b
```

**Responses are slow**

This is normal for CPU-only machines running local AI models.
- Switch to a smaller model: `shellai --set-model tinyllama`
- Run `shellai --review` regularly to grow your local database — approved entries
  answer instantly on future queries with no model involved at all.

---

## Running tests

```bash
pip install pytest pytest-cov
pytest tests/ -v
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Project structure

```
shellai/
├── main.py              Entry point and CLI orchestrator
├── ai.py                Routes queries: memory cache → SQLite → Ollama
├── db.py                SQLite database, two-level cache, pending queue
├── ollama_engine.py     Ollama streaming client with retry logic
├── intent.py            Detects questions, greetings, non-command input
├── display.py           All terminal output — consistent formatting
├── placeholders.py      Detects and fills {{PLACEHOLDER}} tokens
├── profiles.py          OS and model preferences
├── confirm.py           Shows plan and handles confirmation
├── executor.py          Runs commands via subprocess with live output
├── safety.py            Three-level safety checking system
├── dataset_builder.py   Pending review queue management
├── config.py            Paths, thresholds, constants
├── install.sh           One-line installer (HTTPS, no login needed)
├── uninstall.sh         Clean uninstaller with optional flags
│
├── data/
│   ├── commands.json    Curated seed dataset
│   └── seed.sql         Pre-built database for instant first run
│
└── tests/
    ├── test_local_engine.py
    ├── test_safety.py
    ├── test_placeholders.py
    ├── test_dataset_builder.py
    └── test_executor.py
```

---

## Contributing

Contributions are welcome.

**Adding commands to the dataset**

The fastest way to help is to add entries to `data/commands.json`:

```json
{
  "intent": "description of what the user wants to do",
  "tags": ["relevant", "keywords"],
  "os": "all",
  "commands": [
    {
      "command": "the exact shell command",
      "explanation": "one sentence explaining what this does"
    }
  ],
  "summary": "one sentence describing what all these commands accomplish"
}
```

Use `"os": "all"` for cross-platform commands, `"os": "ubuntu"` or
`"os": "macos"` for platform-specific ones.

For commands that need user-specific values, use placeholders:
```json
"command": "git config --global user.name \"{{YOUR_NAME}}\""
```

**Before opening a pull request:**
1. Run `pytest tests/ -v` — all tests must pass
2. Add tests for any new functionality
3. Never commit credentials, API keys, or personal data

---

## Privacy

- All queries go to your local Ollama model — nothing leaves your machine
- No telemetry, no analytics, no usage tracking of any kind
- Your database and profile live at `~/.shellai/` on your own machine
- No accounts, no sign-ups, no external servers ever

---

## License

MIT — do whatever you want with it.

---

## Acknowledgements

Built with [Ollama](https://ollama.com), [colorama](https://pypi.org/project/colorama/),
and [requests](https://pypi.org/project/requests/).

Inspired by the universal developer experience of forgetting what flags `tar` takes.

---

<p align="center">
  Made by <a href="https://github.com/Kxrishx03">Karishma Mandal</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Kxrishx03/shellai/issues">Report a bug</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Kxrishx03/shellai/issues">Request a feature</a>
</p>