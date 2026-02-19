"""Escuta hotkey global para toggle de ditado."""

import logging
import re
from pynput import keyboard

logger = logging.getLogger("vozterminal.hotkey")

# Mapeamento de nomes amigáveis para keys do pynput
MODIFIER_MAP = {
    "super": keyboard.Key.cmd,
    "ctrl": keyboard.Key.ctrl_l,
    "alt": keyboard.Key.alt_l,
    "shift": keyboard.Key.shift_l,
}

# Teclas especiais (não-modificadores)
SPECIAL_KEY_MAP = {
    "f1": keyboard.Key.f1,
    "f2": keyboard.Key.f2,
    "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7,
    "f8": keyboard.Key.f8,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "f11": keyboard.Key.f11,
    "f12": keyboard.Key.f12,
    "esc": keyboard.Key.esc,
    "space": keyboard.Key.space,
    "tab": keyboard.Key.tab,
}


def parse_hotkey(hotkey_str: str) -> tuple[set, object]:
    """
    Parseia hotkey string em (modifiers, key).
    Ex: "ctrl+shift+v" → ({Key.ctrl_l, Key.shift_l}, KeyCode('v'))
    Ex: "f9" → (set(), Key.f9)
    """
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    modifiers = set()
    main_key = None

    for part in parts:
        if part in MODIFIER_MAP:
            modifiers.add(MODIFIER_MAP[part])
        elif part in SPECIAL_KEY_MAP:
            main_key = SPECIAL_KEY_MAP[part]
        elif len(part) == 1:
            main_key = keyboard.KeyCode.from_char(part)
        else:
            logger.warning(f"Tecla desconhecida: '{part}'")

    return modifiers, main_key


class HotkeyListener:
    """Escuta hotkey global e chama callback."""

    def __init__(self, hotkey_str: str, on_activate: callable):
        self._hotkey_str = hotkey_str
        self._on_activate = on_activate
        self._modifiers, self._main_key = parse_hotkey(hotkey_str)
        self._pressed_modifiers: set = set()
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        """Inicia listener em thread daemon."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info(f"Hotkey '{self._hotkey_str}' registrada.")

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None

    def update_hotkey(self, new_hotkey_str: str) -> None:
        """Atualiza hotkey em runtime."""
        self.stop()
        self._hotkey_str = new_hotkey_str
        self._modifiers, self._main_key = parse_hotkey(new_hotkey_str)
        self._pressed_modifiers.clear()
        self.start()

    def _on_press(self, key) -> None:
        # Rastreia modificadores pressionados
        if key in MODIFIER_MAP.values():
            self._pressed_modifiers.add(key)
            return

        # Normaliza a tecla para comparação
        if self._main_key is None:
            return

        key_match = False
        if isinstance(self._main_key, keyboard.Key):
            key_match = (key == self._main_key)
        elif isinstance(self._main_key, keyboard.KeyCode):
            if isinstance(key, keyboard.KeyCode):
                key_match = (key.char == self._main_key.char if key.char else False)

        if key_match and self._modifiers.issubset(self._pressed_modifiers):
            self._on_activate()

    def _on_release(self, key) -> None:
        if key in MODIFIER_MAP.values():
            self._pressed_modifiers.discard(key)
