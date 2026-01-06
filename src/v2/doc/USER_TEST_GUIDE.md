# Blender MCP V2 - ユーザーテストガイド

## 🎯 テスト目的

Blender MCP V2 の以下の機能をテストします：

- ✅ 自動インストール (Phase 5)
- ✅ 常駐化 (Phase 6)
- ✅ セッション管理
- ✅ ログシステム
- ✅ セッション永続化

---

## 📋 テスト環境要件

### 必須

- Windows 10/11
- Python 3.10+
- Blender 4.0+
- PowerShell 5.0+

### インストール済み

- uv (Python パッケージマネージャー)
- Git

---

## 🚀 テスト手順

### Step 1: 自動インストール (Phase 5)

#### 1.1 インストールスクリプト実行

```powershell
# PowerShell を管理者として実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# インストール実行
.\src\v2\install.ps1
```

**期待される結果**:
- ✅ Python 依存がインストールされる
- ✅ Blender Addon がインストールされる
- ✅ 環境変数が設定される
- ✅ MCP Server が起動テストされる

**チェックリスト**:
- [ ] インストール完了メッセージが表示される
- [ ] エラーが発生しない
- [ ] ログファイルが作成される

---

### Step 2: Daemon 起動 (Phase 6)

#### 2.1 Daemon を起動

```powershell
# Daemon 起動
.\src\v2\start_daemon.ps1

# または、バックグラウンドで実行
Start-Process powershell -ArgumentList ".\src\v2\start_daemon.ps1"
```

**期待される結果**:
- ✅ Session Manager が起動
- ✅ MCP Server が起動
- ✅ Blender が起動
- ✅ ヘルスチェックが成功

**チェックリスト**:
- [ ] 3つのプロセスが起動する
- [ ] ログファイルが作成される
- [ ] ヘルスチェックが成功

#### 2.2 Daemon ステータス確認

```powershell
# ステータス確認
.\src\v2\start_daemon.ps1 -Status
```

**期待される結果**:
- ✅ 3つのプロセスが実行中と表示される
- ✅ ログファイルパスが表示される

**チェックリスト**:
- [ ] Session Manager が実行中
- [ ] MCP Server が実行中
- [ ] Blender が実行中

---

### Step 3: Blender Addon 確認

#### 3.1 Blender を起動

```bash
blender
```

#### 3.2 Addon を有効化

1. Edit > Preferences > Add-ons
2. "BlenderMCP V2" を検索
3. チェックボックスを有効化

**期待される結果**:
- ✅ Addon が表示される
- ✅ Addon が有効化できる
- ✅ サイドバーに "BlenderMCP V2" パネルが表示される

**チェックリスト**:
- [ ] Addon が見つかる
- [ ] Addon が有効化できる
- [ ] パネルが表示される

#### 3.3 MCP Server に接続

1. BlenderMCP V2 パネルで "Connect to MCP server" をクリック
2. 接続成功メッセージが表示される

**期待される結果**:
- ✅ 接続成功メッセージが表示される
- ✅ ステータスが "Running" に変わる

**チェックリスト**:
- [ ] 接続成功メッセージが表示される
- [ ] ステータスが更新される

---

### Step 4: セッション管理テスト

#### 4.1 セッション作成

MCP Client (Claude, Cursor など) から:

```python
# セッション作成
session_id = create_session()
print(f"Session created: {session_id}")
```

**期待される結果**:
- ✅ セッション ID が返される
- ✅ ログファイルが作成される

**チェックリスト**:
- [ ] セッション ID が返される
- [ ] `logs/sessions/{session_id}/` ディレクトリが作成される

#### 4.2 セッション情報取得

```python
# セッション情報取得
info = get_session_info(session_id=session_id)
print(info)
```

**期待される結果**:
- ✅ セッション情報が返される
- ✅ ログサマリーが含まれる

**チェックリスト**:
- [ ] セッション情報が返される
- [ ] command_count が 0 である
- [ ] log_summary が含まれる

---

### Step 5: ログシステムテスト (Phase 3)

#### 5.1 コマンド実行

```python
# Blender コマンド実行
result = execute_blender_code(
    code="bpy.ops.mesh.primitive_cube_add()",
    session_id=session_id
)
```

**期待される結果**:
- ✅ コマンドが実行される
- ✅ ログファイルに記録される

**チェックリスト**:
- [ ] コマンドが実行される
- [ ] `command.log` に記録される
- [ ] `blender.log` に記録される

#### 5.2 ログファイル確認

```bash
# ログファイルを確認
cat logs/sessions/{session_id}/command.log
cat logs/sessions/{session_id}/blender.log
cat logs/sessions/{session_id}/state.json
```

**期待される結果**:
- ✅ command.log に JSONL 形式でコマンドが記録されている
- ✅ blender.log に JSONL 形式で操作が記録されている
- ✅ state.json に状態が保存されている

**チェックリスト**:
- [ ] command.log が存在する
- [ ] blender.log が存在する
- [ ] state.json が存在する

#### 5.3 設計ドキュメント確認

```bash
# セッションをクローズ
close_session(session_id=session_id)

# 設計ドキュメントを確認
cat logs/sessions/{session_id}/design.md
```

**期待される結果**:
- ✅ design.md が自動生成される
- ✅ コマンド履歴が記載されている
- ✅ Blender操作履歴が記載されている

**チェックリスト**:
- [ ] design.md が生成される
- [ ] コマンド履歴が記載されている
- [ ] 最終状態が記載されている

---

### Step 6: セッション永続化テスト (Phase 4)

#### 6.1 セッション保存確認

```bash
# セッションファイルを確認
ls data/sessions/
cat data/sessions/{session_id}.json
```

**期待される結果**:
- ✅ セッションファイルが作成される
- ✅ JSON 形式で保存されている

**チェックリスト**:
- [ ] `data/sessions/{session_id}.json` が存在する
- [ ] JSON 形式で保存されている

#### 6.2 セッション復元テスト

```python
# セッション復元
restored = manager.restore_session(session_id)
print(f"Session restored: {restored}")

# 復元されたセッション情報を確認
info = get_session_info(session_id=session_id)
print(info)
```

**期待される結果**:
- ✅ セッションが復元される
- ✅ 状態が保持されている

**チェックリスト**:
- [ ] セッションが復元される
- [ ] 状態が保持されている

---

### Step 7: Daemon 停止

#### 7.1 Daemon を停止

```powershell
# Daemon 停止
.\src\v2\start_daemon.ps1 -Stop
```

**期待される結果**:
- ✅ 3つのプロセスが停止される
- ✅ PID ファイルが削除される

**チェックリスト**:
- [ ] Session Manager が停止される
- [ ] MCP Server が停止される
- [ ] Blender が停止される

---

## 📊 テスト結果レポート

### テスト実施日

- **日時**: _______________
- **テスター**: _______________
- **環境**: Windows _____, Python _____, Blender _____

### テスト結果

| テスト項目 | 結果 | 備考 |
|---|---|---|
| Phase 5: 自動インストール | ✅ / ⚠ / ❌ | |
| Phase 6: Daemon 起動 | ✅ / ⚠ / ❌ | |
| Blender Addon 確認 | ✅ / ⚠ / ❌ | |
| セッション管理 | ✅ / ⚠ / ❌ | |
| Phase 3: ログシステム | ✅ / ⚠ / ❌ | |
| Phase 4: セッション永続化 | ✅ / ⚠ / ❌ | |
| Daemon 停止 | ✅ / ⚠ / ❌ | |

### 問題報告

#### 問題 1

- **タイトル**: _______________
- **説明**: _______________
- **重要度**: 高 / 中 / 低
- **再現手順**: _______________

#### 問題 2

- **タイトル**: _______________
- **説明**: _______________
- **重要度**: 高 / 中 / 低
- **再現手順**: _______________

### 改善提案

1. _______________
2. _______________
3. _______________

### 全体評価

- **機能性**: ⭐⭐⭐⭐⭐ / 5
- **使いやすさ**: ⭐⭐⭐⭐⭐ / 5
- **安定性**: ⭐⭐⭐⭐⭐ / 5
- **パフォーマンス**: ⭐⭐⭐⭐⭐ / 5

### コメント

_______________

---

## 📞 サポート

### よくある問題

#### Q: インストールが失敗する

**A**: 以下を確認してください：
- Python 3.10+ がインストールされているか
- uv がインストールされているか
- PowerShell の実行ポリシーが設定されているか

#### Q: Daemon が起動しない

**A**: 以下を確認してください：
- Blender がインストールされているか
- ポート 9876 が使用可能か
- ログファイルを確認してください

#### Q: セッションが保存されない

**A**: 以下を確認してください：
- `data/sessions/` ディレクトリが存在するか
- ディスク容量が十分か
- ファイルの書き込み権限があるか

---

## 📝 テスト完了後

1. このレポートを記入してください
2. 問題があれば GitHub Issues に報告してください
3. フィードバックをお送りください

ご協力ありがとうございました！

