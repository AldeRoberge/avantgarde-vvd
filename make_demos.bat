@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  SlashV - regenerate preview PNGs
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Oops - Python was not found on your PATH.
    goto :fail
)

echo [1/4] demo_avant_garde.py
python scripts\demo_avant_garde.py
if errorlevel 1 goto :fail

echo.
echo [2/4] demo_adventor.py
python scripts\demo_adventor.py
if errorlevel 1 goto :fail

echo.
echo [3/4] demo_compare.py
python scripts\demo_compare.py
if errorlevel 1 goto :fail

echo.
echo [4/4] preview.py
python scripts\preview.py
if errorlevel 1 goto :fail

echo.
echo ------------------------------------------------------------
echo  Previews written to images\
echo ------------------------------------------------------------
goto :done

:fail
echo.
echo ------------------------------------------------------------
echo  Preview generation didn't finish. Scroll up for the details.
echo ------------------------------------------------------------
echo.
pause
exit /b 1

:done
echo.
pause
exit /b 0
