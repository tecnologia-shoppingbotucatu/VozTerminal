"""Inserção de texto na janela ativa via xdotool."""

import subprocess
import logging

logger = logging.getLogger("vozterminal.inserter")

XDOTOOL_PATH = "/usr/bin/xdotool"


class TextInserter:
    """Insere texto usando xdotool type."""

    def __init__(self, typing_delay_ms: int = 12):
        self._delay = typing_delay_ms

    def insert(self, text: str) -> bool:
        """Insere texto na janela ativa."""
        if not text:
            return True

        try:
            cmd = [
                XDOTOOL_PATH,
                "type",
                "--clearmodifiers",
                "--delay",
                str(self._delay),
                "--",
                text,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.error(f"xdotool falhou (rc={result.returncode}): {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error("xdotool timeout (texto muito longo?)")
            return False
        except Exception as e:
            logger.error(f"Erro ao inserir texto: {e}")
            return False

    def insert_with_newline(self, text: str) -> bool:
        """Insere texto seguido de Enter."""
        return self.insert(text) and self._press_key("Return")

    def _press_key(self, key_name: str) -> bool:
        try:
            subprocess.run(
                [XDOTOOL_PATH, "key", "--clearmodifiers", key_name],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao pressionar {key_name}: {e}")
            return False
