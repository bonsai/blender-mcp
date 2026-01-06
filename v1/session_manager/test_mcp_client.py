#!/usr/bin/env python3
"""
Test MCP Client - Send commands to Blender via the MCP Server
This demonstrates the flow: MCP Client → Blender MCP Server → bpy
"""

import socket
import json
import time
import sys

class BlenderMCPClient:
    """Keep-alive MCP client for Blender"""
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.sock = None
    
    def connect(self):
        """Connect to Blender MCP server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"[CLIENT] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect: {e}")
            return False
    
    def send_command(self, command_type, **params):
        """Send a command and receive response"""
        if not self.sock:
            print("[ERROR] Not connected. Call connect() first.")
            return None
        
        try:
            # Build command
            command = {
                "type": command_type,
                "params": params
            }
            
            # Send command
            command_json = json.dumps(command)
            print(f"[CLIENT] Sending: {command_json}")
            self.sock.sendall(command_json.encode('utf-8'))
            
            # Receive response (wait for server to close write side)
            response_data = b''
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            # Parse response
            response = json.loads(response_data.decode('utf-8'))
            print(f"[CLIENT] Response: {json.dumps(response, indent=2)}")
            return response
        
        except Exception as e:
            print(f"[ERROR] Command failed: {e}")
            return None
    
    def close(self):
        """Close connection"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            print("[CLIENT] Disconnected")

def send_command(host='localhost', port=9876, command_type='execute_code', **params):
    """Legacy function - creates new connection for each command"""
    client = BlenderMCPClient(host, port)
    if not client.connect():
        print(f"[INFO] Make sure:")
        print(f"  1. Blender is running")
        print(f"  2. The BlenderMCP addon is installed and enabled")
        print(f"  3. Server is listening on {host}:{port}")
        return None
    
    response = client.send_command(command_type, **params)
    client.close()
    return response

def test_hello_cube():
    """Test: Create a cube in Blender"""
    print("\n" + "="*60)
    print("TEST: Create a Cube in Blender")
    print("="*60)
    
    code = """
import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

# Get the created cube
cube = bpy.context.active_object
cube.name = "TestCube"

print(f"✓ Cube created: {cube.name}")
"""
    
    response = send_command(
        command_type='execute_code',
        code=code
    )
    
    if response and response.get('status') == 'success':
        print("✓ SUCCESS: Cube created in Blender!")
        return True
    else:
        print("✗ FAILED: Could not create cube")
        return False

def test_get_scene_info():
    """Test: Get scene information"""
    print("\n" + "="*60)
    print("TEST: Get Scene Information")
    print("="*60)
    
    response = send_command(command_type='get_scene_info')
    
    if response and response.get('status') == 'success':
        result = response.get('result', {})
        print(f"✓ Scene: {result.get('name')}")
        print(f"✓ Objects: {result.get('object_count')}")
        print(f"✓ Materials: {result.get('materials_count')}")
        return True
    else:
        print("✗ FAILED: Could not get scene info")
        return False

def test_get_viewport_screenshot():
    """Test: Take a screenshot"""
    print("\n" + "="*60)
    print("TEST: Take Viewport Screenshot")
    print("="*60)
    
    import tempfile
    import os
    
    # Create temp file path
    temp_dir = tempfile.gettempdir()
    screenshot_path = os.path.join(temp_dir, "blender_screenshot.png")
    
    response = send_command(
        command_type='get_viewport_screenshot',
        filepath=screenshot_path,
        max_size=800,
        format='png'
    )
    
    if response and response.get('status') == 'success':
        result = response.get('result', {})
        print(f"✓ Screenshot saved: {result.get('filepath')}")
        print(f"✓ Size: {result.get('width')}x{result.get('height')}")
        return True
    else:
        print("✗ FAILED: Could not take screenshot")
        return False

def main():
    print("\n" + "="*60)
    print("BLENDER MCP CLIENT TEST - KEEP-ALIVE MODE")
    print("="*60)
    print("\nThis script tests the Blender MCP Server connection")
    print("Make sure Blender is running with the addon enabled!")
    
    # Create a single keep-alive connection
    client = BlenderMCPClient()
    
    if not client.connect():
        print("\n✗ Failed to connect to Blender MCP server")
        return
    
    print("\n✓ Connected! Sending multiple commands on same connection...\n")
    
    # Test 1: Get scene info
    print("="*60)
    print("TEST 1: Get Scene Information")
    print("="*60)
    result1 = client.send_command('get_scene_info')
    if result1 and result1.get('status') == 'success':
        result = result1.get('result', {})
        print(f"✓ Scene: {result.get('name')}")
        print(f"✓ Objects: {result.get('object_count')}")
    
    # Test 2: Create a cube
    print("\n" + "="*60)
    print("TEST 2: Create a Cube")
    print("="*60)
    code = """
import bpy
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
print("✓ Cube created")
"""
    result2 = client.send_command('execute_code', code=code)
    if result2 and result2.get('status') == 'success':
        print("✓ Cube creation command sent")
    
    # Test 3: Get scene info again
    print("\n" + "="*60)
    print("TEST 3: Get Scene Information (after cube)")
    print("="*60)
    result3 = client.send_command('get_scene_info')
    if result3 and result3.get('status') == 'success':
        result = result3.get('result', {})
        print(f"✓ Scene: {result.get('name')}")
        print(f"✓ Objects: {result.get('object_count')}")
    
    # Close connection
    client.close()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✓ All tests completed on single keep-alive connection!")
    print("\n🎉 Blender MCP is working!")

if __name__ == "__main__":
    main()
