# Session Manager 起動スクリプト
# 用途: 3つのサーバ（OLLAMA / MCP / Blender）を横断して状態を管理

param(
    [string]$BlenderHost = "127.0.0.1",
    [int]$BlenderPort = 9876,
    [int]$ManagerPort = 8765,
    [switch]$NoPull,
    [switch]$StartOllama,
    [switch]$StartMcp
)

# 色定義
$colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
}

function Write-Log {
    param([string]$Message, [string]$Level = "Info")
    $color = $colors[$Level]
    Write-Host "[$Level] $Message" -ForegroundColor $color
}

function Test-Port {
    param([int]$Port)
    try {
        $socket = New-Object System.Net.Sockets.TcpClient
        $socket.Connect("127.0.0.1", $Port)
        $socket.Close()
        return $true
    } catch {
        return $false
    }
}

# ========================================
# 1. 環境チェック
# ========================================
Write-Log "=== Session Manager Startup ===" "Info"
Write-Log "Checking environment..." "Info"

# Python チェック
try {
    $pythonVersion = python --version 2>&1
    Write-Log "✓ Python found: $pythonVersion" "Success"
} catch {
    Write-Log "✗ Python not found. Please install Python 3.10+" "Error"
    exit 1
}

# uv チェック
try {
    $uvVersion = uv --version 2>&1
    Write-Log "✓ uv found: $uvVersion" "Success"
} catch {
    Write-Log "✗ uv not found. Please install uv" "Error"
    exit 1
}

# ========================================
# 2. OLLAMA 起動（オプション）
# ========================================
if ($StartOllama) {
    Write-Log "Starting OLLAMA..." "Info"
    
    if (Test-Port 11434) {
        Write-Log "✓ OLLAMA already running on port 11434" "Success"
    } else {
        try {
            # OLLAMA起動（バックグラウンド）
            $ollamaProcess = Start-Process -FilePath "ollama" -ArgumentList "serve" -PassThru -NoNewWindow
            $ollamaPid = $ollamaProcess.Id
            
            # PIDを保存
            $ollamaPid | Out-File -FilePath ".\.run\ollama.pid" -Force
            
            Write-Log "✓ OLLAMA started (PID: $ollamaPid)" "Success"
            
            # モデルロード（オプション）
            if (-not $NoPull) {
                Write-Log "Pulling OLLAMA model..." "Info"
                Start-Sleep -Seconds 3
                & ollama pull llama2
            }
        } catch {
            Write-Log "✗ Failed to start OLLAMA: $_" "Error"
        }
    }
}

# ========================================
# 3. MCP Server 起動（オプション）
# ========================================
if ($StartMcp) {
    Write-Log "Starting MCP Server..." "Info"
    
    try {
        # MCP Server起動（バックグラウンド）
        $mcpProcess = Start-Process -FilePath "uvx" -ArgumentList "blender-mcp" -PassThru -NoNewWindow
        $mcpPid = $mcpProcess.Id
        
        # PIDを保存
        $mcpPid | Out-File -FilePath ".\.run\mcp.pid" -Force
        
        Write-Log "✓ MCP Server started (PID: $mcpPid)" "Success"
        Start-Sleep -Seconds 2
    } catch {
        Write-Log "✗ Failed to start MCP Server: $_" "Error"
    }
}

# ========================================
# 4. Session Manager 起動
# ========================================
Write-Log "Starting Session Manager..." "Info"

try {
    # 環境変数設定
    $env:BLENDER_HOST = $BlenderHost
    $env:BLENDER_PORT = $BlenderPort
    $env:MANAGER_PORT = $ManagerPort
    
    Write-Log "Configuration:" "Info"
    Write-Log "  Blender Host: $BlenderHost" "Info"
    Write-Log "  Blender Port: $BlenderPort" "Info"
    Write-Log "  Manager Port: $ManagerPort" "Info"
    
    # Session Manager起動
    $managerScript = Join-Path $PSScriptRoot "manager.py"
    
    if (-not (Test-Path $managerScript)) {
        Write-Log "✗ manager.py not found at $managerScript" "Error"
        exit 1
    }
    
    # Python スクリプト実行
    & python $managerScript
    
} catch {
    Write-Log "✗ Failed to start Session Manager: $_" "Error"
    exit 1
}

Write-Log "Session Manager stopped" "Info"
