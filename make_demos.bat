@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  avantgarde-vvd  -  regenerate preview PNGs
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] python not found on PATH.
    goto :fail
)

echo [1/3] demo_avant_garde.py
python scripts\demo_avant_garde.py
if errorlevel 1 goto :fail

echo.
echo [2/3] demo_adventor.py
python scripts\demo_adventor.py
if errorlevel 1 goto :fail

echo.
echo [3/3] preview.py
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
echo  Preview generation FAILED. Scroll up for details.
echo ------------------------------------------------------------
echo.
pause
exit /b 1

:done
echo.
pause
exit /b 0
