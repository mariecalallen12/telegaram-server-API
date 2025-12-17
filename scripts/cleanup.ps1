<# 
Cleanup script for server-first repository layout.

WARNING:
- Only run after you have backed up any real sessions/runs/reports you need.
- This deletes local virtualenv and caches.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Cleaning virtualenv + caches..."

if (Test-Path "venv") {
  Remove-Item -Recurse -Force "venv"
}

Get-ChildItem -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
  Remove-Item -Recurse -Force $_.FullName
}

Get-ChildItem -Recurse -File -Filter "*.pyc" | ForEach-Object {
  Remove-Item -Force $_.FullName
}

Write-Host "Optional artifacts (uncomment to remove):"
Write-Host " - dist/, build/ (PyInstaller outputs)"
Write-Host " - reports/, telegram_runs/ (generated runtime data)"

Write-Host "Done."


