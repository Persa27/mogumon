# MoguMoguMonster launch script
# MoguMoguMonster is now a static site (no backend) - this just serves ./public locally.
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3."
    exit 1
}

Write-Host "Starting MoguMoguMonster..."
Write-Host "URL: http://localhost:$Port"
Write-Host "Stop: Ctrl+C"
Write-Host ""

Set-Location $PSScriptRoot
python -m http.server $Port --directory public
