RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

print_step()  { echo -e "\n${CYAN}${BOLD}→ $1${NC}"; }
print_ok()    { echo -e "  ${GREEN}✓ $1${NC}"; }
print_warn()  { echo -e "  ${YELLOW}⚠ $1${NC}"; }
print_skip()  { echo -e "  ${YELLOW}– $1 (not found, skipping)${NC}"; }

INSTALL_DIR="$HOME/.shellai-app"
DATA_DIR="$HOME/.shellai"
LAUNCHER="$HOME/.local/bin/shellai"
MODEL="phi3:mini"
REMOVE_OLLAMA=false
REMOVE_MODEL=false

for arg in "$@"; do
    case "$arg" in
        --remove-ollama) REMOVE_OLLAMA=true ;;
        --remove-model)  REMOVE_MODEL=true  ;;
    esac
done

echo -e "\n${BOLD}╔══════════════════════════════════╗"
echo -e "║       ShellAI Uninstaller        ║"
echo -e "╚══════════════════════════════════╝${NC}"
echo ""
echo -e "  This will remove ShellAI from your system."

if $REMOVE_OLLAMA; then
    echo -e "  ${RED}--remove-ollama flag set: Ollama will also be removed.${NC}"
fi
if $REMOVE_MODEL; then
    echo -e "  ${YELLOW}--remove-model flag set: $MODEL will be deleted.${NC}"
fi

echo ""
read -rp "  Continue? [y/N] " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "\n  Cancelled.\n"
    exit 0
fi

# ── 1. Launcher ───────────────────────────────────────────────────────────────
print_step "Removing launcher"
if [ -f "$LAUNCHER" ]; then
    rm -f "$LAUNCHER"
    print_ok "Removed $LAUNCHER"
else
    print_skip "$LAUNCHER"
fi

# ── 2. App directory ──────────────────────────────────────────────────────────
print_step "Removing app files"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    print_ok "Removed $INSTALL_DIR"
else
    print_skip "$INSTALL_DIR"
fi

# ── 3. User data (database, profile) ─────────────────────────────────────────
print_step "Removing user data"
if [ -d "$DATA_DIR" ]; then
    echo ""
    read -rp "  Also delete your ShellAI database and profile at $DATA_DIR? [y/N] " DEL_DATA
    if [[ "$DEL_DATA" =~ ^[Yy]$ ]]; then
        rm -rf "$DATA_DIR"
        print_ok "Removed $DATA_DIR"
    else
        print_warn "Kept $DATA_DIR (re-install will reuse it)"
    fi
else
    print_skip "$DATA_DIR"
fi

# ── 4. PATH line in shell RC files ───────────────────────────────────────────
print_step "Cleaning up PATH export"
for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
    if [ -f "$RC" ] && grep -q 'local/bin' "$RC"; then
        # Remove only the line we added — leave everything else intact
        sed -i '/export PATH="\$HOME\/.local\/bin:\$PATH"/d' "$RC"
        print_ok "Cleaned $RC"
    fi
done

if $REMOVE_MODEL; then
    print_step "Removing Ollama model ($MODEL)"
    if command -v ollama &>/dev/null; then
        ollama rm "$MODEL" 2>/dev/null && print_ok "Removed $MODEL" \
            || print_warn "Could not remove $MODEL (may not be installed)"
    else
        print_skip "ollama not found"
    fi
fi

if $REMOVE_OLLAMA; then
    print_step "Removing Ollama"
    if command -v ollama &>/dev/null; then
        # Stop service if running
        sudo systemctl stop ollama 2>/dev/null || true
        sudo systemctl disable ollama 2>/dev/null || true

        # Remove binary
        sudo rm -f /usr/local/bin/ollama

        # Remove systemd service
        sudo rm -f /etc/systemd/system/ollama.service
        sudo systemctl daemon-reload 2>/dev/null || true

        # Remove model cache
        rm -rf "$HOME/.ollama"
        print_ok "Ollama removed"
    else
        print_skip "Ollama not found"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════╗"
echo -e "║   ShellAI uninstalled. Bye! 👋   ║"
echo -e "╚══════════════════════════════════╝${NC}"
echo ""
echo "  To reinstall later:"
echo "    curl -sSL https://raw.githubusercontent.com/Kxrishx03/shellai/master/install.sh | bash"
echo ""