@echo off
:: ============================================================
:: start.bat – One-click launcher for Livelihood Assistant
:: Works even if Python is not on PATH by searching common paths
:: ============================================================

TITLE Livelihood Assistant - Powered by Gemma 4
COLOR 0B

echo.
echo  ==========================================
echo   Livelihood Assistant ^| Gemma 4 Powered
echo   Empowering India's Informal Workers
echo  ==========================================
echo.

:: Try to find Python
SET PYTHON_EXE=

:: Check common install locations
FOR %%P IN (
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
  "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
  "C:\Python312\python.exe"
  "C:\Python311\python.exe"
  "C:\Python310\python.exe"
  "%USERPROFILE%\miniconda3\python.exe"
  "%USERPROFILE%\anaconda3\python.exe"
) DO (
  IF EXIST %%P (
    SET PYTHON_EXE=%%P
    GOTO :found_python
  )
)

:: Try PATH
WHERE python >NUL 2>NUL
IF %ERRORLEVEL% EQU 0 (
  SET PYTHON_EXE=python
  GOTO :found_python
)

WHERE python3 >NUL 2>NUL
IF %ERRORLEVEL% EQU 0 (
  SET PYTHON_EXE=python3
  GOTO :found_python
)

echo [ERROR] Python not found. Please install Python 3.10+ from:
echo         https://www.python.org/downloads/
echo         Then re-run this script.
pause
EXIT /B 1

:found_python
echo [OK] Python found: %PYTHON_EXE%
echo.

:: Install dependencies if not present
echo [INFO] Checking/installing dependencies...
%PYTHON_EXE% -m pip install fastapi "uvicorn[standard]" python-multipart --quiet --disable-pip-version-check

IF %ERRORLEVEL% NEQ 0 (
  echo [WARN] Dependency install had issues. Trying to start anyway...
)

echo.
echo [OK] Starting server at http://localhost:8000
echo [OK] Press CTRL+C to stop
echo.

:: Open browser after short delay (Windows only)
START "" /B timeout /t 2 /nobreak >NUL & START "" "http://localhost:8000"

:: Run the server
%PYTHON_EXE% app.py

pause
