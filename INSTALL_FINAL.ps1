$ErrorActionPreference = 'Stop'
$Target = 'C:\digital\platform'
$Source = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`nSEID DIGITAL PLATFORM — FINAL INSTALLER" -ForegroundColor Cyan
Write-Host "Source: $Source"
Write-Host "Target: $Target`n"

if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Path $Target -Force | Out-Null }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backup = Join-Path $Target "backups\pre_final_upgrade_$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null

# Preserve the user's existing database, media, environment file and Git history.
foreach ($name in @('db.sqlite3','db.sqlite3.bak','.env')) {
    $path = Join-Path $Target $name
    if (Test-Path $path) { Copy-Item $path $backup -Force }
}
foreach ($name in @('media','staticfiles')) {
    $path = Join-Path $Target $name
    if (Test-Path $path) { Copy-Item $path $backup -Recurse -Force }
}

# Copy the final application code. Existing data folders and local environment are excluded.
$exclude = @('db.sqlite3','db.sqlite3.bak','.env','venv','.git','media','staticfiles','backups')
Get-ChildItem -LiteralPath $Source -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Target -Recurse -Force
}

Set-Location $Target
if (-not (Test-Path '.\venv\Scripts\python.exe')) {
    Write-Host 'Creating virtual environment...' -ForegroundColor Yellow
    python -m venv venv
}
$Python = Join-Path $Target 'venv\Scripts\python.exe'

Write-Host 'Installing/updating dependencies...' -ForegroundColor Yellow
& $Python -m pip install -r requirements.txt

Write-Host 'Applying database migrations...' -ForegroundColor Yellow
& $Python manage.py migrate --noinput

Write-Host 'Creating safe seed data...' -ForegroundColor Yellow
& $Python manage.py site_seed

Write-Host 'Collecting static files...' -ForegroundColor Yellow
$env:DEBUG = 'True'
& $Python manage.py collectstatic --noinput
Remove-Item Env:DEBUG -ErrorAction SilentlyContinue

Write-Host "`nFINAL INSTALL COMPLETE." -ForegroundColor Green
Write-Host "Backup: $backup" -ForegroundColor Green
Write-Host "Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "Then: `$env:DEBUG = 'True'; python manage.py runserver" -ForegroundColor Cyan
Write-Host "Admin: http://127.0.0.1:8000/secure-console-7f3a91/" -ForegroundColor Cyan
