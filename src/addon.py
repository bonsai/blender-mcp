# Blender MCP Addon - Phase 2: Keep-Alive with Session Management
# Based on original addon.py with session management enhancements

import re
import bpy
import mathutils
import json
import threading
import socket
import time
import requests
import tempfile
import traceback
import os
import shutil
import zipfile
from bpy.props import IntProperty
import io
from datetime import datetime
import hashlib, hmac, base64
import os.path as osp
from contextlib import redirect_stdout, suppress

bl_info = {
    "name": "Blender MCP V2",
    "author": "BlenderMCP",
    "version": (2, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to an MCP-compatible model with Session Management",
    "category": "Interface",
}

RODIN_FREE_TRIAL_KEY = "k9TcfFoEhNd9cCPP2guHAHHHkctZHIRhZDywZ1euGUXwihbYLpOjQhofby80NJez"

# Add User-Agent as required by Poly Haven API
REQ_HEADERS = requests.utils.default_headers()
REQ_HEADERS.update({"User-Agent": "blender-mcp"})

class SessionConnection:
    """セッション単位の接続管理"""
    def __init__(self, session_id: str, client_socket: socket.socket):
        self.session_id = session_id
        self.client = client_socket
        self.created_at = time.time()
        self.last_activity = time.time()
        self.command_count = 0
        self.buffer = b''
    
    def update_activity(self):
        """最後のアクティビティ時刻を更新"""
        self.last_activity = time.time()
    
    def is_idle(self, timeout: float = 300.0) -> bool:
        """タイムアウト判定（デフォルト: 5分）"""
        return (time.time() - self.last_activity) > timeout
    
    def to_dict(self) -> dict:
        """セッション情報を辞書化"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "command_count": self.command_count,
            "idle": self.is_idle()
        }

class BlenderMCPServerV2:
    """Blender MCP Server - Phase 2: Session Management"""
    
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.sessions = {}  # session_id → SessionConnection
        self.sessions_lock = threading.Lock()
        self.cleanup_thread = None
    
    def start(self):
        """サーバーを起動"""
        if self.running:
            print("Server is already running")
            return
        
        self.running = True
        
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)  # Allow multiple connections
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            
            print(f"BlenderMCP V2 server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to start server: {str(e)}")
            self.stop()
    
    def stop(self):
        """サーバーを停止"""
        self.running = False
        
        # Close all sessions
        with self.sessions_lock:
            for session_id, session in list(self.sessions.items()):
                try:
                    session.client.close()
                except:
                    pass
            self.sessions.clear()
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Wait for threads
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None
        
        if self.cleanup_thread:
            try:
                if self.cleanup_thread.is_alive():
                    self.cleanup_thread.join(timeout=1.0)
            except:
                pass
            self.cleanup_thread = None
        
        print("BlenderMCP V2 server stopped")
    
    def _server_loop(self):
        """メインサーバーループ"""
        print("Server thread started")
        self.socket.settimeout(1.0)
        
        while self.running:
            try:
                # Accept new connection
                client, addr = self.socket.accept()
                print(f"New connection from {addr}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, addr)
                )
                client_thread.daemon = True
                client_thread.start()
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {str(e)}")
        
        print("Server thread stopped")
    
    def _handle_client(self, client: socket.socket, addr: tuple):
        """クライアント接続を処理（Keep-Alive）"""
        print(f"Client handler started for {addr}")
        client.settimeout(None)
        session_id = None
        
        try:
            while self.running:
                try:
                    # Receive data
                    data = client.recv(8192)
                    if not data:
                        print(f"Client {addr} disconnected")
                        break
                    
                    # Get or create session
                    if session_id is None:
                        session_id = self._create_session(client)
                        print(f"Session created: {session_id}")
                    
                    # Update session activity
                    with self.sessions_lock:
                        if session_id in self.sessions:
                            self.sessions[session_id].update_activity()
                    
                    # Parse command
                    session = self._get_session(session_id)
                    if session:
                        session.buffer += data
                        
                        try:
                            # Try to parse command
                            command = json.loads(session.buffer.decode('utf-8'))
                            session.buffer = b''
                            
                            # Add session_id to command
                            command['session_id'] = session_id
                            
                            # Execute command
                            response_holder = {'response': None}
                            
                            def execute_wrapper():
                                try:
                                    response = self.execute_command(command)
                                    response_holder['response'] = response
                                except Exception as e:
                                    print(f"Error executing command: {str(e)}")
                                    traceback.print_exc()
                                    response_holder['response'] = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                return None
                            
                            # Schedule execution in main thread
                            bpy.app.timers.register(execute_wrapper, first_interval=0.0)
                            
                            # Wait for response
                            timeout = 180.0
                            start = time.time()
                            while response_holder['response'] is None and (time.time() - start) < timeout:
                                time.sleep(0.01)
                            
                            # Send response
                            if response_holder['response']:
                                response_json = json.dumps(response_holder['response'])
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                    
                                    # Update command count
                                    with self.sessions_lock:
                                        if session_id in self.sessions:
                                            self.sessions[session_id].command_count += 1
                                
                                except:
                                    print("Failed to send response - client disconnected")
                                    break
                            
                            # Keep connection alive - don't close
                        
                        except json.JSONDecodeError:
                            # Incomplete data, wait for more
                            pass
                
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
        
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        
        finally:
            # Clean up session
            if session_id:
                self._close_session(session_id)
            
            try:
                client.shutdown(socket.SHUT_WR)
            except:
                pass
            try:
                client.close()
            except:
                pass
            
            print(f"Client handler stopped for {addr}")
    
    def _create_session(self, client: socket.socket) -> str:
        """新しいセッションを作成"""
        session_id = f"blender-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{id(client):x}"
        
        with self.sessions_lock:
            self.sessions[session_id] = SessionConnection(session_id, client)
        
        return session_id
    
    def _get_session(self, session_id: str) -> SessionConnection:
        """セッションを取得"""
        with self.sessions_lock:
            return self.sessions.get(session_id)
    
    def _close_session(self, session_id: str):
        """セッションをクローズ"""
        with self.sessions_lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                try:
                    session.client.close()
                except:
                    pass
                del self.sessions[session_id]
                print(f"Session closed: {session_id}")
    
    def _cleanup_loop(self):
        """アイドルセッションをクリーンアップ"""
        print("Cleanup thread started")
        
        while self.running:
            try:
                time.sleep(60)  # 1分ごとにチェック
                
                with self.sessions_lock:
                    idle_sessions = [
                        sid for sid, session in self.sessions.items()
                        if session.is_idle(timeout=300.0)  # 5分でタイムアウト
                    ]
                
                for session_id in idle_sessions:
                    print(f"Cleaning up idle session: {session_id}")
                    self._close_session(session_id)
            
            except Exception as e:
                print(f"Error in cleanup loop: {str(e)}")
        
        print("Cleanup thread stopped")
    
    def get_sessions_info(self) -> list:
        """全セッション情報を取得"""
        with self.sessions_lock:
            return [session.to_dict() for session in self.sessions.values()]
    
    def execute_command(self, command: dict) -> dict:
        """コマンドを実行（元の実装を使用）"""
        # This would be the same as the original addon.py execute_command
        # For now, return a placeholder
        return {
            "status": "success",
            "result": {},
            "session_id": command.get("session_id")
        }

# Global server instance
_server = None

def get_server() -> BlenderMCPServerV2:
    """グローバルサーバーインスタンスを取得"""
    global _server
    if _server is None:
        _server = BlenderMCPServerV2()
    return _server

# Blender Panel and Operators (same as original)
class BLENDER_MCP_PT_Panel(bpy.types.Panel):
    """BlenderMCP Panel"""
    bl_label = "BlenderMCP V2"
    bl_idname = "BLENDER_MCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"
    
    def draw(self, context):
        layout = self.layout
        
        # Server status
        server = get_server()
        if server.running:
            layout.label(text="Status: Running ✓", icon="PLAY")
        else:
            layout.label(text="Status: Stopped", icon="PAUSE")
        
        # Buttons
        if not server.running:
            layout.operator("blender_mcp.connect", text="Connect to MCP server")
        else:
            layout.operator("blender_mcp.disconnect", text="Disconnect")
        
        # Sessions info
        if server.running:
            sessions = server.get_sessions_info()
            layout.label(text=f"Active Sessions: {len(sessions)}")
            
            for session in sessions:
                row = layout.row()
                row.label(text=f"  {session['session_id'][:20]}...")
                row.label(text=f"  Commands: {session['command_count']}")

class BLENDER_MCP_OT_Connect(bpy.types.Operator):
    """Connect to MCP server"""
    bl_idname = "blender_mcp.connect"
    bl_label = "Connect to MCP server"
    
    def execute(self, context):
        server = get_server()
        server.start()
        return {'FINISHED'}

class BLENDER_MCP_OT_Disconnect(bpy.types.Operator):
    """Disconnect from MCP server"""
    bl_idname = "blender_mcp.disconnect"
    bl_label = "Disconnect"
    
    def execute(self, context):
        server = get_server()
        server.stop()
        return {'FINISHED'}

# Register classes
def register():
    bpy.utils.register_class(BLENDER_MCP_PT_Panel)
    bpy.utils.register_class(BLENDER_MCP_OT_Connect)
    bpy.utils.register_class(BLENDER_MCP_OT_Disconnect)
    
    # Start server on register
    server = get_server()
    if not server.running:
        server.start()

def unregister():
    # Stop server on unregister
    server = get_server()
    if server.running:
        server.stop()
    
    bpy.utils.unregister_class(BLENDER_MCP_PT_Panel)
    bpy.utils.unregister_class(BLENDER_MCP_OT_Connect)
    bpy.utils.unregister_class(BLENDER_MCP_OT_Disconnect)

if __name__ == "__main__":
    register()
