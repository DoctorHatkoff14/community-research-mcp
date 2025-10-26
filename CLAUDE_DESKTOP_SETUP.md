# Claude Desktop Setup Guide

## Method 1: Automatic (Recommended)

### Step 1: Run the Installer
Double-click `initialize.bat`

It will:
- Check for Python
- Install dependencies
- Prompt you to add API key
- Configure Claude Desktop automatically

### Step 2: Restart Claude Desktop
- Close Claude Desktop completely
- Start it again

### Step 3: Test
In Claude Desktop, say:
```
use get_server_context
```

You should see server info and available tools!

---

## Method 2: Manual Setup (If Auto Fails)

### Step 1: Install Dependencies
```bash
pip install mcp fastmcp httpx pydantic
```

### Step 2: Create .env File
Create a file named `.env` in this folder:
```
GEMINI_API_KEY=your_key_here
```

Get free key: https://makersuite.google.com/app/apikey

### Step 3: Get Full Path to Server

**Windows (CMD):**
```cmd
cd C:\path\to\community-research-mcp
echo %CD%\community_research_mcp.py
```

**Windows (PowerShell):**
```powershell
cd C:\path\to\community-research-mcp
(Get-Location).Path + "\community_research_mcp.py"
```

Copy the full path!

### Step 4: Edit Claude Desktop Config

**Config file location:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Usually: `C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json`

**If file exists:**
Add this section to the JSON:
```json
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\FULL\\PATH\\community_research_mcp.py"]
    }
  }
}
```

**If file doesn't exist:**
Create it with this content:
```json
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\FULL\\PATH\\community_research_mcp.py"]
    }
  }
}
```

Replace `C:\\FULL\\PATH\\` with your actual path from Step 3!

**Important:** Use double backslashes `\\` in the path!

Example:
```json
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\Users\\John\\Downloads\\community-research-mcp\\community_research_mcp.py"]
    }
  }
}
```

### Step 5: Restart Claude Desktop
Close and restart Claude Desktop completely.

---

## Verification

### Check 1: Config File is Correct

Open: `%APPDATA%\Claude\claude_desktop_config.json`

Should look like:
```json
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\full\\path\\to\\community_research_mcp.py"]
    }
  }
}
```

Common mistakes:
- ❌ Relative path → Must be FULL path
- ❌ Single backslash `\` → Must be double `\\`
- ❌ Missing .py extension
- ❌ Wrong Python command

### Check 2: API Key is Set

Open `.env` file in the server folder:
```
GEMINI_API_KEY=AIzaSy...
```

Should have your actual key, not empty!

### Check 3: Dependencies Installed

Run:
```bash
python -c "from mcp.server.fastmcp import FastMCP; print('OK')"
```

Should print "OK" without errors.

---

## Testing

In Claude Desktop, try these:

**Test 1: Check server is running**
```
use get_server_context
```

Expected: Returns workspace info, detected languages, and available tools.

**Test 2: Search community**
```
search for Python FastAPI background task solutions
```

Expected: Returns 3-5 recommendations with code, community scores, and evidence.

---

## Troubleshooting

### Problem: "Server not found" or no tools available

**Cause:** Config file not found or incorrect

**Fix:**
1. Check config file exists: `%APPDATA%\Claude\claude_desktop_config.json`
2. Verify path is FULL path (from C:\ on Windows)
3. Check double backslashes in path
4. Restart Claude Desktop

### Problem: "No module named 'mcp'"

**Cause:** Dependencies not installed

**Fix:**
```bash
pip install mcp fastmcp httpx pydantic
```

### Problem: "No API key configured"

**Cause:** Missing or empty `.env` file

**Fix:**
1. Create `.env` file in server folder
2. Add: `GEMINI_API_KEY=your_actual_key`
3. No spaces around `=`
4. Get key: https://makersuite.google.com/app/apikey

### Problem: Server starts but returns errors

**Cause:** API key invalid or rate limited

**Fix:**
1. Check API key is correct in `.env`
2. Verify key works at: https://makersuite.google.com/app/apikey
3. Wait if rate limited (1,500 free requests/day)

### Problem: "Python not found"

**Cause:** Python not in PATH or wrong Python used

**Fix Option 1:** Use full Python path in config:
```json
{
  "mcpServers": {
    "community-research": {
      "command": "C:\\Python311\\python.exe",
      "args": ["C:\\full\\path\\to\\community_research_mcp.py"]
    }
  }
}
```

**Fix Option 2:** Add Python to PATH, then restart Claude Desktop

---

## Advanced

### Using a Virtual Environment

If you use a Python venv:

```json
{
  "mcpServers": {
    "community-research": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\community_research_mcp.py"]
    }
  }
}
```

### Checking Logs

Claude Desktop logs MCP server output.

Windows logs location:
```
%APPDATA%\Claude\logs\
```

Look for errors about community-research server.

### Multiple API Keys

In `.env`:
```
GEMINI_API_KEY=primary_key
OPENAI_API_KEY=backup_key
```

Server will use first available key.

---

## Example Complete Setup

**1. Your server folder:**
```
C:\MCP\community-research-mcp\
├── community_research_mcp.py
├── .env                    <- API key here
├── requirements.txt
└── ...
```

**2. Your .env:**
```
GEMINI_API_KEY=AIzaSyC1234567890abcdefg
```

**3. Your config file:**
`C:\Users\YourName\AppData\Roaming\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\MCP\\community-research-mcp\\community_research_mcp.py"]
    }
  }
}
```

**4. Test in Claude Desktop:**
```
use get_server_context
```

Should show tools and workspace!

---

## Still Not Working?

1. ✅ Check config file path is correct
2. ✅ Verify full (absolute) path to .py file
3. ✅ Confirm double backslashes in Windows paths
4. ✅ Make sure .env has API key
5. ✅ Test: `python community_research_mcp.py` runs without errors
6. ✅ Restart Claude Desktop after changes
7. ✅ Check Claude Desktop logs for errors

If still stuck, check `README.md` for more details or verify each step above.
