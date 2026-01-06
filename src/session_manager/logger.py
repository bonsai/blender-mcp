"""
Session Logger - コマンド履歴・Blender操作・状態を記録
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger("SessionLogger")


class SessionLogger:
    """セッションのログを管理"""
    
    def __init__(self, session_id: str, log_dir: str = "logs/sessions"):
        self.session_id = session_id
        self.log_dir = Path(log_dir) / session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.command_log_file = self.log_dir / "command.log"
        self.blender_log_file = self.log_dir / "blender.log"
        self.state_file = self.log_dir / "state.json"
        self.design_file = self.log_dir / "design.md"
        
        logger.info(f"SessionLogger initialized for {session_id}")
    
    def log_command(self, user_input: str, tool_name: str, args: Dict[str, Any]):
        """自然言語コマンドを記録"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "user_input": user_input,
                "tool": tool_name,
                "args": args
            }
            
            with open(self.command_log_file, "a") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"Command logged: {tool_name}")
        except Exception as e:
            logger.error(f"Error logging command: {e}")
    
    def log_blender_operation(self, command: str, result: Dict[str, Any], duration: float = 0.0):
        """Blender操作を記録"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "command": command,
                "result": result,
                "duration": duration
            }
            
            with open(self.blender_log_file, "a") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            logger.debug(f"Blender operation logged: {command}")
        except Exception as e:
            logger.error(f"Error logging Blender operation: {e}")
    
    def save_state(self, state: Dict[str, Any]):
        """状態スナップショットを保存"""
        try:
            state_data = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "state": state
            }
            
            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"State saved for {self.session_id}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """コマンド履歴を取得"""
        try:
            if not self.command_log_file.exists():
                return []
            
            history = []
            with open(self.command_log_file, "r") as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
            
            return history
        except Exception as e:
            logger.error(f"Error reading command history: {e}")
            return []
    
    def get_blender_history(self) -> List[Dict[str, Any]]:
        """Blender操作履歴を取得"""
        try:
            if not self.blender_log_file.exists():
                return []
            
            history = []
            with open(self.blender_log_file, "r") as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
            
            return history
        except Exception as e:
            logger.error(f"Error reading Blender history: {e}")
            return []
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """現在の状態を取得"""
        try:
            if not self.state_file.exists():
                return None
            
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading state: {e}")
            return None
    
    def generate_design_doc(self) -> str:
        """設計ドキュメントを自動生成"""
        try:
            doc = f"# 設計ドキュメント - {self.session_id}\n\n"
            doc += f"**作成日時**: {datetime.now().isoformat()}\n\n"
            
            command_history = self.get_command_history()
            if command_history:
                doc += "## 実行されたコマンド\n\n"
                for i, cmd in enumerate(command_history, 1):
                    doc += f"{i}. **{cmd.get('tool', 'Unknown')}** ({cmd.get('timestamp', 'N/A')})\n"
                    if cmd.get('user_input'):
                        doc += f"   - ユーザー入力: {cmd['user_input']}\n"
                    doc += "\n"
            
            blender_history = self.get_blender_history()
            if blender_history:
                doc += "## Blender操作履歴\n\n"
                for i, op in enumerate(blender_history, 1):
                    doc += f"{i}. **{op.get('command', 'Unknown')}** ({op.get('duration', 0):.2f}s)\n"
                    doc += f"   - 結果: {op.get('result', {}).get('status', 'unknown')}\n"
                    doc += "\n"
            
            state = self.get_state()
            if state:
                doc += "## 最終状態\n\n"
                doc += f"```json\n{json.dumps(state, indent=2, ensure_ascii=False)}\n```\n"
            
            with open(self.design_file, "w") as f:
                f.write(doc)
            
            logger.info(f"Design document generated for {self.session_id}")
            return doc
        except Exception as e:
            logger.error(f"Error generating design document: {e}")
            return ""
    
    def get_log_summary(self) -> Dict[str, Any]:
        """ログサマリーを取得"""
        try:
            command_history = self.get_command_history()
            blender_history = self.get_blender_history()
            state = self.get_state()
            
            return {
                "session_id": self.session_id,
                "command_count": len(command_history),
                "blender_operation_count": len(blender_history),
                "log_dir": str(self.log_dir),
                "has_state": state is not None,
                "has_design_doc": self.design_file.exists()
            }
        except Exception as e:
            logger.error(f"Error getting log summary: {e}")
            return {}
