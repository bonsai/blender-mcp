# 🚀 今すぐテスト開始

## ステップ 1: インストール

```powershell
# PowerShell を管理者として実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# インストール実行
.\src\v2\install.ps1
```

**期待される結果**:
```
✓ Python 3.10+ インストール済み
✓ uv インストール済み
✓ Blender を検出: C:\Program Files\Blender Foundation\Blender 4.0\blender.exe
✓ 依存インストール完了
✓ Addon をインストール
✓ 環境変数を設定
✓ MCP Server が起動しました
✓ Blender MCP V2 のインストールが完了しました！
```

---

## ステップ 2: Daemon 起動

```powershell
# Daemon を起動
.\src\v2\start_daemon.ps1
```

**期待される結果**:
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

## ステップ 3: Blender で Addon を有効化

1. Blender が起動したら、Edit > Preferences > Add-ons
2. "BlenderMCP V2" を検索
3. チェックボックスを有効化
4. BlenderMCP V2 パネルで "Connect to MCP server" をクリック

---

## ステップ 4: MCP Client で使用

Claude, Cursor などの MCP Client から：

```python
# セッション作成
session_id = create_session()
print(f"Session: {session_id}")

# コマンド実行
result = execute_blender_code(
    code="bpy.ops.mesh.primitive_cube_add()",
    session_id=session_id
)

# セッション情報確認
info = get_session_info(session_id=session_id)
print(info)

# ログ確認
logs = get_session_logs(session_id=session_id)
print(logs)
```

---

## ステップ 5: ログ確認

```bash
# ログファイルを確認
cat logs/sessions/{session_id}/command.log
cat logs/sessions/{session_id}/blender.log
cat logs/sessions/{session_id}/design.md
cat data/sessions/{session_id}.json
```

---

## ステップ 6: Daemon 停止

```powershell
# Daemon を停止
.\src\v2\start_daemon.ps1 -Stop
```

---

## ステップ 7: テスト結果報告

以下の情報を記入してください：

### テスト環境
- OS: Windows _____
- Python: _____
- Blender: _____

### テスト結果
- インストール: ✅ / ⚠ / ❌
- Daemon 起動: ✅ / ⚠ / ❌
- Addon 有効化: ✅ / ⚠ / ❌
- セッション作成: ✅ / ⚠ / ❌
- コマンド実行: ✅ / ⚠ / ❌
- ログ確認: ✅ / ⚠ / ❌
- Daemon 停止: ✅ / ⚠ / ❌

### 問題があれば
- 問題の説明: _____
- エラーメッセージ: _____
- 再現手順: _____

---

## 📞 ヘルプ

### インストール失敗

```powershell
# Python 確認
python --version

# uv 確認
uv --version

# Blender 確認
Get-Item "C:\Program Files\Blender Foundation\Blender*\blender.exe"
```

### Daemon が起動しない

```powershell
# ログ確認
cat $env:APPDATA\BlenderMCP\logs\session_manager.log
cat $env:APPDATA\BlenderMCP\logs\mcp_server.log
cat $env:APPDATA\BlenderMCP\logs\blender.log
```

### ステータス確認

```powershell
# Daemon のステータスを確認
.\src\v2\start_daemon.ps1 -Status
```

---

ご協力ありがとうございました！

