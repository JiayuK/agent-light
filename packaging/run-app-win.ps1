# Launch bundled Agent Light on Windows x64
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ScriptDir "Agent Light"
$MainExe = Join-Path $DistDir "Agent Light.exe"
$HooksExe = Join-Path $DistDir "agent-light-hooks.exe"
$DataHome = Join-Path $env:USERPROFILE ".agent-light"
$PidFile = Join-Path $DataHome "agent-light.pid"

if (-not (Test-Path $MainExe)) {
    Write-Host "✗ 未找到 Agent Light.exe"
    exit 1
}

if ($args.Count -gt 0 -and $args[0] -eq "stop") {
    if (Test-Path $PidFile) {
        $procId = [int](Get-Content $PidFile -Raw).Trim()
        if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
            "stop" | Set-Content (Join-Path $DataHome "shutdown.request")
            Stop-Process -Id $procId -ErrorAction SilentlyContinue
            Write-Host "✓ 已发送停止请求 (PID $procId)"
        }
    } else {
        Write-Host "Agent Light 未在运行"
    }
    exit 0
}

if ($args.Count -gt 0 -and $args[0] -eq "status") {
    if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
        Write-Host "✓ Agent Light 运行中 (PID $(Get-Content $PidFile))"
    } else {
        Write-Host "✗ Agent Light 未运行"
    }
    exit 0
}

if ($args.Count -gt 0 -and $args[0] -eq "install-hooks") {
    & $HooksExe
    exit $LASTEXITCODE
}
if ($args.Count -gt 0 -and $args[0] -eq "uninstall-hooks") {
    & $HooksExe --uninstall
    exit $LASTEXITCODE
}

if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
    Write-Host "Agent Light 已在运行"
    exit 0
}

$exeArgs = @("--quiet")
if ($args.Count -gt 0 -and $args[0] -in @("verbose", "--verbose", "-v")) {
    $exeArgs = @("--verbose")
}
Start-Process -FilePath $MainExe -ArgumentList $exeArgs -WindowStyle Hidden
Start-Sleep -Seconds 1
if ((Test-Path $PidFile) -and (Get-Process -Id ([int](Get-Content $PidFile)) -ErrorAction SilentlyContinue)) {
    Write-Host "✓ Agent Light 已启动 (PID $(Get-Content $PidFile))"
} else {
    Write-Host "✗ 启动失败"
    exit 1
}
