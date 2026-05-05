@echo off
setlocal
set ROOT=%~dp0

echo Starting AI Discovery Platform...

start "AI Discovery Backend" powershell -NoExit -Command "Set-Location '%ROOT%backend'; if (!(Test-Path .venv)) { py -3 -m venv .venv }; .\.venv\Scripts\Activate.ps1; python -m pip install --upgrade pip; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000"

start "AI Discovery Frontend" powershell -NoExit -Command "Set-Location '%ROOT%frontend'; if (!(Test-Path node_modules)) { npm install }; npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 6 /nobreak >nul
start http://localhost:5173

echo Backend:  http://localhost:8000
echo Swagger:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo Для остановки закройте окна backend и frontend
pause
