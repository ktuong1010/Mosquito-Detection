# Quick deploy script
# Usage: .\deployment\deploy_now.ps1 [IP_ADDRESS]

param(
    [string]$RpiIP = ""
)

$ProjectDir = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectDir

# Try to find IP
if ([string]::IsNullOrEmpty($RpiIP)) {
    Write-Host "`n=== Finding Raspberry Pi ===" -ForegroundColor Cyan
    
    # Try common IPs
    $commonIPs = @("192.168.88.237", "192.168.1.100", "192.168.0.100", "192.168.1.101", "192.168.0.101")
    
    foreach ($ip in $commonIPs) {
        Write-Host "Trying $ip..." -ForegroundColor Gray -NoNewline
        $result = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
        if ($result) {
            $test = ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no khanhtuong@${ip} "echo OK" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host " [FOUND!]" -ForegroundColor Green
                $RpiIP = $ip
                break
            }
        }
        Write-Host " [No]" -ForegroundColor DarkGray
    }
    
    # Try hostname
    if ([string]::IsNullOrEmpty($RpiIP)) {
        Write-Host "Trying raspberrypi.local..." -ForegroundColor Gray -NoNewline
        $test = ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no khanhtuong@raspberrypi.local "echo OK" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [FOUND!]" -ForegroundColor Green
            $RpiIP = "raspberrypi.local"
        } else {
            Write-Host " [No]" -ForegroundColor DarkGray
        }
    }
}

if ([string]::IsNullOrEmpty($RpiIP)) {
    Write-Host "`nCould not find Raspberry Pi automatically." -ForegroundColor Red
    Write-Host "Please provide IP address:" -ForegroundColor Yellow
    Write-Host "  .\deployment\deploy_now.ps1 -RpiIP 192.168.x.x" -ForegroundColor Gray
    exit 1
}

$RpiHost = "khanhtuong@${RpiIP}"
Write-Host "`n=== Deploying to $RpiHost ===" -ForegroundColor Green

# Deploy files
$files = @(
    "config.py",
    "src/model.py", 
    "main.py",
    "scripts/demo.py"
)

foreach ($file in $files) {
    $filePath = Join-Path $ProjectDir $file
    if (Test-Path $filePath) {
        Write-Host "  Deploying $file..." -ForegroundColor Gray -NoNewline
        Get-Content $filePath -Raw | ssh -o ConnectTimeout=10 $RpiHost "cat > ~/MosquitoDetection/$file" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
        } else {
            Write-Host " [FAILED]" -ForegroundColor Red
        }
    } else {
        Write-Host "  $file not found" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Verifying ===" -ForegroundColor Cyan
ssh $RpiHost "cd ~/MosquitoDetection && python3 << 'EOF'
from config import CONFIDENCE_THRESHOLD, MIN_MOSQUITO_CONFIDENCE_MARGIN
print('Config OK:', CONFIDENCE_THRESHOLD, MIN_MOSQUITO_CONFIDENCE_MARGIN)
EOF
"
ssh $RpiHost "cd ~/MosquitoDetection && python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from scripts.demo import DemoSystem
print('Import OK!')
EOF
"

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "Raspberry Pi IP: $RpiIP" -ForegroundColor Yellow
Write-Host "Test with: ssh $RpiHost 'cd ~/MosquitoDetection && python3 scripts/demo.py'" -ForegroundColor Gray
