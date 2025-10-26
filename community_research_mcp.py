#!/usr/bin/env python3
"""
Community Research MCP Server

An MCP server that searches Stack Overflow, Reddit, GitHub issues, and forums
to find real solutions from real developers. No more AI hallucinations - find
what people actually use in production.

Features:
- Multi-source search (Stack Overflow, Reddit, GitHub, HackerNews)
- Query validation (rejects vague queries with helpful suggestions)
- LLM-powered synthesis using Gemini, OpenAI, or Anthropic
- Smart caching and retry logic
- Workspace context detection
"""

import os
import json
import asyncio
import hashlib
import time
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pathlib import Path
import re
from datetime import datetime, timedelta

import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use system environment variables only
    pass

# Initialize MCP server
mcp = FastMCP("community_research_mcp")

# Constants
CHARACTER_LIMIT = 25000
API_TIMEOUT = 30.0
MAX_RETRIES = 3
CACHE_TTL_SECONDS = 3600  # 1 hour
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_CALLS = 10

# Global state
_cache: Dict[str, Dict[str, Any]] = {}
_rate_limit_tracker: Dict[str, List[float]] = {}

# ============================================================================
# Response Format Enum
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ============================================================================
# Pydantic Models
# ============================================================================

class CommunitySearchInput(BaseModel):
    """Input model for community search."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    language: str = Field(
        ...,
        description="Programming language (e.g., 'Python', 'JavaScript', 'Rust')",
        min_length=2,
        max_length=50
    )
    topic: str = Field(
        ...,
        description=(
            "Specific, detailed topic. Be VERY specific - not just 'settings' or 'performance'. "
            "Examples: 'FastAPI background task queue with Redis', "
            "'React custom hooks for form validation', "
            "'Docker multi-stage builds to reduce image size'"
        ),
        min_length=10,
        max_length=500
    )
    goal: Optional[str] = Field(
        default=None,
        description="What you want to achieve (e.g., 'async task processing without blocking requests')",
        max_length=500
    )
    current_setup: Optional[str] = Field(
        default=None,
        description=(
            "Your current tech stack and setup. HIGHLY RECOMMENDED for implementation questions. "
            "Example: 'FastAPI app with SQLAlchemy, need queue for long-running jobs'"
        ),
        max_length=1000
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default, human-readable) or 'json' (machine-readable)"
    )

    @field_validator('topic')
    @classmethod
    def validate_topic_specificity(cls, v: str) -> str:
        """Ensure topic is specific enough to get useful results."""
        v = v.strip()
        
        # List of vague terms that indicate a non-specific query
        vague_terms = [
            'settings', 'configuration', 'config', 'setup', 'performance',
            'optimization', 'best practices', 'how to', 'tutorial',
            'getting started', 'basics', 'help', 'issue', 'problem',
            'error', 'debugging', 'install', 'installation'
        ]
        
        # Check if topic is just one or two vague words
        words = v.lower().split()
        if len(words) <= 2 and any(term in v.lower() for term in vague_terms):
            raise ValueError(
                f"Topic '{v}' is too vague. Be more specific! "
                f"Instead of 'settings', say 'GUI settings dialog with tabs and save/load buttons'. "
                f"Instead of 'performance', say 'reduce Docker image size with multi-stage builds'. "
                f"Include specific technologies, libraries, or patterns you're interested in."
            )
        
        return v


class DeepAnalyzeInput(BaseModel):
    """Input model for deep workspace analysis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    user_query: str = Field(
        ...,
        description="What you want to understand or improve about your codebase",
        min_length=10,
        max_length=1000
    )
    workspace_path: Optional[str] = Field(
        default=None,
        description="Path to workspace to analyze (defaults to current directory)"
    )
    target_language: Optional[str] = Field(
        default=None,
        description="Specific language to focus on (e.g., 'Python', 'JavaScript')"
    )


# ============================================================================
# Workspace Context Detection
# ============================================================================

def detect_workspace_context() -> Dict[str, Any]:
    """
    Detect programming languages and frameworks in the current workspace.
    
    Returns:
        Dictionary with workspace context including languages, frameworks, and structure
    """
    cwd = Path.cwd()
    
    languages = set()
    frameworks = set()
    config_files = []
    
    # Language detection patterns
    language_patterns = {
        'Python': ['.py'],
        'JavaScript': ['.js', '.jsx'],
        'TypeScript': ['.ts', '.tsx'],
        'Java': ['.java'],
        'C++': ['.cpp', '.cc', '.cxx'],
        'C#': ['.cs'],
        'Go': ['.go'],
        'Rust': ['.rs'],
        'Ruby': ['.rb'],
        'PHP': ['.php'],
        'Swift': ['.swift'],
        'Kotlin': ['.kt'],
    }
    
    # Framework detection patterns
    framework_files = {
        'Django': ['manage.py', 'settings.py'],
        'FastAPI': ['main.py'],  # Common convention
        'Flask': ['app.py'],
        'React': ['package.json'],
        'Vue': ['vue.config.js'],
        'Angular': ['angular.json'],
        'Next.js': ['next.config.js'],
        'Express': ['package.json'],
    }
    
    # Scan directory (limit to first 100 files to avoid performance issues)
    file_count = 0
    max_files = 100
    
    try:
        for root, dirs, files in os.walk(cwd):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}]
            
            for file in files:
                if file_count >= max_files:
                    break
                    
                file_path = Path(root) / file
                file_ext = file_path.suffix
                
                # Detect language
                for lang, extensions in language_patterns.items():
                    if file_ext in extensions:
                        languages.add(lang)
                
                # Detect frameworks
                for framework, marker_files in framework_files.items():
                    if file in marker_files:
                        frameworks.add(framework)
                
                # Track config files
                if file in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pom.xml']:
                    config_files.append(file)
                
                file_count += 1
            
            if file_count >= max_files:
                break
                
    except Exception as e:
        # If scan fails, just return minimal context
        pass
    
    return {
        "workspace": str(cwd),
        "languages": sorted(list(languages)),
        "frameworks": sorted(list(frameworks)),
        "config_files": config_files,
        "scan_limited": file_count >= max_files
    }


# ============================================================================
# Caching & Rate Limiting
# ============================================================================

def get_cache_key(tool_name: str, **params) -> str:
    """Generate cache key from tool name and parameters."""
    param_str = json.dumps(params, sort_keys=True)
    return hashlib.md5(f"{tool_name}:{param_str}".encode()).hexdigest()


def get_cached_result(cache_key: str) -> Optional[str]:
    """Retrieve cached result if not expired."""
    if cache_key in _cache:
        cached = _cache[cache_key]
        if time.time() - cached['timestamp'] < CACHE_TTL_SECONDS:
            return cached['result']
        else:
            del _cache[cache_key]
    return None


def set_cached_result(cache_key: str, result: str) -> None:
    """Store result in cache with timestamp."""
    _cache[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }


def check_rate_limit(tool_name: str) -> bool:
    """
    Check if tool call is within rate limit.
    Returns True if allowed, False if rate limited.
    """
    now = time.time()
    if tool_name not in _rate_limit_tracker:
        _rate_limit_tracker[tool_name] = []
    
    # Remove old timestamps outside the window
    _rate_limit_tracker[tool_name] = [
        ts for ts in _rate_limit_tracker[tool_name]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    
    # Check if under limit
    if len(_rate_limit_tracker[tool_name]) >= RATE_LIMIT_MAX_CALLS:
        return False
    
    # Add current timestamp
    _rate_limit_tracker[tool_name].append(now)
    return True


# ============================================================================
# API Key Management
# ============================================================================

def get_available_llm_provider() -> Optional[tuple[str, str]]:
    """
    Check which LLM API key is available.
    Returns tuple of (provider_name, api_key) or None.
    Priority: Gemini > OpenAI > Anthropic > OpenRouter > Perplexity
    """
    providers = [
        ('gemini', os.getenv('GEMINI_API_KEY')),
        ('openai', os.getenv('OPENAI_API_KEY')),
        ('anthropic', os.getenv('ANTHROPIC_API_KEY')),
        ('openrouter', os.getenv('OPENROUTER_API_KEY')),
        ('perplexity', os.getenv('PERPLEXITY_API_KEY')),
    ]
    
    for provider, key in providers:
        if key and key.strip():
            return (provider, key)
    
    return None


# ============================================================================
# Search Functions
# ============================================================================

async def search_stackoverflow(query: str, language: str) -> List[Dict[str, Any]]:
    """Search Stack Overflow using the Stack Exchange API."""
    try:
        url = "https://api.stackexchange.com/2.3/search/advanced"
        params = {
            'order': 'desc',
            'sort': 'relevance',
            'q': query,
            'tagged': language.lower(),
            'site': 'stackoverflow',
            'filter': 'withbody'
        }
        
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', [])[:5]:  # Top 5 results
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'score': item.get('score', 0),
                    'answer_count': item.get('answer_count', 0),
                    'snippet': item.get('body', '')[:500]
                })
            return results
    except Exception as e:
        return []


async def search_github(query: str, language: str) -> List[Dict[str, Any]]:
    """Search GitHub issues and discussions."""
    try:
        url = "https://api.github.com/search/issues"
        params = {
            'q': f"{query} language:{language} is:issue",
            'sort': 'reactions',
            'order': 'desc',
            'per_page': 5
        }
        
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('html_url', ''),
                    'state': item.get('state', ''),
                    'comments': item.get('comments', 0),
                    'snippet': (item.get('body', '') or '')[:500]
                })
            return results
    except Exception as e:
        return []


async def search_reddit(query: str, language: str) -> List[Dict[str, Any]]:
    """Search Reddit programming subreddits."""
    try:
        # Map languages to relevant subreddits
        subreddit_map = {
            'python': 'python+learnpython+pythontips',
            'javascript': 'javascript+learnjavascript+reactjs',
            'java': 'java+learnjava',
            'rust': 'rust',
            'go': 'golang',
            'cpp': 'cpp_questions+cpp',
            'csharp': 'csharp',
        }
        
        subreddit = subreddit_map.get(language.lower(), 'programming+learnprogramming')
        
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            'q': query,
            'sort': 'relevance',
            'limit': 5,
            'restrict_sr': 'on'
        }
        
        headers = {
            'User-Agent': 'CommunityResearchMCP/1.0'
        }
        
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('data', {}).get('children', []):
                post = item.get('data', {})
                results.append({
                    'title': post.get('title', ''),
                    'url': f"https://www.reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'comments': post.get('num_comments', 0),
                    'snippet': post.get('selftext', '')[:500]
                })
            return results
    except Exception as e:
        return []


async def search_hackernews(query: str) -> List[Dict[str, Any]]:
    """Search Hacker News for high-quality tech discussions."""
    try:
        url = "https://hn.algolia.com/api/v1/search"
        params = {
            'query': query,
            'tags': 'story',
            'numericFilters': 'points>100'  # High-quality posts only
        }
        
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('hits', [])[:3]:  # Top 3 results
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', f"https://news.ycombinator.com/item?id={item.get('objectID')}"),
                    'points': item.get('points', 0),
                    'comments': item.get('num_comments', 0),
                    'snippet': ''
                })
            return results
    except Exception as e:
        return []


async def aggregate_search_results(query: str, language: str) -> Dict[str, Any]:
    """Run all searches in parallel and aggregate results."""
    tasks = [
        search_stackoverflow(query, language),
        search_github(query, language),
        search_reddit(query, language),
        search_hackernews(query),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        'stackoverflow': results[0] if isinstance(results[0], list) else [],
        'github': results[1] if isinstance(results[1], list) else [],
        'reddit': results[2] if isinstance(results[2], list) else [],
        'hackernews': results[3] if isinstance(results[3], list) else [],
    }


# ============================================================================
# LLM Synthesis
# ============================================================================

async def synthesize_with_llm(
    search_results: Dict[str, Any],
    query: str,
    language: str,
    goal: Optional[str],
    current_setup: Optional[str]
) -> Dict[str, Any]:
    """
    Use LLM to synthesize search results into actionable recommendations.
    """
    provider_info = get_available_llm_provider()
    if not provider_info:
        return {
            'error': 'No LLM API key configured. Please set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file.',
            'findings': []
        }
    
    provider, api_key = provider_info
    
    # Build prompt
    prompt = f"""You are a technical research assistant analyzing community solutions.

Query: {query}
Language: {language}
"""
    
    if goal:
        prompt += f"Goal: {goal}\n"
    if current_setup:
        prompt += f"Current Setup: {current_setup}\n"
    
    prompt += f"""
Search Results:
{json.dumps(search_results, indent=2)}

Analyze these search results and extract 3-5 actionable recommendations. For each recommendation:

1. **Problem**: What specific problem does this solve (quote real users)
2. **Solution**: Step-by-step implementation with working code examples
3. **Benefit**: Measurable improvements (performance, simplicity, reliability)
4. **Evidence**: GitHub stars, Stack Overflow votes, community adoption
5. **Difficulty**: Easy/Medium/Hard
6. **Gotchas**: Edge cases and warnings from the community

Return ONLY valid JSON with this structure (no markdown, no backticks):
{{
  "findings": [
    {{
      "title": "Short descriptive title",
      "problem": "Problem description with user quotes",
      "solution": "Detailed solution with code",
      "benefit": "Measurable benefits",
      "evidence": "Community validation",
      "difficulty": "Easy|Medium|Hard",
      "community_score": 85,
      "gotchas": "Important warnings"
    }}
  ]
}}
"""
    
    try:
        # Call appropriate LLM
        if provider == 'gemini':
            return await call_gemini(api_key, prompt)
        elif provider == 'openai':
            return await call_openai(api_key, prompt)
        elif provider == 'anthropic':
            return await call_anthropic(api_key, prompt)
        elif provider == 'openrouter':
            return await call_openrouter(api_key, prompt)
        elif provider == 'perplexity':
            return await call_perplexity(api_key, prompt)
        else:
            return {'error': f'Unknown provider: {provider}', 'findings': []}
            
    except Exception as e:
        return {'error': f'LLM synthesis failed: {str(e)}', 'findings': []}


async def call_gemini(api_key: str, prompt: str) -> Dict[str, Any]:
    """Call Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 4096
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        text = data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up markdown code blocks if present
        text = text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
        
        return json.loads(text)


async def call_openai(api_key: str, prompt: str) -> Dict[str, Any]:
    """Call OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a technical research assistant. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        text = data['choices'][0]['message']['content']
        text = text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
        
        return json.loads(text)


async def call_anthropic(api_key: str, prompt: str) -> Dict[str, Any]:
    """Call Anthropic Claude API."""
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 4096,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        text = data['content'][0]['text']
        text = text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
        
        return json.loads(text)


async def call_openrouter(api_key: str, prompt: str) -> Dict[str, Any]:
    """Call OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        text = data['choices'][0]['message']['content']
        text = text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
        
        return json.loads(text)


async def call_perplexity(api_key: str, prompt: str) -> Dict[str, Any]:
    """Call Perplexity API."""
    url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        text = data['choices'][0]['message']['content']
        text = text.replace('```json\n', '').replace('\n```', '').replace('```', '').strip()
        
        return json.loads(text)


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="get_server_context",
    annotations={
        "title": "Get Community Research Server Context",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_server_context() -> str:
    """
    Get the Community Research MCP server context and capabilities.
    
    This tool returns information about what the server detected in your workspace,
    including programming languages, frameworks, and default context values. ALWAYS
    call this first before using other tools.
    
    Returns:
        str: JSON-formatted server context including:
            - handshake: Server identification and status
            - project_context: Detected workspace information
            - context_defaults: Default values for search
            - available_providers: Which LLM providers are configured
    
    Examples:
        - Use when: Starting any research task
        - Use when: Need to know what languages are detected
        - Use when: Want to see available LLM providers
    """
    workspace_context = detect_workspace_context()
    provider_info = get_available_llm_provider()
    
    context = {
        "handshake": {
            "server": "community-research-mcp",
            "version": "1.0.0",
            "status": "initialized",
            "description": "Searches Stack Overflow, Reddit, GitHub, forums for real solutions",
            "capabilities": {
                "multi_source_search": True,
                "query_validation": True,
                "llm_synthesis": True,
                "caching": True,
                "rate_limiting": True
            }
        },
        "project_context": workspace_context,
        "context_defaults": {
            "language": workspace_context["languages"][0] if workspace_context["languages"] else None
        },
        "available_providers": {
            "configured": provider_info[0] if provider_info else None,
            "supported": ["gemini", "openai", "anthropic", "openrouter", "perplexity"]
        }
    }
    
    return json.dumps(context, indent=2)


@mcp.tool(
    name="community_search",
    annotations={
        "title": "Search Community Resources",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def community_search(params: CommunitySearchInput) -> str:
    """
    Search Stack Overflow, Reddit, GitHub, and forums for real solutions.
    
    This tool searches multiple community sources in parallel, aggregates results,
    and uses an LLM to synthesize actionable recommendations with working code,
    measurable benefits, and community validation.
    
    Args:
        params (CommunitySearchInput): Validated search parameters containing:
            - language (str): Programming language (e.g., "Python", "JavaScript")
            - topic (str): Specific, detailed topic (NOT vague like "settings")
            - goal (Optional[str]): What you want to achieve
            - current_setup (Optional[str]): Your tech stack (highly recommended)
            - response_format (ResponseFormat): "markdown" (default) or "json"
    
    Returns:
        str: Formatted recommendations with:
            - Problem descriptions with real user quotes
            - Step-by-step solutions with working code
            - Benefits with measurable improvements
            - Evidence (GitHub stars, SO votes, blog mentions)
            - Difficulty ratings (Easy/Medium/Hard)
            - Community scores and adoption metrics
            - Gotchas and edge cases from real users
    
    Examples:
        GOOD queries:
        - language="Python", topic="FastAPI background task queue with Redis and Celery"
        - language="JavaScript", topic="React custom hooks for form validation with Yup"
        - language="Rust", topic="async/await patterns for HTTP clients with tokio"
        
        BAD queries (will be rejected):
        - language="Python", topic="settings"  # Too vague
        - language="JavaScript", topic="performance"  # Too vague
        - language="Go", topic="how to"  # Too vague
    
    Error Handling:
        - Validates query specificity (rejects vague queries with helpful suggestions)
        - Returns helpful error messages if no LLM provider configured
        - Caches results for 1 hour to reduce API calls
        - Rate limited to 10 requests per minute
        - Auto-retries failed searches up to 3 times
    """
    # Check rate limit
    if not check_rate_limit('community_search'):
        return json.dumps({
            'error': 'Rate limit exceeded. Maximum 10 requests per minute. Please wait and try again.'
        }, indent=2)
    
    # Check cache
    cache_key = get_cache_key(
        'community_search',
        language=params.language,
        topic=params.topic,
        goal=params.goal,
        current_setup=params.current_setup
    )
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return cached_result
    
    # Build search query
    search_query = f"{params.language} {params.topic}"
    if params.goal:
        search_query += f" {params.goal}"
    
    # Execute search with retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Search all sources in parallel
            search_results = await aggregate_search_results(search_query, params.language)
            
            # Check if we got any results
            total_results = sum(len(results) for results in search_results.values())
            if total_results == 0:
                result = json.dumps({
                    'error': f'No results found for "{params.topic}" in {params.language}. Try different search terms or a more common topic.',
                    'findings': []
                }, indent=2)
                set_cached_result(cache_key, result)
                return result
            
            # Synthesize with LLM
            synthesis = await synthesize_with_llm(
                search_results,
                params.topic,
                params.language,
                params.goal,
                params.current_setup
            )
            
            # Format response
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = [
                    f"# Community Research: {params.topic}",
                    f"**Language**: {params.language}",
                    ""
                ]
                
                if 'error' in synthesis:
                    lines.append(f"**Error**: {synthesis['error']}")
                    lines.append("")
                
                findings = synthesis.get('findings', [])
                if findings:
                    lines.append(f"## Found {len(findings)} Recommendations")
                    lines.append("")
                    
                    for i, finding in enumerate(findings, 1):
                        lines.extend([
                            f"### {i}. {finding.get('title', 'Recommendation')}",
                            f"**Difficulty**: {finding.get('difficulty', 'Unknown')} | **Community Score**: {finding.get('community_score', 'N/A')}/100",
                            "",
                            "**Problem**:",
                            finding.get('problem', 'No problem description'),
                            "",
                            "**Solution**:",
                            finding.get('solution', 'No solution provided'),
                            "",
                            "**Benefits**:",
                            finding.get('benefit', 'No benefits listed'),
                            "",
                            "**Evidence**:",
                            finding.get('evidence', 'No evidence provided'),
                            "",
                            "**Gotchas**:",
                            finding.get('gotchas', 'None noted'),
                            "",
                            "---",
                            ""
                        ])
                    
                    # Add source summary
                    lines.append("## Sources Searched")
                    lines.append(f"- Stack Overflow: {len(search_results['stackoverflow'])} results")
                    lines.append(f"- GitHub: {len(search_results['github'])} results")
                    lines.append(f"- Reddit: {len(search_results['reddit'])} results")
                    lines.append(f"- Hacker News: {len(search_results['hackernews'])} results")
                
                result = "\n".join(lines)
            else:
                # JSON format
                response = {
                    'language': params.language,
                    'topic': params.topic,
                    'total_sources': total_results,
                    'findings': synthesis.get('findings', []),
                    'error': synthesis.get('error'),
                    'sources_searched': {
                        'stackoverflow': len(search_results['stackoverflow']),
                        'github': len(search_results['github']),
                        'reddit': len(search_results['reddit']),
                        'hackernews': len(search_results['hackernews'])
                    }
                }
                result = json.dumps(response, indent=2)
            
            # Check character limit
            if len(result) > CHARACTER_LIMIT:
                # Truncate findings
                if params.response_format == ResponseFormat.JSON:
                    response_dict = json.loads(result)
                    original_count = len(response_dict.get('findings', []))
                    response_dict['findings'] = response_dict['findings'][:max(1, original_count // 2)]
                    response_dict['truncated'] = True
                    response_dict['truncation_message'] = f"Response truncated from {original_count} to {len(response_dict['findings'])} findings due to size limits."
                    result = json.dumps(response_dict, indent=2)
                else:
                    result = result[:CHARACTER_LIMIT] + "\n\n[Response truncated due to size limits. Use JSON format for full data.]"
            
            # Cache and return
            set_cached_result(cache_key, result)
            return result
            
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                error_response = json.dumps({
                    'error': f'Search failed after {MAX_RETRIES} attempts: {str(e)}',
                    'findings': []
                }, indent=2)
                return error_response
            
            # Wait before retry (exponential backoff)
            await asyncio.sleep(2 ** attempt)
    
    # Should never reach here, but just in case
    return json.dumps({'error': 'Unexpected error', 'findings': []}, indent=2)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
