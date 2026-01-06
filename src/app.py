"""
Flask Web Server - LegoDesigner V3
QR コードアクセス対応 + MCP Client 統合
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_session import Session
import logging
import os
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
import json
import subprocess
import sys
from pathlib import Path
import psutil

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask アプリケーション初期化
app = Flask(__name__)
CORS(app)

# セッション設定
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
Session(app)

# データディレクトリ
DATA_DIR = 'data'
SESSIONS_DIR = os.path.join(DATA_DIR, 'sessions')
MODELS_DIR = os.path.join(DATA_DIR, 'models')
ORDERS_DIR = os.path.join(DATA_DIR, 'orders')
QR_DIR = os.path.join(DATA_DIR, 'qr_codes')

# ディレクトリ作成
for directory in [SESSIONS_DIR, MODELS_DIR, ORDERS_DIR, QR_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========================================
# MCP Client 管理
# ========================================

class MCPClient:
    """MCP Server との通信を管理"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process = None
        self.request_id = 0
    
    def start(self):
        """MCP Server プロセスを起動"""
        try:
            # プロジェクトルート
            project_root = Path(__file__).parent.parent
            
            # MCP Server を subprocess で起動
            self.process = subprocess.Popen(
                [sys.executable, "-m", "blender_mcp.server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root),
                text=True,
                bufsize=1
            )
            
            logger.info(f"MCP Server started for session {self.session_id} (PID: {self.process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start MCP Server: {e}")
            return False
    
    def send_request(self, method: str, params: dict = None, session_id: str = None) -> dict:
        """MCP Server に JSON-RPC リクエストを送信"""
        if not self.process:
            raise Exception("MCP Server not started")
        
        self.request_id += 1
        
        request_obj = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # ログに記録
            if session_id:
                add_communication_log(session_id, "request", request_obj, "pending")
            
            # リクエスト送信
            request_json = json.dumps(request_obj)
            self.process.stdin.write(request_json + "\n")
            self.process.stdin.flush()
            
            logger.debug(f"Sent: {request_json}")
            
            # レスポンス受信
            response_line = self.process.stdout.readline()
            if not response_line:
                raise Exception("MCP Server closed connection")
            
            response = json.loads(response_line)
            logger.debug(f"Received: {response_line}")
            
            # ログに記録
            if session_id:
                status = "success" if "error" not in response else "error"
                add_communication_log(session_id, "response", response, status)
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            return response.get("result", {})
        
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            if session_id:
                add_communication_log(session_id, "response", {"error": str(e)}, "error")
            raise
    
    def stop(self):
        """MCP Server プロセスを停止"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info(f"MCP Server stopped for session {self.session_id}")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning(f"MCP Server killed for session {self.session_id}")
            finally:
                self.process = None

# セッションごとの MCP Client を管理
_mcp_clients = {}

# 通信ログ管理
_communication_logs = {}

def get_mcp_client(session_id: str) -> MCPClient:
    """セッションの MCP Client を取得（なければ作成）"""
    if session_id not in _mcp_clients:
        client = MCPClient(session_id)
        if client.start():
            _mcp_clients[session_id] = client
            _communication_logs[session_id] = []
        else:
            raise Exception("Failed to start MCP Server")
    
    return _mcp_clients[session_id]

def cleanup_mcp_client(session_id: str):
    """セッションの MCP Client をクリーンアップ"""
    if session_id in _mcp_clients:
        _mcp_clients[session_id].stop()
        del _mcp_clients[session_id]
    if session_id in _communication_logs:
        del _communication_logs[session_id]

def add_communication_log(session_id: str, direction: str, data: dict, status: str = "success"):
    """通信ログを追加"""
    if session_id not in _communication_logs:
        _communication_logs[session_id] = []
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "direction": direction,  # "request" or "response"
        "status": status,  # "success", "error", "pending"
        "data": data,
        "size": len(json.dumps(data))
    }
    
    _communication_logs[session_id].append(log_entry)
    logger.debug(f"Communication log: {log_entry}")

# ========================================
# QR コード生成
# ========================================

def generate_qr_code(session_id: str, host: str = 'localhost', port: int = 5000) -> str:
    """
    QR コードを生成して Base64 エンコード
    
    Args:
        session_id: セッションID
        host: ホスト名
        port: ポート番号
    
    Returns:
        Base64 エンコードされた QR コード画像
    """
    # アクセスURL生成
    url = f"http://{host}:{port}/join/{session_id}"
    
    # QR コード生成
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # 画像生成
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Base64 エンコード
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    logger.info(f"QR code generated for session: {session_id}")
    
    return f"data:image/png;base64,{img_base64}"

# ========================================
# セッション管理
# ========================================

def create_session() -> str:
    """新しいセッションを作成"""
    session_id = f"lego-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # セッション情報を保存
    session_data = {
        'session_id': session_id,
        'created_at': datetime.now().isoformat(),
        'messages': [],
        'models': [],
        'orders': []
    }
    
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Session created: {session_id}")
    
    return session_id

def get_session_data(session_id: str) -> dict:
    """セッションデータを取得"""
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    if not os.path.exists(session_file):
        return None
    
    with open(session_file, 'r') as f:
        return json.load(f)

def save_session_data(session_id: str, data: dict):
    """セッションデータを保存"""
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    with open(session_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========================================
# ルート
# ========================================

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/status')
def status_page():
    """サーバーステータスページ"""
    return render_template('server_status.html')

@app.route('/new')
def new_session():
    """新しいセッションを作成"""
    session_id = create_session()
    
    # QR コード生成
    host = request.host.split(':')[0]
    port = request.host.split(':')[1] if ':' in request.host else 5000
    qr_code = generate_qr_code(session_id, host, int(port))
    
    return render_template('new_session.html', 
                         session_id=session_id,
                         qr_code=qr_code)

@app.route('/join/<session_id>')
def join_session(session_id: str):
    """QR コードからセッションに参加"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return render_template('error.html', 
                             message=f"セッションが見つかりません: {session_id}"), 404
    
    # ブラウザセッションに保存
    session['session_id'] = session_id
    session.permanent = True
    
    logger.info(f"User joined session: {session_id}")
    
    return redirect(url_for('chat', session_id=session_id))

@app.route('/chat/<session_id>')
def chat(session_id: str):
    """チャット画面"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return render_template('error.html', 
                             message=f"セッションが見つかりません: {session_id}"), 404
    
    return render_template('chat.html', 
                         session_id=session_id,
                         session_data=session_data)

@app.route('/preview/<session_id>')
def preview(session_id: str):
    """3Dプレビュー画面"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return render_template('error.html', 
                             message=f"セッションが見つかりません: {session_id}"), 404
    
    return render_template('preview.html', 
                         session_id=session_id,
                         session_data=session_data)

@app.route('/order/<session_id>')
def order(session_id: str):
    """発注フロー"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return render_template('error.html', 
                             message=f"セッションが見つかりません: {session_id}"), 404
    
    return render_template('order.html', 
                         session_id=session_id,
                         session_data=session_data)

# ========================================
# クリーンアップ
# ========================================

@app.teardown_appcontext
def cleanup(error=None):
    """アプリケーション終了時にクリーンアップ"""
    # 全ての MCP Client を停止
    for session_id in list(_mcp_clients.keys()):
        cleanup_mcp_client(session_id)

# ========================================
# API エンドポイント
# ========================================

@app.route('/api/session/info/<session_id>', methods=['GET'])
def api_session_info(session_id: str):
    """セッション情報を取得"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'created_at': session_data.get('created_at'),
        'message_count': len(session_data.get('messages', [])),
        'model_count': len(session_data.get('models', [])),
        'order_count': len(session_data.get('orders', []))
    })

@app.route('/api/session/qr/<session_id>', methods=['GET'])
def api_session_qr(session_id: str):
    """セッションの QR コードを取得"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    # QR コード生成
    host = request.host.split(':')[0]
    port = request.host.split(':')[1] if ':' in request.host else 5000
    qr_code = generate_qr_code(session_id, host, int(port))
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'qr_code': qr_code
    })

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    """チャットメッセージを送信"""
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    
    if not session_id or not message:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
    
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    try:
        # MCP Client を取得
        mcp_client = get_mcp_client(session_id)
        
        # MCP Server に処理を依頼
        result = mcp_client.send_request("process_message", {
            "message": message,
            "session_id": session_id
        }, session_id)
        
        # メッセージを追加
        msg_obj = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'role': 'user',
            'content': message,
            'mcp_result': result
        }
        
        session_data['messages'].append(msg_obj)
        save_session_data(session_id, session_data)
        
        logger.info(f"Message sent in session {session_id}: {message}")
        
        return jsonify({
            'status': 'success',
            'message_id': msg_obj['id'],
            'timestamp': msg_obj['timestamp'],
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
def api_chat_history(session_id: str):
    """チャット履歴を取得"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'messages': session_data.get('messages', [])
    })

@app.route('/api/model/create', methods=['POST'])
def api_model_create():
    """3Dモデルを作成"""
    data = request.json
    session_id = data.get('session_id')
    model_data = data.get('model')
    
    if not session_id or not model_data:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
    
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    # モデルを追加
    model_obj = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'data': model_data
    }
    
    session_data['models'].append(model_obj)
    save_session_data(session_id, session_data)
    
    logger.info(f"Model created in session {session_id}: {model_obj['id']}")
    
    return jsonify({
        'status': 'success',
        'model_id': model_obj['id'],
        'timestamp': model_obj['timestamp']
    })

@app.route('/api/model/list/<session_id>', methods=['GET'])
def api_model_list(session_id: str):
    """セッションのモデル一覧を取得"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'models': session_data.get('models', [])
    })

@app.route('/api/order/create', methods=['POST'])
def api_order_create():
    """発注を作成"""
    data = request.json
    session_id = data.get('session_id')
    model_id = data.get('model_id')
    
    if not session_id or not model_id:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
    
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    # 発注を追加
    order_obj = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'model_id': model_id,
        'status': 'pending'
    }
    
    session_data['orders'].append(order_obj)
    save_session_data(session_id, session_data)
    
    logger.info(f"Order created in session {session_id}: {order_obj['id']}")
    
    return jsonify({
        'status': 'success',
        'order_id': order_obj['id'],
        'timestamp': order_obj['timestamp']
    })

@app.route('/api/order/list/<session_id>', methods=['GET'])
def api_order_list(session_id: str):
    """セッションの発注一覧を取得"""
    session_data = get_session_data(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'orders': session_data.get('orders', [])
    })

# ========================================
# ヘルスチェック
# ========================================

@app.route('/api/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0'
    })

@app.route('/api/mcp/execute', methods=['POST'])
def api_mcp_execute():
    """MCP に直接コマンドを実行"""
    data = request.json
    session_id = data.get('session_id')
    method = data.get('method')
    params = data.get('params', {})
    
    if not session_id or not method:
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
    
    try:
        mcp_client = get_mcp_client(session_id)
        result = mcp_client.send_request(method, params, session_id)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'method': method,
            'result': result
        })
    except Exception as e:
        logger.error(f"Error executing MCP command: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
def api_communication_logs(session_id: str):
    """セッションの通信ログを取得"""
    logs = _communication_logs.get(session_id, [])
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'log_count': len(logs),
        'logs': logs
    })

@app.route('/api/server-status', methods=['GET'])
def api_server_status():
    """MCP Server のステータスを取得"""
    status_info = {
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(_mcp_clients),
        'sessions': [],
        'active_ports': get_active_ports()
    }
    
    for session_id, client in _mcp_clients.items():
        session_info = {
            'session_id': session_id,
            'pid': client.process.pid if client.process else None,
            'running': client.process is not None and client.process.poll() is None,
            'log_count': len(_communication_logs.get(session_id, []))
        }
        status_info['sessions'].append(session_info)
    
    return jsonify(status_info)

def get_active_ports():
    """アクティブなポート情報を取得"""
    try:
        ports = []
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN':
                ports.append({
                    'port': conn.laddr.port,
                    'address': conn.laddr.ip,
                    'protocol': 'TCP' if conn.type == 1 else 'UDP',
                    'pid': conn.pid
                })
        
        # Blender MCP 関連のポートをフィルタ
        mcp_ports = [p for p in ports if p['port'] in [9876, 5000]]
        return mcp_ports
    except Exception as e:
        logger.error(f"Error getting active ports: {e}")
        return []

# ========================================
# エラーハンドリング
# ========================================

@app.errorhandler(404)
def not_found(error):
    """404 エラー"""
    return render_template('error.html', 
                         message='ページが見つかりません'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 エラー"""
    logger.error(f"Internal error: {error}")
    return render_template('error.html', 
                         message='サーバーエラーが発生しました'), 500

# ========================================
# メイン
# ========================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
