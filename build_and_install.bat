@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  avantgarde-vvd  -  build + install (one click)
echo ============================================================
echo.

call "%~dp0build.bat" /nopause
if errorlevel 1 goto :fail

echo.
call "%~dp0install.bat" /nopause
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  Done. Families installed:
echo    - AvantGarde SlashV
echo    - Adventor SlashV
echo  Restart Word / Illustrator / etc. if they were open.
echo ============================================================
goto :done

:fail
echo.
echo ============================================================
echo  FAILED. Scroll up for the error logs.
echo ============================================================
echo.
pause
exit /b 1

:done
echo.
pause
exit /b 0
