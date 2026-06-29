# Agent Light launcher for Windows x64
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$DataHome = Join-Path $env:USERPROFILE ".agent-light"
$PidFile = Join-Path $DataHome "agent-light.pid"
$LogFile = Join-Path $DataHome "logs\agent-light.log"

if ($args.Count -gt 0 -and $args[0] -eq "stop") {
    if (Test-Path $PidFile) {
        $pidText = Get-Content $PidFile -Raw
        $procId = [int]$pidText.Trim()
        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
            New-Item -ItemType Directory -Force -Path $DataHome | Out-Null
            "stop" | Set-Content (Join-Path $DataHome "shutdown.request")
            Stop-Process -Id $procId -ErrorAction SilentlyContinue
            Write-Host "✓ 已发送停止请求 (PID $procId)"
        } else {
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            Write-Host "进程 $procId 已不存在，清理 PID 文件"
        }
    } else {
        Write-Host "Agent Light 未在运行"
    }
    exit 0
}

if ($args.Count -gt 0 -and $args[0] -eq "status") {
    if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
        Write-Host "✓ Agent Light 运行中 (PID $(Get-Content $PidFile))"
        if (Test-Path $LogFile) { Write-Host "  日志: $LogFile" }
    } else {
        Write-Host "✗ Agent Light 未运行"
    }
    exit 0
}

$Python = $null
foreach ($candidate in @("python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        if ($candidate -eq "py") {
            $Python = "py -3"
        } else {
            $Python = "python"
        }
        break
    }
}
if (-not $Python) {
    Write-Host "✗ 未找到 Python 3.9+"
    exit 1
}

$VenvPy = Join-Path $ScriptDir ".venv\Scripts\python.exe"
function Test-Venv {
    return (Test-Path $VenvPy) -and (& $VenvPy -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { $true } else { $false })
}

if (-not (Test-Venv)) {
    if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
    Write-Host "首次运行，正在创建虚拟环境..."
    if ($Python -eq "py -3") { & py -3 -m venv .venv } else { & python -m venv .venv }
    & $VenvPy -m pip install --upgrade pip setuptools -q
    & $VenvPy -m pip install -e . -q
    Write-Host "✓ 依赖安装完成"
}

if ($args.Count -gt 0 -and $args[0] -eq "install-hooks") {
    & $VenvPy -m agent_light.agent_hooks.install
    exit $LASTEXITCODE
}
if ($args.Count -gt 0 -and $args[0] -eq "uninstall-hooks") {
    & $VenvPy -m agent_light.agent_hooks.install --uninstall
    exit $LASTEXITCODE
}
if ($args.Count -gt 0 -and $args[0] -eq "paths") {
    & $VenvPy -m agent_light.path_check
    exit $LASTEXITCODE
}

$VerboseArgs = @()
if ($args.Count -gt 0 -and $args[0] -in @("verbose", "--verbose", "-v")) {
    $VerboseArgs = @("--verbose")
    $args = $args[1..($args.Length)]
}

if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
    Write-Host "Agent Light 已在运行 (PID $(Get-Content $PidFile))"
    exit 0
}

Write-Host "启动 Agent Light..."
if ($VerboseArgs.Count -gt 0) {
    & $VenvPy -m agent_light.main @VerboseArgs @args
} else {
    Start-Process -FilePath $VenvPy -ArgumentList @("-m", "agent_light.main", "--quiet") -WindowStyle Hidden
    Start-Sleep -Seconds 1
    if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
        Write-Host "✓ Agent Light 已启动 (PID $(Get-Content $PidFile))"
    } else {
        Write-Host "✗ 启动失败，请运行 .\run.ps1 verbose"
        exit 1
    }
}
