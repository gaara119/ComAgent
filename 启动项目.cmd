@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_project.ps1"
if errorlevel 1 (
  echo Project startup failed. See the message above.
  pause
)
