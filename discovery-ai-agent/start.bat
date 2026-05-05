@echo off
cd /d %~dp0

REM Русский комментарий: запускаем frontend в отдельном окне PowerShell.
start "AI Discovery Frontend" powershell -NoExit -Command "Set-Location '%CD%\\frontend'; if (!(Test-Path node_modules)) { npm install }; npm run dev"

cd backend
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
