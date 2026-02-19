# VozTerminal - Instruções do Projeto

Ditado por voz em tempo real para terminais Linux. Captura audio via microfone, transcreve com Groq/OpenAI Whisper, e insere texto na janela ativa via xdotool.

## Setup

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

## Comandos

```bash
# Rodar
vozterminal gui                    # Interface grafica
vozterminal start -f               # Daemon em foreground
vozterminal start                  # Daemon em background
vozterminal stop                   # Parar daemon

# Testes
pytest tests/ -v

# Build executavel
bash build_exe.sh                  # Gera dist/VozTerminal

# Instalar atalho desktop
bash install_desktop.sh
```

## Estrutura

```
src/vozterminal/
  config.py          # Dataclass Config + load/save (~/.vozterminal/config.json)
  audio.py           # PyAudio + webrtcvad (VAD com janela deslizante)
  transcriber.py     # Groq API (primario) + OpenAI (fallback)
  text_processor.py  # Pipeline: snippets → fillers → dicionario → pontuacao
  inserter.py        # xdotool type --clearmodifiers
  hotkey.py          # pynput keyboard.Listener (F9 padrao)
  dictionary.py      # Dicionario pessoal + snippets (JSON)
  daemon.py          # Orquestrador: conecta todos os componentes
  cli.py             # Click CLI (start/stop/status/gui/dict/snippet)
  gui.py             # CustomTkinter (3 abas: Ditado, Config, Sobre)
tests/
  test_text_processor.py   # 15 testes
  test_dictionary.py       # 16 testes
```

## Convencoes

- Python 3.11+, type hints com `X | None`
- Codigo e comentarios em portugues BR
- Logging via `logging.getLogger("vozterminal.modulo")`
- Config dir do usuario: `~/.vozterminal/`
- API keys: env vars tem prioridade sobre config.json
- Hotkey padrao: F9 (configuravel)
- Audio: 16kHz, 16-bit, mono, frames de 30ms

## Dependencias de Sistema

- `portaudio19-dev` - biblioteca de audio (compilacao PyAudio)
- `xdotool` - insercao de texto sintetico na janela ativa (X11)

## Branch Workflow

- `main` - versao estavel
- `feat/gui` - branch atual (GUI + executavel)
- Apenas o usuario decide quando fazer PR/merge
