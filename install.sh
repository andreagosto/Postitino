#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
NAME="Postitino"
EXEC="python3 $DIR/main.py"
ICON_NAME="it.andrea.postitino"
ICON_DEST="$HOME/.local/share/icons/hicolor/scalable/apps/$ICON_NAME.svg"

echo "==> Verifico Python, GTK3 e gi-cairo..."

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 non trovato. Installa Python prima."
    exit 1
fi

NEED=""

if ! python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null; then
    NEED="$NEED python3-gi gir1.2-gtk-3.0"
fi

if ! python3 -c "import gi; gi.require_version('Gtk','3.0'); gi.require_foreign('cairo')" 2>/dev/null; then
    NEED="$NEED python3-gi-cairo python3-cairo"
fi

if [ -n "$NEED" ]; then
    echo "Dipendenze mancanti: $NEED"
    echo "Le installo (richiede sudo)…"
    sudo apt install -y $NEED gir1.2-ayatanaappindicator3-0.1
fi

echo "==> Installo l'icona nel tema icone…"
mkdir -p "$(dirname "$ICON_DEST")"
cp "$DIR/postitino.svg" "$ICON_DEST"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "==> Creo la voce nel menu applicazioni…"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/postitino.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$NAME
Comment=Desktop sticky notes and to-do lists
Exec=$EXEC
Icon=$ICON_NAME
Terminal=false
Categories=Utility;
EOF

echo "==> Abilito l'avvio automatico al login…"
mkdir -p "$HOME/.config/autostart"
cp "$HOME/.local/share/applications/postitino.desktop" "$HOME/.config/autostart/postitino.desktop"

echo ""
echo "Fatto!"
echo "Avvia con:  python3 $DIR/main.py"
echo "Oppure dal menu applicazioni: $NAME"
echo "Per togliere l'autostart: rm $HOME/.config/autostart/postitino.desktop"
