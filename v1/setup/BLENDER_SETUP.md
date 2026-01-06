# Blender MCP Addon Setup Guide

## Step 1: Open Blender

1. Launch Blender on your system
2. Wait for it to fully load (you'll see the splash screen and main interface)
3. You should see the 3D viewport in the center

## Step 2: Install the Blender MCP Addon

1. You already have Preferences open - click on **Add-ons** in the left sidebar
2. Click the **Install...** button (top right of the Add-ons panel)
3. Navigate to your blender-mcp project folder: `C:\Users\dance\blender-mcp`
4. Select `addon.py` and click **Install Add-on**
5. Search for "BlenderMCP" or "blender-mcp" in the Add-ons search box
6. Check the checkbox next to it to **Enable** the addon
7. You should see a confirmation message

## Step 3: Configure the Addon Connection

1. After enabling the addon, look for the **BlenderMCP** panel in Blender
   - It may appear in the right sidebar (press `N` if you don't see it)
   - Or check under **Window** → **Toggle Sidebar**

2. In the BlenderMCP panel, you should see connection settings:
   - **Host**: Set to `localhost`
   - **Port**: Set to `9876`

3. Click **Connect** or **Start Server** button (exact name depends on addon version)

4. You should see a status message indicating:
   - ✓ Connected to MCP server
   - ✓ Ready to use Blender tools

## Step 4: Verify the Connection

1. Check the Blender system console for connection logs:
   - **Window** → **Toggle System Console** (on Windows)
   - Look for messages like "Connected to MCP server" or "Ready"

2. In your PowerShell terminal where the MCP server is running, you should see:
   - Connection logs from Blender
   - Tool availability messages

3. If you see errors, check:
   - Is the MCP server still running? (Check PowerShell window)
   - Is the host/port correct? (localhost:9876)
   - Is Blender's firewall access allowed?

## Troubleshooting

### Addon doesn't appear after install
- Restart Blender completely
- Check that `addon.py` is in the correct location
- Look for error messages in the system console

### Can't connect to MCP server
- Verify the server is running: `ollama ps` should show gpt-oss running
- Check the MCP server is still active in PowerShell
- Restart both the server and Blender
- Try: `c:\Users\dance\blender-mcp\start.ps1 -Model "gpt-oss" -NoPull -StartUv`

### Connection times out
- Make sure firewall isn't blocking port 9876
- Try connecting to `127.0.0.1` instead of `localhost`
- Check if another application is using port 9876

## Next Steps

Once connected, you can:
- Use Blender tools through the MCP interface
- Run AI-powered operations on your 3D models
- Access the full Blender API through the MCP server
