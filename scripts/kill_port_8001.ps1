# Libere le port 8001 (API DataSens) — tue run_e2_api, uvicorn et ecouteurs residuels.
# Usage: .\scripts\kill_port_8001.ps1

$port = 8001
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }

function Stop-PortListeners {
    $pids = @()
    try {
        $pids = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    } catch {
        # Fallback netstat si Get-NetTCPConnection indisponible
    }
    if (-not $pids) {
        $connections = netstat -ano | Select-String ":$port\s+.*LISTENING"
        foreach ($line in $connections) {
            if ($line -match '\s(\d+)\s*$') { $pids += [int]$Matches[1] }
        }
        $pids = $pids | Select-Object -Unique
    }
    foreach ($procId in $pids) {
        if ($procId -and $procId -ne 0) {
            Write-Host "Arret ecouteur port $port PID $procId..."
            taskkill /PID $procId /F /T 2>$null | Out-Null
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

function Stop-ApiProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object {
            $_.CommandLine -match 'run_e2_api\.py|uvicorn|src\.e2\.api\.main:app'
        } |
        ForEach-Object {
            Write-Host "Arret processus API PID $($_.ProcessId)..."
            taskkill /PID $_.ProcessId /F /T 2>$null | Out-Null
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

1..5 | ForEach-Object {
    Stop-ApiProcesses
    Stop-PortListeners
    Start-Sleep -Milliseconds 800
}

# Netstat Windows peut afficher un PID fantome (ex. 1752 introuvable) : test bind reel.
$bindOk = $false
try {
    $bindCheck = & $pythonExe -c "import socket; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('127.0.0.1', $port)); s.close()" 2>$null
    if ($LASTEXITCODE -eq 0) { $bindOk = $true }
} catch { }

if ($bindOk) {
    Write-Host "Port $port libre (test bind OK)." -ForegroundColor Green
    exit 0
}

$remaining = netstat -ano | Select-String ":$port\s+.*LISTENING"
if ($remaining) {
    Write-Host "ATTENTION: port $port encore occupe (bind impossible)." -ForegroundColor Yellow
    Write-Host "Essayez stop_full.bat ou Gestionnaire des taches (python.exe)." -ForegroundColor Yellow
    $remaining | ForEach-Object { Write-Host $_ }
    exit 1
}

Write-Host "Port $port libre." -ForegroundColor Green
exit 0
