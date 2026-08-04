@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SlashV - build fonts
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Oops - Python was not found on your PATH.
    echo Install Python 3.10+ and tick "Add python.exe to PATH".
    goto :fail
)

echo Starting the build. Detailed progress will scroll below...
echo.
python scripts\make_font.py
if errorlevel 1 goto :fail

echo.
echo ------------------------------------------------------------
echo  All good - fonts are ready in the fonts\ folder.
echo ------------------------------------------------------------
goto :done

:fail
echo.
echo ------------------------------------------------------------
echo  The build didn't finish. Scroll up for the friendly error notes.
echo ------------------------------------------------------------
exit /b 1

:done
if /i "%~1"=="/nopause" exit /b 0
echo.
pause
exit /b 0
