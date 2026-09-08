param(
    [switch]$Launch
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

New-Item -ItemType Directory -Force .\logs | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = ".\logs\diagnostics-$Stamp.log"

function Write-Log([string]$Message) {
    $Message | Tee-Object -FilePath $LogPath -Append
}

Write-Log "=== Voice Foundry GPU diagnostics ==="
Write-Log "Timestamp: $(Get-Date -Format o)"
Write-Log "Directory: $(Get-Location)"
Write-Log ""

Write-Log "=== NVIDIA ==="
try { nvidia-smi 2>&1 | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "=== Python ==="
try { & .\.venv\Scripts\python.exe --version 2>&1 | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "=== PyTorch CUDA ==="
$CudaCheck = @"
import torch
print('Torch:', torch.__version__)
print('CUDA build:', torch.version.cuda)
print('CUDA available:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Unavailable')
"@
try { $CudaCheck | & .\.venv\Scripts\python.exe - 2>&1 | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "=== Chatterbox import ==="
try { & .\.venv\Scripts\python.exe -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; print('Chatterbox import passed')" 2>&1 | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "=== Source checks ==="
try { Select-String -Path .\cloud_gpu_app.py -Pattern 'sf.write|torchaudio.save|LANGUAGES' | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "=== Git ==="
try { git status --short --branch 2>&1 | Tee-Object -FilePath $LogPath -Append } catch { Write-Log $_ }

Write-Log "Log written to: $LogPath"

if ($Launch) {
    Write-Log "=== Launching app ==="
    $PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $Command = '"' + $PythonPath + '" cloud_gpu_app.py 2>&1'
    cmd.exe /c $Command | Tee-Object -FilePath $LogPath -Append
    Write-Log "App process exited with code: $LASTEXITCODE"
}