@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
  python "%~dp0scripts\codex_history_manager.py" %*
) else (
  py -3 "%~dp0scripts\codex_history_manager.py" %*
)
exit /b %errorlevel%
