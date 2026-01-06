"""
Session Persistence - セッションをJSONで永続化
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger("SessionPersistence")


class SessionPersistence:
    """セッションの永続化を管理"""
    
    def __init__(self, storage_dir: str = "data/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SessionPersistence initialized at {self.storage_dir}")
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """セッションをJSONで保存"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            
            data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "data": session_data
            }
            
            with open(session_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session saved: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションをJSONから復元"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            
            if not session_file.exists():
                logger.warning(f"Session file not found: {session_id}")
                return None
            
            with open(session_file, "r") as f:
                data = json.load(f)
            
            logger.info(f"Session loaded: {session_id}")
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """全セッション一覧を取得"""
        try:
            sessions = [f.stem for f in self.storage_dir.glob("*.json")]
            logger.info(f"Found {len(sessions)} sessions")
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """セッションを削除"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session deleted: {session_id}")
                return True
            else:
                logger.warning(f"Session file not found: {session_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def session_exists(self, session_id: str) -> bool:
        """セッションが存在するか確認"""
        session_file = self.storage_dir / f"{session_id}.json"
        return session_file.exists()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッション情報を取得"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, "r") as f:
                data = json.load(f)
            
            return {
                "session_id": session_id,
                "saved_at": data.get("saved_at"),
                "file_size": session_file.stat().st_size,
                "file_path": str(session_file)
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    def export_sessions(self, export_file: str) -> bool:
        """全セッションをエクスポート"""
        try:
            sessions = {}
            for session_id in self.list_sessions():
                session_data = self.load_session(session_id)
                if session_data:
                    sessions[session_id] = session_data
            
            with open(export_file, "w") as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Sessions exported to {export_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting sessions: {e}")
            return False
    
    def import_sessions(self, import_file: str) -> bool:
        """セッションをインポート"""
        try:
            with open(import_file, "r") as f:
                sessions = json.load(f)
            
            for session_id, session_data in sessions.items():
                self.save_session(session_id, session_data)
            
            logger.info(f"Sessions imported from {import_file}")
            return True
        except Exception as e:
            logger.error(f"Error importing sessions: {e}")
            return False
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """古いセッションをクリーンアップ"""
        try:
            from datetime import timedelta
            import time
            
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            for session_file in self.storage_dir.glob("*.json"):
                if session_file.stat().st_mtime < cutoff_time:
                    session_file.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old sessions")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """ストレージ統計を取得"""
        try:
            sessions = self.list_sessions()
            total_size = sum(
                (self.storage_dir / f"{sid}.json").stat().st_size
                for sid in sessions
                if (self.storage_dir / f"{sid}.json").exists()
            )
            
            return {
                "session_count": len(sessions),
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "storage_dir": str(self.storage_dir)
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}


# グローバルインスタンス
_persistence: Optional[SessionPersistence] = None


def get_persistence(storage_dir: str = "data/sessions") -> SessionPersistence:
    """グローバルSessionPersistenceを取得"""
    global _persistence
    if _persistence is None:
        _persistence = SessionPersistence(storage_dir)
    return _persistence
