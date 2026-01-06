# Blender MCP V2 - クイックスタート

## 🚀 5分で始める

### 1. インストール

```powershell
# PowerShell を管理者として実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# インストール実行
.\src\v2\install.ps1
```

### 2. Daemon 起動

```powershell
# Daemon を起動
.\src\v2\start_daemon.ps1
```

### 3. Blender で Addon を有効化

- Blender を起動
- Edit > Preferences > Add-ons
- "BlenderMCP V2" を検索して有効化
- BlenderMCP V2 パネルで "Connect to MCP server" をクリック

### 4. MCP Client で使用開始

```python
# セッション作成
session_id = create_session()

# コマンド実行
result = execute_blender_code(
    code="bpy.ops.mesh.primitive_cube_add()",
    session_id=session_id
)

# セッション情報確認
info = get_session_info(session_id=session_id)
```

---

## 📚 ドキュメント

- `README.md` - 概要
- `USER_TEST_GUIDE.md` - テストガイド
- `doc/` - 詳細ドキュメント

---

## 🛑 停止

```powershell
# Daemon を停止
.\src\v2\start_daemon.ps1 -Stop
```

---

## 📊 ステータス確認

```powershell
# Daemon のステータスを確認
.\src\v2\start_daemon.ps1 -Status
```

