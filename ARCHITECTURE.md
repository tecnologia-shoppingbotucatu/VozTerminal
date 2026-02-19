# VozTerminal - Arquitetura

## Visao Geral

VozTerminal e um aplicativo de ditado por voz em tempo real para Linux. Captura audio do microfone, detecta fala com VAD, transcreve via API cloud, processa o texto e insere na janela ativa.

```
Usuario fala → Microfone → VAD → Transcricao API → Processamento → xdotool → Janela ativa
```

## Diagrama de Fluxo de Dados

```
                    ┌─────────────────────────┐
                    │   HOTKEY (F9)            │
                    │   pynput.keyboard        │
                    └────────┬────────────────┘
                             │ toggle ON/OFF
                             v
┌──────────────────────────────────────────────────────────┐
│  AudioCapture (audio.py)                                 │
│                                                          │
│  PyAudio stream → callback a cada 30ms (480 samples)     │
│       │                                                  │
│       v                                                  │
│  webrtcvad.is_speech(frame, 16kHz)                       │
│       │                                                  │
│       v                                                  │
│  Ring Buffer (10 frames = 300ms)                         │
│  ┌─────────────────────────────────────┐                 │
│  │ Trigger:   90% voiced   → gravar   │                 │
│  │ Detrigger: 90% unvoiced → emitir   │                 │
│  └─────────────────────────────────────┘                 │
│       │                                                  │
│       v                                                  │
│  Filtro RMS (energia minima 500)                         │
│  Rejeita segmentos de ruido de fundo                     │
└──────────────────┬───────────────────────────────────────┘
                   │ PCM bytes (1-15s de fala)
                   │ Thread separada por segmento
                   v
┌──────────────────────────────────────────────────────────┐
│  Transcriber (transcriber.py)                            │
│                                                          │
│  1. PCM 16-bit → WAV (io.BytesIO em memoria)            │
│  2. Groq API (whisper-large-v3-turbo) ← primario        │
│  3. OpenAI API (whisper-1)             ← fallback        │
│  4. Retorna texto ou None                                │
└──────────────────┬───────────────────────────────────────┘
                   │ Texto bruto
                   v
┌──────────────────────────────────────────────────────────┐
│  Deteccao de Alucinacoes (daemon.py)                     │
│                                                          │
│  Rejeita: "thank you", "subscribe", "obrigado por       │
│  assistir", textos < 3 caracteres, etc.                  │
└──────────────────┬───────────────────────────────────────┘
                   │ Texto validado
                   v
┌──────────────────────────────────────────────────────────┐
│  TextProcessor (text_processor.py)                       │
│                                                          │
│  Pipeline sequencial:                                    │
│  1. Snippets    → "git commit" expande para template     │
│  2. Fillers     → remove "ee", "hum", "tipo", "ne"      │
│  3. Dicionario  → "pitom" → "Python"                    │
│  4. Pontuacao   → "ponto" → ".", "virgula" → ","        │
│  5. Espacos     → limpa duplicados e antes de pontuacao  │
│  6. Capitalize  → primeira letra + apos pontuacao        │
└──────────────────┬───────────────────────────────────────┘
                   │ Texto processado
                   v
┌──────────────────────────────────────────────────────────┐
│  TextInserter (inserter.py)                              │
│                                                          │
│  xdotool type --clearmodifiers --delay 12 -- "texto"     │
│  Insere na janela que estiver em foco (X11)              │
└──────────────────────────────────────────────────────────┘
```

## Modulos

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| Config | `config.py` | Dataclass com load/save JSON, env vars > arquivo |
| Audio | `audio.py` | Captura PyAudio + VAD webrtcvad + filtro RMS |
| Transcriber | `transcriber.py` | Groq API + fallback OpenAI, PCM→WAV em memoria |
| TextProcessor | `text_processor.py` | Pipeline de 6 etapas de pos-processamento |
| Inserter | `inserter.py` | xdotool type na janela ativa |
| Hotkey | `hotkey.py` | pynput Listener, suporta F1-F12 e combinacoes |
| Dictionary | `dictionary.py` | CRUD dicionario + snippets em JSON |
| Daemon | `daemon.py` | Orquestra tudo + filtro anti-alucinacao |
| CLI | `cli.py` | Click com 15+ comandos |
| GUI | `gui.py` | CustomTkinter dark mode, 3 abas |

## Sistema de Configuracao

```
Prioridade: env vars > config.json

~/.vozterminal/
  config.json       # Configuracoes gerais
  dictionary.json   # Dicionario pessoal {"errado": "correto"}
  snippets.json     # Snippets {"nome": "texto expandido"}
  vozterminal.log   # Log de execucao
```

A classe `Config` (dataclass) carrega valores de `config.json` e sobrescreve com env vars:
- `GROQ_API_KEY` e `OPENAI_API_KEY` tem prioridade sobre o arquivo
- O metodo `save(save_keys=True)` permite salvar API keys (usado pela GUI)
- O metodo `save()` sem parametro nunca salva API keys (usado pela CLI)

## VAD - Voice Activity Detection

Implementacao baseada no padrao oficial do webrtcvad:

1. **Frame**: 30ms de audio (480 samples a 16kHz)
2. **Classificacao**: webrtcvad classifica cada frame como speech/silence
3. **Janela deslizante**: Ring buffer de 10 frames (300ms)
4. **Trigger**: 90% dos frames na janela sao fala → inicia gravacao
5. **Detrigger**: 90% dos frames na janela sao silencio → para gravacao
6. **Filtro RMS**: Rejeita segmentos com energia < 500 (ruido de fundo)
7. **Limites**: Minimo 1s, maximo 15s por segmento

## Threads e Concorrencia

```
Thread Principal (main)
  └── signal.wait() ou tkinter.mainloop()

Thread pynput (daemon)
  └── keyboard.Listener escuta F9

Thread PyAudio (C-level callback)
  └── _audio_callback() a cada 30ms

Threads transientes (1 por segmento)
  └── transcreve + processa + insere
```

- `AudioCapture` usa `threading.Lock` para proteger start/stop
- `VozTerminalDaemon` usa `threading.Lock` para toggle
- Segmentos sao processados em threads daemon separadas
- GUI usa `self.after()` para updates thread-safe no tkinter

## GUI

Framework: CustomTkinter (dark mode, tema blue)

| Aba | Conteudo |
|-----|----------|
| Ditado | Botao toggle, status (Parado/Ouvindo), log de transcricoes |
| Configuracoes | API keys, idioma, microfone, hotkey, VAD, delay, auto-capitalize |
| Sobre | Versao, creditos, info tecnica |

- Hotkey global F9 funciona mesmo com GUI em segundo plano
- Polling a cada 200ms sincroniza visual com estado do daemon
- Log handler customizado redireciona logging para textbox

## Build e Distribuicao

```
PyInstaller (vozterminal.spec)
  Entry point: src/vozterminal/gui.py
  Binarios:    libportaudio.so.2 (bundled)
  Dados:       CustomTkinter themes/assets
  Hidden:      Todos os modulos + groq/openai/pynput/Xlib
  Excludes:    matplotlib, numpy, pandas, scipy
  Output:      dist/VozTerminal (~26MB, ELF 64-bit)

Scripts:
  build_exe.sh         → Gera dist/VozTerminal
  install_desktop.sh   → Cria atalho .desktop no Linux
```

## Dependencias

### Python (pyproject.toml)
| Pacote | Versao | Uso |
|--------|--------|-----|
| pyaudio | >=0.2.14 | Captura de audio |
| webrtcvad-wheels | >=2.0.14 | Deteccao de voz |
| groq | >=0.11.0 | API Groq Whisper |
| openai | >=1.40.0 | API OpenAI Whisper |
| pynput | >=1.7.6 | Hotkey global |
| click | >=8.1.0 | CLI |
| customtkinter | >=5.2.0 | GUI |

### Sistema
| Pacote | Comando | Uso |
|--------|---------|-----|
| portaudio19-dev | `sudo apt install portaudio19-dev` | Biblioteca de audio |
| xdotool | `sudo apt install xdotool` | Insercao de texto (X11) |
