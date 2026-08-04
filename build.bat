@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  avantgarde-vvd  -  build SlashV fonts
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python not found on PATH.
    echo Install Python 3.10+ and check "Add python.exe to PATH".
    goto :fail
)

echo Running: python scripts\make_font.py
echo.
python scripts\make_font.py
if errorlevel 1 goto :fail

echo.
echo ------------------------------------------------------------
echo  Build OK. Fonts are in fonts\
echo ------------------------------------------------------------
goto :done

:fail
echo.
echo ------------------------------------------------------------
echo  Build FAILED. Scroll up for details.
echo ------------------------------------------------------------
exit /b 1

:done
if /i "%~1"=="/nopause" exit /b 0
echo.
pause
exit /b 0
