@echo off
title A.L.P. Screen Translator
cd /d "%~dp0"
echo Ekran Cevirici Baslatiliyor...

:: 1. Kullanıcı Profili Yolu (%USERPROFILE%\python311\python.exe)
if exist "%USERPROFILE%\python311\python.exe" (
    "%USERPROFILE%\python311\python.exe" main.py
    goto end
)

:: 2. Standart AppData Python Yolu
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" main.py
    goto end
)

:: 3. Windows Python Launcher (py -3)
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    py -3 main.py
    goto end
)

:: 4. System PATH uzerindeki python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python main.py
    goto end
)

echo.
echo [HATA] Python calistirilamadi! Lutfen Python 3'un kurulu oldugundan emin olun.
echo.

:end
pause
