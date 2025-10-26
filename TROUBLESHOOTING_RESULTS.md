# Troubleshooting: Poor Results & API Configuration

## Problem: Getting Limited or Poor Search Results

### Why This Happens

1. **Limited Free APIs**
   - Stack Overflow API: Limited to tagged questions
   - GitHub API: Only searches issues/discussions
   - Reddit API: Hit or miss for technical content
   - Hacker News API: Limited technical coverage

2. **Niche/New Topics**
   - Newer technologies have less community content
   - Niche topics have fewer discussions
   - Version-specific queries get fewer results

3. **No Google Search Access**
   - Free APIs don't include Google
   - Most comprehensive answers are in Google results

### Solution: Add Better Search APIs

The server **fully supports** additional search APIs. Add them to your `.env` file:

#### Option A: Add Serper (BEST FIX - Recommended)
**Gives you Google Search access!**

1. Go to: https://serper.dev/
2. Sign up (free account)
3. Get API key (2,500 free searches/month)
4. Add to `.env`:
   ```
   SERPER_API_KEY=your_key_here
   ```
5. Restart Claude Desktop

**Result:** Access to Google Search = dramatically better results!

#### Option B: Add Perplexity
**Has built-in web search and real-time data**

1. Go to: https://www.perplexity.ai/settings/api
2. Get API key (5 free requests/day, then paid)
3. Add to `.env`:
   ```
   PERPLEXITY_API_KEY=your_key_here
   ```

**Result:** Better web coverage, especially for recent topics

#### Option C: Add Brave Search
**Privacy-focused alternative to Google**

1. Go to: https://brave.com/search/api/
2. Get API key (2,000 free/month)
3. Add to `.env`:
   ```
   BRAVE_SEARCH_API_KEY=your_key_here
   ```

### Solution: Improve Search Queries

**Instead of very specific queries:**
```
search for React hooks useState with TypeScript generic types
```

**Try broader terms:**
```
search for React hooks TypeScript
```

**Or general concepts:**
```
search for React state management
```

**Why?** More content exists for general topics than hyper-specific ones.

---

## Problem: "Can't Add Other API Keys"

### The Options Aren't Missing!

The server **fully supports** these APIs:
- ✅ Gemini (LLM)
- ✅ OpenAI (LLM)
- ✅ Anthropic (LLM)
- ✅ OpenRouter (LLM - 100+ models)
- ✅ Perplexity (LLM + web search)
- ✅ Serper (Google Search)
- ✅ Brave Search

### How to Add API Keys

**Step 1: Open your `.env` file**

Location: Same folder as `community_research_mcp.py`

If it doesn't exist:
```bash
# Copy the example
copy .env.example .env
```

**Step 2: Add your keys**

Edit the `.env` file:
```bash
# LLM Providers (need at least one)
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
PERPLEXITY_API_KEY=pplx-...

# Search APIs (optional but highly recommended)
SERPER_API_KEY=...          # ⭐ BEST for improving results
BRAVE_SEARCH_API_KEY=...
```

**Step 3: Restart Claude Desktop**

Close completely and restart.

**Step 4: Verify**

In Claude Desktop:
```
use get_server_context
```

Should show your configured provider under `available_providers.configured`

### Why You Might Think Options Are Missing

The server uses **environment variables** (`.env` file) for configuration, not a UI panel.

This is by design for:
- **Security** - API keys not stored in visible config files
- **Flexibility** - Easy to change or update
- **Portability** - Works across different systems

---

## Improving Results: Step-by-Step

### Step 1: Check Current Setup

In Claude Desktop:
```
use get_server_context
```

Look at:
- `available_providers.configured` - Which LLM you're using
- No mention of SERPER/BRAVE - Using only free APIs

### Step 2: Add Serper API Key (Biggest Impact)

1. **Get key:** https://serper.dev/
2. **Add to `.env`:**
   ```
   SERPER_API_KEY=your_key_here
   ```
3. **Restart Claude Desktop**
4. **Test:**
   ```
   search for Python async best practices
   ```

You should see dramatically more results!

### Step 3: Try Better LLM Providers (Optional)

If you're using Gemini (free) and want better synthesis:

**OpenRouter** (Free $5 credit):
```
OPENROUTER_API_KEY=your_key
```

**Perplexity** (5 free/day + web search):
```
PERPLEXITY_API_KEY=your_key
```

### Step 4: Adjust Search Strategy

**For new/niche topics:**
- Use broader terms
- Search for general concepts
- Avoid version-specific queries

**For popular topics:**
- Can be more specific
- More community content available

---

## Verification Checklist

### ✅ Check 1: .env File Exists

Windows:
```cmd
dir C:\path\to\community-research-mcp\.env
```

Should show the file. If not, copy from `.env.example`

### ✅ Check 2: API Keys Are Set

Windows:
```cmd
type C:\path\to\community-research-mcp\.env
```

Should show your keys (not empty)

### ✅ Check 3: Server Recognizes Keys

In Claude Desktop:
```
use get_server_context
```

Check `available_providers.configured` field

### ✅ Check 4: Test Search Works

Try a popular topic:
```
search for JavaScript async await patterns
```

Should return multiple results. If yes, setup is correct!

---

## Free API Key Recommendations

### For Best Results (Recommended):

1. **SERPER_API_KEY** (2,500 free/month)
   - Get it: https://serper.dev/
   - Why: Google Search access = 10x better results
   - Cost: FREE

2. **GEMINI_API_KEY** (1,500 free/day)
   - Get it: https://makersuite.google.com/app/apikey
   - Why: Free LLM for synthesis
   - Cost: FREE

### For Even Better Results:

3. **PERPLEXITY_API_KEY** (5 free/day)
   - Get it: https://www.perplexity.ai/settings/api
   - Why: Built-in web search + LLM
   - Cost: 5 free/day, then paid

4. **OPENROUTER_API_KEY** ($5 free credit)
   - Get it: https://openrouter.ai/keys
   - Why: Access to 100+ models
   - Cost: $5 free credit

---

## Summary

**Problem:** Poor/limited search results

**Root Causes:**
- Using only free APIs (SO, GitHub, Reddit, HN)
- No Google Search access
- Niche or new topics have less content

**Best Solution:**
Add SERPER_API_KEY for Google Search (2,500 free/month)

**How to Add API Keys:**
1. Edit `.env` file in server folder
2. Add keys (see `.env.example` for all options)
3. Restart Claude Desktop
4. Use `get_server_context` to verify

**All Options ARE Available:**
Just add them to `.env` - no missing features!

---

## Still Having Issues?

1. ✅ Check `.env.example` for all available options
2. ✅ Make sure `.env` exists (not just .env.example)
3. ✅ Add at least one LLM key
4. ✅ Add SERPER_API_KEY for best results
5. ✅ Restart Claude Desktop after changes
6. ✅ Use broader search terms for niche topics
7. ✅ Verify with `get_server_context`

See **CLAUDE_DESKTOP_SETUP.md** for more troubleshooting help.
