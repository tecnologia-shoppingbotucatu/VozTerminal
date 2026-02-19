#!/bin/bash
# Script de build do VozTerminal - gera executável standalone
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== VozTerminal - Build do Executável ==="
echo ""

# Verifica venv
if [ ! -d ".venv" ]; then
    echo "ERRO: .venv não encontrado. Execute: python3 -m venv .venv"
    exit 1
fi

# Ativa venv
source .venv/bin/activate

# Verifica dependências de build
echo "[1/4] Verificando dependências..."
pip install -q pyinstaller customtkinter

# Verifica portaudio
if [ ! -f "/usr/lib/x86_64-linux-gnu/libportaudio.so.2" ]; then
    echo "AVISO: libportaudio não encontrada. Instale com:"
    echo "  sudo apt install portaudio19-dev"
    exit 1
fi

# Limpa builds anteriores
echo "[2/4] Limpando builds anteriores..."
rm -rf build/ dist/

# Gera executável
echo "[3/4] Gerando executável (pode demorar 1-2 minutos)..."
pyinstaller vozterminal.spec --clean --noconfirm 2>&1 | tail -5

# Verifica resultado
if [ -f "dist/VozTerminal" ]; then
    echo ""
    echo "[4/4] Build concluído com sucesso!"
    echo ""
    SIZE=$(du -sh dist/VozTerminal | cut -f1)
    echo "  Executável: dist/VozTerminal"
    echo "  Tamanho:    $SIZE"
    echo ""
    echo "Para usar: chmod +x dist/VozTerminal && ./dist/VozTerminal"
else
    echo ""
    echo "ERRO: Executável não foi gerado. Verifique os logs acima."
    exit 1
fi
