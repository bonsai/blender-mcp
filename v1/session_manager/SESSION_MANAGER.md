# Session Manager - 中央司令塔

## 概要

Session Manager は、3つのサーバ（OLLAMA / MCP / Blender）を横断して状態を管理する中央司令塔です。

```
🧠 OLLAMA (自然言語処理)
   ↓
🧑‍✈️ Session Manager (状態管理・ルーティング) ← ★ここが心臓
   ↓
🧰 MCP Server (Tool定義)
   ↓
🎮 Blender MCP Addon (Python実行)
```

---

## 主な機能

### 1. セッション管理
- **セッションID発行**: 各ユーザーに一意のセッションIDを割り当て
- **状態保持**: Blenderの状態（オブジェクト、選択、履歴）を記録
- **Keep-Alive**: Blender接続を常時保持（毎回接続を張り直さない）

### 2. コマンドルーティング
- MCP Tool Call を Blender コマンドに変換
- セッション単位でBlenderに送信
- 結果を受け取って状態を更新

### 3. 履歴管理
- コマンド実行履歴を記録
- タイムスタンプ、引数、結果、実行時間を保存

### 4. クリーンアップ
- アイドルセッションを自動削除
- Blender接続を適切にクローズ

---

## ファイル構成

```
src/session_manager/
├── manager.py              # Session Manager 本体
├── router.py               # MCP ルーター
├── start_manager.ps1       # 起動スクリプト
├── SESSION_MANAGER.md      # このファイル
├── test_mcp_client.py      # テストクライアント
└── HELLO_CUBE_DEMO.md      # デモ
```

---

## 使用方法

### 1. Session Manager を起動

```powershell
# 基本的な起動
.\start_manager.ps1

# OLLAMA と MCP も一緒に起動
.\start_manager.ps1 -StartOllama -StartMcp

# Blender ホストを指定
.\start_manager.ps1 -BlenderHost "192.168.1.100" -BlenderPort 9876
```

### 2. Python から使用

```python
from manager import get_session_manager

# Session Manager を取得
sm = get_session_manager()

# セッション作成
session_id = sm.create_session()
# → "scene-20260106-101530-a1b2c3d4"

# Blender コマンド送信
result = sm.send_command(
    session_id,
    "execute_code",
    {"code": "bpy.ops.mesh.primitive_cube_add()"}
)

# セッション情報取得
info = sm.get_session_info(session_id)
print(info)
# {
#   "session_id": "scene-20260106-101530-a1b2c3d4",
#   "created_at": 1704528000,
#   "blender": {
#     "connected": true,
#     "host": "127.0.0.1",
#     "port": 9876
#   },
#   "state": {
#     "objects": ["Cube", "Camera", "Light", "Cube.001"],
#     "selection": "Cube.001",
#     "last_command": "execute_code"
#   }
# }

# セッション履歴取得
history = sm.get_session_history(session_id)
for cmd in history:
    print(f"{cmd['command']}: {cmd['result']} ({cmd['duration']:.2f}s)")

# セッションクローズ
sm.close_session(session_id)
```

### 3. MCP Server に統合

```python
from mcp.server.fastmcp import FastMCP, Context
from router import get_router
import json

mcp = FastMCP("BlenderMCP")
router = get_router()

@mcp.tool()
def execute_blender_code(ctx: Context, code: str, session_id: str = None) -> str:
    """Blender Python コード実行"""
    
    # セッションがなければ作成
    if not session_id:
        session_id = router.create_session()
    
    # Tool Call をハンドル
    result = router.handle_tool_call(
        session_id,
        "execute_blender_code",
        {"code": code}
    )
    
    return json.dumps(result, indent=2)

@mcp.tool()
def get_scene_info(ctx: Context, session_id: str = None) -> str:
    """シーン情報取得"""
    
    if not session_id:
        session_id = router.create_session()
    
    result = router.handle_tool_call(
        session_id,
        "get_scene_info",
        {}
    )
    
    return json.dumps(result, indent=2)
```

---

## Session 構造

```json
{
  "session_id": "scene-20260106-101530-a1b2c3d4",
  "created_at": 1704528000.123,
  "last_activity": 1704528015.456,
  "blender": {
    "connected": true,
    "host": "127.0.0.1",
    "port": 9876,
    "last_heartbeat": 1704528015.456
  },
  "state": {
    "objects": ["Cube", "Camera", "Light", "Cube.001"],
    "selection": "Cube.001",
    "last_command": "execute_code",
    "last_result": {
      "status": "success",
      "object_name": "Cube.001"
    }
  },
  "command_count": 5
}
```

---

## API リファレンス

### SessionManager

#### `create_session() -> str`
新しいセッションを作成
```python
session_id = sm.create_session()
```

#### `get_session(session_id: str) -> Session`
セッションを取得
```python
session = sm.get_session(session_id)
```

#### `send_command(session_id: str, command_type: str, params: Dict) -> Dict`
Blender コマンドを送信
```python
result = sm.send_command(
    session_id,
    "execute_code",
    {"code": "..."}
)
```

#### `update_state(session_id: str, **kwargs)`
セッション状態を更新
```python
sm.update_state(
    session_id,
    objects=["Cube", "Camera"],
    selection="Cube"
)
```

#### `get_session_info(session_id: str) -> Dict`
セッション情報を取得
```python
info = sm.get_session_info(session_id)
```

#### `get_session_history(session_id: str) -> List`
コマンド履歴を取得
```python
history = sm.get_session_history(session_id)
```

#### `list_sessions() -> List`
全セッション一覧
```python
sessions = sm.list_sessions()
```

#### `close_session(session_id: str)`
セッションをクローズ
```python
sm.close_session(session_id)
```

#### `cleanup_idle_sessions(timeout: float = 300.0)`
アイドルセッションをクリーンアップ
```python
sm.cleanup_idle_sessions(timeout=300)  # 5分以上アイドル
```

---

## Keep-Alive メカニズム

### 従来の方式（問題あり）

```
Request 1: socket.open() → send → recv → socket.close()
Request 2: socket.open() → send → recv → socket.close()
Request 3: socket.open() → send → recv → socket.close()

❌ 毎回接続を張り直す
❌ Blender 側の状態が失われる可能性
❌ 遅い
```

### Session Manager 方式（改善）

```
Session Start: socket.open() → keep-alive
Request 1: send → recv (socket 再利用)
Request 2: send → recv (socket 再利用)
Request 3: send → recv (socket 再利用)
Session End: socket.close()

✓ 1回の接続で複数リクエスト処理
✓ Blender 状態を保持
✓ 高速
```

---

## ログ出力

Session Manager はログを出力します：

```
[2026-01-06 10:00:00] SessionManager initialized (Blender: 127.0.0.1:9876)
[2026-01-06 10:00:05] ✓ Session created: scene-20260106-100005-a1b2c3d4
[2026-01-06 10:00:05] ✓ Blender connected for session scene-20260106-100005-a1b2c3d4
[2026-01-06 10:00:05] → Command sent: execute_code (session: scene-20260106-100005-a1b2c3d4)
[2026-01-06 10:00:05] ← Response: success (0.15s)
[2026-01-06 10:00:10] → Command sent: execute_code (session: scene-20260106-100005-a1b2c3d4)
[2026-01-06 10:00:10] ← Response: success (0.12s)
[2026-01-06 10:00:15] ✓ Session closed: scene-20260106-100005-a1b2c3d4
```

---

## トラブルシューティング

### Blender に接続できない

```
Error: Failed to connect to Blender: [Errno 10061] No connection could be made
```

**解決方法:**
1. Blender が起動しているか確認
2. BlenderMCP Addon が有効になっているか確認
3. "Connect to MCP server" ボタンをクリックしたか確認
4. ホスト・ポート設定が正しいか確認

```powershell
# ホスト・ポートを指定して起動
.\start_manager.ps1 -BlenderHost "127.0.0.1" -BlenderPort 9876
```

### タイムアウトエラー

```
Error: Timeout waiting for Blender response
```

**解決方法:**
- Blender が重い処理をしていないか確認
- コマンドを小分けにして送信
- タイムアウト値を増やす（manager.py の `sock.settimeout(180.0)` を変更）

### セッションが見つからない

```
Error: Session not found: scene-20260106-100005-a1b2c3d4
```

**解決方法:**
- セッションIDが正しいか確認
- セッションがタイムアウトで削除されていないか確認
- `sm.list_sessions()` で有効なセッションを確認

---

## パフォーマンス

### ベンチマーク

| 操作 | 時間 |
|---|---|
| セッション作成 | ~1ms |
| Blender 接続 | ~50ms |
| コマンド送信・受信 | ~100-200ms |
| 状態更新 | ~1ms |

### スケーラビリティ

- **同時セッション数**: 100+ (メモリ許す限り)
- **コマンド履歴**: セッションごとに無制限（メモリ許す限り）
- **クリーンアップ**: 自動（5分ごと）

---

## セキュリティ考慮事項

⚠️ **注意**: Session Manager は localhost のみで動作することを想定しています。

リモートアクセスが必要な場合：
1. ファイアウォール設定を確認
2. 認証機構を追加
3. TLS/SSL を使用

---

## 今後の拡張

- [ ] Redis を使用した分散セッション管理
- [ ] セッション永続化（DB保存）
- [ ] マルチユーザー対応
- [ ] セッション共有機能
- [ ] リアルタイム状態同期（WebSocket）

---

## ライセンス

このプロジェクトと同じライセンスに従います。
