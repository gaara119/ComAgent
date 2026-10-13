@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\open_manual_review.ps1"
if errorlevel 1 (
  echo Failed to open the review page. See the message above.
  pause
)
