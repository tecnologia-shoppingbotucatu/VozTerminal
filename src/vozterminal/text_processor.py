"""Pipeline de pós-processamento de texto transcrito."""

import re
import logging
from vozterminal.dictionary import Dictionary

logger = logging.getLogger("vozterminal.text_processor")

# Fillers em português para remover
DEFAULT_FILLERS = [
    r"\b[eé]{2,}\b",
    r"\bhum+\b",
    r"\bahn+\b",
    r"\btipo assim\b",
    r"\btipo\b",
    r"\bné\b",
    r"\bsabe\b",
    r"\bassi+m\b",
]

# Substituições de pontuação (fala → caractere)
DEFAULT_PUNCTUATION_MAP = {
    "ponto final": ".",
    "ponto": ".",
    "vírgula": ",",
    "virgula": ",",
    "exclamação": "!",
    "exclamacao": "!",
    "interrogação": "?",
    "interrogacao": "?",
    "dois pontos": ":",
    "ponto e vírgula": ";",
    "ponto e virgula": ";",
    "abre parênteses": "(",
    "fecha parênteses": ")",
    "abre parenteses": "(",
    "fecha parenteses": ")",
    "nova linha": "\n",
    "enter": "\n",
    "tab": "\t",
}


class TextProcessor:
    """Pipeline de pós-processamento de texto transcrito."""

    def __init__(
        self,
        dictionary: Dictionary | None = None,
        extra_fillers: list[str] | None = None,
        extra_punctuation: dict[str, str] | None = None,
        enable_auto_capitalize: bool = True,
    ):
        self._dictionary = dictionary
        self._enable_auto_capitalize = enable_auto_capitalize

        # Compila fillers em regex único
        all_fillers = DEFAULT_FILLERS + (extra_fillers or [])
        self._filler_pattern = re.compile(
            "|".join(f"(?:{f})" for f in all_fillers),
            re.IGNORECASE,
        )

        # Punctuation map (mais longo primeiro para evitar match parcial)
        self._punctuation_map = {**DEFAULT_PUNCTUATION_MAP, **(extra_punctuation or {})}
        sorted_keys = sorted(self._punctuation_map.keys(), key=len, reverse=True)
        self._punctuation_pattern = re.compile(
            "|".join(re.escape(k) for k in sorted_keys),
            re.IGNORECASE,
        )

    def process(self, text: str) -> str:
        """Pipeline completo de processamento."""
        if not text:
            return ""

        # 1. Snippets (antes de tudo - podem substituir texto inteiro)
        snippet_result = self._apply_snippets(text)
        if snippet_result != text:
            return snippet_result  # Snippet expandido, retorna sem mais processamento
        text = snippet_result

        # 2. Remove fillers
        text = self._remove_fillers(text)

        # 3. Aplica substituições do dicionário pessoal
        text = self._apply_dictionary(text)

        # 4. Converte palavras de pontuação
        text = self._apply_punctuation(text)

        # 5. Limpa espaços extras
        text = re.sub(r" {2,}", " ", text).strip()

        # 6. Ajusta espaços antes de pontuação (" ." → ".")
        text = re.sub(r"\s+([.,!?;:)\]])", r"\1", text)

        # 7. Auto-capitalize após pontuação final
        if self._enable_auto_capitalize:
            text = self._auto_capitalize(text)

        return text

    def _apply_snippets(self, text: str) -> str:
        """Detecta 'snippet <nome>' e expande."""
        if not self._dictionary:
            return text
        match = re.match(r"^snippet\s+(.+)$", text.strip(), re.IGNORECASE)
        if match:
            snippet_name = match.group(1).strip().lower()
            expanded = self._dictionary.get_snippet(snippet_name)
            if expanded:
                return expanded
        return text

    def _remove_fillers(self, text: str) -> str:
        return self._filler_pattern.sub("", text)

    def _apply_dictionary(self, text: str) -> str:
        if not self._dictionary:
            return text
        for wrong, correct in self._dictionary.get_replacements():
            text = re.sub(
                rf"\b{re.escape(wrong)}\b",
                correct,
                text,
                flags=re.IGNORECASE,
            )
        return text

    def _apply_punctuation(self, text: str) -> str:
        def replace_match(m):
            return self._punctuation_map.get(m.group(0).lower(), m.group(0))
        return self._punctuation_pattern.sub(replace_match, text)

    def _auto_capitalize(self, text: str) -> str:
        if text:
            text = text[0].upper() + text[1:]
        text = re.sub(
            r"([.!?]\s+)(\w)",
            lambda m: m.group(1) + m.group(2).upper(),
            text,
        )
        return text
