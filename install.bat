@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SlashV - install fonts (this Windows user)
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_fonts.ps1"
if errorlevel 1 goto :fail

echo.
echo ------------------------------------------------------------
echo  Install finished.
echo  Restart any app that already had the fonts open.
echo ------------------------------------------------------------
goto :done

:fail
echo.
echo ------------------------------------------------------------
echo  Install didn't complete. Scroll up for the details.
echo ------------------------------------------------------------
exit /b 1

:done
if /i "%~1"=="/nopause" exit /b 0
echo.
pause
exit /b 0
