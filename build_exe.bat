@echo off
REM Script de build do VozTerminal para Windows - gera executavel standalone
echo === VozTerminal - Build do Executavel (Windows) ===
echo.

REM Verifica venv
if not exist ".venv" (
    echo ERRO: .venv nao encontrado. Execute: python -m venv .venv
    exit /b 1
)

REM Ativa venv
call .venv\Scripts\activate.bat

REM Verifica dependencias de build
echo [1/3] Verificando dependencias...
pip install -q pyinstaller customtkinter

REM Limpa builds anteriores
echo [2/3] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Gera executavel
echo [3/3] Gerando executavel (pode demorar 1-2 minutos)...
pyinstaller vozterminal.spec --clean --noconfirm

REM Verifica resultado
if exist "dist\VozTerminal.exe" (
    echo.
    echo Build concluido com sucesso!
    echo.
    echo   Executavel: dist\VozTerminal.exe
    echo.
    echo Para usar: dist\VozTerminal.exe
) else (
    echo.
    echo ERRO: Executavel nao foi gerado. Verifique os logs acima.
    exit /b 1
)

pause
