# Blender MCP V2 - 完全自動セットアップスクリプト
# Enterを押すだけで全て完了

param(
    [ValidateSet("install", "daemon", "test", "help", "full", "status", "")]
    [string]$Action = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ========================================
# グローバル変数
# ========================================

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$DAEMON_DIR = "$env:APPDATA\BlenderMCP"
$PID_FILE = Join-Path $DAEMON_DIR "daemon.pid"
$LOG_DIR = Join-Path $DAEMON_DIR "logs"
$script:CHECKS = @()
$script:BLENDER_PATH = $null

# Ensure the src directory is added to the PYTHONPATH
# Log the PYTHONPATH setting for debugging
Write-Host "Setting PYTHONPATH to: $PSScriptRoot"
$env:PYTHONPATH = "$PSScriptRoot"

# Ensure telemetry module is available
if (!(Test-Path "$PSScriptRoot\blender_mcp\telemetry.py")) {
    Write-Host "Copying telemetry.py from v1 to src..."
    Copy-Item -Path "$PSScriptRoot\..\v1\blender_mcp\telemetry.py" -Destination "$PSScriptRoot\blender_mcp"
}

# ========================================
# UI 関数
# ========================================

function Show-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║                                                          ║" -ForegroundColor Cyan
    Write-Host "  ║        🚀 Blender MCP V2 - 完全自動セットアップ 🚀       ║" -ForegroundColor Cyan
    Write-Host "  ║                                                          ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "  ▶ $Message" -ForegroundColor Blue
}

function Write-OK {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Add-Check {
    param([string]$Name, [bool]$Passed, [string]$Details = "")
    $script:CHECKS += @{ Name = $Name; Passed = $Passed; Details = $Details }
    if ($Passed) { Write-OK "$Name" } else { Write-Fail "$Name" }
    if ($Details) { Write-Info $Details }
}

function Ask-Continue {
    param([string]$Message = "続行しますか？")
    Write-Host ""
    Write-Host "  $Message [Enter で続行 / Ctrl+C で中止]" -ForegroundColor Yellow
    Read-Host | Out-Null
}

function Show-Summary {
    $passed = ($script:CHECKS | Where-Object { $_.Passed }).Count
    $failed = ($script:CHECKS | Where-Object { -not $_.Passed }).Count
    
    Write-Host ""
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  結果: ✓ $passed 成功  ✗ $failed 失敗" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor Cyan
    
    return $failed -eq 0
}

# ========================================
# ディレクトリ初期化
# ========================================

function Initialize-Directories {
    if (-not (Test-Path $DAEMON_DIR)) { New-Item -ItemType Directory -Path $DAEMON_DIR -Force | Out-Null }
    if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null }
}

# ========================================
# Blender 検出・インストール
# ========================================

function Find-BlenderPath {
    # 環境変数
    if ($env:BLENDER_PATH -and (Test-Path $env:BLENDER_PATH)) {
        return $env:BLENDER_PATH
    }
    
    # 標準パス
    $paths = @(
        "C:\Program Files\Blender Foundation\Blender*\blender.exe",
        "C:\Program Files (x86)\Blender Foundation\Blender*\blender.exe",
        "$env:LOCALAPPDATA\Blender Foundation\Blender*\blender.exe"
    )
    
    foreach ($pattern in $paths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    
    # PATH
    try { return (Get-Command blender -ErrorAction Stop).Source } catch { return $null }
}

function Install-BlenderGuide {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "  ║              📦 Blender インストールが必要です           ║" -ForegroundColor Yellow
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  インストール方法を選択してください:" -ForegroundColor White
    Write-Host ""
    Write-Host "    [1] winget でインストール (推奨・自動)" -ForegroundColor Green
    Write-Host "    [2] 公式サイトからダウンロード (手動)" -ForegroundColor White
    Write-Host "    [3] パスを手動で入力" -ForegroundColor White
    Write-Host "    [0] 中止" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "  選択 (0-3)"
    
    switch ($choice) {
        "1" {
            Write-Step "winget で Blender をインストール中..."
            try {
                $result = winget install BlenderFoundation.Blender --accept-source-agreements --accept-package-agreements 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "Blender インストール完了"
                    Start-Sleep -Seconds 2
                    return Find-BlenderPath
                } else {
                    Write-Fail "winget インストール失敗"
                    Write-Info "手動でインストールしてください: https://www.blender.org/download/"
                    return $null
                }
            } catch {
                Write-Fail "winget が利用できません"
                return $null
            }
        }
        "2" {
            Write-Host ""
            Write-Host "  ブラウザで公式サイトを開きます..." -ForegroundColor Cyan
            Start-Process "https://www.blender.org/download/"
            Write-Host ""
            Write-Host "  インストール完了後、Enter を押してください" -ForegroundColor Yellow
            Read-Host | Out-Null
            return Find-BlenderPath
        }
        "3" {
            Write-Host ""
            $path = Read-Host "  Blender.exe のパスを入力"
            if (Test-Path $path) {
                return $path
            } else {
                Write-Fail "パスが見つかりません: $path"
                return $null
            }
        }
        default {
            return $null
        }
    }
}


# ========================================
# 環境チェック
# ========================================

function Test-Python {
    Write-Step "Python をチェック中..."
    try {
        $ver = python --version 2>&1
        if ($ver -match "3\.(1[0-9]|[2-9])") {
            Add-Check "Python" $true $ver
            return $true
        } else {
            Add-Check "Python" $false "バージョン 3.10+ が必要です (現在: $ver)"
            return $false
        }
    } catch {
        Add-Check "Python" $false "インストールされていません"
        return $false
    }
}

function Test-UV {
    Write-Step "uv をチェック中..."
    try {
        $ver = uv --version 2>&1
        Add-Check "uv" $true $ver
        return $true
    } catch {
        Write-Warn "uv が見つかりません。インストールを試みます..."
        try {
            Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -OutFile "$env:TEMP\install-uv.ps1"
            & "$env:TEMP\install-uv.ps1"
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
            Add-Check "uv" $true "インストール完了"
            return $true
        } catch {
            Add-Check "uv" $false "インストール失敗"
            return $false
        }
    }
}

function Test-Blender {
    Write-Step "Blender をチェック中..."
    $script:BLENDER_PATH = Find-BlenderPath
    
    if ($script:BLENDER_PATH) {
        Add-Check "Blender" $true $script:BLENDER_PATH
        [Environment]::SetEnvironmentVariable("BLENDER_PATH", $script:BLENDER_PATH, "User")
        return $true
    }
    
    # インストールガイド
    $script:BLENDER_PATH = Install-BlenderGuide
    if ($script:BLENDER_PATH) {
        Add-Check "Blender" $true $script:BLENDER_PATH
        [Environment]::SetEnvironmentVariable("BLENDER_PATH", $script:BLENDER_PATH, "User")
        return $true
    }
    
    Add-Check "Blender" $false "見つかりません"
    return $false
}

# ========================================
# インストール処理
# ========================================

function Install-Dependencies {
    Write-Step "Python 依存パッケージをインストール中..."
    try {
        Push-Location $SCRIPT_DIR
        $output = uv pip install -e ../.. 2>&1
        Pop-Location
        
        if ($LASTEXITCODE -eq 0) {
            Add-Check "依存パッケージ" $true
            return $true
        } else {
            # フォールバック: 直接インストール
            $output = uv pip install "mcp[cli]>=1.3.0" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Add-Check "依存パッケージ" $true "mcp のみ"
                return $true
            }
            Add-Check "依存パッケージ" $false $output
            return $false
        }
    } catch {
        Add-Check "依存パッケージ" $false $_
        return $false
    }
}

function Install-Addon {
    Write-Step "Blender Addon をインストール中..."
    try {
        $blenderDir = Split-Path -Parent $script:BLENDER_PATH
        $versionMatch = [regex]::Match($blenderDir, "Blender\s*(\d+\.\d+)")
        
        if ($versionMatch.Success) {
            $version = $versionMatch.Groups[1].Value
        } else {
            $version = (Get-Item $blenderDir).Name -replace "Blender\s*", ""
        }
        
        $addonDir = "$env:APPDATA\Blender Foundation\Blender\$version\scripts\addons"
        
        if (-not (Test-Path $addonDir)) {
            New-Item -ItemType Directory -Path $addonDir -Force | Out-Null
        }
        
        $addonSource = Join-Path $SCRIPT_DIR "addon.py"
        $addonDest = Join-Path $addonDir "blender_mcp_v2.py"
        
        if (Test-Path $addonSource) {
            Copy-Item $addonSource $addonDest -Force
            Add-Check "Addon インストール" $true $addonDest
            return $true
        } else {
            Add-Check "Addon インストール" $false "addon.py が見つかりません"
            return $false
        }
    } catch {
        Add-Check "Addon インストール" $false $_
        return $false
    }
}

function Set-Environment {
    Write-Step "環境変数を設定中..."
    try {
        [Environment]::SetEnvironmentVariable("BLENDER_HOST", "localhost", "User")
        [Environment]::SetEnvironmentVariable("BLENDER_PORT", "9876", "User")
        $env:BLENDER_HOST = "localhost"
        $env:BLENDER_PORT = "9876"
        Add-Check "環境変数" $true "BLENDER_HOST=localhost, BLENDER_PORT=9876"
        return $true
    } catch {
        Add-Check "環境変数" $false $_
        return $false
    }
}


# ========================================
# Daemon 管理
# ========================================

function Start-Daemon {
    Write-Step "MCP Server を起動中..."
    Initialize-Directories
    
    # 既存プロセス停止
    if (Test-Path $PID_FILE) {
        $oldPid = Get-Content $PID_FILE -ErrorAction SilentlyContinue
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
        Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    
    try {
        $stdoutLog = Join-Path $LOG_DIR "server_stdout.log"
        $stderrLog = Join-Path $LOG_DIR "server_stderr.log"
        
        # ログファイル初期化
        "" | Out-File $stdoutLog -Force
        "" | Out-File $stderrLog -Force
        
        # プロジェクトルートから実行
        $projectRoot = Split-Path -Parent $SCRIPT_DIR
        
        $process = Start-Process -FilePath "python" `
            -ArgumentList "-m blender_mcp.server" `
            -WorkingDirectory $projectRoot `
            -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutLog `
            -RedirectStandardError $stderrLog
        
        $process.Id | Out-File -FilePath $PID_FILE -Force
        Start-Sleep -Seconds 3
        
        if (-not $process.HasExited) {
            Add-Check "MCP Server 起動" $true "PID: $($process.Id)"
            Write-Info "ログ: $stdoutLog"
            return $true
        } else {
            $err = Get-Content $stderrLog -ErrorAction SilentlyContinue | Select-Object -First 5
            Add-Check "MCP Server 起動" $false ($err -join "; ")
            return $false
        }
    } catch {
        Add-Check "MCP Server 起動" $false $_
        return $false
    }
}

function Stop-Daemon {
    Write-Step "MCP Server を停止中..."
    if (Test-Path $PID_FILE) {
        $procId = Get-Content $PID_FILE
        try {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Remove-Item $PID_FILE -Force
            Add-Check "MCP Server 停止" $true "PID: $procId"
            return $true
        } catch {
            Add-Check "MCP Server 停止" $false $_
            return $false
        }
    } else {
        Write-Warn "実行中の Server がありません"
        return $true
    }
}

function Get-DaemonStatus {
    Write-Host ""
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  MCP Server ステータス" -ForegroundColor Cyan
    Write-Host "  ─────────────────────────────────────────────────────────" -ForegroundColor Cyan
    
    if (Test-Path $PID_FILE) {
        $procId = Get-Content $PID_FILE
        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
        
        if ($proc) {
            Write-OK "実行中 (PID: $procId)"
            Write-Info "メモリ: $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB"
        } else {
            Write-Warn "停止 (古い PID ファイルあり)"
            Remove-Item $PID_FILE -Force
        }
    } else {
        Write-Info "停止中"
    }
    
    $logFile = Join-Path $LOG_DIR "server_stdout.log"
    if (Test-Path $logFile) {
        Write-Host ""
        Write-Host "  最新ログ:" -ForegroundColor Gray
        Get-Content $logFile -Tail 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    }
    Write-Host ""
}

# ========================================
# テスト
# ========================================

function Test-Server {
    Write-Step "MCP Server をテスト中..."
    
    # サーバーが起動しているか確認
    if (-not (Test-Path $PID_FILE)) {
        Add-Check "Server テスト" $false "Server が起動していません"
        return $false
    }
    
    $procId = Get-Content $PID_FILE
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    
    if ($proc) {
        Add-Check "Server テスト" $true "正常動作中 (PID: $procId)"
        return $true
    } else {
        Add-Check "Server テスト" $false "プロセスが見つかりません"
        return $false
    }
}

function Test-AddonInstalled {
    Write-Step "Addon インストールを確認中..."
    
    $blenderDir = Split-Path -Parent $script:BLENDER_PATH
    $versionMatch = [regex]::Match($blenderDir, "Blender\s*(\d+\.\d+)")
    
    if ($versionMatch.Success) {
        $version = $versionMatch.Groups[1].Value
    } else {
        $version = (Get-Item $blenderDir).Name -replace "Blender\s*", ""
    }
    
    $addonPath = "$env:APPDATA\Blender Foundation\Blender\$version\scripts\addons\blender_mcp_v2.py"
    
    if (Test-Path $addonPath) {
        Add-Check "Addon 確認" $true $addonPath
        return $true
    } else {
        Add-Check "Addon 確認" $false "見つかりません"
        return $false
    }
}


# ========================================
# メイン処理
# ========================================

function Invoke-FullSetup {
    Show-Banner
    
    Write-Host "  このスクリプトは以下を自動で行います:" -ForegroundColor White
    Write-Host ""
    Write-Host "    1. 環境チェック (Python, uv, Blender)" -ForegroundColor Gray
    Write-Host "    2. 依存パッケージのインストール" -ForegroundColor Gray
    Write-Host "    3. Blender Addon のインストール" -ForegroundColor Gray
    Write-Host "    4. 環境変数の設定" -ForegroundColor Gray
    Write-Host "    5. MCP Server の起動" -ForegroundColor Gray
    Write-Host "    6. 動作テスト" -ForegroundColor Gray
    Write-Host ""
    
    Ask-Continue "準備ができたら Enter を押してください"
    
    # ========== STEP 1: 環境チェック ==========
    Write-Host ""
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  STEP 1: 環境チェック" -ForegroundColor Blue
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    
    Initialize-Directories
    
    if (-not (Test-Python)) {
        Write-Host ""
        Write-Fail "Python 3.10+ をインストールしてください"
        Write-Info "https://www.python.org/downloads/"
        return $false
    }
    
    if (-not (Test-UV)) {
        Write-Host ""
        Write-Fail "uv のインストールに失敗しました"
        return $false
    }
    
    if (-not (Test-Blender)) {
        Write-Host ""
        Write-Fail "Blender が必要です"
        return $false
    }
    
    Ask-Continue
    
    # ========== STEP 2: インストール ==========
    Write-Host ""
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  STEP 2: インストール" -ForegroundColor Blue
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    
    Install-Dependencies | Out-Null
    Install-Addon | Out-Null
    Set-Environment | Out-Null
    
    Ask-Continue
    
    # ========== STEP 3: 起動 ==========
    Write-Host ""
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  STEP 3: MCP Server 起動" -ForegroundColor Blue
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    
    Start-Daemon | Out-Null
    
    Ask-Continue
    
    # ========== STEP 4: テスト ==========
    Write-Host ""
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  STEP 4: テスト" -ForegroundColor Blue
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    
    Test-Server | Out-Null
    Test-AddonInstalled | Out-Null
    
    # ========== 完了 ==========
    $success = Show-Summary
    
    if ($success) {
        Write-Host ""
        Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "  ║                  🎉 セットアップ完了！ 🎉                ║" -ForegroundColor Green
        Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
        Write-Host ""
        Write-Host "  次のステップ:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "    1. Blender を起動" -ForegroundColor White
        Write-Host "    2. Edit → Preferences → Add-ons" -ForegroundColor Gray
        Write-Host "    3. 'blender_mcp' を検索して有効化 ✓" -ForegroundColor Gray
        Write-Host "    4. MCP クライアントから接続" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "  ║              ⚠️ 一部のステップが失敗しました             ║" -ForegroundColor Red
        Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Red
        Write-Host ""
        Write-Host "  上記のエラーを確認して、再度実行してください:" -ForegroundColor Yellow
        Write-Host "    .\setup.ps1" -ForegroundColor Gray
        Write-Host ""
    }
    
    return $success
}

function Show-Help {
    Write-Host ""
    Write-Host "  使用方法:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    .\setup.ps1           # 完全自動セットアップ (推奨)" -ForegroundColor White
    Write-Host "    .\setup.ps1 full      # 同上" -ForegroundColor Gray
    Write-Host "    .\setup.ps1 install   # インストールのみ" -ForegroundColor Gray
    Write-Host "    .\setup.ps1 daemon    # Server 起動" -ForegroundColor Gray
    Write-Host "    .\setup.ps1 status    # Server ステータス確認" -ForegroundColor Gray
    Write-Host "    .\setup.ps1 test      # テスト実行" -ForegroundColor Gray
    Write-Host "    .\setup.ps1 help      # ヘルプ表示" -ForegroundColor Gray
    Write-Host ""
}

# ========================================
# エントリーポイント
# ========================================

switch ($Action) {
    "" { Invoke-FullSetup }
    "full" { Invoke-FullSetup }
    "install" {
        Show-Banner
        Initialize-Directories
        Test-Python | Out-Null
        Test-UV | Out-Null
        Test-Blender | Out-Null
        Install-Dependencies | Out-Null
        Install-Addon | Out-Null
        Set-Environment | Out-Null
        Show-Summary | Out-Null
    }
    "daemon" {
        Show-Banner
        Start-Daemon | Out-Null
    }
    "status" {
        Show-Banner
        Get-DaemonStatus
    }
    "test" {
        Show-Banner
        $script:BLENDER_PATH = Find-BlenderPath
        Test-Server | Out-Null
        Test-AddonInstalled | Out-Null
        Show-Summary | Out-Null
    }
    "help" {
        Show-Banner
        Show-Help
    }
}
