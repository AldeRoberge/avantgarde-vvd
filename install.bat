@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  avantgarde-vvd  -  install SlashV fonts (current user)
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_fonts.ps1"
if errorlevel 1 goto :fail

echo.
echo ------------------------------------------------------------
echo  Install OK.
echo  Restart apps that already had the font loaded.
echo ------------------------------------------------------------
goto :done

:fail
echo.
echo ------------------------------------------------------------
echo  Install FAILED. Scroll up for details.
echo ------------------------------------------------------------
exit /b 1

:done
if /i "%~1"=="/nopause" exit /b 0
echo.
pause
exit /b 0
