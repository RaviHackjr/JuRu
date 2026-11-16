#!/bin/sh
# JuRu one-step install - puts the interpreter on your PATH, like a
# real setup. Tries /usr/local/bin (direct, then with sudo) and falls
# back to ~/.local/bin when neither works - it always succeeds somewhere
# and tells you if one PATH line remains.

DIR="$(cd "$(dirname "$0")" && pwd)"

# copy + chmod into $1; with sudo when $2 is set. Fails quietly so the
# next option gets its turn.
install_to() {
    DEST="$1"
    if [ -n "$2" ]; then
        sudo cp "$DIR/juru" "$DEST/juru" 2>/dev/null || return 1
        sudo chmod +x "$DEST/juru" 2>/dev/null || return 1
    else
        cp "$DIR/juru" "$DEST/juru" 2>/dev/null || return 1
        chmod +x "$DEST/juru" 2>/dev/null || return 1
    fi
}

echo
echo " JuRu setup - installing the interpreter"
echo

if install_to /usr/local/bin ""; then
    :
elif command -v sudo >/dev/null 2>&1 && install_to /usr/local/bin sudo; then
    :
else
    DEST="$HOME/.local/bin"
    mkdir -p "$DEST"
    cp "$DIR/juru" "$DEST/juru"
    chmod +x "$DEST/juru"
fi

echo "  installed: $DEST/juru"

case ":$PATH:" in
    *":$DEST:"*) ;;
    *) echo "  PATH: one line left - add it to ~/.bashrc or ~/.zshrc:"
       echo "        export PATH=\"\$PATH:$DEST\"" ;;
esac

echo
echo " done. Open a NEW terminal, then:"
echo
echo "     juru --version"
echo "     juru --new mygame starter"
echo "     juru mygame.jr"
echo
