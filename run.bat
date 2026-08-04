@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SlashV - build, install, and demos
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Oops - Python was not found on your PATH.
    echo Install Python 3.10+ and tick "Add python.exe to PATH".
    goto :fail
)

echo [1/3] Building fonts...
echo.
python scripts\make_font.py
if errorlevel 1 goto :fail

echo.
echo [2/3] Installing fonts for this Windows user...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_fonts.ps1"
if errorlevel 1 goto :fail

echo.
echo [3/3] Creating preview images...
echo.
echo   demo_avant_garde.py
python scripts\demo_avant_garde.py
if errorlevel 1 goto :fail

echo.
echo   demo_adventor.py
python scripts\demo_adventor.py
if errorlevel 1 goto :fail

echo.
echo   demo_compare.py
python scripts\demo_compare.py
if errorlevel 1 goto :fail

echo.
echo   preview.py
python scripts\preview.py
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  You're all set.
echo    Fonts:   fonts\output\  ^(also installed for this user^)
echo    Previews: images\
echo    Families: AvantGarde SlashV, Adventor SlashV
echo  Restart Word / Illustrator / etc. if they were already open.
echo ============================================================
goto :done

:fail
echo.
echo ============================================================
echo  Something went wrong. Scroll up for the notes, then try again.
echo ============================================================
echo.
pause
exit /b 1

:done
echo.
pause
exit /b 0
