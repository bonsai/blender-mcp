# 🎯 Blender MCP V2 - 初心者ガイド

初めての方向けの簡潔なセットアップガイドです。

---

## 📋 準備物

以下がインストールされていることを確認してください：

- **Python 3.10 以上** - [ダウンロード](https://www.python.org/downloads/)
- **Blender 4.0 以上** - [ダウンロード](https://www.blender.org/download/)
- **uv** - Python パッケージマネージャー

### uv のインストール

```powershell
pip install uv
```

---

## 🚀 セットアップ（3ステップ）

### ステップ 1: セットアップウィザードを実行

PowerShell を開いて以下を実行：

```powershell
# プロジェクトフォルダに移動
cd C:\Users\[ユーザー名]\blender-mcp

# セットアップウィザードを実行
.\src\v2\setup_wizard.ps1
```

**ウィザードが自動的に以下を行います：**
- ✓ 環境チェック
- ✓ 依存パッケージのインストール
- ✓ Blender Addon のインストール
- ✓ MCP Server の起動
- ✓ Blender の起動
- ✓ Addon の有効化
- ✓ MCP Server への接続

### ステップ 2: ウィザードの指示に従う

ウィザードが各ステップで一呼吸置いて、あなたの確認を待ちます。

**各ステップで以下を行ってください：**

1. **環境チェック** - 自動実行
2. **依存インストール** - 自動実行（1-2分）
3. **Addon インストール** - 自動実行
4. **MCP Server 起動** - 自動実行
5. **Blender 起動** - 自動実行
6. **Addon 有効化** - 手動（Blender で操作）
7. **MCP Server 接続** - 手動（Blender で操作）
8. **テスト** - 完了

### ステップ 3: 完了

セットアップウィザードが完了したら、すぐに使用開始できます。

---

## 💡 使い方

### セッション作成

MCP Client (Claude, Cursor など) で：

```python
session_id = create_session()
print(f"セッション ID: {session_id}")
```

### Blender コマンド実行

```python
result = execute_blender_code(
    code="bpy.ops.mesh.primitive_cube_add()",
    session_id=session_id
)
```

### セッション情報確認

```python
info = get_session_info(session_id=session_id)
print(info)
```

---

## ❓ よくある質問

### Q: セットアップウィザードが失敗した

**A:** 以下を確認してください：

```powershell
# Python が正しくインストールされているか
python --version

# uv が正しくインストールされているか
uv --version

# Blender がインストールされているか
Get-Item "C:\Program Files\Blender Foundation\Blender*\blender.exe"
```

### Q: Blender が起動しない

**A:** 以下を試してください：

1. Blender を手動で起動
2. Edit > Preferences > Add-ons
3. "BlenderMCP V2" を検索して有効化
4. Blender を再起動

### Q: MCP Server に接続できない

**A:** 以下を確認してください：

1. MCP Server のターミナルウィンドウが開いているか
2. エラーメッセージが表示されていないか
3. Blender の右側パネルに "BlenderMCP V2" が表示されているか

### Q: セッションが見つからないエラー

**A:** セッションがタイムアウトしている可能性があります。

```python
# 新しいセッションを作成
session_id = create_session()
```

---

## 📞 トラブルシューティング

### ログを確認

```powershell
# MCP Server のログ
cat $env:APPDATA\BlenderMCP\logs\mcp_server.log

# Blender のログ
cat $env:APPDATA\BlenderMCP\logs\blender.log

# セッションマネージャーのログ
cat $env:APPDATA\BlenderMCP\logs\session_manager.log
```

### MCP Server を再起動

```powershell
# MCP Server のターミナルウィンドウで Ctrl+C を押す
# その後、セットアップウィザードを再実行
.\src\v2\setup_wizard.ps1
```

---

## 📚 次のステップ

セットアップが完了したら、以下を参照してください：

- `README.md` - 詳細なドキュメント
- `TEST_NOW.md` - テストガイド
- `doc/` - API ドキュメント

---

## 🎓 学習ポイント

1. **セッション** - Blender 操作を追跡するための ID
2. **MCP Server** - Blender と通信するサーバー
3. **Addon** - Blender 内で MCP Server と通信するプラグイン
4. **MCP Client** - Claude, Cursor などから Blender を操作

---

## 🆘 ヘルプが必要な場合

1. `BEGINNER_GUIDE.md` (このファイル) を確認
2. `README.md` で詳細を確認
3. ログファイルでエラーを確認
4. GitHub Issues で報告

---

**楽しい Blender MCP V2 ライフを！** 🎉
