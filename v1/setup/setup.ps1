<#
.SYNOPSIS
Automates setup for BlenderMCP on Windows (PowerShell 7+).

.DESCRIPTION
This script will:
  - Verify PowerShell and Python versions
  - Create a virtual environment at `.venv` (optional)
  - Install Python dependencies into the venv (or system Python if venv skipped)
  - Optionally install `uv` (uvx) if missing
  - Add `$env:USERPROFILE\.local\bin` to the user PATH if needed
  - Set `BLENDER_HOST` and `BLENDER_PORT` using `setx`

.PARAMETER Force
If specified, skip interactive prompts and use defaults.

.PARAMETER BlenderHost
Value to set for BLENDER_HOST (default: host.docker.internal)

.PARAMETER BlenderPort
Value to set for BLENDER_PORT (default: 9876)

.PARAMETER NoUvInstall
If present, skip trying to install `uv` even if missing.

.EXAMPLE
./setup.ps1 -Force

#>

param(
    [switch]$Force,
    [string]$BlenderHost = "host.docker.internal",
    [int]$BlenderPort = 9876,
    [switch]$NoUvInstall
)

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m) { Write-Host "[ERR]  $m" -ForegroundColor Red }

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Warn "PowerShell 7+ is recommended. Detected: $($PSVersionTable.PSVersion)"
    if (-not $Force) {
        $ans = Read-Host "Continue anyway? [y/N]"
        if ($ans -notin @('y','Y','yes','Yes')) { Write-Err "Aborting."; exit 2 }
    }
}

# Find Python executable
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)?.Path
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command python3 -ErrorAction SilentlyContinue)?.Path
}
if (-not $pythonCmd) {
    Write-Err "Python 3.10+ not found in PATH. Please install Python and retry."; exit 1
}

# Check Python version
# Use a single-quoted Python command to avoid PowerShell interpolation of $ and braces
$pyVer = & $pythonCmd -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))' 2>$null
if (-not $pyVer) { Write-Err "Unable to detect Python version"; exit 1 }
$pyMajor, $pyMinor = $pyVer -split '\.'
if ([int]$pyMajor -lt 3 -or ([int]$pyMajor -eq 3 -and [int]$pyMinor -lt 10)) {
    Write-Err "Python 3.10+ is required. Detected: $pyVer"; exit 1
}
Write-Ok "Detected Python $pyVer"

# Create virtual environment
if (-not (Test-Path .venv)) {
    if ($Force -or (Read-Host "Create virtual environment at .venv? [Y/n]") -ne 'n') {
        Write-Info "Creating virtual environment at .venv ..."
        & $pythonCmd -m venv .venv
        if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create virtual environment"; exit 1 }
        Write-Ok "Virtual environment created at .venv"
    }
}

$venvPython = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Warn "Virtual environment Python not found; using system Python ($pythonCmd) to install packages"
    $venvPython = $pythonCmd
} else {
    Write-Info "Using venv Python: $venvPython"
}

# Upgrade pip and install project (editable)
Write-Info "Upgrading pip and installing project dependencies..."
& $venvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { Write-Warn "pip upgrade had non-zero exit code" }
& $venvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { Write-Err "Failed to install project dependencies"; exit 1 }
Write-Ok "Python dependencies installed"

# Check for uvx/uv
if (-not $NoUvInstall) {
    if (-not (Get-Command uvx -ErrorAction SilentlyContinue)) {
        if ($Force -or (Read-Host "'uvx' not found. Install uv now? [Y/n]") -ne 'n') {
            Write-Info "Installing uv (uvx) ..."
            try {
                Invoke-Expression (Invoke-RestMethod 'https://astral.sh/uv/install.ps1')
                Write-Ok "uv install script executed."
            } catch {
                Write-Warn "Failed to run uv install script: $_"
            }
        } else {
            Write-Warn "Skipping uv installation. You can run the install script manually later."
        }
    } else {
        Write-Ok "Found uvx: $(Get-Command uvx).Path"
    }

    # Add $env:USERPROFILE\.local\bin to user PATH if present
    $localBin = "$env:USERPROFILE\.local\bin"
    if (Test-Path $localBin) {
        $currentUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        $pathParts = $currentUserPath -split ';' | Where-Object { $_ -ne '' }
        if ($pathParts -notcontains $localBin) {
            Write-Info "Adding $localBin to user PATH ..."
            $newUserPath = "$currentUserPath;$localBin"
            [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
            Write-Ok "Added $localBin to the user PATH. Restart your terminal/VS Code or your MCP client (e.g., Ollama) to pick up the change."
        } else {
            Write-Ok "$localBin already in user PATH"
        }
    } else {
        Write-Warn "$localBin not found. If uv installs here later, re-run this script or add the folder to your PATH manually."
    }
}

# Set BLENDER_HOST and BLENDER_PORT using setx
try {
    Write-Info "Setting BLENDER_HOST and BLENDER_PORT for the user (persistent)..."
    & setx BLENDER_HOST "$BlenderHost" | Out-Null
    & setx BLENDER_PORT "$BlenderPort" | Out-Null
    Write-Ok "Set BLENDER_HOST=$BlenderHost and BLENDER_PORT=$BlenderPort (user environment)."
    Write-Info "Note: restart your terminal / VS Code or your MCP client (e.g., Ollama) to see these values in new processes."
} catch {
    Write-Warn "Failed to set environment variables with setx: $_"
}

Write-Host "`nSetup complete ✅" -ForegroundColor Green
Write-Host "Next steps: restart your terminal/VS Code or your MCP client (e.g., Ollama); run 'uvx' to confirm uv is installed; ensure Blender addon is installed in Blender." -ForegroundColor Cyan
