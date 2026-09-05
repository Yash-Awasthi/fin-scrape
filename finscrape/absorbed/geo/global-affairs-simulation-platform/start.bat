@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title IR Intelligence Platform

cd /d "%~dp0"
set "ROOT=%CD%"
set "FRONT=%ROOT%\frontend"

echo.
echo  +==============================================+
echo  ^|   IR Intelligence Platform - Starting...    ^|
echo  +==============================================+
echo.

echo [1/7] Python...
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo  FAIL: Python 3 not found ^| https://www.python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('py -3 --version 2^>^&1') do echo  OK: Python %%v

echo [2/7] Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo  FAIL: Node.js not found ^| https://nodejs.org
    pause
    exit /b 1
)
for /f %%v in ('node --version') do echo  OK: Node.js %%v

echo [3/7] Config...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  WARN: .env created from template. Please set ANTHROPIC_API_KEY.
        start notepad ".env"
        pause
        exit /b 0
    )
    echo  FAIL: .env not found
    pause
    exit /b 1
)
echo  OK

echo [4/7] Python packages...
py -3 -c "import fastapi,sqlalchemy,anthropic,uvicorn,feedparser,pydantic_settings,slowapi,jwt,passlib,reportlab,geopy" >nul 2>&1
if errorlevel 1 (
    echo  Installing... ^(first run may take a few minutes^)
    py -3 -m pip install -r backend\requirements.txt -q --disable-pip-version-check
    if errorlevel 1 (
        echo  FAIL: pip install failed
        echo  Run manually: py -3 -m pip install -r backend\requirements.txt
        pause
        exit /b 1
    )
)
echo  OK

echo [5/7] Database migration...
py -3 -m alembic upgrade head 2>nul
if errorlevel 1 (
    echo  WARN: alembic migration had issues, trying create_all fallback...
    py -3 -c "from backend.db.database import create_all_tables; create_all_tables()" >nul 2>&1
    if errorlevel 1 (
        echo  FAIL: database initialization failed
        pause
        exit /b 1
    )
)
echo  OK

echo [6/7] npm packages...
if not exist "frontend\node_modules" (
    echo  Installing... ^(first run may take a few minutes^)
    pushd frontend
    call npm install --silent
    set "NPM_RC=!ERRORLEVEL!"
    popd
    if not "!NPM_RC!"=="0" (
        echo  FAIL: npm install failed
        pause
        exit /b 1
    )
)
echo  OK

echo [7/7] Checking ports...
call :check_port 8000
call :check_port 5173
echo  OK

echo.
echo Killing any old processes on 8000 / 5173...
call :kill_port 8000
call :kill_port 5173
timeout /t 2 /nobreak >nul

echo Starting backend...
start "IR-Backend [8000]" /d "%ROOT%" cmd /c "py -3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 75 --log-level warning"

echo Waiting for backend...
set /a BE_OK=0
for /L %%i in (1,1,40) do (
    py -3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=2)" >nul 2>&1
    if not errorlevel 1 (
        set /a BE_OK=1
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
)
:backend_ready
if !BE_OK!==1 (
    echo  Backend ready  ^(http://localhost:8000^)
) else (
    echo  WARN: backend is slow to start. Check the IR-Backend window.
)

echo Starting frontend...
start "IR-Frontend [5173]" /d "%FRONT%" cmd /c "npm run dev"

echo Waiting for frontend...
set /a FE_OK=0
for /L %%i in (1,1,40) do (
    py -3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5173/',timeout=2)" >nul 2>&1
    if not errorlevel 1 (
        set /a FE_OK=1
        goto :frontend_ready
    )
    timeout /t 1 /nobreak >nul
)
:frontend_ready
if !FE_OK!==1 (
    echo  Frontend ready ^(http://localhost:5173^)
) else (
    echo  WARN: Vite is still compiling. Browser will open anyway.
)

start "" "http://localhost:5173"

echo.
echo  +==============================================+
echo  ^|  Frontend :  http://localhost:5173          ^|
echo  ^|  Backend  :  http://localhost:8000          ^|
echo  ^|  API Docs :  http://localhost:8000/api/docs ^|
echo  ^|                                              ^|
echo  ^|  Close the two terminal windows to stop.    ^|
echo  +==============================================+
echo.
pause
exit /b 0

:kill_port
set "TARGET_PORT=%~1"
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%TARGET_PORT% " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)
exit /b 0

:check_port
set "CHK_PORT=%~1"
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%CHK_PORT% " ^| findstr "LISTENING"') do (
    echo  WARN: Port %CHK_PORT% is in use ^(PID %%p^), will be killed
)
exit /b 0
