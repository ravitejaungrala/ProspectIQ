import httpx
import re
from typing import Optional


async def scrape_website(url: str) -> dict:
    """Scrape website content and extract all useful metadata.
    Returns dict with content, demo_video_url, calendly_url, phone, emails, product_link, social_links.
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/plain"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(jina_url, headers=headers)
            response.raise_for_status()
            text = response.text[:15000]
        except httpx.HTTPError:
            text = await _direct_scrape(url, client)

        # Also fetch raw HTML to find video embeds, calendly, meta tags
        raw_html = ""
        try:
            html_resp = await client.get(url, follow_redirects=True, timeout=15.0)
            raw_html = html_resp.text
        except Exception:
            pass

    combined = raw_html + " " + text
    demo_video_url = _extract_video_url(raw_html, text)
    calendly_url = _extract_calendly_url(combined)
    demo_link = _extract_demo_link(raw_html, text)
    phone = _extract_phone(text)
    emails = _extract_emails(combined)
    social_links = _extract_social_links(combined)

    return {
        "content": text,
        "demo_video_url": demo_video_url or "",
        "calendly_url": calendly_url or "",
        "demo_booking_url": calendly_url or demo_link or "",
        "phone": phone or "",
        "emails": emails,
        "product_link": url,
        "social_links": social_links,
    }


def _extract_video_url(html: str, text: str) -> str:
    """Extract demo/product video URL from HTML and text content."""
    combined = html + " " + text
    # YouTube embeds
    yt_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
    ]
    for pat in yt_patterns:
        m = re.search(pat, combined)
        if m:
            return f"https://www.youtube.com/watch?v={m.group(1)}"

    # Vimeo
    vimeo = re.search(r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)', combined)
    if vimeo:
        return f"https://vimeo.com/{vimeo.group(1)}"

    # Loom
    loom = re.search(r'(https?://(?:www\.)?loom\.com/share/[a-zA-Z0-9]+)', combined)
    if loom:
        return loom.group(1)

    # Wistia
    wistia = re.search(r'(https?://[a-zA-Z0-9-]+\.wistia\.com/medias/[a-zA-Z0-9]+)', combined)
    if wistia:
        return wistia.group(1)

    # Generic video tag src
    video_src = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', html)
    if video_src:
        return video_src.group(1)

    # og:video meta
    og_video = re.search(r'<meta[^>]*property=["\']og:video["\'][^>]*content=["\']([^"\']+)["\']', html)
    if og_video:
        return og_video.group(1)

    return ""


def _extract_calendly_url(text: str) -> str:
    """Extract Calendly or similar scheduling links."""
    patterns = [
        r'(https?://calendly\.com/[a-zA-Z0-9_/-]+)',
        r'(https?://(?:app\.)?hubspot\.com/meetings/[a-zA-Z0-9_/-]+)',
        r'(https?://(?:www\.)?cal\.com/[a-zA-Z0-9_/-]+)',
        r'(https?://(?:www\.)?tidycal\.com/[a-zA-Z0-9_/-]+)',
        r'(https?://(?:www\.)?savvycal\.com/[a-zA-Z0-9_/-]+)',
        r'(https?://(?:www\.)?koalendar\.com/[a-zA-Z0-9_/-]+)',
        r'(https?://outlook\.office365\.com/owa/calendar/[a-zA-Z0-9_/@-]+)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).rstrip('/')
    return ""


def _extract_demo_link(html: str, text: str) -> str:
    """Extract demo request / book a demo / contact us link from HTML anchors."""
    # Video domains to exclude
    video_domains = ['youtube.com', 'youtu.be', 'vimeo.com', 'loom.com', 'wistia.com']

    def _is_video_url(url: str) -> bool:
        low = url.lower()
        return any(d in low for d in video_domains) or low.endswith(('.mp4', '.webm', '.mov'))

    # Look for <a> tags with booking/contact text
    demo_anchors = re.findall(
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*(?:book\s*(?:a\s*)?demo|request\s*(?:a\s*)?demo|schedule|live\s*demo|contact\s*us|get\s*started|free\s*trial|talk\s*to\s*(?:us|sales)|start\s*free)[^<]*)</a>',
        html, re.IGNORECASE
    )
    for href, _ in demo_anchors:
        if (href.startswith('http') or href.startswith('/')) and not _is_video_url(href):
            return href

    # Look for URLs with booking/contact keywords (exclude video URLs)
    demo_url = re.search(
        r'(https?://[^\s<>"]+(?:book-demo|request-demo|schedule|contact|get-started|free-trial|talk-to-sales|start-free|pricing)[^\s<>"]*)',
        text, re.IGNORECASE
    )
    if demo_url and not _is_video_url(demo_url.group(1)):
        return demo_url.group(1)

    return ""


def _extract_phone(text: str) -> str:
    """Extract phone number from text content."""
    phone_patterns = [
        r'[\+]?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'[\+]\d{1,3}[-.\s]?\d{4,14}',
    ]
    for pat in phone_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0).strip()
    return ""


def _extract_emails(text: str) -> list:
    """Extract contact email addresses from content."""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    # Deduplicate and filter out common non-contact emails
    seen = set()
    result = []
    skip = {'noreply', 'no-reply', 'donotreply', 'unsubscribe', 'mailer-daemon', 'postmaster'}
    for e in emails:
        low = e.lower()
        prefix = low.split('@')[0]
        if low not in seen and prefix not in skip:
            seen.add(low)
            result.append(low)
    return result[:5]  # Max 5


def _extract_social_links(text: str) -> dict:
    """Extract social media links."""
    social = {}
    patterns = {
        "linkedin": r'(https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_-]+)',
        "twitter": r'(https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+)',
        "facebook": r'(https?://(?:www\.)?facebook\.com/[a-zA-Z0-9._-]+)',
        "instagram": r'(https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._-]+)',
        "github": r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+)',
    }
    for name, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            social[name] = m.group(1)
    return social


async def _direct_scrape(url: str, client: httpx.AsyncClient) -> str:
    """Fallback scraper using direct HTTP + basic text extraction."""
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:15000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
