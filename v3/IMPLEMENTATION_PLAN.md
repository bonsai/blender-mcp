# V3 実装計画 - LegoDesigner System

## 📋 概要

V3 は Flask Web Server をメインに、Go で JSONL 処理を行う簡素化されたシステムです。

```
ブラウザ (HTML/CSS/JS)
    ↓
Flask Web Server (Python)
    ↓
Session Manager (Python)
    ↓
Blender MCP (Python)
    ↓
Go 処理エンジン (JSONL処理・発注フロー)
```

---

## 🏗️ ディレクトリ構成

```
v3/
├── app.py                      # Flask メインアプリ
├── requirements.txt            # Python 依存
├── requirements-dev.txt        # 開発用依存
├── Makefile                    # ビルド・実行スクリプト
├── Dockerfile                  # Docker設定
├── docker-compose.yml          # Docker Compose設定
│
├── templates/                  # HTML テンプレート
│   ├── index.html             # メインページ
│   ├── chat.html              # チャット画面
│   ├── preview.html           # 3Dプレビュー
│   └── order.html             # 発注フロー
│
├── static/                     # 静的ファイル
│   ├── css/
│   │   ├── style.css          # メインスタイル
│   │   └── responsive.css     # レスポンシブ
│   ├── js/
│   │   ├── app.js             # メインアプリ
│   │   ├── chat.js            # チャット処理
│   │   ├── preview.js         # 3Dプレビュー (Three.js)
│   │   └── api.js             # API通信
│   └── images/
│       └── logo.png
│
├── api/                        # Flask API
│   ├── __init__.py
│   ├── chat.py                # チャットエンドポイント
│   ├── session.py             # セッション管理
│   ├── preview.py             # プレビュー生成
│   ├── order.py               # 発注フロー
│   └── health.py              # ヘルスチェック
│
├── models/                     # データモデル
│   ├── __init__.py
│   ├── session.py             # セッションモデル
│   ├── message.py             # メッセージモデル
│   └── order.py               # 発注モデル
│
├── services/                   # ビジネスロジック
│   ├── __init__.py
│   ├── chat_service.py        # チャット処理
│   ├── blender_service.py     # Blender連携
│   ├── jsonl_service.py       # JSONL処理
│   └── order_service.py       # 発注処理
│
├── utils/                      # ユーティリティ
│   ├── __init__.py
│   ├── logger.py              # ロギング
│   ├── config.py              # 設定
│   └── validators.py          # バリデーション
│
├── tests/                      # テスト
│   ├── __init__.py
│   ├── test_api.py            # API テスト
│   ├── test_services.py       # サービス テスト
│   └── test_models.py         # モデル テスト
│
├── data/                       # データディレクトリ
│   ├── sessions/              # セッション JSONL
│   ├── models/                # 3D モデル
│   └── orders/                # 発注データ
│
└── go/                         # Go 処理エンジン
    ├── go.mod
    ├── go.sum
    ├── cmd/
    │   ├── processor/         # JSONL 処理
    │   │   └── main.go
    │   ├── order/             # 発注フロー
    │   │   └── main.go
    │   └── ml-export/         # ML データ エクスポート
    │       └── main.go
    ├── pkg/
    │   ├── jsonl/             # JSONL 処理ライブラリ
    │   │   ├── reader.go
    │   │   ├── writer.go
    │   │   └── processor.go
    │   ├── order/             # 発注処理ライブラリ
    │   │   ├── manager.go
    │   │   └── notifier.go
    │   └── ml/                # ML データ処理
    │       ├── normalizer.go
    │       └── exporter.go
    └── tests/
        ├── jsonl_test.go
        ├── order_test.go
        └── ml_test.go
```

---

## 📝 実装フェーズ

### Phase 1: Flask Web Server 基本実装 (3日)

#### 1.1 Flask アプリケーション構造

**ファイル**: `v3/app.py`

```python
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API ブループリント登録
from api import chat_bp, session_bp, preview_bp, order_bp, health_bp

app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(session_bp, url_prefix='/api/session')
app.register_blueprint(preview_bp, url_prefix='/api/preview')
app.register_blueprint(order_bp, url_prefix='/api/order')
app.register_blueprint(health_bp, url_prefix='/api/health')

# ルート
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### 1.2 HTML テンプレート

**ファイル**: `v3/templates/index.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 LegoDesigner</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="app">
        <header>
            <h1>🏠 LegoDesigner</h1>
            <p id="session-info">Session: <span id="session-id">-</span></p>
        </header>
        
        <main>
            <div id="chat-container">
                <div id="messages"></div>
                <div id="input-area">
                    <input type="text" id="message-input" placeholder="何を作りたい？">
                    <button id="send-btn">送信</button>
                </div>
            </div>
            
            <div id="preview-container">
                <div id="canvas"></div>
                <div id="controls">
                    <button id="download-btn">📥 ダウンロード</button>
                    <button id="order-btn">💳 発注する</button>
                </div>
            </div>
        </main>
    </div>
    
    <script src="/static/js/app.js"></script>
    <script src="/static/js/chat.js"></script>
    <script src="/static/js/preview.js"></script>
    <script src="/static/js/api.js"></script>
</body>
</html>
```

#### 1.3 API エンドポイント

**ファイル**: `v3/api/chat.py`

```python
from flask import Blueprint, request, jsonify
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)
chat_service = ChatService()

@chat_bp.route('/send', methods=['POST'])
def send_message():
    """チャットメッセージを送信"""
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    
    try:
        result = chat_service.process_message(session_id, message)
        return jsonify({
            'status': 'success',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@chat_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """チャット履歴を取得"""
    try:
        history = chat_service.get_history(session_id)
        return jsonify({
            'status': 'success',
            'history': history
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
```

**チェックリスト**
- [ ] Flask アプリケーション構造実装
- [ ] HTML テンプレート作成
- [ ] API エンドポイント実装
- [ ] ローカルテスト確認

---

### Phase 2: チャット履歴 JSONL 保存 (2日)

#### 2.1 JSONL 処理

**ファイル**: `v3/services/jsonl_service.py`

```python
import json
import os
from datetime import datetime
from pathlib import Path

class JSONLService:
    def __init__(self, data_dir='data/sessions'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_message(self, session_id: str, message: dict):
        """メッセージを JSONL に保存"""
        file_path = self.data_dir / f"{session_id}.jsonl"
        
        # タイムスタンプ追加
        message['timestamp'] = datetime.now().isoformat()
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(message, ensure_ascii=False) + '\n')
    
    def get_history(self, session_id: str) -> list:
        """セッション履歴を取得"""
        file_path = self.data_dir / f"{session_id}.jsonl"
        
        if not file_path.exists():
            return []
        
        messages = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        
        return messages
    
    def search(self, session_id: str, keyword: str) -> list:
        """キーワード検索"""
        history = self.get_history(session_id)
        return [msg for msg in history if keyword in msg.get('content', '')]
```

**チェックリスト**
- [ ] JSONL 読み書き実装
- [ ] メッセージ保存機能
- [ ] 履歴取得機能
- [ ] 検索機能

---

### Phase 3: 3Dプレビュー実装 (3日)

#### 3.1 Three.js プレビュー

**ファイル**: `v3/static/js/preview.js`

```javascript
class LegoPreview {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        
        this.init();
    }
    
    init() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);
        
        // ライト設定
        const light = new THREE.DirectionalLight(0xffffff, 1);
        light.position.set(5, 5, 5);
        this.scene.add(light);
        
        // カメラ位置
        this.camera.position.z = 5;
        
        // アニメーション開始
        this.animate();
    }
    
    loadSTL(stlUrl) {
        // STL ファイルを読み込んで表示
        fetch(stlUrl)
            .then(response => response.arrayBuffer())
            .then(buffer => {
                const geometry = this.parseSTL(buffer);
                const material = new THREE.MeshPhongMaterial({ color: 0xff0000 });
                const mesh = new THREE.Mesh(geometry, material);
                this.scene.add(mesh);
            });
    }
    
    parseSTL(buffer) {
        // STL パーサー実装
        // (簡略版)
        const geometry = new THREE.BufferGeometry();
        // ... パース処理
        return geometry;
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
}
```

**チェックリスト**
- [ ] Three.js 初期化
- [ ] STL ローダー実装
- [ ] 回転・拡大機能
- [ ] ライト・カメラ設定

---

### Phase 4: Go 処理エンジン (3日)

#### 4.1 JSONL 処理 (Go)

**ファイル**: `v3/go/pkg/jsonl/processor.go`

```go
package jsonl

import (
    "bufio"
    "encoding/json"
    "os"
)

type Message struct {
    SessionID string                 `json:"session_id"`
    Timestamp string                 `json:"timestamp"`
    Role      string                 `json:"role"`
    Content   string                 `json:"content"`
    Intent    string                 `json:"intent,omitempty"`
    Entities  map[string]interface{} `json:"entities,omitempty"`
}

type Processor struct {
    filePath string
}

func NewProcessor(filePath string) *Processor {
    return &Processor{filePath: filePath}
}

func (p *Processor) ReadAll() ([]Message, error) {
    file, err := os.Open(p.filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()
    
    var messages []Message
    scanner := bufio.NewScanner(file)
    
    for scanner.Scan() {
        var msg Message
        if err := json.Unmarshal(scanner.Bytes(), &msg); err != nil {
            continue
        }
        messages = append(messages, msg)
    }
    
    return messages, scanner.Err()
}

func (p *Processor) Search(keyword string) ([]Message, error) {
    messages, err := p.ReadAll()
    if err != nil {
        return nil, err
    }
    
    var results []Message
    for _, msg := range messages {
        if contains(msg.Content, keyword) {
            results = append(results, msg)
        }
    }
    
    return results, nil
}

func contains(s, substr string) bool {
    // 簡略版
    return len(s) > 0 && len(substr) > 0
}
```

**チェックリスト**
- [ ] JSONL リーダー実装
- [ ] メッセージ構造体定義
- [ ] 検索機能実装
- [ ] テスト実装

---

### Phase 5: 発注フロー (2日)

#### 5.1 発注処理

**ファイル**: `v3/api/order.py`

```python
from flask import Blueprint, request, jsonify
from services.order_service import OrderService

order_bp = Blueprint('order', __name__)
order_service = OrderService()

@order_bp.route('/create', methods=['POST'])
def create_order():
    """発注を作成"""
    data = request.json
    session_id = data.get('session_id')
    model_id = data.get('model_id')
    
    try:
        order = order_service.create_order(session_id, model_id)
        return jsonify({
            'status': 'success',
            'order_id': order['id']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@order_bp.route('/status/<order_id>', methods=['GET'])
def get_status(order_id):
    """発注ステータスを取得"""
    try:
        status = order_service.get_status(order_id)
        return jsonify({
            'status': 'success',
            'order_status': status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
```

**チェックリスト**
- [ ] 発注作成機能
- [ ] ステータス追跡
- [ ] 親への通知
- [ ] テスト実装

---

## 🧪 テスト戦略

### ユニットテスト

```python
# v3/tests/test_services.py

import pytest
from services.chat_service import ChatService
from services.jsonl_service import JSONLService

def test_save_message():
    service = JSONLService()
    message = {
        'role': 'user',
        'content': 'テスト'
    }
    service.save_message('test-session', message)
    # 検証

def test_get_history():
    service = JSONLService()
    history = service.get_history('test-session')
    assert isinstance(history, list)
```

### 統合テスト

```python
# v3/tests/test_api.py

def test_chat_endpoint(client):
    response = client.post('/api/chat/send', json={
        'session_id': 'test-001',
        'message': 'テスト'
    })
    assert response.status_code == 200
```

**チェックリスト**
- [ ] ユニットテスト実装
- [ ] 統合テスト実装
- [ ] カバレッジ > 80%

---

## 🚀 デプロイ

### Docker

**ファイル**: `v3/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY v3/ .

EXPOSE 5000

CMD ["python", "app.py"]
```

**チェックリスト**
- [ ] Docker イメージ構築
- [ ] Docker Compose 設定
- [ ] 本番環境テスト

---

## 📊 成功指標

| 指標 | 目標 |
|---|---|
| **API応答時間** | < 500ms |
| **3D生成時間** | < 2秒 |
| **チャット保存成功率** | > 99.9% |
| **ページ読み込み** | < 1秒 |
| **テストカバレッジ** | > 80% |

---

## 📅 スケジュール

| 週 | Phase | 目標 |
|---|---|---|
| **Week 1** | 1-2 | Flask + JSONL 基本実装 |
| **Week 2** | 3-4 | 3Dプレビュー + Go 処理 |
| **Week 3** | 5 | 発注フロー + テスト |
| **Week 4** | - | デプロイ + ドキュメント |

---

## 🔗 依存関係

```
Phase 1 (Flask)
    ↓
Phase 2 (JSONL)
    ↓
Phase 3 (3D Preview)
    ├─→ Phase 4 (Go)
    └─→ Phase 5 (Order)
         ↓
    Deployment
```

---

## 📝 注記

- V1/V2 のセッション管理は完全に引き継ぎ
- Blender MCP は既存のまま使用
- Go は JSONL 処理と発注フロー専用
- 全データは JSONL 形式で保存
- ML学習用データは自動エクスポート可能
