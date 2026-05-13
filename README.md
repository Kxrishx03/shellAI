<p align="center">
  <h1 align="center">ShellAI</h1>
  <p align="center">Run developer tasks by describing them in plain English</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/ollama-required-green.svg" alt="Ollama">
  <img src="https://img.shields.io/badge/works_offline-yes-brightgreen.svg" alt="Offline">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL2-lightblue.svg" alt="Platform">
</p>

---

```bash
shellai initialize a react project with typescript and tailwind
shellai merge branch feature/login into main with message "add auth"
shellai find all files larger than 100mb and show their sizes
shellai set up postgresql and create a database called myapp
```

---

## What is ShellAI

ShellAI is a local-first command line tool that turns plain English descriptions
into shell commands — and runs them for you.

You describe what you want to do. ShellAI figures out the exact commands,
shows you everything before running it, and asks for your confirmation.
No commands ever run silently.

Everything runs on your own machine. No API keys. No internet required after setup.
No usage limits. No data sent anywhere.

---

## How it works

```
You type:   shellai initialize a react project with typescript

Step 1:     ShellAI checks its local command database (instant)
            ✓ Found in local database (confidence: 91%)

Step 2:     Shows you the plan

            ┌─ Plan ─────────────────────────────────────────────────
            │  Create a new React project with TypeScript pre-configured
            │
            │  1. npx create-react-app my-app --template typescript
            │     → Creates a new React project with TypeScript
            │
            │  2. cd my-app
            │     → Enter the project folder
            │
            │  3. npm start
            │     → Start the development server on localhost:3000
            └────────────────────────────────────────────────────────

Step 3:     Asks for your name for the project
            Project name: my-app

Step 4:     Run 3 commands? [yes / no / edit]:

Step 5:     Runs each command with live output
```

---

## Features

- **Plain English input** — describe what you want, not the syntax
- **Local database** — common tasks answered instantly from a curated dataset
- **Local AI** — powered by Ollama, runs entirely on your machine
- **Fully offline** — no internet needed after initial model download
- **No API keys** — ever
- **Confirmation gate** — you see every command before it runs
- **Placeholder detection** — asks for your name, email, project name etc before running
- **Edit mode** — pick which commands from the plan to actually run
- **Safety system** — blocks dangerous commands, warns on destructive ones
- **Self-improving** — learns from every query and grows smarter over time
- **OS-aware** — generates the right commands for your OS (Ubuntu, macOS, Arch, Fedora)

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.8 or higher |
| Ollama | Latest |
| RAM | 4GB available minimum |
| OS | Linux, macOS, or Windows WSL2 |

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/shellai.git
cd shellai
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install ShellAI

```bash
pip install -e .
```

### Step 4 — Install Ollama

**Linux / WSL2:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

If you see a `zstd` error on WSL2:
```bash
sudo apt update && sudo apt install -y zstd
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

Or download the installer from [ollama.com](https://ollama.com)

### Step 5 — Pull a model

Choose based on your available RAM (`free -h` to check):

```bash
# 4GB+ RAM — recommended for most machines
ollama pull phi3:mini

# 8GB+ RAM — better quality responses
ollama pull mistral:7b

# Fastest option, lower quality
ollama pull tinyllama
```

### Step 6 — Start Ollama

```bash
# Ollama usually starts automatically after install
# If not, start it manually:
ollama serve &
```

> **Note for WSL2 users:** If you see `address already in use`, Ollama is already
> running as a system service. This is fine — just continue to the next step.

### Step 7 — Run ShellAI

ShellAI runs a one-time setup wizard on first launch.
It will ask for your OS and which model you want to use.

```bash
shellai --help
```

---

## Usage

### Basic

```bash
shellai <describe what you want to do>
```

### With careful mode (confirm each command individually)

```bash
shellai --careful <describe what you want to do>
```

---

## Examples

### Git

```bash
shellai initialize a new git repository
shellai configure git username and email
shellai create and switch to a new branch called feature/auth
shellai merge branch feature/login into main with message "add authentication"
shellai undo the last commit but keep the changes
shellai show all branches including remote
```

### Project Setup

```bash
shellai initialize a react project with typescript
shellai initialize a react project with typescript and tailwind
shellai set up a python virtual environment and install django
shellai create a new node project with express and nodemon
shellai initialize a next.js project with typescript
```

### File Management

```bash
shellai find all files larger than 100mb
shellai find all files containing the text TODO
shellai compress the dist folder into a tar.gz
shellai sync two directories with rsync
shellai find and delete all node_modules folders
shellai show disk usage of each folder in current directory
shellai watch the logs file in real time
shellai compare two files and show differences
```

### Docker

```bash
shellai build a docker image called myapp
shellai run docker compose in the background
shellai stop all running docker containers
shellai show logs from all docker containers
shellai remove all unused docker images
```

### Database

```bash
shellai install postgresql
shellai create a postgresql database called myapp
shellai dump the myapp database to a backup file
shellai restore database from backup file
```

### System

```bash
shellai check which process is using port 3000 and kill it
shellai check available disk space
shellai generate an ssh key pair for github
shellai check memory usage
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

In edit mode you pick by number:
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

## Safety System

ShellAI has a three-level safety system that runs on every command
before you are even asked to confirm.

### Level 1 — Blocked

Some commands are refused entirely, regardless of what you type.
These are commands that could destroy your operating system or
expose your machine to security risks.

Examples of what is blocked:
- `rm -rf /` — deletes the entire operating system
- Fork bombs — crash the system
- Writing directly to disk devices — wipes drives
- Piping internet content directly to bash — security risk

### Level 2 — Warning

Destructive but legitimate commands show a red warning and require
you to type `yes` in full (not just `y`) before they run.

Examples:
- `rm -rf ./old-project`
- `DROP DATABASE`
- `mkfs` (format a filesystem)

### Level 3 — Notice

Commands using `sudo` or touching sensitive system paths
show an informational notice so you are aware.

### Placeholder Validation

When a command needs your email, port number, or project name,
ShellAI validates the value makes sense before proceeding.
It will not let you enter a file path where a name is expected,
or a word where a port number is expected.

---

## How the Local Database Grows

ShellAI has a self-improving dataset. Here is how it works:

```
You ask something not in the local database
            ↓
Ollama generates an answer
            ↓
ShellAI silently saves it to a pending queue
            ↓
You run:  shellai --review
            ↓
You approve or reject each pending entry
            ↓
Approved entries join the local database permanently
            ↓
Next time the same task is asked — instant answer, no model needed
```

The more you use ShellAI, the faster it gets.

To review pending entries:
```bash
shellai --review
```

You will see each entry with its commands and can approve, reject, or skip.

---

## Changing Models

```bash
# Switch to a different model
shellai --set-model mistral:7b

# Make sure the model is downloaded first
ollama pull mistral:7b
```

Available models and their RAM requirements:

| Model | RAM needed | Speed | Quality |
|-------|-----------|-------|---------|
| `tinyllama` | 1-2 GB | Very fast | Basic |
| `phi3:mini` | 2-4 GB | Fast | Good — recommended default |
| `llama3.2:3b` | 3-5 GB | Fast | Good |
| `mistral:7b` | 6-8 GB | Medium | Better |
| `codellama:7b` | 6-8 GB | Medium | Better for code |

Check your available RAM with:
```bash
free -h
```

Look at the `available` column in the `Mem:` row.

---

## Troubleshooting

### `Ollama is not running`

```bash
# Check if it is already running
curl http://localhost:11434

# If not running, start it
ollama serve &

# On Linux, check the service
sudo systemctl status ollama
sudo systemctl start ollama
```

### `address already in use` when starting Ollama

Ollama is already running as a system service. This is normal.
Just continue using ShellAI — everything is fine.

### `Model not downloaded`

```bash
ollama pull phi3:mini
```

### Model returns invalid JSON

Switch to a larger model — bigger models follow format instructions better:

```bash
shellai --set-model mistral:7b
```

### `command not found: shellai`

Your virtual environment is not active:

```bash
cd shellai
source venv/bin/activate
shellai --help
```

### Slow responses

This is expected when Ollama runs on CPU without a GPU.
Options:

1. Switch to a smaller model: `shellai --set-model tinyllama`
2. Run `shellai --review` regularly to grow the local database — common
   tasks get answered instantly once they are in the dataset
3. The more you use ShellAI, the more queries hit the local database
   and the fewer go to Ollama

### `zstd` error during Ollama install on WSL2

```bash
sudo apt update && sudo apt install -y zstd
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run a specific test file
pytest tests/test_safety.py -v
```

---

## Project Structure

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

Contributions are welcome.

### Adding commands to the dataset

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

Use `"os": "all"` if the command works on all platforms.
Use `"os": "ubuntu"`, `"os": "macos"`, etc. for platform-specific commands.

For commands that need user-specific values, use placeholders:
```json
"command": "git config --global user.name \"{{YOUR_NAME}}\""
```

### Adding safety patterns

If you find a dangerous command pattern that is not blocked,
add it to `safety.py` in the appropriate list with a clear reason string.

### Before submitting a pull request

1. Run the full test suite — all tests must pass
2. Add tests for any new functionality
3. Never commit API keys, credentials, or personal data
4. Keep `data/commands.json` entries accurate and tested

---

## Privacy

ShellAI is designed for complete privacy.

- All queries go to your local Ollama model — nothing leaves your machine
- No telemetry, no analytics, no usage tracking
- Your command history stays on your machine in `~/.shellai/`
- The dataset you build stays on your machine
- There are no accounts, no sign-ups, no servers

---

## License

MIT License — do whatever you want with it.

---

## Acknowledgements

Built with:
- [Ollama](https://ollama.com) — local LLM runtime
- [scikit-learn](https://scikit-learn.org) — TF-IDF matching
- [colorama](https://pypi.org/project/colorama/) — terminal colors
- [requests](https://pypi.org/project/requests/) — HTTP client

Inspired by the universal developer experience of forgetting
what flags `tar` takes.
