"""
Blender script to manually start the MCP server
Run this in Blender's Scripting tab
"""

import bpy

# Get the addon's server class
if hasattr(bpy.types, 'blendermcp_server'):
    print("Server already exists")
    server = bpy.types.blendermcp_server
else:
    print("Creating new server...")
    # Import the addon module to get BlenderMCPServer
    import sys
    import os
    
    # Find addon path
    addon_path = os.path.join(
        bpy.utils.user_resource('SCRIPTS'),
        'addons',
        'blender_mcp'
    )
    
    if not os.path.exists(addon_path):
        # Try alternative path
        addon_path = os.path.join(
            bpy.utils.user_resource('EXTENSIONS'),
            'blender_org',
            'blender_mcp'
        )
    
    print(f"Addon path: {addon_path}")
    
    # Try to import from addon
    try:
        # Get the addon module
        import importlib.util
        addon_file = os.path.join(addon_path, 'addon.py')
        
        if os.path.exists(addon_file):
            spec = importlib.util.spec_from_file_location("blender_mcp_addon", addon_file)
            addon_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(addon_module)
            
            # Get BlenderMCPServer class
            BlenderMCPServer = addon_module.BlenderMCPServer
            
            # Create and start server
            port = bpy.context.scene.blendermcp_port
            server = BlenderMCPServer(port=port)
            bpy.types.blendermcp_server = server
            server.start()
            
            print(f"✓ Server started on localhost:{port}")
        else:
            print(f"✗ Addon file not found: {addon_file}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

# Mark as running
bpy.context.scene.blendermcp_server_running = True
print("✓ Server is now running")
