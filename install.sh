set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

print_step()  { echo -e "\n${CYAN}${BOLD}→ $1${NC}"; }
print_ok()    { echo -e "  ${GREEN}✓ $1${NC}"; }
print_warn()  { echo -e "  ${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "  ${RED}✗ $1${NC}"; exit 1; }
print_skip()  { echo -e "  ${YELLOW}– $1 (skipping)${NC}"; }

INSTALL_DIR="$HOME/.shellai-app"
LAUNCHER="$HOME/.local/bin/shellai"
MODEL="phi3:mini"
REPO_HTTPS="https://github.com/Kxrishx03/shellai.git"
REPO_SSH="git@github.com:Kxrishx03/shellai.git"

# ── Parse flags ───────────────────────────────────────────────────────────────
USE_SSH=false
for arg in "$@"; do
    case "$arg" in
        --ssh) USE_SSH=true ;;
    esac
done

echo -e "\n${BOLD}╔══════════════════════════════════╗"
echo -e "║        ShellAI Installer         ║"
echo -e "╚══════════════════════════════════╝${NC}"

# ── 1. Python ─────────────────────────────────────────────────────────────────
print_step "Checking Python"
if ! command -v python3 &>/dev/null; then
    print_error "Python 3 is not installed. Fix: sudo apt install python3 python3-pip"
fi
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MINOR" -lt 8 ]; then
    print_error "Python 3.8+ required (found 3.${PY_MINOR})."
fi
print_ok "$(python3 --version)"

# ── 2. pip ────────────────────────────────────────────────────────────────────
print_step "Checking pip"
if ! command -v pip3 &>/dev/null; then
    print_warn "pip3 not found — installing..."
    sudo apt-get install -y python3-pip 2>/dev/null || python3 -m ensurepip --upgrade
fi
print_ok "pip ready"

# ── 3. git ────────────────────────────────────────────────────────────────────
print_step "Checking git"
if ! command -v git &>/dev/null; then
    print_warn "git not found — installing..."
    sudo apt-get install -y git 2>/dev/null
fi
print_ok "git $(git --version | awk '{print $3}')"

# ── 4. Ollama ─────────────────────────────────────────────────────────────────
print_step "Checking Ollama"
if ! command -v ollama &>/dev/null; then
    print_warn "Ollama not found — installing..."
    if grep -qi microsoft /proc/version 2>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y zstd 2>/dev/null
    fi
    curl -fsSL https://ollama.com/install.sh | sh
    print_ok "Ollama installed"
else
    print_ok "Ollama $(ollama --version 2>/dev/null | head -1)"
fi

# Start Ollama in background if not already running
if ! pgrep -x ollama &>/dev/null; then
    print_warn "Starting Ollama server in background..."
    ollama serve &>/dev/null &
    sleep 3
    print_ok "Ollama server started"
fi

# ── 5. Clone / update repo ────────────────────────────────────────────────────
print_step "Fetching ShellAI source"

if [ "$USE_SSH" = true ]; then
    # ── SSH mode ──────────────────────────────────────────────────────────────
    # Requires the user to have an SSH key added to their GitHub account.
    # Test the connection before attempting — gives a clear error if keys
    # aren't set up rather than a confusing git failure.
    echo "  Using SSH clone (--ssh flag set)"
    if ! ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        echo ""
        echo -e "  ${RED}✗ SSH authentication failed.${NC}"
        echo "    Your SSH key is not connected to GitHub. Either:"
        echo "      a) Add your key: https://github.com/settings/keys"
        echo "      b) Re-run without --ssh to use HTTPS instead:"
        echo "         bash install.sh"
        exit 1
    fi
    CLONE_URL="$REPO_SSH"
else
    echo "  Using HTTPS clone (public repo — no login needed)"
    export GIT_TERMINAL_PROMPT=0
    CLONE_URL="$REPO_HTTPS"
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    print_warn "Existing install found — updating..."
    GIT_TERMINAL_PROMPT=0 git -C "$INSTALL_DIR" pull --ff-only origin master
else
    GIT_TERMINAL_PROMPT=0 git clone "$CLONE_URL" "$INSTALL_DIR"
fi
print_ok "Source ready at $INSTALL_DIR"

print_step "Setting up Python environment"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install -q --upgrade pip
pip install -q -e "$INSTALL_DIR"
print_ok "Dependencies installed"

# ── 7. Launcher script ────────────────────────────────────────────────────────
# We write a tiny shell script to ~/.local/bin/shellai.
# This is the file the user actually runs when they type `shellai`.
# It activates the venv first, then hands off to main.py.
print_step "Creating shellai command"
mkdir -p "$HOME/.local/bin"
cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
exec python3 "$INSTALL_DIR/main.py" "\$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"
print_ok "Launcher created at $LAUNCHER"

print_step "Checking PATH"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
ADDED_TO=""

for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
    if [ -f "$RC" ] && ! grep -q '.local/bin' "$RC"; then
        echo "$PATH_LINE" >> "$RC"
        ADDED_TO="$RC"
        print_ok "Added ~/.local/bin to PATH in $RC"
    fi
done

if [ -z "$ADDED_TO" ]; then
    print_ok "~/.local/bin already in PATH"
fi

export PATH="$HOME/.local/bin:$PATH"

print_step "Pulling AI model ($MODEL — ~2.3 GB, one-time download)"
echo "  This may take a few minutes on first install..."
ollama pull "$MODEL"
print_ok "Model ready"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════╗"
echo -e "║   ShellAI installed! ✓           ║"
echo -e "╚══════════════════════════════════╝${NC}"
echo ""
echo "  Open a new terminal (or run: source ~/.bashrc)"
echo "  Then try:"
echo -e "    ${BOLD}shellai --help${NC}"
echo -e "    ${BOLD}shellai initialize a new git repository${NC}"
echo ""
echo "  Bugs / feedback:"
echo "    https://github.com/Kxrishx03/shellai/issues"
echo ""