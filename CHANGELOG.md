# Changelog

Todas as mudancas notaveis do VozTerminal serao documentadas neste arquivo.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [0.1.0] - 2026-02-19

### Adicionado

#### Core
- Daemon principal com orquestracao de todos os componentes
- Captura de audio via PyAudio com callback em tempo real (16kHz, 16-bit, mono)
- Deteccao de atividade de voz (VAD) com webrtcvad usando janela deslizante
  - Trigger: 90% dos frames voiced em janela de 300ms
  - Detrigger: 90% dos frames unvoiced em janela de 300ms
  - Filtro de energia RMS (minimo 500) para rejeitar ruido de fundo
- Transcricao via Groq API (whisper-large-v3-turbo) com fallback OpenAI (whisper-1)
- Filtro anti-alucinacao do Whisper (rejeita frases genericas como "thank you", "subscribe")
- Pipeline de processamento de texto com 6 etapas:
  - Expansao de snippets
  - Remocao de fillers (ee, hum, tipo, ne, sabe)
  - Substituicao por dicionario pessoal
  - Conversao de pontuacao falada (ponto, virgula, interrogacao, nova linha)
  - Limpeza de espacos
  - Auto-capitalizacao
- Insercao de texto na janela ativa via xdotool (--clearmodifiers --delay 12ms)
- Hotkey global F9 via pynput (configuravel, suporta F1-F12 e combinacoes)
- Dicionario pessoal e snippets persistidos em JSON

#### CLI
- `vozterminal start [--foreground]` - Inicia daemon
- `vozterminal stop` - Para daemon
- `vozterminal status` - Mostra status do daemon
- `vozterminal gui` - Abre interface grafica
- `vozterminal init` - Inicializa ~/.vozterminal/
- `vozterminal devices` - Lista dispositivos de audio
- `vozterminal dict add/remove/list` - Gerenciar dicionario
- `vozterminal snippet add/remove/list` - Gerenciar snippets

#### GUI
- Interface grafica CustomTkinter com dark mode
- 3 abas: Ditado (controle + log), Configuracoes (API keys, audio, hotkey), Sobre
- Campos de API key com botao mostrar/ocultar
- Seletores de idioma, microfone, hotkey (F1-F12)
- Sliders de VAD aggressiveness e delay de digitacao
- Hotkey F9 global funcional direto da GUI (sem precisar clicar botao)
- Polling de estado para sincronizar GUI com daemon (200ms)
- Log de transcricoes em tempo real

#### Distribuicao
- Executavel standalone via PyInstaller (26MB)
- Script de build automatizado (build_exe.sh)
- Script de instalacao de atalho desktop Linux (install_desktop.sh)
- Integracao com menu de aplicativos

#### Testes
- 31 testes unitarios (text_processor + dictionary)
- Cobertura: fillers, pontuacao, dicionario, snippets, auto-capitalize, persistencia
