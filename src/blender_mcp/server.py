# blender_mcp_server.py - V2 Phase 1: Session Manager 統合版
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
import tempfile
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Optional
import os
from pathlib import Path
import base64
from urllib.parse import urlparse
import sys

# Import Session Manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from session_manager.manager import get_session_manager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876

@dataclass
class BlenderConnection:
    host: str
    port: int
    sock: socket.socket = None
    
    def connect(self) -> bool:
        """Connect to the Blender addon socket server"""
        if self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender: {str(e)}")
            self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from the Blender addon"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Blender: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        sock.settimeout(180.0)
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Blender and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Blender")
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"Command sent, waiting for response...")
            
            self.sock.settimeout(180.0)
            
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")
            
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")
            
            if response.get("status") == "error":
                logger.error(f"Blender error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Blender"))
            
            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Blender")
            self.sock = None
            raise Exception("Timeout waiting for Blender response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Blender lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Blender: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Blender: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    try:
        logger.info("BlenderMCP server starting up")
        yield {}
    finally:
        logger.info("BlenderMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "BlenderMCP",
    lifespan=server_lifespan
)

# Global connection
_blender_connection = None

def get_blender_connection():
    """Get or create a persistent Blender connection"""
    global _blender_connection
    
    if _blender_connection is not None:
        try:
            return _blender_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None
    
    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", DEFAULT_PORT))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            logger.error("Failed to connect to Blender")
            _blender_connection = None
            raise Exception("Could not connect to Blender. Make sure the Blender addon is running.")
        logger.info("Created new persistent connection to Blender")
    
    return _blender_connection

# ========================================
# Session-Aware Tools (Phase 1)
# ========================================

@mcp.tool()
def get_scene_info(ctx: Context, session_id: str = None) -> str:
    """Get detailed information about the current Blender scene
    
    Parameters:
    - session_id: Optional session ID for session management. If not provided, a new session will be created.
    """
    try:
        sm = get_session_manager()
        
        if not session_id:
            session_id = sm.create_session()
        
        # TODO: Implement actual scene info retrieval
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "message": "Scene info retrieval not yet implemented"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info: {str(e)}")
        return f"Error getting scene info: {str(e)}"

@mcp.tool()
def get_object_info(ctx: Context, object_name: str, session_id: str = None) -> str:
    """
    Get detailed information about a specific object in the Blender scene.
    
    Parameters:
    - object_name: The name of the object to get information about
    - session_id: Optional session ID for session management. If not provided, a new session will be created.
    """
    try:
        sm = get_session_manager()
        
        if not session_id:
            session_id = sm.create_session()
        
        # TODO: Implement actual object info retrieval
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "object_name": object_name,
            "message": "Object info retrieval not yet implemented"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info: {str(e)}")
        return f"Error getting object info: {str(e)}"

@mcp.tool()
def execute_blender_code(ctx: Context, code: str, session_id: str = None) -> str:
    """
    Execute arbitrary Python code in Blender. Make sure to do it step-by-step by breaking it into smaller chunks.

    Parameters:
    - code: The Python code to execute
    - session_id: Optional session ID for session management. If not provided, a new session will be created.
    """
    try:
        sm = get_session_manager()
        
        if not session_id:
            session_id = sm.create_session()
        
        # TODO: Implement actual code execution
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "message": "Code execution not yet implemented"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return f"Error executing code: {str(e)}"

@mcp.tool()
def get_viewport_screenshot(ctx: Context, max_size: int = 800, session_id: str = None) -> Image:
    """
    Capture a screenshot of the current Blender 3D viewport.
    
    Parameters:
    - max_size: Maximum size in pixels for the largest dimension (default: 800)
    - session_id: Optional session ID for session management. If not provided, a new session will be created.
    
    Returns the screenshot as an Image.
    """
    try:
        sm = get_session_manager()
        
        if not session_id:
            session_id = sm.create_session()
        
        # TODO: Implement actual screenshot capture
        raise Exception("Screenshot capture not yet implemented")
        
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise Exception(f"Screenshot failed: {str(e)}")

# ========================================
# Session Management Tools
# ========================================

@mcp.tool()
def create_session(ctx: Context) -> str:
    """Create a new session for managing Blender operations
    
    Returns:
    - session_id: The ID of the newly created session
    """
    try:
        sm = get_session_manager()
        session_id = sm.create_session()
        logger.info(f"Session created: {session_id}")
        return json.dumps({
            "status": "success",
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def process_message(ctx: Context, message: str, session_id: str = None) -> str:
    """Process a user message and return a response
    
    Parameters:
    - message: The user message to process
    - session_id: Optional session ID for session management
    """
    try:
        sm = get_session_manager()
        
        if not session_id:
            session_id = sm.create_session()
        
        # TODO: Implement actual message processing
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "message": message,
            "response": "Message processing not yet implemented"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def get_session_info(ctx: Context, session_id: str) -> str:
    """Get information about a specific session
    
    Parameters:
    - session_id: The session ID to get information about
    
    Returns:
    - Session information including state, command history, and Blender connection status
    """
    try:
        sm = get_session_manager()
        info = sm.get_session_info(session_id)
        return json.dumps(info, indent=2)
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def list_sessions(ctx: Context) -> str:
    """List all active sessions
    
    Returns:
    - A list of all active sessions with their information
    """
    try:
        sm = get_session_manager()
        sessions = sm.list_sessions()
        return json.dumps({
            "status": "success",
            "session_count": len(sessions),
            "sessions": sessions
        }, indent=2)
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def get_session_history(ctx: Context, session_id: str) -> str:
    """Get command history for a specific session
    
    Parameters:
    - session_id: The session ID to get history for
    
    Returns:
    - A list of all commands executed in the session with their results
    """
    try:
        sm = get_session_manager()
        history = sm.get_session_history(session_id)
        return json.dumps({
            "status": "success",
            "session_id": session_id,
            "command_count": len(history),
            "history": history
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def close_session(ctx: Context, session_id: str) -> str:
    """Close a session and clean up resources
    
    Parameters:
    - session_id: The session ID to close
    
    Returns:
    - Confirmation of session closure
    """
    try:
        sm = get_session_manager()
        sm.close_session(session_id)
        logger.info(f"Session closed: {session_id}")
        return json.dumps({
            "status": "success",
            "message": f"Session {session_id} closed successfully"
        })
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

# ========================================
# Main execution
# ========================================

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
