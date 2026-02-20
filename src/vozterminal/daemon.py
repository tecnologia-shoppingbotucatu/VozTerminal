"""Daemon principal do VozTerminal. Orquestra todos os componentes."""

import os
import sys
import signal
import logging
import tempfile
import threading
from pathlib import Path

from vozterminal.config import Config
from vozterminal.audio import AudioCapture
from vozterminal.transcriber import Transcriber
from vozterminal.text_processor import TextProcessor
from vozterminal.inserter import TextInserter
from vozterminal.hotkey import HotkeyListener
from vozterminal.dictionary import Dictionary

logger = logging.getLogger("vozterminal")


def _get_pid_file() -> Path:
    """Retorna caminho do PID file adequado para a plataforma."""
    if sys.platform == "win32":
        return Path(tempfile.gettempdir()) / "vozterminal.pid"
    return Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "vozterminal.pid"


PID_FILE = _get_pid_file()


class VozTerminalDaemon:
    """Daemon principal do VozTerminal."""

    def __init__(self, config: Config):
        self._config = config
        self._is_active = False
        self._is_running = False
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()

        # Inicializa componentes
        self._dictionary = Dictionary(config.dictionary_path, config.snippets_path)

        self._transcriber = Transcriber(
            groq_api_key=config.groq_api_key,
            openai_api_key=config.openai_api_key,
            language=config.language,
            prompt_hint=self._dictionary.get_prompt_hint(),
        )

        self._processor = TextProcessor(
            dictionary=self._dictionary,
            extra_fillers=config.extra_fillers,
            extra_punctuation=config.extra_punctuation,
            enable_auto_capitalize=config.auto_capitalize,
        )

        self._inserter = TextInserter(typing_delay_ms=config.typing_delay_ms)

        self._audio = AudioCapture(
            on_segment=self._on_audio_segment,
            vad_aggressiveness=config.vad_aggressiveness,
            silence_threshold_ms=config.silence_threshold_ms,
            device_index=config.audio_device_index,
        )

        self._hotkey = HotkeyListener(
            hotkey_str=config.hotkey,
            on_activate=self._toggle_dictation,
        )

    def run(self) -> None:
        """Inicia o daemon. Bloqueia até receber SIGTERM/SIGINT."""
        self._write_pid_file()
        self._setup_signals()
        self._is_running = True

        self._hotkey.start()
        logger.info(
            "VozTerminal daemon iniciado. Pressione %s para ativar/desativar ditado.",
            self._config.hotkey,
        )

        try:
            self._shutdown_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Desliga o daemon graciosamente."""
        if not self._is_running:
            return
        logger.info("Desligando VozTerminal...")
        self._is_running = False
        if self._is_active:
            self._audio.stop()
        self._hotkey.stop()
        self._remove_pid_file()
        logger.info("VozTerminal desligado.")

    def _toggle_dictation(self) -> None:
        """Chamado pelo hotkey. Alterna entre gravando/parado."""
        with self._lock:
            if self._is_active:
                self._is_active = False
                self._audio.stop()
                logger.info(">> Ditado DESATIVADO")
            else:
                self._is_active = True
                self._audio.start()
                logger.info(">> Ditado ATIVADO - fale agora!")

    # Frases que o Whisper "alucina" quando recebe só ruído
    HALLUCINATION_PATTERNS = [
        "thank you",
        "thanks for watching",
        "subscribe",
        "like and subscribe",
        "see you next time",
        "it seems",
        "you",
        "bye",
        "...",
        "the end",
        "obrigado por assistir",
        "inscreva-se",
        "legendas pela comunidade",
    ]

    def _is_hallucination(self, text: str) -> bool:
        """Detecta alucinações comuns do Whisper com ruído."""
        lower = text.strip().lower().rstrip(".")
        if len(lower) < 3:
            return True
        for pattern in self.HALLUCINATION_PATTERNS:
            if lower == pattern or lower.startswith(pattern):
                return True
        return False

    def _on_audio_segment(self, pcm_data: bytes) -> None:
        """Callback do AudioCapture. Transcreve e insere texto."""
        if not self._is_active:
            return

        duration = len(pcm_data) / (16000 * 2)
        logger.debug(f"Segmento recebido: {len(pcm_data)} bytes ({duration:.1f}s)")

        text = self._transcriber.transcribe(pcm_data)
        if not text:
            logger.debug("Transcrição vazia, ignorando.")
            return

        if self._is_hallucination(text):
            logger.info(f"Alucinação descartada: '{text}'")
            return

        logger.info(f"Transcrição: '{text}'")
        processed = self._processor.process(text)
        logger.debug(f"Processado: '{processed}'")

        if processed:
            # Adiciona espaço antes se não começa com pontuação
            if processed[0] not in ".,!?;:)\n\t":
                processed = " " + processed
            self._inserter.insert(processed)

    def _setup_signals(self) -> None:
        signal.signal(signal.SIGINT, lambda *_: self._shutdown_event.set())
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, lambda *_: self._shutdown_event.set())

    def _write_pid_file(self) -> None:
        PID_FILE.write_text(str(os.getpid()))

    def _remove_pid_file(self) -> None:
        PID_FILE.unlink(missing_ok=True)

    @staticmethod
    def is_running() -> int | None:
        """Retorna PID do daemon se estiver rodando, None caso contrário."""
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                if sys.platform == "win32":
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                    handle = kernel32.OpenProcess(
                        PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                    )
                    if handle:
                        kernel32.CloseHandle(handle)
                        return pid
                    else:
                        PID_FILE.unlink(missing_ok=True)
                else:
                    os.kill(pid, 0)  # Checa se processo existe
                    return pid
            except (OSError, ValueError):
                PID_FILE.unlink(missing_ok=True)
        return None
