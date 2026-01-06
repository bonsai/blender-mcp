# Package the Blender MCP addon for Blender 5.0
# This creates a zip file with the proper folder structure
# CRITICAL: The zip must contain blender_mcp/ folder at top level, not files directly

$addonName = "blender_mcp"
$zipName = "blender_mcp.zip"
$tempBaseDir = Join-Path -Path $env:TEMP -ChildPath "blender_mcp_build"
$tempDir = Join-Path -Path $tempBaseDir -ChildPath $addonName
$zipPath = Join-Path -Path (Get-Location) -ChildPath $zipName

# Clean up any existing temp directory
if (Test-Path $tempBaseDir) {
    Remove-Item -Path $tempBaseDir -Recurse -Force
}

# Create the addon folder structure: tempBaseDir/blender_mcp/
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy addon.py to the temp directory
Copy-Item -Path "addon.py" -Destination (Join-Path -Path $tempDir -ChildPath "addon.py")

# Create __init__.py (empty file to mark as Python package)
$initPath = Join-Path -Path $tempDir -ChildPath "__init__.py"
Set-Content -Path $initPath -Value ""

# Remove existing zip if present
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

# Create the zip file from the base directory (so blender_mcp/ is at top level)
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempBaseDir, $zipPath)

# Clean up temp directory
Remove-Item -Path $tempBaseDir -Recurse -Force

Write-Host "✓ Addon packaged successfully: $zipName" -ForegroundColor Green
Write-Host ""
Write-Host "ZIP structure verified:" -ForegroundColor Cyan
Write-Host "  blender_mcp.zip"
Write-Host "  └─ blender_mcp/"
Write-Host "     ├─ addon.py"
Write-Host "     └─ __init__.py"
Write-Host ""
Write-Host "Next steps in Blender:" -ForegroundColor Cyan
Write-Host "1. Go to Edit → Preferences → Add-ons"
Write-Host "2. Click 'Install...' button (top right)"
Write-Host "3. Select '$zipName'"
Write-Host "4. Search for 'BlenderMCP' and enable it"
Write-Host ""
Write-Host "The zip file is ready at: $zipPath" -ForegroundColor Yellow
