"""
Phase 1 テスト: Session Manager 統合
"""

import sys
import json
import time
from pathlib import Path

# パス設定
src_path = str(Path(__file__).parent.parent)
sys.path.insert(0, src_path)

from session_manager.manager import get_session_manager

def test_session_creation():
    """セッション作成テスト"""
    print("\n=== Test 1: Session Creation ===")
    
    sm = get_session_manager()
    session_id = sm.create_session()
    
    print(f"✓ Session created: {session_id}")
    assert session_id.startswith("scene-"), "Session ID format error"
    print("✓ Session ID format is correct")
    
    return session_id

def test_session_info(session_id):
    """セッション情報取得テスト"""
    print("\n=== Test 2: Get Session Info ===")
    
    sm = get_session_manager()
    info = sm.get_session_info(session_id)
    
    print(f"✓ Session info retrieved")
    print(json.dumps(info, indent=2))
    
    assert info["session_id"] == session_id, "Session ID mismatch"
    assert "created_at" in info, "Missing created_at"
    assert "blender" in info, "Missing blender info"
    assert "state" in info, "Missing state"
    
    print("✓ Session info structure is correct")

def test_list_sessions():
    """セッション一覧テスト"""
    print("\n=== Test 3: List Sessions ===")
    
    sm = get_session_manager()
    sessions = sm.list_sessions()
    
    print(f"✓ Found {len(sessions)} active sessions")
    
    for session in sessions:
        print(f"  - {session['session_id']}")
    
    assert len(sessions) > 0, "No sessions found"
    print("✓ Session list is not empty")

def test_session_history(session_id):
    """セッション履歴テスト"""
    print("\n=== Test 4: Get Session History ===")
    
    sm = get_session_manager()
    history = sm.get_session_history(session_id)
    
    print(f"✓ Session history retrieved")
    print(f"  Command count: {len(history)}")
    
    if history:
        print("  Recent commands:")
        for cmd in history[-3:]:
            print(f"    - {cmd['command']} ({cmd['duration']:.2f}s)")
    
    assert isinstance(history, list), "History should be a list"
    print("✓ Session history structure is correct")

def test_session_manager_direct():
    """SessionManager 直接テスト"""
    print("\n=== Test 5: SessionManager Direct Access ===")
    
    sm = get_session_manager()
    
    # セッション作成
    session_id = sm.create_session()
    print(f"✓ Session created: {session_id}")
    
    # セッション取得
    session = sm.get_session(session_id)
    assert session is not None, "Session not found"
    print(f"✓ Session retrieved")
    
    # セッション情報
    info = sm.get_session_info(session_id)
    print(f"✓ Session info: {info['session_id']}")
    
    # セッション一覧
    sessions = sm.list_sessions()
    print(f"✓ Total sessions: {len(sessions)}")
    
    # セッションクローズ
    sm.close_session(session_id)
    print(f"✓ Session closed")
    
    # クローズ後は見つからない
    session = sm.get_session(session_id)
    assert session is None, "Session should be closed"
    print(f"✓ Session properly closed")

def test_session_timeout():
    """セッションタイムアウトテスト"""
    print("\n=== Test 6: Session Timeout ===")
    
    sm = get_session_manager()
    
    # セッション作成
    session_id = sm.create_session()
    session = sm.get_session(session_id)
    
    print(f"✓ Session created: {session_id}")
    
    # タイムアウト判定（デフォルト: 5分）
    is_idle = session.is_idle(timeout=1.0)  # 1秒でテスト
    print(f"✓ Session idle check: {is_idle}")
    
    # アクティビティ更新
    session.update_activity()
    is_idle = session.is_idle(timeout=1.0)
    print(f"✓ After activity update: {is_idle}")
    
    assert not is_idle, "Session should not be idle after update"
    print("✓ Session timeout logic works correctly")

def test_multiple_sessions():
    """複数セッション管理テスト"""
    print("\n=== Test 7: Multiple Sessions ===")
    
    sm = get_session_manager()
    
    # 複数セッション作成
    session_ids = []
    for i in range(3):
        session_id = sm.create_session()
        session_ids.append(session_id)
        print(f"✓ Session {i+1} created: {session_id}")
    
    # 全セッション確認
    sessions = sm.list_sessions()
    print(f"✓ Total sessions: {len(sessions)}")
    
    # 各セッション情報確認
    for session_id in session_ids:
        info = sm.get_session_info(session_id)
        assert info["session_id"] == session_id, "Session ID mismatch"
        print(f"✓ Session {session_id} verified")
    
    print("✓ Multiple session management works correctly")

def test_session_state_update():
    """セッション状態更新テスト"""
    print("\n=== Test 8: Session State Update ===")
    
    sm = get_session_manager()
    session_id = sm.create_session()
    
    print(f"✓ Session created: {session_id}")
    
    # 状態更新
    sm.update_state(
        session_id,
        objects=["Cube", "Light", "Camera"],
        selection="Cube"
    )
    
    # 状態確認
    session = sm.get_session(session_id)
    assert session.state.objects == ["Cube", "Light", "Camera"], "Objects mismatch"
    assert session.state.selection == "Cube", "Selection mismatch"
    
    print(f"✓ State updated correctly")
    print(f"  Objects: {session.state.objects}")
    print(f"  Selection: {session.state.selection}")

def run_all_tests():
    """全テスト実行"""
    print("=" * 60)
    print("Phase 1: Session Manager Integration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Session Creation
        session_id = test_session_creation()
        
        # Test 2: Session Info
        test_session_info(session_id)
        
        # Test 3: List Sessions
        test_list_sessions()
        
        # Test 4: Session History
        test_session_history(session_id)
        
        # Test 5: SessionManager Direct
        test_session_manager_direct()
        
        # Test 6: Session Timeout
        test_session_timeout()
        
        # Test 7: Multiple Sessions
        test_multiple_sessions()
        
        # Test 8: Session State Update
        test_session_state_update()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        return True
    
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
