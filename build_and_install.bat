@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SlashV - build and install (one click)
echo ============================================================
echo.

call "%~dp0build.bat" /nopause
if errorlevel 1 goto :fail

echo.
call "%~dp0install.bat" /nopause
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  You're all set.
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
