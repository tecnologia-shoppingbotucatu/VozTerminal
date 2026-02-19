#!/bin/bash
# Instala atalho do VozTerminal no desktop e no menu de aplicativos
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXE_PATH="$SCRIPT_DIR/dist/VozTerminal"
DESKTOP_FILE="$HOME/.local/share/applications/vozterminal.desktop"
DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
DESKTOP_LINK="$DESKTOP_DIR/VozTerminal.desktop"

# Verifica se o executável existe
if [ ! -f "$EXE_PATH" ]; then
    echo "ERRO: Executável não encontrado em $EXE_PATH"
    echo "Execute primeiro: bash build_exe.sh"
    exit 1
fi

# Cria o .desktop file
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=VozTerminal
Comment=Ditado por voz para terminais Linux
Exec=$EXE_PATH
Type=Application
Categories=Utility;Accessibility;
Terminal=false
StartupNotify=true
EOF

# Copia para o Desktop também
cp "$DESKTOP_FILE" "$DESKTOP_LINK"
chmod +x "$DESKTOP_LINK"

# Marca como confiável (Linux Mint/Cinnamon)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_LINK" metadata::trusted true 2>/dev/null || true
fi

echo "Atalho criado com sucesso!"
echo "  - Menu de aplicativos: VozTerminal"
echo "  - Desktop: $DESKTOP_LINK"
echo ""
echo "Agora é só clicar duas vezes no ícone!"
