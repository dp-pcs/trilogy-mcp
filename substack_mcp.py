from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Optional, Any

import feedparser
import requests
from bs4 import BeautifulSoup

from mcp.server.fastmcp.server import FastMCP, Context

FEED_URL = "https://trilogyai.substack.com/feed"

# Simple in-memory cache for feed data
_CACHE: dict[str, Any] = {"posts": None, "fetched": None}


def fetch_posts(force: bool = False) -> list[dict]:
    """Fetch and parse Trilogy AI Substack feed."""
    now = datetime.utcnow()
    if (
        force
        or _CACHE["posts"] is None
        or _CACHE["fetched"] is None
        or (now - _CACHE["fetched"]) > timedelta(minutes=10)
    ):
        response = requests.get(FEED_URL)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        posts = []
        for entry in feed.entries:
            posts.append(
                {
                    "id": entry.get("id", entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published"),
                    "tags": [t["term"] for t in entry.get("tags", [])],
                }
            )
        _CACHE["posts"] = posts
        _CACHE["fetched"] = now
    return list(_CACHE["posts"])


def get_post_by_id(post_id: str) -> Optional[dict]:
    for post in fetch_posts():
        if post["id"] == post_id or post["link"].endswith(post_id):
            return post
    return None


def get_post_by_title(title: str) -> Optional[dict]:
    title_lower = title.lower()
    for post in fetch_posts():
        if post["title"].lower() == title_lower:
            return post
    return None


server = FastMCP(
    name="Trilogy Substack MCP",
    instructions="Access Trilogy AI Center of Excellence publications via tools and resources.",
)


@server.resource("trilogy://publications", description="All Trilogy AI Substack posts as JSON")
def trilogy_publications() -> list[dict]:
    return fetch_posts()


@server.resource("trilogy://stats", description="Statistical overview of Trilogy AI Substack")
def trilogy_stats() -> dict:
    posts = fetch_posts()
    authors = {}
    now = datetime.utcnow()
    recent_cutoff = now - timedelta(days=30)
    recent_posts = 0
    for post in posts:
        author = post["author"] or "Unknown"
        authors[author] = authors.get(author, 0) + 1
        pub_date = None
        if post.get("published"):
            try:
                pub_date = datetime(*post.published_parsed[:6])  # type: ignore[attr-defined]
            except Exception:
                pass
        if pub_date and pub_date >= recent_cutoff:
            recent_posts += 1
    return {
        "total_posts": len(posts),
        "recent_posts": recent_posts,
        "authors": authors,
    }


@server.tool()
def list_trilogy_posts(max_posts: int = 5, days: int = 30) -> list[dict]:
    """List recent Trilogy AI posts."""
    posts = fetch_posts()
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = []
    for post in posts:
        pub_date = None
        if post.get("published"):
            try:
                pub_date = datetime(*post.published_parsed[:6])  # type: ignore[attr-defined]
            except Exception:
                pass
        if pub_date and pub_date >= cutoff:
            filtered.append(post)
    return filtered[:max_posts]


@server.tool()
def read_trilogy_article(
    post_id: Optional[str] = None, post_title: Optional[str] = None
) -> str:
    """Return the plain text content of a Trilogy AI article."""
    post = None
    if post_id:
        post = get_post_by_id(post_id)
    if post is None and post_title:
        post = get_post_by_title(post_title)
    if post is None:
        raise ValueError("Article not found")
    res = requests.get(post["link"])
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    body = soup.find(class_=re.compile("body")) or soup.find("article")
    text = body.get_text(separator="\n") if body else soup.get_text()
    return text


@server.tool()
def search_trilogy_articles(query: str) -> list[dict]:
    """Search Trilogy AI articles by title or summary."""
    query_lower = query.lower()
    results = [
        p
        for p in fetch_posts()
        if query_lower in p["title"].lower() or query_lower in p.get("summary", "").lower()
    ]
    return results


@server.tool()
def analyze_trilogy_content(
    post_id: Optional[str] = None,
    post_title: Optional[str] = None,
) -> dict:
    """Return basic content statistics for an article."""
    text = read_trilogy_article(post_id=post_id, post_title=post_title)
    words = re.findall(r"\w+", text)
    sentences = re.split(r"[.!?]+", text)
    return {
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
    }


@server.prompt()
def analyze_trilogy_ai_trends() -> str:
    """Generate analysis of trends across Trilogy AI Center of Excellence publications."""
    return """Please analyze the trends in Trilogy AI Center of Excellence Substack publications.

First, use the trilogy://publications resource to get an overview of all posts, then:
1. **AI Research Focus**: Identify the main AI research themes and innovation areas
2. **Publishing Patterns**: Look for patterns in publishing frequency and content evolution
3. **Technical Depth**: Analyze the technical complexity and target audience
4. **Innovation Insights**: Identify cutting-edge AI topics and emerging trends
5. **Strategic Recommendations**: Provide insights for Trilogy AI's content strategy

Use the available tools to:
- Search for specific AI topics using search_trilogy_articles()
- Analyze key articles with analyze_trilogy_content()
- Get statistical overview from trilogy://stats resource

Format your analysis with clear headings and actionable insights for AI research and innovation."""


@server.prompt()
def trilogy_content_audit(focus_area: str = "AI innovation") -> str:
    """Perform a detailed content audit of Trilogy AI publications."""
    return f"""Conduct a comprehensive content audit of Trilogy AI Center of Excellence focusing on: {focus_area}

**Audit Process:**
1. **Content Inventory**: Use list_trilogy_posts() to get recent AI publications
2. **Quality Assessment**:
   - Analyze 3-5 representative articles using read_trilogy_article() and analyze_trilogy_content()
   - Check for consistency in AI research voice and technical depth
3. **Gap Analysis**:
   - Search for coverage of key AI topics using search_trilogy_articles()
   - Identify missing or underrepresented AI research areas
4. **Performance Analysis**:
   - Look at word counts, readability scores, and technical complexity
   - Compare different content approaches

**Deliverables:**
- Trilogy AI content inventory summary
- Quality assessment with specific examples from AI research
- Gap analysis with AI innovation recommendations
- Action plan for strengthening AI thought leadership

Focus your analysis on: {focus_area}
Use specific examples from Trilogy AI publications to support your findings."""


@server.prompt()
def trilogy_ai_competitive_analysis() -> str:
    """Analyze Trilogy AI content positioning in the AI research landscape."""
    return """Analyze Trilogy AI Center of Excellence content for competitive positioning in AI research:

**Analysis Framework:**
1. **AI Research Positioning**:
   - What unique AI research angles does Trilogy AI take?
   - How do we differentiate from standard AI industry content?

2. **AI Topic Coverage**:
   - Use search_trilogy_articles() to map coverage of key AI research areas
   - Identify Trilogy AI's content pillars and AI expertise areas

3. **Technical Content Quality**:
   - Analyze top-performing posts with analyze_trilogy_content()
   - Look for patterns in successful AI research communication

4. **AI Innovation Gaps & Opportunities**:
   - What AI research topics are we missing?
   - Where can Trilogy AI establish thought leadership?

**Methodology:**
- Review recent posts across different AI research topics
- Use both automated analysis and manual review
- Focus on unique AI insights and research perspectives

Provide specific recommendations for strengthening Trilogy AI's position in the AI research community."""


@server.prompt()
def debug_trilogy_mcp_server() -> str:
    """Guide for debugging and testing the Trilogy AI MCP server."""
    return """# Trilogy AI MCP Server Debugging Guide

Use this prompt to systematically test and debug the Trilogy AI Center of Excellence Substack MCP server.

## Testing with MCP Inspector

1. **Start the Inspector**:
   ```bash
   mcp dev substack_mcp.py
   ```

2. **Test Resources** (should load automatically):
   - Check if `trilogy://publications` loads the Trilogy AI publication list
   - Verify `trilogy://stats` shows Trilogy AI statistical overview
   - Look for any error messages in resource loading

3. **Test Tools** (try each one):
   - `list_trilogy_posts()` - Try with different parameters
   - `read_trilogy_article()` - Test with both post_id and post_title
   - `search_trilogy_articles()` - Search for AI-related terms
   - `analyze_trilogy_content()` - Try different analysis types

4. **Test Prompts**:
   - Try each Trilogy AI-focused prompt
   - Check if the prompt instructions are clear and actionable

## Common Issues to Check:

**Connection Issues:**
- Is https://trilogyai.substack.com/ accessible?
- Are network requests working?
- Check the feed URL: https://trilogyai.substack.com/feed

**Data Issues:**
- Are Trilogy AI posts being parsed correctly?
- Is content extraction working for different post formats?
- Are author attributions correct (Leonardo Gonzalez)?

**Tool Issues:**
- Do tools return proper error messages?
- Are parameter validations working?
- Is the Trilogy AI branding consistent?

## Debug Commands to Try:

1. Test basic functionality:
   - `list_trilogy_posts(max_posts=3)`

2. Test error handling:
   - `read_trilogy_article(post_id="nonexistent")`

3. Test AI-focused search:
   - `search_trilogy_articles("artificial intelligence")`

4. Test analysis:
   - Get a post ID from list_trilogy_posts, then use analyze_trilogy_content()

Report any issues specific to Trilogy AI content and suggested improvements!"""

if __name__ == "__main__":
    server.run(transport="sse")
