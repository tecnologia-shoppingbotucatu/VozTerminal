# VozTerminal - Instruções do Projeto

Ditado por voz em tempo real para terminais (Linux e Windows). Captura audio via microfone, transcreve com Groq/OpenAI Whisper, e insere texto na janela ativa.

## Setup Linux

```bash
# Dependencias de sistema
sudo apt install portaudio19-dev xdotool

# Ambiente Python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# API Key (obrigatorio - pelo menos uma)
export GROQ_API_KEY='sua-chave'
export OPENAI_API_KEY='sua-chave'   # opcional, fallback
```

## Setup Windows

```cmd
# Ambiente Python (nao precisa de dependencias de sistema)
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"

# API Key
set GROQ_API_KEY=sua-chave
set OPENAI_API_KEY=sua-chave
```

## Comandos

```bash
# Rodar (Linux e Windows)
vozterminal gui                    # Interface grafica
vozterminal start -f               # Daemon em foreground
vozterminal start                  # Daemon em background
vozterminal stop                   # Parar daemon

# Testes
pytest tests/ -v

# Build executavel
bash build_exe.sh                  # Linux: gera dist/VozTerminal
build_exe.bat                      # Windows: gera dist\VozTerminal.exe

# Instalar atalho desktop (Linux apenas)
bash install_desktop.sh
```

## Estrutura

```
src/vozterminal/
  config.py          # Dataclass Config + load/save (multiplataforma)
  audio.py           # PyAudio + webrtcvad (VAD com janela deslizante)
  transcriber.py     # Groq API (primario) + OpenAI (fallback)
  text_processor.py  # Pipeline: snippets → fillers → dicionario → pontuacao
  inserter.py        # Multiplataforma: xdotool (Linux) / SendInput (Windows)
  hotkey.py          # pynput keyboard.Listener (F9 padrao)
  dictionary.py      # Dicionario pessoal + snippets (JSON)
  daemon.py          # Orquestrador: conecta todos os componentes
  cli.py             # Click CLI (start/stop/status/gui/dict/snippet)
  gui.py             # CustomTkinter (3 abas: Ditado, Config, Sobre)
tests/
  test_text_processor.py   # 15 testes
  test_dictionary.py       # 16 testes
  test_inserter.py         # testes do inserter multiplataforma
```

## Convencoes

- Python 3.11+, type hints com `X | None`
- Codigo e comentarios em portugues BR
- Logging via `logging.getLogger("vozterminal.modulo")`
- Config dir: `~/.vozterminal/` (Linux) ou `%APPDATA%\VozTerminal\` (Windows)
- API keys: env vars tem prioridade sobre config.json
- Hotkey padrao: F9 (configuravel)
- Audio: 16kHz, 16-bit, mono, frames de 30ms
- Deteccao de plataforma: `sys.platform == "win32"`

## Dependencias de Sistema

### Linux
- `portaudio19-dev` - biblioteca de audio (compilacao PyAudio)
- `xdotool` - insercao de texto sintetico na janela ativa (X11)

### Windows
- Nenhuma dependencia de sistema (PyAudio e pynput usam Win32 API nativa)

## Branch Workflow

- `main` - versao estavel
- `feat/windows` - suporte multiplataforma (Windows + Linux)
- Apenas o usuario decide quando fazer PR/merge
