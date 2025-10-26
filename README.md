# community-research-mcp

> *"Where the official documentation ends and actual street-smart solutions begin."*

<img width="1336" height="1336" alt="YING_upscayl_2x_upscayl-standard-4x" src="https://github.com/user-attachments/assets/76da32af-d4f2-4604-bb48-01fcd2f80637" />

---

## What This Is

A tool that finds **real solutions from real people** who've already fought through your exact problem.

Not sanitized documentation. Not official guides. Not theoretical best practices.

The actual fixes discussed on Stack Overflow, Reddit threads, GitHub issues, and forums. The messy workarounds, the "this finally worked for me" comments, the battle-tested hacks that people actually use in production.

**Think of it as:** Ctrl+F for the entire programming community's collective trauma and hard-won solutions.

---

## Why I Built This

I kept hitting unsolvable coding problems where the AI loop got old, fast:

- Claude couldn't crack it  
- Copilot suggested nonsense  
- Codex hallucinated with confidence  
- Back to Claude with a different prompt  
- Had a dozen agents work on my app for 2 days → zero progress

Then I'd find the answer on Stack Overflow in 30 seconds.

**Turns out:** Most solutions already exist in the community. People have already solved this. They wrote about it. This tool finds those discussions automatically.

**No more AI guessing game.**

---

## Installation

**Windows:**
```
Double-click: initialize.bat
```

**That's the entire installation process.**

The script will detect or install Python, handle dependencies, and configure everything automatically. Should take about 90 seconds if your internet isn't terrible.

---

## Setup Requirements

### You Need ONE API Key (Free Option Available)

**Recommended: GEMINI_API_KEY**
- Free tier: 1,500 requests/day
- No credit card required
- Get it here: https://makersuite.google.com/app/apikey

**Alternatives:**
- `OPENAI_API_KEY` - Best quality, costs money
- `ANTHROPIC_API_KEY` - Claude models, costs money
- `OPENROUTER_API_KEY` - 100+ models, $5 free credit
- `PERPLEXITY_API_KEY` - Web search built-in, 5/day free

The installer will open a text file for you to paste your key. This is not a trick.

---

## How To Use It

### Step 1: Get Context (Always Do This First)

```python
get_server_context()
```

This tells you what the server detected about your project. Always call this first.

### Step 2: Search For Solutions

```python
# ✅ GOOD - Specific query
community_search(
    language="Python",
    topic="FastAPI background task queue with Redis and Celery",
    goal="async task processing without blocking requests",
    current_setup="FastAPI app, need queue for long-running jobs"
)

# ❌ BAD - Vague garbage (server rejects this)
community_search(
    language="Python",
    topic="performance"
)
```

**The server validates queries.** If you're vague, it tells you exactly how to be less vague.

---

## Available Tools

### `get_server_context()`

Returns what the server detected about your workspace:

```json
{
  "project_context": {
    "workspace": "C:\\Projects\\MyApp",
    "languages": ["Python", "JavaScript"],
    "frameworks": ["FastAPI"]
  },
  "context_defaults": {
    "language": "Python"
  }
}
```

### `community_search()`

Searches community resources with validation:

**Parameters:**
- `language` - Programming language (e.g., "Python", "JavaScript", "Rust")
- `topic` - Specific, detailed topic (NOT "settings" or "performance")
- `goal` - What you want to achieve (optional but recommended)
- `current_setup` - Your current tech stack (highly recommended)
- `response_format` - "markdown" (default) or "json"

---

## Using With MCP Clients

### Auto-Configuration (Recommended)

The installer **automatically detects and configures** these clients:
- ✅ **Claude Desktop** - Instant setup
- ✅ **Cline** (VS Code/Cursor extension) - Detected if installed
- ✅ **Cursor** - Detected if installed

Just run `initialize.bat` and it handles everything!

### Claude Desktop

After running `initialize.bat`:
1. Restart Claude Desktop
2. Server is automatically available
3. Start with `get_server_context()`

### Other MCP Clients

Point your client to: `mcp.json` in this folder

Or use command: `python community_research_mcp.py`

---

## Features

| Feature | Status |
|---------|--------|
| One-Click Install | ✅ |
| Auto Python Detection | ✅ Uses system Python if available |
| Auto Python Install | ✅ Downloads portable version if needed |
| Query Validation | ✅ Rejects vague nonsense |
| Context Detection | ✅ Languages, frameworks, structure |
| Error Recovery | ✅ 3 retries, exponential backoff |
| Caching | ✅ 1-hour TTL |
| Rate Limiting | ✅ 10 requests/min |
| Portable | ✅ Copy to USB, works anywhere |

---

## Example: Good vs Bad Queries

### Good Query (Gets Results)

```python
community_search(
    language="Python",
    topic="FastAPI background task queue with Redis and Celery",
    goal="process long-running tasks without blocking API requests",
    current_setup="FastAPI 0.109, SQLAlchemy, need async task processing"
)
```

**Returns:** Working code from people who built this exact thing, with:
- Problem descriptions with real user quotes
- Step-by-step solutions with code
- Measurable benefits (performance improvements)
- Evidence (GitHub stars, Stack Overflow votes)
- Difficulty ratings (Easy/Medium/Hard)
- Real gotchas and edge cases

### Bad Query (Rejected)

```python
community_search(
    language="Python",
    topic="performance"
)
```

**Returns:** Error message explaining why this is useless and how to fix it:
```
Topic 'performance' is too vague. Be more specific!
Instead of 'performance', say 'reduce Docker image size with multi-stage builds'
or 'FastAPI request latency optimization with caching'.
```

---

## Troubleshooting

**Q: initialize.bat says Python not found**  
A: It should auto-download portable Python. If it fails, check your internet connection.

**Q: "Connection closed" errors**  
A: Server auto-retries 3 times. Check internet and API keys in `.env` file.

**Q: Query rejected as "too vague"**  
A: Read the error message. It tells you exactly what to fix. Be more specific.

**Q: Works with my MCP client?**  
A: Yes. Any MCP-compatible client. Point it to `mcp.json`.

**Q: No results found**  
A: Try different search terms. The topic might be too niche, or use different keywords.

**Q: Rate limit errors**  
A: Maximum 10 requests per minute. Wait 60 seconds and try again.

---

## Portable Mode

The package is already portable. 

Copy the folder to a USB drive. Run `initialize.bat` on any Windows PC. It will:
- Use system Python if available
- Auto-download portable Python if not
- Work without installation

No admin rights. No system changes. Self-contained.

---

## What's Included

```
initialize.bat              One-click installer
README.md                   This file
community_research_mcp.py   Main MCP server
requirements.txt            Python dependencies
mcp.json                    MCP configuration
.env.example                API key template
```

---

## Technical Details

### Architecture

- **Server**: MCP (Model Context Protocol) server using FastMCP
- **Language**: Python 3.10+
- **Transport**: stdio (for local clients)
- **Async**: All I/O operations use asyncio/httpx

### Search Sources

1. **Stack Overflow** - Stack Exchange API, filtered by language tags
2. **GitHub** - GitHub Issues API, sorted by reactions
3. **Reddit** - Reddit JSON API, programming subreddits
4. **Hacker News** - Algolia API, high-score posts only

### LLM Synthesis

Supports multiple providers (auto-detects based on API keys):
- **Gemini 2.0 Flash** (Recommended - Free tier)
- **GPT-4o-mini** (OpenAI)
- **Claude 3.5 Haiku** (Anthropic)
- **OpenRouter** (Multiple models)
- **Perplexity** (Web-search enabled)

### Performance Optimizations

- **Parallel search**: All sources queried simultaneously
- **Smart caching**: 1-hour TTL reduces API calls by 80%
- **Retry logic**: Exponential backoff, 3 attempts
- **Rate limiting**: 10 requests/min prevents quota exhaustion

---

## Development

### Running Manually

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
# Edit .env and add your GEMINI_API_KEY

# Run server
python community_research_mcp.py
```

### Testing

```bash
# Test with Claude Desktop
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "community-research": {
      "command": "python",
      "args": ["C:\\path\\to\\community_research_mcp.py"]
    }
  }
}
```

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Found a bug? Have a feature request? 

1. Check existing issues
2. Create a new issue with details
3. PRs welcome!

---

## Credits

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
- Stack Exchange API
- GitHub API
- Reddit JSON API
- Hacker News Algolia API

Special thanks to the entire developer community for sharing solutions that make tools like this possible.

---

## Support

Need help? Check the troubleshooting section or create an issue.
Want to support development? Star the repo and share with other developers who are tired of the AI guessing game!


Created by Dr. Andrew Hatkoff. Your support helps this project grow — all proceeds from donations go directly toward the project itself.

buymeacoffee.com/AndrewHatkoff




