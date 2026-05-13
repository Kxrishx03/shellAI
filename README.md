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

  Step 1 — Checks local database instantly
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

## Features

- **Plain English input** — describe intent, not syntax
- **Instant local database** — common tasks answered in milliseconds from a curated dataset
- **Local AI fallback** — powered by Ollama, runs entirely on your machine
- **Fully offline** — no internet needed after the one-time model download
- **No API keys** — ever
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

---

## Installation

### One-line install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/Kxrishx03/shellai/main/install.sh | bash
```

This single command will:
- Check your Python version
- Install Ollama if not already installed
- Clone ShellAI and set up the Python environment
- Create the `shellai` command so it works from anywhere
- Pull the default AI model (phi3:mini, ~2.3 GB one-time download)

After it finishes, restart your terminal and run:

```bash
shellai --help
```

ShellAI runs a one-time setup wizard on first launch to ask for your OS
and preferred model. That is it — you are ready to go.

---

### Manual installation

If you prefer to install step by step:

**Step 1 — Install Ollama**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

> **WSL2 users:** If you see a `zstd` error, run this first:
> ```bash
> sudo apt update && sudo apt install -y zstd
> curl -fsSL https://ollama.com/install.sh | sh
> ```

> **macOS users:**
> ```bash
> brew install ollama
> ```

**Step 2 — Pull a model**

Check your available RAM first:
```bash
free -h   # look at the "available" column
```

Then pull the right model for your machine:

```bash
# 4 GB+ available RAM — recommended for most machines
ollama pull phi3:mini

# 8 GB+ available RAM — better quality responses
ollama pull mistral:7b

# Minimal RAM — fastest but lower quality
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

**Step 4 — Start Ollama and run ShellAI**

```bash
# Ollama usually starts automatically after install
# If not, start it manually:
ollama serve &

# Run ShellAI
shellai --help
```

---

### Install directly from GitHub via pip

```bash
pip install git+https://github.com/Kxrishx03/shellai.git
```

---

## Ollama already running error

If you see `address already in use` when starting Ollama, it is already running
as a system service. This is completely normal — just continue:

```bash
# Verify Ollama is running
curl http://localhost:11434
# Should return: Ollama is running
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
```

**Project setup**
```bash
shellai initialize a react project with typescript
shellai initialize a react project with typescript and tailwind
shellai set up a python virtual environment and install django
shellai create a new node project with express and nodemon
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
```

**Database**
```bash
shellai install postgresql
shellai create a postgresql database called myapp
shellai dump the myapp database to a backup file
```

**System**
```bash
shellai check which process is using port 3000 and kill it
shellai check available disk space
shellai generate an ssh key pair for github
```

---

## All Flags

| Flag | Description |
|------|-------------|
| `--careful` | Confirm each individual command before it runs |
| `--setup` | Re-run the first-time setup wizard |
| `--review` | Review and approve pending dataset entries |
| `--set-model <name>` | Switch Ollama model |
| `--help` | Show help message |
| `--version` | Show version number |

---

## Confirmation Options

When ShellAI shows you the plan, you have three choices:

| Type | What happens |
|------|-------------|
| `y` or `yes` | Run all commands |
| `n` or `no` | Cancel everything |
| `e` or `edit` | Choose which commands to run |

**Edit mode example:**
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
# Pull a new model first
ollama pull mistral:7b

# Tell ShellAI to use it
shellai --set-model mistral:7b
```

| Model | RAM needed | Speed | Notes |
|-------|-----------|-------|-------|
| `tinyllama` | 1–2 GB | Very fast | Lower quality |
| `phi3:mini` | 2–4 GB | Fast | **Recommended default** |
| `llama3.2:3b` | 3–5 GB | Fast | Strong instruction following |
| `mistral:7b` | 6–8 GB | Medium | Better quality |
| `codellama:7b` | 6–8 GB | Medium | Better for code tasks |

---

## Safety

ShellAI has a three-level safety system that runs on every command
before you are even asked to confirm.

**Level 1 — Blocked (never runs)**
Commands that could destroy your OS or expose security risks
are refused entirely regardless of confirmation.

Examples of what is blocked:
- `rm -rf /` — deletes the entire operating system
- Fork bombs — crash your system
- Writing directly to disk devices
- Piping internet content directly to bash

**Level 2 — Warning (requires typing `yes` in full)**
Destructive but legitimate commands get a red warning and
require you to type the full word `yes` before running.

Examples: `rm -rf ./old-project`, `DROP DATABASE`, `mkfs`

**Level 3 — Notice (informational)**
Commands using `sudo` or touching sensitive system paths
show a dim notice so you are aware.

**Placeholder validation**
When a command needs your email, port number, or project name,
ShellAI validates the value before proceeding — it will not let
you enter a file path where a name is expected.

---

## How the local database grows

```
You ask something not in the local database
            ↓
Ollama generates the answer
            ↓
ShellAI saves it to a pending queue automatically
            ↓
You run: shellai --review
            ↓
You approve or reject each pending entry
            ↓
Approved entries join the local database permanently
            ↓
Same task asked next time — instant answer, no model needed
```

The more you use ShellAI, the faster it becomes.

```bash
shellai --review
```

---

## Troubleshooting

**`Ollama is not running`**
```bash
ollama serve &
# or on Linux:
sudo systemctl start ollama
```

**`address already in use` when starting Ollama**
Ollama is already running as a system service. Run `curl http://localhost:11434`
to confirm. If it says `Ollama is running` you are fine — just use ShellAI normally.

**`Model not downloaded`**
```bash
ollama pull phi3:mini
```

**`command not found: shellai` after manual install**
```bash
source venv/bin/activate
pip install -e .
```

**`zstd` error during Ollama install on WSL2**
```bash
sudo apt update && sudo apt install -y zstd
curl -fsSL https://ollama.com/install.sh | sh
```

**Model returns invalid JSON**
Switch to a larger model — bigger models follow format instructions better:
```bash
shellai --set-model mistral:7b
```

**Responses are slow**
This is normal for CPU-only machines running local LLMs.
- Use a smaller model: `shellai --set-model tinyllama`
- Run `shellai --review` regularly — approved entries answer instantly next time
- The more you use ShellAI, the more queries hit the local database

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
├── main.py              Entry point and orchestrator
├── ai.py                Routes queries to local database or Ollama
├── ollama_engine.py     Talks to local Ollama server
├── local_engine.py      TF-IDF search over the command dataset
├── placeholders.py      Detects and fills in {{PLACEHOLDER}} tokens
├── profiles.py          Stores OS and model preferences
├── confirm.py           Shows plan and handles confirmation
├── executor.py          Runs commands via subprocess
├── config.py            Central configuration and paths
├── dataset_builder.py   Manages the pending review queue
├── safety.py            Three-level safety checking system
├── install.sh           One-line installer script
│
├── data/
│   └── commands.json    Curated command dataset (grows over time)
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

Contributions are welcome and appreciated.

**Adding commands to the dataset**

The fastest way to improve ShellAI for everyone is to add entries
to `data/commands.json`. Follow the existing format:

```json
{
  "intent": "description of what the user wants to do",
  "tags": ["relevant", "keywords", "for", "matching"],
  "os": "all",
  "commands": [
    {
      "command": "the exact command to run",
      "explanation": "one sentence explaining what this does"
    }
  ],
  "summary": "one sentence describing what all these commands accomplish"
}
```

Use `"os": "all"` for cross-platform commands.
Use `"os": "ubuntu"`, `"os": "macos"` etc. for platform-specific ones.

For commands needing user-specific values, use placeholders:
```json
"command": "git config --global user.name \"{{YOUR_NAME}}\""
```

**Before submitting a pull request**
1. Run `pytest tests/ -v` — all tests must pass
2. Add tests for any new functionality
3. Never commit API keys, credentials, or personal data

---

## Privacy

- All queries go to your local Ollama model — nothing leaves your machine
- No telemetry, no analytics, no usage tracking of any kind
- Your command history stays on your machine in `~/.shellai/`
- No accounts, no sign-ups, no external servers

---

## License

MIT — do whatever you want with it.

---

## Acknowledgements

Built with [Ollama](https://ollama.com), [scikit-learn](https://scikit-learn.org),
[colorama](https://pypi.org/project/colorama/), and [requests](https://pypi.org/project/requests/).

Inspired by the universal developer experience of forgetting what flags `tar` takes.

---

<p align="center">
  Made by <a href="https://github.com/Kxrishx03">Karishma Mandal</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Kxrishx03/shellai/issues">Report a bug</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Kxrishx03/shellai/issues">Request a feature</a>
</p>