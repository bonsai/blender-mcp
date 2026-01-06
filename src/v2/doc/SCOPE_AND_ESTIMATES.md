# V2 リファクタリング - 作業範囲と見積もり

## 📊 全体概要

**プロジェクト**: Blender MCP V1 → V2 リファクタリング  
**目的**: セッション管理・常駐化・永続化の実装  
**期間**: 4週間（推定）  
**チーム**: 1-2名  

---

## 🎯 Phase 別 作業範囲と見積もり

### Phase 1: Session Manager 統合（3日）

**目的**: V1 の MCP Server に Session Manager を組み込む

#### 1.1 MCP Server 修正

**ファイル**: `src/blender_mcp/server.py`

**作業内容**:
- [ ] router import 追加
- [ ] 全ツール（15個以上）に `session_id` パラメータ追加
- [ ] Tool Call → router.handle_tool_call() に統一
- [ ] エラーハンドリング追加

**見積もり**: 1.5日
- ツール修正: 1日（15ツール × 4分 = 60分）
- テスト・デバッグ: 0.5日

**リスク**: 
- 既存ツールの互換性破損（低）
- パラメータ型の不一致（中）

---

#### 1.2 テスト実装

**ファイル**: `v2/tests/test_session_integration.py`

**作業内容**:
- [ ] ユニットテスト（各ツール）
- [ ] 統合テスト（Session Manager + MCP）
- [ ] エラーケーステスト

**見積もり**: 1.5日
- テストコード作成: 1日
- テスト実行・修正: 0.5日

**テストカバレッジ目標**: > 80%

---

### Phase 2: Keep-Alive 対応（3日）

**目的**: Socket 接続を常時保持、複数リクエストに対応

#### 2.1 Addon 修正

**ファイル**: `addon.py`

**作業内容**:
- [ ] `_handle_client()` をループ化
- [ ] セッション ID で接続を管理
- [ ] コマンド受信ロジック改善
- [ ] エラーハンドリング強化
- [ ] Keep-Alive タイムアウト設定

**見積もり**: 2日
- ロジック設計: 0.5日
- 実装: 1day
- テスト・デバッグ: 0.5日

**リスク**:
- Socket 接続の安定性（中）
- メモリリーク（中）
- タイムアウト設定の最適化（低）

---

#### 2.2 Keep-Alive テスト

**ファイル**: `v2/tests/test_keep_alive.py`

**作業内容**:
- [ ] 複数リクエストテスト
- [ ] 接続保持テスト
- [ ] タイムアウトテスト
- [ ] メモリリークテスト

**見積もり**: 1day
- テストコード: 0.5day
- テスト実行・修正: 0.5day

---

### Phase 3: ログシステム構築（2.5日）

**目的**: 設計意図・操作履歴・状態を記録

#### 3.1 Logger 実装

**ファイル**: `src/session_manager/logger.py`

**作業内容**:
- [ ] SessionLogger クラス実装
- [ ] command.log 記録機能
- [ ] blender.log 記録機能
- [ ] state.json スナップショット
- [ ] design.md 自動生成

**見積もり**: 1.5day
- クラス設計: 0.5day
- 実装: 0.8day
- テスト: 0.2day

**ログ形式**:
```
logs/sessions/{session_id}/
├── command.log      # 自然言語コマンド
├── blender.log      # Blender操作
├── state.json       # 状態スナップショット
└── design.md        # 設計ドキュメント
```

---

#### 3.2 Manager 統合

**ファイル**: `src/session_manager/manager.py`

**作業内容**:
- [ ] logger インスタンス追加
- [ ] ログ記録呼び出し追加
- [ ] ログディレクトリ管理

**見積もり**: 1day
- 統合: 0.7day
- テスト: 0.3day

---

### Phase 4: セッション永続化（2.5日）

**目的**: セッションをDB/JSONで永続管理

#### 4.1 Persistence 実装

**ファイル**: `src/session_manager/persistence.py`

**作業内容**:
- [ ] SessionPersistence クラス実装
- [ ] JSON 保存機能
- [ ] JSON 復元機能
- [ ] セッション一覧機能
- [ ] クエリ機能

**見積もり**: 1.5day
- クラス設計: 0.5day
- 実装: 0.8day
- テスト: 0.2day

**ストレージ形式**:
```
data/sessions/
├── scene-20260106-101530-a1b2c3d4.json
├── scene-20260106-102000-b2c3d4e5.json
└── ...
```

---

#### 4.2 Manager 統合

**ファイル**: `src/session_manager/manager.py`

**作業内容**:
- [ ] persistence インスタンス追加
- [ ] save_session() 呼び出し
- [ ] load_session() 呼び出し
- [ ] セッション復元ロジック

**見積もり**: 1day
- 統合: 0.7day
- テスト: 0.3day

---

### Phase 5: 自動インストール（2日）

**目的**: 環境構築を「1コマンド」にする

#### 5.1 install.ps1 実装

**ファイル**: `install.ps1`

**作業内容**:
- [ ] 環境チェック（Python, uv, Blender）
- [ ] Python 依存インストール
- [ ] Blender Addon 配置
- [ ] MCP Server 依存解決
- [ ] Session Manager セットアップ
- [ ] Ollama 接続確認
- [ ] エラーハンドリング
- [ ] ロールバック機能

**見積もり**: 2day
- スクリプト設計: 0.5day
- 実装: 1.2day
- テスト: 0.3day

**チェック項目**:
- [ ] Python 3.10+ インストール確認
- [ ] uv インストール確認
- [ ] Blender インストール確認
- [ ] 依存パッケージインストール
- [ ] Addon 配置確認
- [ ] 接続テスト

---

### Phase 6: 常駐化（2.5日）

**目的**: Blender / MCP / Session Manager を自動起動・保持

#### 6.1 start_daemon.ps1 実装

**ファイル**: `start_daemon.ps1`

**作業内容**:
- [ ] Session Manager 起動
- [ ] Blender 起動（--background）
- [ ] MCP Server 起動
- [ ] ヘルスチェック実装
- [ ] Windows Task Scheduler 登録
- [ ] 自動再起動機能
- [ ] ログ管理

**見積もり**: 1.5day
- スクリプト設計: 0.5day
- 実装: 0.8day
- テスト: 0.2day

---

#### 6.2 daemon.py 実装

**ファイル**: `src/session_manager/daemon.py`

**作業内容**:
- [ ] Daemon クラス実装
- [ ] プロセス管理
- [ ] ヘルスチェック
- [ ] 自動再起動ロジック
- [ ] ログ記録

**見積もり**: 1day
- 実装: 0.7day
- テスト: 0.3day

---

### Phase 7: 外部UI連携（3日）

**目的**: IDE・チャットを設計UIにする

#### 7.1 Slack Handler 実装

**ファイル**: `src/integrations/slack_handler.py`

**作業内容**:
- [ ] SlackHandler クラス実装
- [ ] メッセージハンドリング
- [ ] セッション管理
- [ ] Tool Call ルーティング
- [ ] 応答送信
- [ ] エラーハンドリング

**見積もり**: 1.5day
- 実装: 1day
- テスト: 0.5day

**Slack API 統合**:
- Webhook 設定
- Bot Token 管理
- メッセージ形式

---

#### 7.2 Continue Handler 実装

**ファイル**: `src/integrations/continue_handler.py`

**作業内容**:
- [ ] ContinueHandler クラス実装
- [ ] IDE 連携
- [ ] テキスト選択処理
- [ ] Tool Call ルーティング
- [ ] 結果反映

**見積もり**: 1.5day
- 実装: 1day
- テスト: 0.5day

---

### Phase 8: 建築プロンプト辞書（1.5日）

**目的**: 建築用語を自動解釈

#### 8.1 architecture_dict.json 実装

**ファイル**: `src/prompts/architecture_dict.json`

**作業内容**:
- [ ] 建築用語定義（50+）
- [ ] Blender コマンドマッピング
- [ ] パラメータ定義
- [ ] デフォルト値設定

**見積もり**: 0.8day
- 辞書作成: 0.6day
- テスト: 0.2day

**含まれる用語**:
- 壁、柱、梁、床、屋根
- 窓、ドア、階段
- スパン、高さ、奥行き
- 材質、色、テクスチャ

---

#### 8.2 system_prompt.md 実装

**ファイル**: `src/prompts/system_prompt.md`

**作業内容**:
- [ ] OLLAMA プロンプト設計
- [ ] 建築用語の説明
- [ ] 例文作成
- [ ] 制約条件定義

**見積もり**: 0.7day
- プロンプト設計: 0.5day
- テスト: 0.2day

---

## 📋 作業範囲サマリー

| Phase | 内容 | 日数 | リスク |
|---|---|---|---|
| **1** | Session 統合 | 3 | 中 |
| **2** | Keep-Alive | 3 | 中 |
| **3** | ログシステム | 2.5 | 低 |
| **4** | 永続化 | 2.5 | 低 |
| **5** | 自動インストール | 2 | 低 |
| **6** | 常駐化 | 2.5 | 中 |
| **7** | 外部UI連携 | 3 | 中 |
| **8** | 建築辞書 | 1.5 | 低 |
| **合計** | | **20日** | |

---

## 🎯 実装スケジュール

### Week 1: Phase 1-2（6日）
```
Mon-Tue: Phase 1 (Session 統合)
  - MCP Server 修正: 1.5day
  - テスト実装: 1.5day

Wed-Fri: Phase 2 (Keep-Alive)
  - Addon 修正: 2day
  - Keep-Alive テスト: 1day
```

### Week 2: Phase 3-4（5日）
```
Mon-Tue: Phase 3 (ログシステム)
  - Logger 実装: 1.5day
  - Manager 統合: 1day

Wed-Fri: Phase 4 (永続化)
  - Persistence 実装: 1.5day
  - Manager 統合: 1day
```

### Week 3: Phase 5-6（4.5日）
```
Mon-Tue: Phase 5 (自動インストール)
  - install.ps1: 2day

Wed-Fri: Phase 6 (常駐化)
  - start_daemon.ps1: 1.5day
  - daemon.py: 1day
```

### Week 4: Phase 7-8（4.5日）
```
Mon-Tue: Phase 7 (外部UI連携)
  - Slack Handler: 1.5day
  - Continue Handler: 1.5day

Wed-Fri: Phase 8 (建築辞書)
  - architecture_dict.json: 0.8day
  - system_prompt.md: 0.7day
  - 統合テスト・修正: 1.5day
```

---

## 🧪 テスト戦略

### ユニットテスト（各 Phase）
- 関数単位のテスト
- エッジケーステスト
- エラーハンドリングテスト

**目標**: > 80% カバレッジ

### 統合テスト（Phase 完了後）
- Phase 間の連携テスト
- エンドツーエンドテスト
- パフォーマンステスト

### 実運用テスト（全 Phase 完了後）
- 建築図面ユースケース
- 複数セッション同時実行
- 長時間稼働テスト

---

## 📊 リスク評価

### 高リスク（対応必須）
- **Socket 接続の安定性**: Keep-Alive 実装時
  - 対応: 詳細なエラーハンドリング、タイムアウト設定
  - 見積もり追加: 0.5day

- **メモリリーク**: 長時間稼働時
  - 対応: メモリプロファイリング、定期的なクリーンアップ
  - 見積もり追加: 0.5day

### 中リスク（監視必要）
- **既存ツールの互換性**: Session ID パラメータ追加時
  - 対応: 後方互換性確保、段階的な移行
  - 見積もり追加: 0.3day

- **Slack/Continue 連携**: 外部 API 依存
  - 対応: Mock テスト、エラーハンドリング
  - 見積もり追加: 0.3day

### 低リスク（定期確認）
- **ログシステム**: ディスク容量
  - 対応: ログローテーション、圧縮
  - 見積もり追加: 0.2day

---

## 💰 見積もり合計

### 基本作業
- Phase 1-8: **20日**

### リスク対応
- Socket 安定性: **0.5day**
- メモリリーク対応: **0.5day**
- 互換性確保: **0.3day**
- 外部 API 連携: **0.3day**
- ログ管理: **0.2day**

### 合計
- **基本**: 20日
- **リスク対応**: 1.8日
- **バッファ（15%）**: 3.3日
- **総計**: **25.1日（約5週間）**

---

## 👥 チーム構成

### 推奨構成
- **リード開発者**: 1名（全 Phase 監督）
- **開発者**: 1名（実装）
- **QA**: 0.5名（テスト）

### 最小構成
- **フルスタック開発者**: 1名（全て）
- **期間**: 5-6週間

---

## 📝 成功基準

### 機能的
- [ ] 全 Phase 実装完了
- [ ] テストカバレッジ > 80%
- [ ] 既存ツール互換性維持

### パフォーマンス
- [ ] API 応答時間 < 500ms
- [ ] セッション作成 < 100ms
- [ ] メモリ使用量 < 500MB

### 運用
- [ ] 自動インストール成功率 > 95%
- [ ] 常駐化稼働時間 > 99%
- [ ] ログシステム正常動作

---

## 🚀 次のステップ

1. **承認**: この見積もりを確認・承認
2. **リソース確保**: チーム構成決定
3. **環境準備**: 開発環境セットアップ
4. **Phase 1 開始**: Session Manager 統合

---

## 📞 質問・懸念事項

- **質問**: 既存ツールの互換性をどこまで保つ？
  - **回答**: 後方互換性 100% 維持（session_id はオプション）

- **質問**: テスト環境の準備は？
  - **回答**: 本見積もりに含まれる

- **質問**: ドキュメント作成は？
  - **回答**: 各 Phase ごとに README 更新（見積もり外）

---

## 📄 添付資料

- REFACTOR_PLAN_V1_TO_V2.md（詳細計画）
- SESSION_MANAGER.md（API リファレンス）
- UX.md（ユーザーフロー）
