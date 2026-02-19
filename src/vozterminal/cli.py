"""Interface CLI do VozTerminal."""

import os
import sys
import signal
import logging

import click

from vozterminal.config import Config, CONFIG_DIR, CONFIG_FILE
from vozterminal.daemon import VozTerminalDaemon


@click.group()
@click.version_option(package_name="vozterminal")
def cli():
    """VozTerminal - Ditado por voz para terminais Linux."""
    pass


@cli.command()
@click.option("--foreground", "-f", is_flag=True, help="Roda em foreground (não daemoniza)")
def start(foreground: bool):
    """Inicia o daemon de ditado."""
    existing_pid = VozTerminalDaemon.is_running()
    if existing_pid:
        click.echo(f"VozTerminal já está rodando (PID {existing_pid}).")
        sys.exit(1)

    config = Config.load()
    config.ensure_dirs()

    if not config.groq_api_key and not config.openai_api_key:
        click.echo("ERRO: Configure GROQ_API_KEY ou OPENAI_API_KEY.")
        click.echo("  export GROQ_API_KEY='sua-chave-aqui'")
        click.echo("  export OPENAI_API_KEY='sua-chave-aqui'")
        sys.exit(1)

    # Setup logging
    log_handlers = [logging.FileHandler(config.log_file)]
    if foreground:
        log_handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=log_handlers,
    )

    if foreground:
        click.echo(f"VozTerminal iniciando em foreground. Hotkey: {config.hotkey}")
        click.echo("Pressione Ctrl+C para parar.")
        daemon = VozTerminalDaemon(config)
        daemon.run()
    else:
        pid = os.fork()
        if pid > 0:
            click.echo(f"VozTerminal iniciado em background (PID {pid}). Hotkey: {config.hotkey}")
            sys.exit(0)
        else:
            os.setsid()
            daemon = VozTerminalDaemon(config)
            daemon.run()


@cli.command()
def stop():
    """Para o daemon."""
    pid = VozTerminalDaemon.is_running()
    if pid:
        os.kill(pid, signal.SIGTERM)
        click.echo(f"VozTerminal parado (PID {pid}).")
    else:
        click.echo("VozTerminal não está rodando.")


@cli.command()
def status():
    """Mostra status do daemon."""
    pid = VozTerminalDaemon.is_running()
    if pid:
        click.echo(f"VozTerminal rodando (PID {pid})")
    else:
        click.echo("VozTerminal não está rodando")


@cli.command()
def init():
    """Inicializa configuração (cria ~/.vozterminal/ e arquivos padrão)."""
    config = Config()
    config.ensure_dirs()
    if not CONFIG_FILE.exists():
        config.save()
        click.echo(f"Config criado em {CONFIG_FILE}")
    else:
        click.echo(f"Config já existe em {CONFIG_FILE}")
    click.echo()
    click.echo("Próximos passos:")
    click.echo("  1. Configure sua API key:")
    click.echo("     export GROQ_API_KEY='sua-chave-aqui'")
    click.echo("  2. Inicie o daemon:")
    click.echo("     vozterminal start")
    click.echo(f"  3. Pressione {config.hotkey} para ativar ditado")


@cli.command()
def devices():
    """Lista dispositivos de áudio disponíveis."""
    import pyaudio
    pa = pyaudio.PyAudio()
    click.echo("Dispositivos de entrada de áudio:")
    default_idx = pa.get_default_input_device_info()["index"]
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            default = " (PADRÃO)" if i == default_idx else ""
            click.echo(f"  [{i}] {info['name']}{default}")
    pa.terminate()


# --- Subgrupo: dicionário ---

@cli.group("dict")
def dict_group():
    """Gerenciar dicionário pessoal."""
    pass


@dict_group.command("add")
@click.argument("wrong")
@click.argument("correct")
def dict_add(wrong: str, correct: str):
    """Adiciona termo ao dicionário. Ex: vozterminal dict add 'pitom' 'Python'"""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    d.add_replacement(wrong, correct)
    click.echo(f"Adicionado: '{wrong}' → '{correct}'")


@dict_group.command("remove")
@click.argument("wrong")
def dict_remove(wrong: str):
    """Remove termo do dicionário."""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    if d.remove_replacement(wrong):
        click.echo(f"Removido: '{wrong}'")
    else:
        click.echo(f"Termo '{wrong}' não encontrado.")


@dict_group.command("list")
def dict_list():
    """Lista todos os termos do dicionário."""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    replacements = d.get_replacements()
    if replacements:
        for wrong, correct in replacements:
            click.echo(f"  {wrong} → {correct}")
    else:
        click.echo("Dicionário vazio.")


# --- Subgrupo: snippets ---

@cli.group("snippet")
def snippet_group():
    """Gerenciar snippets de voz."""
    pass


@snippet_group.command("add")
@click.argument("name")
@click.argument("text")
def snippet_add(name: str, text: str):
    """Adiciona snippet. Ex: vozterminal snippet add 'git commit' 'git commit -m \"\"'"""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    d.add_snippet(name, text)
    click.echo(f"Snippet '{name}' adicionado.")


@snippet_group.command("remove")
@click.argument("name")
def snippet_remove(name: str):
    """Remove snippet."""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    if d.remove_snippet(name):
        click.echo(f"Snippet '{name}' removido.")
    else:
        click.echo(f"Snippet '{name}' não encontrado.")


@snippet_group.command("list")
def snippet_list():
    """Lista todos os snippets."""
    from vozterminal.dictionary import Dictionary
    config = Config.load()
    d = Dictionary(config.dictionary_path, config.snippets_path)
    snippets = d.list_snippets()
    if snippets:
        for name, text in snippets.items():
            preview = text[:60] + "..." if len(text) > 60 else text
            click.echo(f"  {name} → {preview}")
    else:
        click.echo("Nenhum snippet configurado.")
