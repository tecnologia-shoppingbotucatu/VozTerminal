"""Inserção de texto na janela ativa - multiplataforma."""

import sys
import subprocess
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("vozterminal.inserter")


class BaseInserter(ABC):
    """Interface base para inserção de texto."""

    @abstractmethod
    def insert(self, text: str) -> bool:
        """Insere texto na janela ativa."""
        ...

    @abstractmethod
    def insert_with_newline(self, text: str) -> bool:
        """Insere texto seguido de Enter."""
        ...


class LinuxInserter(BaseInserter):
    """Insere texto usando xdotool type (X11 Linux)."""

    XDOTOOL_PATH = "/usr/bin/xdotool"

    def __init__(self, typing_delay_ms: int = 12):
        self._delay = typing_delay_ms

    def insert(self, text: str) -> bool:
        if not text:
            return True
        try:
            cmd = [
                self.XDOTOOL_PATH,
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
        return self.insert(text) and self._press_key("Return")

    def _press_key(self, key_name: str) -> bool:
        try:
            subprocess.run(
                [self.XDOTOOL_PATH, "key", "--clearmodifiers", key_name],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao pressionar {key_name}: {e}")
            return False


class WindowsInserter(BaseInserter):
    """Insere texto usando SendInput com KEYEVENTF_UNICODE (Win32 API)."""

    def __init__(self, typing_delay_ms: int = 12):
        self._delay = typing_delay_ms

    def insert(self, text: str) -> bool:
        if not text:
            return True
        try:
            import ctypes
            from ctypes import wintypes

            INPUT_KEYBOARD = 1
            KEYEVENTF_UNICODE = 0x0004
            KEYEVENTF_KEYUP = 0x0002

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
                ]

            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("ki", KEYBDINPUT)]
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("_input", _INPUT),
                ]

            inputs = []
            for char in text:
                code = ord(char)
                # UTF-16 surrogate pairs para caracteres acima de U+FFFF (emojis)
                if code > 0xFFFF:
                    high = 0xD800 + ((code - 0x10000) >> 10)
                    low = 0xDC00 + ((code - 0x10000) & 0x3FF)
                    codes = [high, low]
                else:
                    codes = [code]

                for scan_code in codes:
                    # Key down
                    inp_down = INPUT()
                    inp_down.type = INPUT_KEYBOARD
                    inp_down._input.ki.wVk = 0
                    inp_down._input.ki.wScan = scan_code
                    inp_down._input.ki.dwFlags = KEYEVENTF_UNICODE
                    inp_down._input.ki.time = 0
                    inp_down._input.ki.dwExtraInfo = None
                    inputs.append(inp_down)

                    # Key up
                    inp_up = INPUT()
                    inp_up.type = INPUT_KEYBOARD
                    inp_up._input.ki.wVk = 0
                    inp_up._input.ki.wScan = scan_code
                    inp_up._input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                    inp_up._input.ki.time = 0
                    inp_up._input.ki.dwExtraInfo = None
                    inputs.append(inp_up)

            n_inputs = len(inputs)
            array_type = INPUT * n_inputs
            input_array = array_type(*inputs)
            ctypes.windll.user32.SendInput(n_inputs, input_array, ctypes.sizeof(INPUT))
            return True

        except Exception as e:
            logger.error(f"Erro ao inserir texto (Windows): {e}")
            return False

    def insert_with_newline(self, text: str) -> bool:
        if not self.insert(text):
            return False
        return self._press_enter()

    def _press_enter(self) -> bool:
        """Envia tecla Enter via SendInput."""
        try:
            import ctypes
            from ctypes import wintypes

            INPUT_KEYBOARD = 1
            VK_RETURN = 0x0D

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
                ]

            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("ki", KEYBDINPUT)]
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("_input", _INPUT),
                ]

            inputs = []
            # Key down
            inp_down = INPUT()
            inp_down.type = INPUT_KEYBOARD
            inp_down._input.ki.wVk = VK_RETURN
            inp_down._input.ki.wScan = 0
            inp_down._input.ki.dwFlags = 0
            inp_down._input.ki.time = 0
            inp_down._input.ki.dwExtraInfo = None
            inputs.append(inp_down)

            # Key up
            inp_up = INPUT()
            inp_up.type = INPUT_KEYBOARD
            inp_up._input.ki.wVk = VK_RETURN
            inp_up._input.ki.wScan = 0
            inp_up._input.ki.dwFlags = 0x0002  # KEYEVENTF_KEYUP
            inp_up._input.ki.time = 0
            inp_up._input.ki.dwExtraInfo = None
            inputs.append(inp_up)

            array_type = INPUT * 2
            input_array = array_type(*inputs)
            ctypes.windll.user32.SendInput(2, input_array, ctypes.sizeof(INPUT))
            return True

        except Exception as e:
            logger.error(f"Erro ao pressionar Enter (Windows): {e}")
            return False


class TextInserter(BaseInserter):
    """Facade que seleciona implementação por plataforma automaticamente."""

    def __init__(self, typing_delay_ms: int = 12):
        if sys.platform == "win32":
            self._impl = WindowsInserter(typing_delay_ms)
        else:
            self._impl = LinuxInserter(typing_delay_ms)
        logger.info(f"Inserter: {self._impl.__class__.__name__}")

    def insert(self, text: str) -> bool:
        return self._impl.insert(text)

    def insert_with_newline(self, text: str) -> bool:
        return self._impl.insert_with_newline(text)
