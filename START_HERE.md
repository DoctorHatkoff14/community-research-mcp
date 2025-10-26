# START HERE - Claude Desktop Setup

## Quick Setup (2 Minutes)

### Step 1: Run the Installer
1. Double-click `initialize.bat`
2. Wait for dependencies to install
3. Add your API key when the .env file opens
4. Save and close

### Step 2: Restart Claude Desktop
- Close Claude Desktop completely
- Open it again

### Step 3: Test It!
In Claude Desktop, type:
```
use get_server_context
```

You should see available tools and workspace info!

Then try:
```
search for Python FastAPI background task solutions
```

---

## Get FREE API Key

You need a Gemini API key (FREE - 1,500 requests/day):

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Paste it in `.env` file after `GEMINI_API_KEY=`

No credit card required!

---

## Not Working?

### If initialize.bat didn't work:

See **CLAUDE_DESKTOP_SETUP.md** for manual setup instructions.

You need to:
1. Install dependencies: `pip install mcp fastmcp httpx pydantic`
2. Create `.env` with your API key
3. Edit `%APPDATA%\Claude\claude_desktop_config.json`
4. Add server configuration
5. Restart Claude Desktop

Full instructions in **CLAUDE_DESKTOP_SETUP.md**

---

## Common Issues

**"Server not found"**
- Check: `%APPDATA%\Claude\claude_desktop_config.json` exists
- Make sure path in config is FULL path (e.g., `C:\\Users\\...`)
- Use double backslashes `\\` in Windows paths

**"No module named 'mcp'"**
- Run: `pip install mcp fastmcp httpx pydantic`

**"No API key configured"**
- Check `.env` file has your key: `GEMINI_API_KEY=your_key`
- Make sure there's no space after the `=`

---

## Files in This Package

- **START_HERE.md** - This file
- **initialize.bat** - Auto-installer
- **CLAUDE_DESKTOP_SETUP.md** - Detailed setup & troubleshooting
- **community_research_mcp.py** - The MCP server
- **.env.example** - API key template
- **requirements.txt** - Python dependencies
- **README.md** - Full documentation

---

## What This Does

Searches Stack Overflow, Reddit, GitHub, and Hacker News for real solutions, then uses AI to synthesize findings into actionable recommendations with:

- Working code examples
- Measurable benefits
- Community validation (GitHub stars, SO votes)
- Difficulty ratings
- Gotchas and warnings

**No more AI guessing game!**
