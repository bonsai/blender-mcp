# V1 → V2 リファクタリング計画

## 📊 全体戦略

V2ビジョン（自然言語ファースト・常駐・セッション永続）を実現するため、V1を段階的に改造。

```
V1 (現状)
├─ Blender Addon (socket server)
├─ MCP Server (FastMCP)
└─ Session Manager (新規)
        ↓ [Phase 1-4]
V2 (目標)
├─ 自動インストール (install.ps1)
├─ 常駐化 (background process)
├─ セッション永続化 (DB/JSON)
├─ ログシステム (command/blender/state)
├─ 外部UI連携 (Slack/Continue)
└─ 建築プロンプト辞書
```

---

## 🎯 Phase 1: Session Manager 統合（現在地）

**目的**: V1 の MCP Server に Session Manager を組み込む

**対象ファイル**
- `src/blender_mcp/server.py` ← 修正
- `src/session_manager/manager.py` ← 新規（完成）
- `src/session_manager/router.py` ← 新規（完成）

**実装内容**

```python
# src/blender_mcp/server.py に追加

from session_manager.router import get_router

# FastMCP の各ツールに session_id パラメータを追加
@mcp.tool()
def execute_blender_code(ctx: Context, code: str, session_id: str = None) -> str:
    """Blender Python コード実行"""
    router = get_router()
    
    if not session_id:
        session_id = router.create_session()
    
    result = router.handle_tool_call(
        session_id,
        "execute_blender_code",
        {"code": code}
    )
    
    return json.dumps(result, indent=2)

# 他のツールも同様に修正
```

**チェックリスト**
- [ ] `server.py` に router import
- [ ] 全ツールに `session_id` パラメータ追加
- [ ] Tool Call → router.handle_tool_call() に統一
- [ ] テスト実行確認

**成果物**
- `src/blender_mcp/server.py` (修正版)
- テストスクリプト

---

## 🎯 Phase 2: Blender Addon を Keep-Alive 対応に

**目的**: Socket 接続を常時保持、複数リクエストに対応

**対象ファイル**
- `addon.py` ← 修正

**現在の問題**

```python
# 現在: リクエストごとに接続を張り直す
def _handle_client(self, client):
    # 1リクエスト処理
    # close()
```

**改善内容**

```python
# 改善: セッション単位で接続を保持
class BlenderMCPServer:
    def __init__(self):
        self.sessions = {}  # session_id → client mapping
    
    def _handle_client(self, client):
        """クライアント接続を永続管理"""
        session_id = None
        
        while True:
            try:
                # コマンド受信
                command = self._receive_command(client)
                session_id = command.get("session_id")
                
                # セッション登録
                if session_id not in self.sessions:
                    self.sessions[session_id] = {
                        "client": client,
                        "connected_at": time.time()
                    }
                
                # コマンド実行
                result = self._execute_command(command)
                
                # 結果送信
                self._send_response(client, result)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                break
        
        # クリーンアップ
        if session_id and session_id in self.sessions:
            del self.sessions[session_id]
        client.close()
```

**チェックリスト**
- [ ] `_handle_client()` をループ化
- [ ] セッション ID で接続を管理
- [ ] コマンド受信ロジックを改善
- [ ] エラーハンドリング強化
- [ ] テスト実行確認

**成果物**
- `addon.py` (Keep-Alive 対応版)

---

## 🎯 Phase 3: ログシステム構築

**目的**: 設計意図・操作履歴・状態を記録

**対象ファイル**
- `src/session_manager/logger.py` ← 新規
- `src/session_manager/manager.py` ← 修正

**ログ種別**

```
logs/
├── sessions/
│   └── scene-20260106-101530-a1b2c3d4/
│       ├── command.log      # 自然言語コマンド
│       ├── blender.log      # Blender操作履歴
│       ├── state.json       # 構造状態スナップショット
│       └── design.md        # 設計ドキュメント（自動生成）
```

**実装内容**

```python
# src/session_manager/logger.py

class SessionLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_dir = Path(f"logs/sessions/{session_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_command(self, user_input: str, tool_name: str, args: dict):
        """自然言語コマンドを記録"""
        with open(self.log_dir / "command.log", "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {user_input}\n")
            f.write(f"  Tool: {tool_name}\n")
            f.write(f"  Args: {json.dumps(args)}\n\n")
    
    def log_blender_operation(self, command: str, result: dict):
        """Blender操作を記録"""
        with open(self.log_dir / "blender.log", "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {command}\n")
            f.write(f"  Result: {json.dumps(result)}\n\n")
    
    def save_state(self, state: dict):
        """状態スナップショットを保存"""
        with open(self.log_dir / "state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def generate_design_doc(self) -> str:
        """設計ドキュメントを自動生成"""
        # command.log から Markdown を生成
        pass
```

**チェックリスト**
- [ ] `logger.py` 実装
- [ ] `manager.py` に logger 統合
- [ ] ログディレクトリ構造確認
- [ ] 自動生成ドキュメント確認

**成果物**
- `src/session_manager/logger.py`
- `src/session_manager/manager.py` (修正版)

---

## 🎯 Phase 4: セッション永続化

**目的**: セッションをDB/JSONで永続管理

**対象ファイル**
- `src/session_manager/persistence.py` ← 新規
- `src/session_manager/manager.py` ← 修正

**実装内容**

```python
# src/session_manager/persistence.py

class SessionPersistence:
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session: Session):
        """セッションを JSON で保存"""
        session_file = self.storage_dir / f"{session.session_id}.json"
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def load_session(self, session_id: str) -> dict:
        """セッションを JSON から復元"""
        session_file = self.storage_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, "r") as f:
                return json.load(f)
        return None
    
    def list_sessions(self) -> list:
        """全セッション一覧"""
        return [f.stem for f in self.storage_dir.glob("*.json")]
```

**チェックリスト**
- [ ] `persistence.py` 実装
- [ ] `manager.py` に persistence 統合
- [ ] セッション復元ロジック確認
- [ ] テスト実行確認

**成果物**
- `src/session_manager/persistence.py`
- `src/session_manager/manager.py` (修正版)

---

## 🎯 Phase 5: 自動インストール (install.ps1)

**目的**: 環境構築を「1コマンド」にする

**対象ファイル**
- `install.ps1` ← 新規

**実装内容**

```powershell
# install.ps1

param(
    [switch]$SkipBlender,
    [switch]$SkipOllama
)

# 1. 環境チェック
# 2. Python / uv インストール
# 3. Blender Addon 配置
# 4. MCP Server 依存解決
# 5. Session Manager セットアップ
# 6. Ollama 接続確認
```

**チェックリスト**
- [ ] `install.ps1` 実装
- [ ] 各ステップのエラーハンドリング
- [ ] ロールバック機能
- [ ] テスト実行確認

**成果物**
- `install.ps1`

---

## 🎯 Phase 6: 常駐化 (background process)

**目的**: Blender / MCP / Session Manager を自動起動・保持

**対象ファイル**
- `start_daemon.ps1` ← 新規
- `src/session_manager/daemon.py` ← 新規

**実装内容**

```powershell
# start_daemon.ps1

# 1. Session Manager 起動
# 2. Blender 起動 (--background)
# 3. MCP Server 起動
# 4. ヘルスチェック
# 5. Windows Task Scheduler に登録
```

**チェックリスト**
- [ ] `start_daemon.ps1` 実装
- [ ] `daemon.py` 実装
- [ ] ヘルスチェック機能
- [ ] 自動再起動機能
- [ ] テスト実行確認

**成果物**
- `start_daemon.ps1`
- `src/session_manager/daemon.py`

---

## 🎯 Phase 7: 外部UI連携 (Slack / Continue)

**目的**: IDE・チャットを設計UIにする

**対象ファイル**
- `src/integrations/slack_handler.py` ← 新規
- `src/integrations/continue_handler.py` ← 新規

**実装内容**

```python
# src/integrations/slack_handler.py

class SlackHandler:
    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)
    
    def handle_message(self, user_id: str, text: str, thread_ts: str = None):
        """Slack メッセージをハンドル"""
        # thread_ts = session_id
        session_id = thread_ts or self.create_session(user_id)
        
        # MCP Tool Call
        result = router.handle_tool_call(
            session_id,
            "execute_blender_code",
            {"code": text}
        )
        
        # Slack に返信
        self.client.chat_postMessage(
            channel=user_id,
            thread_ts=thread_ts,
            text=result
        )
```

**チェックリスト**
- [ ] `slack_handler.py` 実装
- [ ] `continue_handler.py` 実装
- [ ] Webhook 設定
- [ ] テスト実行確認

**成果物**
- `src/integrations/slack_handler.py`
- `src/integrations/continue_handler.py`

---

## 🎯 Phase 8: 建築プロンプト辞書

**目的**: 建築用語を自動解釈

**対象ファイル**
- `src/prompts/architecture_dict.json` ← 新規
- `src/prompts/system_prompt.md` ← 新規

**実装内容**

```json
// src/prompts/architecture_dict.json

{
  "壁": {
    "blender_command": "bpy.ops.mesh.primitive_cube_add()",
    "parameters": ["width", "height", "depth"],
    "default": {"width": 4, "height": 3, "depth": 0.2}
  },
  "柱": {
    "blender_command": "bpy.ops.mesh.primitive_cylinder_add()",
    "parameters": ["radius", "height"],
    "default": {"radius": 0.3, "height": 3}
  },
  "スパン": {
    "description": "建物の幅方向の距離",
    "unit": "m"
  }
}
```

**チェックリスト**
- [ ] `architecture_dict.json` 実装
- [ ] `system_prompt.md` 実装
- [ ] OLLAMA プロンプト統合
- [ ] テスト実行確認

**成果物**
- `src/prompts/architecture_dict.json`
- `src/prompts/system_prompt.md`

---

## 📋 実装順序（推奨）

```
Week 1: Phase 1-2 (Session 統合 + Keep-Alive)
  └─ MCP Server に router 統合
  └─ Addon を Keep-Alive 対応に

Week 2: Phase 3-4 (ログ + 永続化)
  └─ ログシステム構築
  └─ セッション永続化

Week 3: Phase 5-6 (自動化)
  └─ install.ps1 実装
  └─ 常駐化

Week 4: Phase 7-8 (拡張)
  └─ 外部UI連携
  └─ 建築プロンプト辞書
```

---

## 🔄 各 Phase の依存関係

```
Phase 1 (Session 統合)
    ↓
Phase 2 (Keep-Alive)
    ↓
Phase 3 (ログシステム)
    ↓
Phase 4 (永続化)
    ├─→ Phase 5 (install.ps1)
    ├─→ Phase 6 (常駐化)
    └─→ Phase 7 (外部UI)
         ↓
    Phase 8 (建築辞書)
```

---

## ✅ 完了チェックリスト

### Phase 1: Session Manager 統合
- [ ] `server.py` に router import
- [ ] 全ツールに `session_id` パラメータ
- [ ] テスト実行確認

### Phase 2: Keep-Alive 対応
- [ ] `addon.py` ループ化
- [ ] セッション管理
- [ ] テスト実行確認

### Phase 3: ログシステム
- [ ] `logger.py` 実装
- [ ] ログディレクトリ構造
- [ ] テスト実行確認

### Phase 4: 永続化
- [ ] `persistence.py` 実装
- [ ] セッション復元
- [ ] テスト実行確認

### Phase 5: 自動インストール
- [ ] `install.ps1` 実装
- [ ] エラーハンドリング
- [ ] テスト実行確認

### Phase 6: 常駐化
- [ ] `start_daemon.ps1` 実装
- [ ] `daemon.py` 実装
- [ ] テスト実行確認

### Phase 7: 外部UI連携
- [ ] `slack_handler.py` 実装
- [ ] `continue_handler.py` 実装
- [ ] テスト実行確認

### Phase 8: 建築辞書
- [ ] `architecture_dict.json` 実装
- [ ] `system_prompt.md` 実装
- [ ] テスト実行確認

---

## 📝 注記

**V1 との互換性**
- 既存の MCP Tool は全て保持
- Session ID は オプション（デフォルト自動生成）
- 段階的な移行が可能

**テスト戦略**
- 各 Phase ごとに単体テスト
- 統合テスト（全 Phase 完了後）
- 実運用テスト（建築図面ユースケース）

**ドキュメント**
- 各 Phase ごとに README 更新
- API ドキュメント更新
- ユーザーガイド作成
