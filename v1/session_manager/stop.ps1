<#
.SYNOPSIS
Stop processes started by start.ps1 (Ollama model and uvx MCP server) and clean up PID files.

.DESCRIPTION
Reads PID files from the .run directory (ollama.pid, uvx.pid), attempts to stop the processes, and removes PID files.

.PARAMETER Force
If specified, don't prompt for confirmation when stopping processes or removing pid files.

.PARAMETER Verbose
If specified, show additional diagnostics (like 'ollama ps' output if ollama is available).

.EXAMPLE
# Stop processes and remove pid files (interactive by default)
./stop.ps1

# Force stop without prompts
./stop.ps1 -Force
#>

param(
    [switch]$Force,
    [switch]$Verbose
)

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m) { Write-Host "[ERR]  $m" -ForegroundColor Red }

$pidDir = Join-Path -Path (Get-Location) -ChildPath ".run"
if (-not (Test-Path $pidDir)) {
    Write-Warn "PID directory '$pidDir' does not exist. Nothing to stop."
    exit 0
}

$pidFiles = @("ollama.pid", "uvx.pid")
$stoppedAny = $false

foreach ($f in $pidFiles) {
    $path = Join-Path -Path $pidDir -ChildPath $f
    if (-not (Test-Path $path)) {
        Write-Info "PID file not found: $f"
        continue
    }

    $content = (Get-Content -Path $path -ErrorAction SilentlyContinue) -join "\n"
    $content = $content.Trim()
    if (-not $content) {
        Write-Warn "PID file '$f' is empty, removing it."
        Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
        continue
    }

    # The file may contain one PID per line; attempt to stop each
    $pids = $content -split '\s+' | Where-Object { $_ -match '^[0-9]+$' }$' }

    foreach ($pidText in $pids) {
        [int]$pid = 0
        try { $pid = [int]$pidText } catch { Write-Warn "Invalid PID in $f: $pidText"; continue }

        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if (-not $proc) {
            Write-Info "No process with PID $pid (from $f) found. Removing pid entry."
            # remove the pid from the file content
            $newContent = ($pids | Where-Object { $_ -ne $pidText }) -join "`n"
            if ($newContent) { Set-Content -Path $path -Value $newContent -Force } else { Remove-Item -Path $path -Force -ErrorAction SilentlyContinue }
            continue
        }

        Write-Info "Found process PID $pid (Name: $($proc.ProcessName)) from $f"

        if (-not $Force) {
            $ans = Read-Host "Stop process PID $pid (Y/n)?"
            if ($ans -notin @('y','Y','yes','Yes','')) { Write-Info "Skipping PID $pid"; continue }
        }

        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Start-Sleep -Milliseconds 300
            $still = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if (-not $still) {
                Write-Ok "Stopped process PID $pid and removed from $f"
                $stoppedAny = $true
            } else {
                Write-Warn "Process PID $pid still running after Stop-Process"
            }
        } catch {
            Write-Warn "Failed to stop PID $pid: $_"
        }

        # Remove the PID from the file after attempting stop
        $remaining = ($pids | Where-Object { $_ -ne $pidText }) -join "`n"
        if ($remaining) {
            Set-Content -Path $path -Value $remaining -Force
        } else {
            Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
        }
    }
}

# If verbose and ollama present, show 'ollama ps' output to help debug
$ollamaCmd = (Get-Command ollama -ErrorAction SilentlyContinue)?.Path
if ($Verbose -and $ollamaCmd) {
    Write-Info "ollama ps output:"
    try { & ollama ps } catch { Write-Warn "Failed to run 'ollama ps': $_" }
}

if ($stoppedAny) { Write-Ok "Stop sequence complete." } else { Write-Info "No processes were stopped by this script." }
