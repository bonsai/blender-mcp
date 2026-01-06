"""
Router - MCP Tool Call を Session Manager 経由で Blender に ルーティング
"""

import json
import logging
from typing import Dict, Any, Optional
try:
    from .manager import get_session_manager
except ImportError:
    from manager import get_session_manager

logger = logging.getLogger("Router")


class SessionAwareRouter:
    """セッション対応ルーター"""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        logger.info("SessionAwareRouter initialized")
    
    def create_session(self) -> str:
        """新しいセッションを作成"""
        session_id = self.session_manager.create_session()
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def handle_tool_call(
        self,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tool Call をハンドル
        
        Args:
            session_id: セッションID
            tool_name: ツール名
            args: ツール引数
        
        Returns:
            {
                "session_id": str,
                "tool": str,
                "result": Any,
                "state": Dict,
                "status": "success" | "error"
            }
        """
        try:
            logger.info(f"Tool call: {tool_name} (session: {session_id})")
            
            # セッション確認
            session = self.session_manager.get_session(session_id)
            if not session:
                return {
                    "status": "error",
                    "message": f"Session not found: {session_id}"
                }
            
            # Tool Call を Blender コマンドに変換
            command_type, params = self._convert_tool_to_command(tool_name, args)
            
            # Blender に送信
            result = self.session_manager.send_command(
                session_id,
                command_type,
                params
            )
            
            # セッション状態を取得
            session_info = self.session_manager.get_session_info(session_id)
            
            return {
                "status": "success",
                "session_id": session_id,
                "tool": tool_name,
                "result": result,
                "state": session_info.get("state", {}),
                "command_count": session_info.get("command_count", 0)
            }
        
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _convert_tool_to_command(self, tool_name: str, args: Dict[str, Any]) -> tuple:
        """
        MCP Tool Call を Blender コマンドに変換
        
        Returns:
            (command_type, params)
        """
        # Tool Name → Blender Command Type マッピング
        tool_to_command = {
            "execute_blender_code": "execute_code",
            "get_scene_info": "get_scene_info",
            "get_object_info": "get_object_info",
            "get_viewport_screenshot": "get_viewport_screenshot",
            "create_object": "create_object",
            "delete_object": "delete_object",
            "set_material": "set_material",
            "search_polyhaven_assets": "search_polyhaven_assets",
            "download_polyhaven_asset": "download_polyhaven_asset",
            "search_sketchfab_models": "search_sketchfab_models",
            "download_sketchfab_model": "download_sketchfab_model",
        }
        
        command_type = tool_to_command.get(tool_name, tool_name)
        return command_type, args
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """セッション情報を取得"""
        return self.session_manager.get_session_info(session_id)
    
    def get_session_history(self, session_id: str) -> list:
        """セッション履歴を取得"""
        return self.session_manager.get_session_history(session_id)
    
    def list_sessions(self) -> list:
        """全セッション一覧"""
        return self.session_manager.list_sessions()
    
    def close_session(self, session_id: str):
        """セッションをクローズ"""
        self.session_manager.close_session(session_id)
        logger.info(f"Session closed: {session_id}")


# グローバルインスタンス
_router: Optional[SessionAwareRouter] = None


def get_router() -> SessionAwareRouter:
    """グローバルRouterを取得"""
    global _router
    if _router is None:
        _router = SessionAwareRouter()
    return _router


# ========================================
# MCP Server 統合用ヘルパー
# ========================================

def create_session_aware_tool(tool_name: str, original_tool_func):
    """
    既存のMCP Toolをセッション対応にラップ
    
    使用例:
    @mcp.tool()
    def execute_blender_code(ctx: Context, code: str, session_id: str = None) -> str:
        router = get_router()
        if not session_id:
            session_id = router.create_session()
        
        result = router.handle_tool_call(
            session_id,
            "execute_blender_code",
            {"code": code}
        )
        
        return json.dumps(result)
    """
    pass


if __name__ == "__main__":
    # テスト用
    router = get_router()
    
    # セッション作成
    session_id = router.create_session()
    print(f"Created session: {session_id}")
    
    # セッション情報
    print(json.dumps(router.get_session_info(session_id), indent=2))
    
    # セッション一覧
    print(f"Active sessions: {len(router.list_sessions())}")
