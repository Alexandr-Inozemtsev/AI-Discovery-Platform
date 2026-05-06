@echo off
for %%P in (8000 5173) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    echo Stopping PID %%A on port %%P
    taskkill /F /PID %%A >nul 2>nul
  )
)
echo Done.
pause
