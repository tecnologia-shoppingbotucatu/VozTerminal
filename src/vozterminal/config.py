"""Sistema de configuração do VozTerminal."""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("vozterminal.config")

CONFIG_DIR = Path.home() / ".vozterminal"
CONFIG_FILE = CONFIG_DIR / "config.json"
DICTIONARY_FILE = CONFIG_DIR / "dictionary.json"
SNIPPETS_FILE = CONFIG_DIR / "snippets.json"
LOG_FILE = CONFIG_DIR / "vozterminal.log"


@dataclass
class Config:
    """Configuração completa do VozTerminal."""

    # API Keys (preferência: env var > config file)
    groq_api_key: str | None = None
    openai_api_key: str | None = None

    # Audio
    language: str = "pt"
    vad_aggressiveness: int = 2  # 0-3
    silence_threshold_ms: int = 800
    audio_device_index: int | None = None  # None = padrão do sistema

    # Hotkey
    hotkey: str = "f9"

    # Inserção
    typing_delay_ms: int = 12

    # Processamento de texto
    auto_capitalize: bool = True
    extra_fillers: list[str] = field(default_factory=list)
    extra_punctuation: dict[str, str] = field(default_factory=dict)

    # Caminhos
    dictionary_path: Path = DICTIONARY_FILE
    snippets_path: Path = SNIPPETS_FILE

    # Logging
    log_level: str = "INFO"
    log_file: Path = LOG_FILE

    @classmethod
    def load(cls) -> "Config":
        """Carrega config do arquivo + env vars."""
        data = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                data = json.load(f)

        # Filtra apenas campos válidos do dataclass
        valid_fields = cls.__dataclass_fields__
        config = cls(**{k: v for k, v in data.items() if k in valid_fields})

        # Env vars têm prioridade sobre arquivo
        config.groq_api_key = os.environ.get("GROQ_API_KEY", config.groq_api_key)
        config.openai_api_key = os.environ.get("OPENAI_API_KEY", config.openai_api_key)

        # Converte paths de string para Path
        config.dictionary_path = Path(config.dictionary_path)
        config.snippets_path = Path(config.snippets_path)
        config.log_file = Path(config.log_file)

        return config

    def save(self) -> None:
        """Salva config no arquivo. API keys NÃO são salvas."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        # Converte Path para string para JSON
        for key in ("dictionary_path", "snippets_path", "log_file"):
            data[key] = str(data[key])
        # NÃO salva API keys no arquivo
        data.pop("groq_api_key", None)
        data.pop("openai_api_key", None)
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Config salvo em {CONFIG_FILE}")

    def ensure_dirs(self) -> None:
        """Cria diretórios necessários."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
