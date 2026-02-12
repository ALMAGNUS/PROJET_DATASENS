# Libere le port 8001 (API DataSens)
# Usage: .\scripts\kill_port_8001.ps1

$port = 8001
$connections = netstat -ano | Select-String ":$port\s+.*LISTENING"
if (-not $connections) {
    Write-Host "Port $port libre." -ForegroundColor Green
    exit 0
}
foreach ($line in $connections) {
    $parts = $line -split '\s+'
    $pid = $parts[-1]
    if ($pid -match '^\d+$') {
        Write-Host "Arret du processus PID $pid sur le port $port..."
        taskkill /PID $pid /F 2>$null
    }
}
Write-Host "Port $port libere." -ForegroundColor Green
