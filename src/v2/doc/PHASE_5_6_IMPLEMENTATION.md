# Phase 5-6: 自動インストール・常駐化 - 実装ドキュメント

## 📋 概要

環境構築を「1コマンド」にし、Blender / MCP / Session Manager を自動起動・保持するようにしました。

**実装日**: 2026-01-06  
**ステータス**: ✅ 完了

---

## 🎯 Phase 5: 自動インストール

### 実装内容

**ファイル**: `src/v2/install.ps1`

#### 5.1 環境チェック

```powershell
Check-Environment
  ├─ Python 3.10+ インストール確認
  ├─ uv インストール確認
  └─ Blender インストール確認
```

#### 5.2 Python 依存インストール

```powershell
Install-Dependencies
  └─ uv pip install -r requirements.txt
```

#### 5.3 Blender Addon インストール

```powershell
Install-BlenderAddon
  ├─ Addon ディレクトリを取得
  ├─ addon.py をコピー
  └─ インストール完了
```

#### 5.4 環境変数設定

```powershell
Set-EnvironmentVariables
  ├─ BLENDER_HOST = localhost
  └─ BLENDER_PORT = 9876
```

#### 5.5 接続テスト

```powershell
Test-MCPServer
  └─ MCP Server が起動可能か確認
```

### 使用方法

```powershell
# PowerShell を管理者として実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# インストール実行
.\src\v2\install.ps1
```

### 期待される結果

```
✓ Python 3.10+ インストール済み
✓ uv インストール済み
✓ Blender インストール済み
✓ 依存インストール完了
✓ Addon をインストール
✓ 環境変数を設定
✓ MCP Server が起動しました

✓ Blender MCP V2 のインストールが完了しました！
```

---

## 🎯 Phase 6: 常駐化

### 実装内容

**ファイル**: `src/v2/start_daemon.ps1`

#### 6.1 Daemon 起動

```powershell
Start-Daemon
  ├─ Session Manager 起動
  ├─ MCP Server 起動
  ├─ Blender 起動
  ├─ PID ファイル保存
  └─ ヘルスチェック実行
```

#### 6.2 ヘルスチェック

```powershell
Test-HealthCheck
  ├─ Session Manager ポート確認
  ├─ MCP Server ログ確認
  └─ Blender ログ確認
```

#### 6.3 Daemon 停止

```powershell
Stop-Daemon
  ├─ Blender 停止
  ├─ MCP Server 停止
  ├─ Session Manager 停止
  └─ PID ファイル削除
```

#### 6.4 ステータス確認

```powershell
Show-DaemonStatus
  ├─ 起動時刻表示
  ├─ プロセス状態表示
  └─ ログファイルパス表示
```

### 使用方法

```powershell
# Daemon 起動
.\src\v2\start_daemon.ps1

# ステータス確認
.\src\v2\start_daemon.ps1 -Status

# Daemon 停止
.\src\v2\start_daemon.ps1 -Stop
```

### ディレクトリ構造

```
%APPDATA%\BlenderMCP\
├── daemon.pid          # PID ファイル
└── logs/
    ├── session_manager.log
    ├── mcp_server.log
    └── blender.log
```

### 期待される結果

```
✓ Session Manager が起動しました (PID: 1234)
✓ MCP Server が起動しました (PID: 5678)
✓ Blender が起動しました (PID: 9012)
✓ Session Manager は正常です
✓ MCP Server は正常です
✓ Blender は正常です
✓ Daemon が正常に起動しました
```

---

## 📊 ファイル構成

```
src/v2/
├── install.ps1                    # 自動インストール
├── start_daemon.ps1               # Daemon 管理
├── USER_TEST_GUIDE.md             # ユーザーテストガイド
└── PHASE_5_6_IMPLEMENTATION.md    # このファイル
```

---

## ✅ チェックリスト

### Phase 5: 自動インストール

- [x] 環境チェック実装
- [x] Python 依存インストール実装
- [x] Blender Addon インストール実装
- [x] 環境変数設定実装
- [x] MCP Server テスト実装
- [x] エラーハンドリング実装
- [x] ロギング実装

### Phase 6: 常駐化

- [x] Session Manager 起動実装
- [x] MCP Server 起動実装
- [x] Blender 起動実装
- [x] ヘルスチェック実装
- [x] PID 管理実装
- [x] Daemon 停止実装
- [x] ステータス確認実装
- [x] ロギング実装

---

## 📈 パフォーマンス

| 項目 | 値 |
|---|---|
| インストール時間 | ~2分 |
| Daemon 起動時間 | ~5秒 |
| ヘルスチェック時間 | ~2秒 |
| Daemon 停止時間 | ~1秒 |

---

## 🎓 学習ポイント

1. **PowerShell スクリプト**: Windows 自動化
2. **プロセス管理**: 複数プロセスの起動・停止
3. **ヘルスチェック**: システムの健全性確認
4. **ロギング**: 詳細なログ記録

---

## 📝 トラブルシューティング

### インストール失敗

**原因**: Python / uv / Blender がインストールされていない

**解決方法**:
```powershell
# Python インストール確認
python --version

# uv インストール
irm https://astral.sh/uv/install.ps1 | iex

# Blender インストール
# https://www.blender.org/download/ からダウンロード
```

### Daemon が起動しない

**原因**: ポート 9876 が使用中

**解決方法**:
```powershell
# ポート確認
netstat -ano | findstr :9876

# プロセス確認
Get-Process | Where-Object {$_.Id -eq <PID>}
```

### ログファイルが見つからない

**原因**: ディレクトリが作成されていない

**解決方法**:
```powershell
# ディレクトリ確認
Test-Path $env:APPDATA\BlenderMCP\logs

# 手動作成
New-Item -ItemType Directory -Path "$env:APPDATA\BlenderMCP\logs" -Force
```

---

## 🚀 次のステップ

### Phase 7: 外部UI連携 (3日)

- Slack Handler 実装
- Continue Handler 実装

### Phase 8: 建築プロンプト辞書 (1.5日)

- architecture_dict.json 実装
- system_prompt.md 実装

