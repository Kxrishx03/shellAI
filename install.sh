#!/bin/bash
# install.sh
# One-line installer for ShellAI
# Usage: curl -sSL https://raw.githubusercontent.com/yourusername/shellai/main/install.sh | bash

set -e  # exit immediately if any command fails

# ── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # no color

print_step()  { echo -e "\n${CYAN}${BOLD}→ $1${NC}"; }
print_ok()    { echo -e "${GREEN}✓ $1${NC}"; }
print_warn()  { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

echo -e "\n${BOLD}ShellAI Installer${NC}"
echo "────────────────────────────────────"

# ── Check Python ──────────────────────────────────────────
print_step "Checking Python version"
if ! command -v python3 &>/dev/null; then
    print_error "Python 3 is not installed."
    echo "Install it with: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 8 ]; then
    print_error "Python 3.8 or higher is required."
    exit 1
fi
print_ok "Python $(python3 --version) found"

# ── Check pip ─────────────────────────────────────────────
print_step "Checking pip"
if ! command -v pip3 &>/dev/null; then
    print_warn "pip3 not found. Installing..."
    sudo apt-get install -y python3-pip 2>/dev/null || \
    python3 -m ensurepip --upgrade
fi
print_ok "pip found"

# ── Check Ollama ──────────────────────────────────────────
print_step "Checking Ollama"
if ! command -v ollama &>/dev/null; then
    print_warn "Ollama not found. Installing..."

    # Handle WSL2 zstd issue
    if grep -qi microsoft /proc/version 2>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y zstd 2>/dev/null
    fi

    curl -fsSL https://ollama.com/install.sh | sh
    print_ok "Ollama installed"
else
    print_ok "Ollama found"
fi

# ── Clone or update repo ──────────────────────────────────
print_step "Installing ShellAI"

INSTALL_DIR="$HOME/.shellai-app"

if [ -d "$INSTALL_DIR" ]; then
    print_warn "Existing installation found. Updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    git clone https://github.com/yourusername/shellai.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── Create virtual environment ────────────────────────────
print_step "Setting up Python environment"
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"
pip install -q -e .
print_ok "Dependencies installed"

# ── Create launcher script ────────────────────────────────
print_step "Creating shellai command"

LAUNCHER="$HOME/.local/bin/shellai"
mkdir -p "$HOME/.local/bin"

cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
source "$INSTALL_DIR/venv/bin/activate"
python3 "$INSTALL_DIR/main.py" "\$@"
LAUNCHER_EOF

chmod +x "$LAUNCHER"

# ── Add to PATH if needed ─────────────────────────────────
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    if [ -n "$SHELL_RC" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        print_ok "Added ~/.local/bin to PATH in $SHELL_RC"
    fi
fi

# ── Pull default model ────────────────────────────────────
print_step "Pulling AI model (phi3:mini — about 2.3GB)"
echo "This is a one-time download. It may take a few minutes..."
ollama pull phi3:mini

# ── Done ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}────────────────────────────────────"
echo -e "ShellAI installed successfully!"
echo -e "────────────────────────────────────${NC}"
echo ""
echo "Restart your terminal, then run:"
echo -e "  ${BOLD}shellai --help${NC}"
echo ""
echo "First run will ask for your OS. Then try:"
echo -e "  ${BOLD}shellai initialize a new git repository${NC}"
echo ""
echo "Found a bug? Open an issue:"
echo "  https://github.com/yourusername/shellai/issues"
echo ""