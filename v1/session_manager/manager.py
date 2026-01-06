"""
Session Manager - 中央司令塔
3つのサーバ（OLLAMA / MCP / Blender）を横断して状態を管理
"""

import time
import json
import socket
import logging
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

# Importlogger
from .logger import 

# ロギング設定
licConfig(
    level=logging.INFO,

)
logger = l")ageran("SessionMggerng.getLooggie)s's - %(messagevelname)%(l - - %(name)s(asctime)s '%   format= 


@dataclass
class BlenderState:
    """Blender内部状態"""
    objects: List[str] = None
    selection: Optional[str] = None
    last_command: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.objects is None:
            self.objects = []


@dataclass
class BlenderConnection:
    """Blender接続情報"""
    conn: Optional[socket.socket] = None
    connected: bool = False
    host: str = "127.0.0.1"
    port: int = 9876
    last_heartbeat: float = 0.0


@dataclass
class CommandHistory:
    """コマンド履歴"""
    timestamp: float
    command: str
    args: Dict[str, Any]
    result: str
    duration: float


class Session:
    """セッション（1ユーザー = 1セッション）"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.blender = BlenderConnection()
        self.state = BlenderState()
        self.command_history: List[CommandHistory] = []
        self.lock = threading.Lock()
    
    def update_activity(self):
        """最後のアクティビティ時刻を更新"""
        self.last_activity = time.time()
    
    def is_idle(self, timeout: float = 300.0) -> bool:
        """タイムアウト判定（デフォルト5分）"""
        return (time.time() - self.last_activity) > timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """セッション情報を辞書化"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "blender": {
                "connected": self.blender.connected,
                "host": self.blender.host,
                "port": self.blender.port,
                "last_heartbeat": self.blender.last_heartbeat
            },
            "state": {
                "objects": self.state.objects,
                "selection": self.state.selection,
                "last_command": self.state.last_command,
                "last_result": self.state.last_result
            },
            "command_count": len(self.command_history)
        }


class SessionManager:
    """セッション管理マン（中央司令塔）"""
    
    def __init__(self, blender_host: str = "127.0.0.1", blender_port: int = 9876):
        self.sessions: Dict[str, Session] = {}
        self.blender_host = blender_host
        self.blender_port = blender_port
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
        
        logger.info(f"SessionManager initialized (Blender: {blender_host}:{blender_port})")
    
    def create_session(self) -> str:
        """新しいセッションを作成"""
        session_id = f"scene-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        with self.lock:
            session = Session(session_id)
            self.sessions[session_id] = session
        
        logger.info(f"✓ Session created: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """セッションを取得"""
        with self.lock:
            return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """全セッション一覧"""
        with self.lock:
            return [session.to_dict() for session in self.sessions.values()]
    
    def get_blender_connection(self, session_id: str) -> Optional[socket.socket]:
        """Blender接続を取得（keep-alive）"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None
        
        with session.lock:
            # 既に接続済みならそれを返す
            if session.blender.connected and session.blender.conn:
                try:
                    # ハートビート確認
                    session.blender.last_heartbeat = time.time()
                    return session.blender.conn
                except Exception as e:
                    logger.warning(f"Connection check failed: {e}")
                    session.blender.connected = False
                    session.blender.conn = None
            
            # 新規接続
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.blender_host, self.blender_port))
                session.blender.conn = sock
                session.blender.connected = True
                session.blender.last_heartbeat = time.time()
                logger.info(f"✓ Blender connected for session {session_id}")
                return sock
            except Exception as e:
                logger.error(f"Failed to connect to Blender: {e}")
                return None
    
    def send_command(self, session_id: str, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Blenderにコマンドを送信"""
        session = self.get_session(session_id)
        if not session:
            return {"status": "error", "message": f"Session not found: {session_id}"}
        
        conn = self.get_blender_connection(session_id)
        if not conn:
            return {"status": "error", "message": "Not connected to Blender"}
        
        try:
            start_time = time.time()
            
            # コマンド構築
            command = {
                "type": command_type,
                "params": params or {},
                "session_id": session_id
            }
            
            # 送信
            conn.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"→ Command sent: {command_type} (session: {session_id})")
            
            # 受信
            conn.settimeout(180.0)
            response_data = self._receive_full_response(conn)
            response = json.loads(response_data.decode('utf-8'))
            
            duration = time.time() - start_time
            
            # セッション状態を更新
            with session.lock:
                session.state.last_command = command_type
                session.state.last_result = response.get("result", {})
                session.update_activity()
                
                # 履歴に記録
                history = CommandHistory(
                    timestamp=start_time,
                    command=command_type,
                    args=params or {},
                    result=response.get("status", "unknown"),
                    duration=duration
                )
                session.command_history.append(history)
            
            logger.info(f"← Response: {response.get('status')} ({duration:.2f}s)")
            return response.get("result", {})
        
        except socket.timeout:
            logger.error("Socket timeout")
            session.blender.connected = False
            session.blender.conn = None
            return {"status": "error", "message": "Timeout waiting for Blender response"}
        except Exception as e:
            logger.error(f"Error: {e}")
            session.blender.connected = False
            session.blender.conn = None
            return {"status": "error", "message": str(e)}
    
    def _receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """完全なレスポンスを受信"""
        chunks = []
        sock.settimeout(180.0)
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving data")
                        break
                    
                    chunks.append(chunk)
                    
                    # JSON完全性チェック
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        return data
                    except json.JSONDecodeError:
                        continue
                
                except socket.timeout:
                    break
        
        except Exception as e:
            logger.error(f"Receive error: {e}")
            raise
        
        if chunks:
            data = b''.join(chunks)
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response")
        else:
            raise Exception("No data received")
    
    def update_state(self, session_id: str, **kwargs):
        """セッション状態を更新"""
        session = self.get_session(session_id)
        if not session:
            return
        
        with session.lock:
            for key, value in kwargs.items():
                if hasattr(session.state, key):
                    setattr(session.state, key, value)
            session.update_activity()
    
    def close_session(self, session_id: str):
        """セッションをクローズ"""
        session = self.get_session(session_id)
        if not session:
            return
        
        with session.lock:
            if session.blender.conn:
                try:
                    session.blender.conn.close()
                except:
                    pass
            session.blender.connected = False
        
        with self.lock:
            del self.sessions[session_id]
        
        logger.info(f"✓ Session closed: {session_id}")
    
    def cleanup_idle_sessions(self, timeout: float = 300.0):
        """アイドルセッションをクリーンアップ"""
        with self.lock:
            idle_sessions = [
                sid for sid, session in self.sessions.items()
                if session.is_idle(timeout)
            ]
        
        for session_id in idle_sessions:
            logger.info(f"Cleaning up idle session: {session_id}")
            self.close_session(session_id)
    
    def start_cleanup_thread(self, interval: float = 60.0):
        """クリーンアップスレッドを開始"""
        self.running = True
        
        def cleanup_loop():
            while self.running:
                time.sleep(interval)
                self.cleanup_idle_sessions()
        
        self.cleanup_thread = threading.Thread(daemon=True, target=cleanup_loop)
        self.cleanup_thread.start()
        logger.info("Cleanup thread started")
    
    def stop_cleanup_thread(self):
        """クリーンアップスレッドを停止"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Cleanup thread stopped")
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """セッション情報を取得"""
        session = self.get_session(session_id)
        if not session:
            return {"error": f"Session not found: {session_id}"}
        
        with session.lock:
            return session.to_dict()
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """セッションのコマンド履歴を取得"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        with session.lock:
            return [
                {
                    "timestamp": h.timestamp,
                    "command": h.command,
                    "args": h.args,
                    "result": h.result,
                    "duration": h.duration
                }
                for h in session.command_history
            ]


# グローバルインスタンス
_session_manager: Optional[SessionManager] = None


def get_session_manager(blender_host: str = "127.0.0.1", blender_port: int = 9876) -> SessionManager:
    """グローバルSessionManagerを取得"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(blender_host, blender_port)
        _session_manager.start_cleanup_thread()
    return _session_manager


if __name__ == "__main__":
    # テスト用
    sm = get_session_manager()
    
    # セッション作成
    session_id = sm.create_session()
    print(f"Created session: {session_id}")
    
    # セッション情報表示
    print(json.dumps(sm.get_session_info(session_id), indent=2))
    
    # セッション一覧
    print(f"Active sessions: {len(sm.list_sessions())}")
