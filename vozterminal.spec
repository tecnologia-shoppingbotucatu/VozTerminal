# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file para VozTerminal."""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Dados do CustomTkinter (temas, assets visuais)
ctk_datas = collect_data_files('customtkinter')

# Binários do sistema: libportaudio
portaudio_binaries = []
portaudio_dir = '/usr/lib/x86_64-linux-gnu'
for fname in os.listdir(portaudio_dir):
    if fname.startswith('libportaudio') and '.so' in fname:
        full_path = os.path.join(portaudio_dir, fname)
        if os.path.isfile(full_path):
            portaudio_binaries.append((full_path, '.'))

a = Analysis(
    ['src/vozterminal/gui.py'],
    pathex=['src'],
    binaries=portaudio_binaries,
    datas=ctk_datas,
    hiddenimports=[
        # Modulos do VozTerminal
        'vozterminal',
        'vozterminal.__init__',
        'vozterminal.config',
        'vozterminal.daemon',
        'vozterminal.audio',
        'vozterminal.transcriber',
        'vozterminal.text_processor',
        'vozterminal.inserter',
        'vozterminal.hotkey',
        'vozterminal.dictionary',
        # Dependencias que PyInstaller pode nao detectar
        'webrtcvad',
        'pyaudio',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._xorg',
        'pynput.mouse',
        'pynput.mouse._xorg',
        'Xlib',
        'groq',
        'openai',
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'httpcore',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sniffio',
        'certifi',
        'click',
        'customtkinter',
        'darkdetect',
    ],
    hookspath=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL',
        'IPython', 'jupyter', 'notebook',
        'test', 'unittest', 'doctest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VozTerminal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)
