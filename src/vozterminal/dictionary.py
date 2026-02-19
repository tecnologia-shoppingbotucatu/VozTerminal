"""Dicionário pessoal e snippets de voz."""

import json
import logging
from pathlib import Path

logger = logging.getLogger("vozterminal.dictionary")


class Dictionary:
    """Dicionário pessoal e snippets de voz."""

    def __init__(self, dictionary_path: Path, snippets_path: Path):
        self._dict_path = dictionary_path
        self._snippets_path = snippets_path
        self._replacements: dict[str, str] = {}  # errado → correto
        self._snippets: dict[str, str] = {}  # nome → texto expandido
        self._load()

    def _load(self) -> None:
        if self._dict_path.exists():
            with open(self._dict_path) as f:
                self._replacements = json.load(f)
            logger.info(f"Dicionário carregado: {len(self._replacements)} termos")

        if self._snippets_path.exists():
            with open(self._snippets_path) as f:
                self._snippets = json.load(f)
            logger.info(f"Snippets carregados: {len(self._snippets)} snippets")

    def get_replacements(self) -> list[tuple[str, str]]:
        """Retorna lista de (errado, correto)."""
        return list(self._replacements.items())

    def get_snippet(self, name: str) -> str | None:
        """Busca snippet por nome (case-insensitive)."""
        return self._snippets.get(name.lower())

    def list_snippets(self) -> dict[str, str]:
        """Retorna todos os snippets."""
        return dict(self._snippets)

    def add_replacement(self, wrong: str, correct: str) -> None:
        self._replacements[wrong.lower()] = correct
        self._save_dict()

    def remove_replacement(self, wrong: str) -> bool:
        if wrong.lower() in self._replacements:
            del self._replacements[wrong.lower()]
            self._save_dict()
            return True
        return False

    def add_snippet(self, name: str, text: str) -> None:
        self._snippets[name.lower()] = text
        self._save_snippets()

    def remove_snippet(self, name: str) -> bool:
        if name.lower() in self._snippets:
            del self._snippets[name.lower()]
            self._save_snippets()
            return True
        return False

    def get_prompt_hint(self) -> str:
        """Gera hint para a API de transcrição com termos do dicionário."""
        terms = list(self._replacements.values())[:50]
        if terms:
            return "Termos comuns: " + ", ".join(terms)
        return ""

    def _save_dict(self) -> None:
        self._dict_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dict_path, "w") as f:
            json.dump(self._replacements, f, indent=2, ensure_ascii=False)

    def _save_snippets(self) -> None:
        self._snippets_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._snippets_path, "w") as f:
            json.dump(self._snippets, f, indent=2, ensure_ascii=False)
