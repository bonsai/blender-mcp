# Hello Cube Demo - Blender MCP End-to-End Test

This demo shows the complete flow:
```
Ollama (LLM) → MCP Server → Blender MCP Addon → bpy (Blender Python API)
```

## Prerequisites

✓ Ollama running with gpt-oss model
✓ MCP Server running (uvx blender-mcp)
✓ Blender 5.0 with BlenderMCP addon installed and enabled

## Step 1: Start Everything

### Terminal 1 - Start Ollama + MCP Server
```powershell
.\start.ps1 -Model "gpt-oss" -NoPull -StartUv
```

Wait for output:
```
[✓] Ollama started (PID: XXXX)
[✓] MCP server started (PID: YYYY)
```

### Terminal 2 - Open Blender
```powershell
blender
```

## Step 2: Enable the Addon in Blender

1. **Edit** → **Preferences** → **Add-ons**
2. Search for "BlenderMCP"
3. Check the box to enable it
4. You should see the panel on the right sidebar (press `N` if hidden)

## Step 3: Start the Blender MCP Server

In Blender:
1. Look for the **BlenderMCP** panel on the right
2. Click **"Connect to MCP server"** button
3. You should see in the console: `[INFO] BlenderMCP server started on localhost:9876`

## Step 4: Run the Test Client

### Terminal 3 - Run the test
```powershell
python test_mcp_client.py
```

This will:
1. ✓ Get scene information
2. ✓ Create a cube in Blender
3. ✓ Get scene info again (showing the cube)
4. ✓ Take a viewport screenshot

## Expected Output

```
============================================================
BLENDER MCP CLIENT TEST
============================================================

============================================================
TEST: Get Scene Information
============================================================
[CLIENT] Sending: {"type": "get_scene_info", "params": {}}
[CLIENT] Response: {
  "status": "success",
  "result": {
    "name": "Scene",
    "object_count": 1,
    "objects": [...],
    "materials_count": 0
  }
}
✓ Scene: Scene
✓ Objects: 1
✓ Materials: 0

============================================================
TEST: Create a Cube
============================================================
[CLIENT] Sending: {"type": "execute_code", "params": {"code": "..."}}
[CLIENT] Response: {
  "status": "success",
  "result": "✓ Cube created: TestCube\n"
}
✓ SUCCESS: Cube created in Blender!

...

🎉 All tests passed! Blender MCP is working!
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Your Computer                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐                                       │
│  │   Ollama     │  (LLM Model)                          │
│  │  gpt-oss     │  Port: 11434                          │
│  └──────┬───────┘                                       │
│         │                                               │
│  ┌──────▼───────────────────────────────────────────┐  │
│  │         MCP Server (uvx blender-mcp)             │  │
│  │  - Exposes Blender tools to LLM                  │  │
│  │  - Listens on stdio                              │  │
│  └──────┬───────────────────────────────────────────┘  │
│         │                                               │
│  ┌──────▼───────────────────────────────────────────┐  │
│  │    Blender MCP Server (addon.py)                 │  │
│  │  - Receives commands on port 9876                │  │
│  │  - Executes bpy commands                         │  │
│  │  - Returns results                               │  │
│  └──────┬───────────────────────────────────────────┘  │
│         │                                               │
│  ┌──────▼───────────────────────────────────────────┐  │
│  │         Blender (bpy)                            │  │
│  │  - 3D Viewport                                   │  │
│  │  - Scene Objects                                 │  │
│  │  - Rendering                                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## What's Happening

1. **Ollama** runs the LLM model (gpt-oss)
2. **MCP Server** (uvx blender-mcp) connects to Ollama and exposes Blender tools
3. **Blender MCP Addon** (addon.py) runs a socket server inside Blender
4. **Test Client** (test_mcp_client.py) sends commands to the Blender server
5. **Blender** executes the commands and returns results

## Key Insight

The addon is **NOT** a client that connects to MCP. It's a **server** that:
- Listens for commands on port 9876
- Executes them in Blender
- Returns results

The MCP Server (uvx blender-mcp) is what connects to Ollama and exposes Blender as a tool.

## Troubleshooting

### "Failed to connect to Blender MCP server"
- Is Blender running?
- Is the addon enabled?
- Did you click "Connect to MCP server" button?
- Check Blender console for errors

### "Cube not created"
- Check Blender console for Python errors
- Make sure Blender is in Object Mode
- Try a simpler command first

### "Screenshot failed"
- Make sure 3D viewport is visible
- Check file permissions on temp directory

## Next Steps

1. **Modify test_mcp_client.py** to send different commands
2. **Use the MCP Server** to send natural language prompts
3. **Build a UI** in Blender to interact with the MCP server
4. **Integrate with Claude** or other LLM clients

## Commands You Can Send

See `addon.py` for available commands:
- `get_scene_info` - Get scene information
- `get_object_info` - Get object details
- `execute_code` - Execute arbitrary Python code
- `get_viewport_screenshot` - Take a screenshot
- `get_polyhaven_categories` - Get asset categories
- `search_polyhaven_assets` - Search for assets
- And many more...

Enjoy! 🚀
