# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file para VozTerminal - multiplataforma."""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Dados do CustomTkinter (temas, assets visuais)
ctk_datas = collect_data_files('customtkinter')

# Binários por plataforma
portaudio_binaries = []
if sys.platform != "win32":
    # Linux: precisa bundlar libportaudio manualmente
    portaudio_dir = '/usr/lib/x86_64-linux-gnu'
    if os.path.isdir(portaudio_dir):
        for fname in os.listdir(portaudio_dir):
            if fname.startswith('libportaudio') and '.so' in fname:
                full_path = os.path.join(portaudio_dir, fname)
                if os.path.isfile(full_path):
                    portaudio_binaries.append((full_path, '.'))
# Windows: PyAudio wheel já inclui portaudio.dll automaticamente

# Hidden imports por plataforma
platform_hiddenimports = []
if sys.platform == "win32":
    platform_hiddenimports = [
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'ctypes',
        'ctypes.wintypes',
    ]
else:
    platform_hiddenimports = [
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
        'Xlib',
    ]

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
        'pynput.mouse',
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
    ] + platform_hiddenimports,
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
    strip=(sys.platform != "win32"),  # strip apenas no Linux
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/icon.ico' if sys.platform == "win32" and os.path.exists('assets/icon.ico') else None,
)
