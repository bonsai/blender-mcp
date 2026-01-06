<#
.SYNOPSIS
Start an Ollama local model and (optionally) the BlenderMCP server (uvx blender-mcp).

.DESCRIPTION
This script helps you run a local Ollama model (pull + run) and optionally starts the MCP server
that connects to Blender (via `uvx blender-mcp`). It records PIDs so you can stop them later.

.PARAMETER Model
Ollama model name to run (e.g., "llama2" or a custom model). Default: "ollama/mcp".

.PARAMETER OllamaPort
Port to check for Ollama model API health (default: 11434).

.PARAMETER NoPull
If specified, skip `ollama pull`.

.PARAMETER StartUv
If specified, start the MCP server after starting Ollama (runs `uvx blender-mcp`).

.PARAMETER BlenderHost
Host for Blender addon (default: localhost).

.PARAMETER BlenderPort
Port for Blender addon (default: 9876).

.PARAMETER Force
Skip interactive confirmations.

.EXAMPLE
./start.ps1 -Model "ollama/mcp" -StartUv
#>

param(
    [string]$Model = "ollama/mcp",
    [int]$OllamaPort = 11434,
    [switch]$NoPull,
    [switch]$StartUv,
    [string]$BlenderHost = "localhost",
    [int]$BlenderPort = 9876,
    [switch]$Force
)

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "[✓]   $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[⚠]   $m" -ForegroundColor Yellow }
function Write-Err([string]$m) { Write-Host "[✗]   $m" -ForegroundColor Red }
function Write-Step([string]$m) { Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan; Write-Host "  $m" -ForegroundColor Cyan; Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan }

# Helpers for pid file
$pidDir = Join-Path -Path (Get-Location) -ChildPath ".run"
if (-not (Test-Path $pidDir)) { New-Item -ItemType Directory -Path $pidDir | Out-Null }
$ollamaPidFile = Join-Path -Path $pidDir -ChildPath "ollama.pid"
$uvxPidFile = Join-Path -Path $pidDir -ChildPath "uvx.pid"

Write-Step "BLENDER MCP STARTUP"
Write-Info "Model: $Model"
Write-Info "Ollama Port: $OllamaPort"
Write-Info "MCP Server: $BlenderHost`:$BlenderPort"
Write-Info "Pull Model: $(if ($NoPull) { 'No' } else { 'Yes' })"
Write-Info "Start MCP: $(if ($StartUv) { 'Yes' } else { 'No' })"

# Ensure ollama is present
$ollamaCmd = (Get-Command ollama -ErrorAction SilentlyContinue)?.Path
if (-not $ollamaCmd) {
    Write-Err "'ollama' CLI not found in PATH. Please install Ollama (https://ollama.com/) and ensure 'ollama' is available in PATH."
    exit 1
}
Write-Ok "Ollama CLI found: $ollamaCmd"

# Check if requested model is already running (using 'ollama ps' if available)
function Get-RunningOllamaProcessId {
    try {
        $psOutput = & ollama ps 2>$null
        if ($LASTEXITCODE -eq 0 -and $psOutput) {
            # If any models are shown, assume there's a running service
            return $true
        }
    } catch {
        # ollama ps may not be supported on older versions; fall back to pid file check
    }
    return $false
}

$alreadyRunning = Get-RunningOllamaProcessId
if ($alreadyRunning) {
    Write-Warn "A running Ollama service seems to be active. If you want to start a new one, stop the existing service first or run with -Force to continue."
    if (-not $Force) {
        $ans = Read-Host "Continue anyway? [y/N]"
        if ($ans -notin @('y','Y','yes','Yes')) { Write-Err "Aborting."; exit 2 }
    }
}

# Optionally pull model
Write-Step "STEP 1: PULL MODEL"
if (-not $NoPull) {
    Write-Info "Pulling model '$Model' (may take a while)..."
    try {
        & ollama pull $Model
        if ($LASTEXITCODE -ne 0) { 
            Write-Warn "ollama pull returned exit code $LASTEXITCODE (model may already exist)"
        } else {
            Write-Ok "Model pulled successfully"
        }
    } catch {
        Write-Warn "Failed to run 'ollama pull $Model': $_"
    }
} else {
    Write-Info "Skipping model pull (-NoPull specified)"
}

# Start Ollama model (run in background)
Write-Step "STEP 2: START OLLAMA"
Write-Info "Starting Ollama model '$Model'..."
try {
    $ollamaProc = Start-Process -FilePath "ollama" -ArgumentList @("run", "$Model") -NoNewWindow -PassThru
    Start-Sleep -Seconds 1
    if ($ollamaProc -and $ollamaProc.Id) {
        Set-Content -Path $ollamaPidFile -Value $ollamaProc.Id -Force
        Write-Ok "Ollama started (PID: $($ollamaProc.Id))"
    } else {
        Write-Warn "Could not determine Ollama PID; it may be running in a different process context"
    }
} catch {
    Write-Err "Failed to start Ollama: $_"
    exit 1
}

# Wait for Ollama to be responsive (simple TCP check)
Write-Step "STEP 3: HEALTH CHECK"
Write-Info "Waiting for Ollama on port $OllamaPort (max 30 seconds)..."
$tries = 0
$max = 30
$ollamaUp = $false
while ($tries -lt $max) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect('localhost', $OllamaPort, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne(1000)
        if ($success -and $tcp.Connected) {
            $tcp.Close()
            $ollamaUp = $true
            break
        }
    } catch {
        # ignore
    }
    Start-Sleep -Seconds 1
    $tries++
    Write-Host "." -NoNewline -ForegroundColor Cyan
}

Write-Host ""
if ($ollamaUp) { 
    Write-Ok "Ollama is responding on port $OllamaPort" 
} else { 
    Write-Warn "Ollama did not respond after 30 seconds (may still be loading)"
    Write-Info "You can check status with: ollama ps"
}

# Optionally start uvx (MCP server)
Write-Step "STEP 4: MCP SERVER"
if ($StartUv) {
    $uvxCmd = (Get-Command uvx -ErrorAction SilentlyContinue)?.Path
    if (-not $uvxCmd) {
        Write-Warn "uvx not found in PATH"
        Write-Info "Install 'uv' from: https://astral.sh/uv/"
        Write-Info "Then run: uvx blender-mcp"
    } else {
        Write-Info "Starting MCP server (uvx blender-mcp)..."
        try {
            $uvxProc = Start-Process -FilePath "uvx" -ArgumentList @("blender-mcp") -NoNewWindow -PassThru
            if ($uvxProc -and $uvxProc.Id) {
                Set-Content -Path $uvxPidFile -Value $uvxProc.Id -Force
                Write-Ok "MCP server started (PID: $($uvxProc.Id))"
            } else {
                Write-Warn "Could not determine uvx PID"
            }
        } catch {
            Write-Warn "Failed to start uvx: $_"
        }
    }
} else {
    Write-Info "MCP server not started (-StartUv not specified)"
    Write-Info "To start it manually: uvx blender-mcp"
}

Write-Step "STARTUP COMPLETE"
Write-Host "Status:" -ForegroundColor Cyan
Write-Host "  Model:        $Model" -ForegroundColor Cyan
Write-Host "  Ollama Port:  $OllamaPort" -ForegroundColor Cyan
Write-Host "  MCP Server:   $BlenderHost`:$BlenderPort" -ForegroundColor Cyan
Write-Host "  PID File:     $ollamaPidFile" -ForegroundColor Cyan
if ($StartUv) { Write-Host "  MCP PID File: $uvxPidFile" -ForegroundColor Cyan }

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Green
Write-Host "  1. Verify Ollama is running:  ollama ps" -ForegroundColor Green
Write-Host "  2. Start Blender and install the addon" -ForegroundColor Green
Write-Host "  3. Configure addon to connect to $BlenderHost`:$BlenderPort" -ForegroundColor Green
Write-Host "  4. Test the connection" -ForegroundColor Green

Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  • Check Ollama status:  ollama ps" -ForegroundColor Yellow
Write-Host "  • Stop all processes:   .\stop.ps1" -ForegroundColor Yellow
Write-Host "  • View MCP logs:        Check the MCP server terminal" -ForegroundColor Yellow
