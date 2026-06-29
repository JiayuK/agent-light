# Build standalone Agent Light for Windows x64 (PyInstaller one-folder zip).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Version = $args[0]
if (-not $Version) {
    $Version = (Select-String -Path pyproject.toml -Pattern '^version = ' | ForEach-Object { $_ -replace '.*"(.*)".*', '$1' })
}

$Dist = Join-Path $Root "dist"
$Stage = Join-Path $Dist "agent-light-$Version-windows-x64"
$ZipPath = Join-Path $Dist "agent-light-$Version-windows-x64.zip"

Write-Host "Building Agent Light $Version for Windows x64 ..."

python -m pip install --upgrade pip setuptools wheel -q
python -m pip install pyinstaller pystray pillow -q
python -m pip install -e . -q

if (Test-Path (Join-Path $Root "build")) { Remove-Item -Recurse -Force (Join-Path $Root "build") }
if (Test-Path (Join-Path $Dist "Agent Light")) { Remove-Item -Recurse -Force (Join-Path $Dist "Agent Light") }
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

python -m PyInstaller packaging/agent-light-win.spec --noconfirm --clean

$Built = Join-Path $Dist "Agent Light"
if (-not (Test-Path (Join-Path $Built "Agent Light.exe"))) {
    Write-Host "✗ 构建失败：未生成 Agent Light.exe"
    exit 1
}

New-Item -ItemType Directory -Force -Path $Stage | Out-Null
Copy-Item -Recurse $Built (Join-Path $Stage "Agent Light")
Copy-Item (Join-Path $Root "packaging/run-app-win.ps1") (Join-Path $Stage "run-app.ps1")

Compress-Archive -Path $Stage -DestinationPath $ZipPath -Force
Write-Host "✓ $ZipPath"
