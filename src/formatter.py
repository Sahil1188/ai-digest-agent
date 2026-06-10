"""
HTML email formatter — builds morning (7 sections) and evening (4 sections) emails.
Inline CSS only: Gmail strips <style> blocks and ignores CSS classes entirely.
Every style attribute is written out in full to guarantee correct rendering.
"""
from datetime import datetime


# Sentiment badge colours — visible at a glance when scanning Community Pulse
SENTIMENT_COLORS: dict[str, str] = {
    "excited":   "#22c55e",   # green  — positive / enthusiastic tone
    "concerned": "#f97316",   # orange — cautionary / worried tone
    "skeptical": "#3b82f6",   # blue   — questioning / doubting tone
    "mixed":     "#a855f7",   # purple — ambivalent / nuanced tone
}

# ── Reusable style strings (inline only) ───────────────────────────────────
_FONT   = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;"
_WRAP   = f"max-width:680px;margin:0 auto;padding:24px;{_FONT}background:#f9fafb;"
_CARD   = "background:#fff;border-radius:8px;padding:20px;margin-bottom:16px;border:1px solid #e5e7eb;"
_H2     = "font-size:17px;font-weight:700;color:#111827;margin:0 0 12px 0;"
_ROW    = "border-bottom:1px solid #f3f4f6;padding:12px 0;"
_LINK   = "font-size:15px;font-weight:600;color:#1d4ed8;text-decoration:none;"
_META   = "font-size:12px;color:#6b7280;margin:4px 0 0;"
_BODY   = "font-size:14px;color:#374151;line-height:1.6;margin:6px 0 0;"
_TAG    = ("display:inline-block;background:#eff6ff;color:#1d4ed8;"
           "border-radius:4px;padding:3px 8px;font-size:12px;margin:3px 3px 0 0;")


# ── Low-level helpers ───────────────────────────────────────────────────────

def _card(title: str, body: str) -> str:
    """Wrap body HTML in a titled white card."""
    return f'<div style="{_CARD}"><h2 style="{_H2}">{title}</h2>{body}</div>'


def _empty(msg: str = "Nothing new today.") -> str:
    return f'<p style="font-size:14px;color:#6b7280;">{msg}</p>'


def _shell(content: str, label: str) -> str:
    """Outer email shell with header and footer."""
    date = datetime.utcnow().strftime("%B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>AI Digest — {label} — {date}</title>
</head>
<body style="margin:0;padding:0;background:#f9fafb;">
<div style="{_WRAP}">
  <div style="text-align:center;padding:16px 0 20px;">
    <h1 style="font-size:24px;font-weight:800;color:#111827;margin:0;">AI Digest</h1>
    <p style="color:#6b7280;font-size:14px;margin:4px 0 0;">{label} Edition &nbsp;·&nbsp; {date}</p>
  </div>
  {content}
  <p style="text-align:center;font-size:12px;color:#9ca3af;margin-top:24px;">
    Built with Python · Gemini 2.0 Flash · Runs free on GitHub Actions
  </p>
</div>
</body>
</html>"""


def _banner(text: str) -> str:
    """Blue summary banner rendered above the first card."""
    return (f'<div style="background:#1d4ed8;color:#fff;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:16px;">'
            f'<p style="margin:0;font-size:14px;line-height:1.6;">{text}</p></div>')


# ── Section renderers ───────────────────────────────────────────────────────

def _render_top_stories(stories: list[dict]) -> str:
    if not stories:
        return _card("Top Stories", _empty())
    rows = ""
    for s in stories:
        rows += (
            f'<div style="{_ROW}">'
            f'  <a href="{s.get("url","#")}" style="{_LINK}">{s.get("title","")}</a>'
            f'  <p style="{_META}">{s.get("source","")}</p>'
            + (f'  <p style="{_BODY}"><strong>What:</strong> {s["what_it_is"]}</p>' if s.get("what_it_is") else "")
            + (f'  <p style="{_BODY}"><strong>Why it matters:</strong> {s["why_it_matters"]}</p>' if s.get("why_it_matters") else "")
            + (f'  <p style="{_BODY}"><strong>What changed:</strong> {s["what_changed"]}</p>' if s.get("what_changed") else "")
            + "</div>"
        )
    return _card("Top Stories", rows)


def _render_new_models(models: list[dict]) -> str:
    if not models:
        return _card("New Models & Embeddings", _empty("No new model releases today."))
    rows = ""
    for m in models:
        badge = (f'<span style="background:#f0fdf4;color:#16a34a;border-radius:4px;'
                 f'padding:2px 7px;font-size:11px;margin-left:8px;">{m.get("type","")}</span>')
        rows += (
            f'<div style="{_ROW}">'
            f'  <a href="{m.get("url","#")}" style="{_LINK}">{m.get("name","")}</a>{badge}'
            + (f'  <p style="{_BODY}">{m["what_it_is"]}</p>' if m.get("what_it_is") else "")
            + (f'  <p style="{_BODY}"><strong>Improvement:</strong> {m["improvement_over_previous"]}</p>' if m.get("improvement_over_previous") else "")
            + "</div>"
        )
    return _card("New Models & Embeddings", rows)


def _render_tools(tools: list[dict]) -> str:
    if not tools:
        return _card("New Tools & Frameworks", _empty("No new tools today."))
    rows = ""
    for t in tools:
        badge = (f'<span style="background:#eff6ff;color:#1d4ed8;border-radius:4px;'
                 f'padding:2px 7px;font-size:11px;margin-left:8px;">{t.get("category","")}</span>')
        rows += (
            f'<div style="{_ROW}">'
            f'  <a href="{t.get("url","#")}" style="{_LINK}">{t.get("name","")}</a>{badge}'
            + (f'  <p style="{_BODY}">{t["what_it_does"]}</p>' if t.get("what_it_does") else "")
            + (f'  <p style="{_BODY}"><strong>Why better:</strong> {t["why_better_than_alternatives"]}</p>' if t.get("why_better_than_alternatives") else "")
            + "</div>"
        )
    return _card("New Tools & Frameworks", rows)


def _render_community(discussions: list[dict]) -> str:
    if not discussions:
        return _card("Community Pulse", _empty("No discussions today."))
    rows = ""
    for d in discussions:
        sentiment = d.get("sentiment", "mixed")
        color = SENTIMENT_COLORS.get(sentiment, SENTIMENT_COLORS["mixed"])
        badge = (f'<span style="background:{color};color:#fff;border-radius:12px;'
                 f'padding:2px 10px;font-size:11px;font-weight:600;margin-left:8px;">'
                 f'{sentiment}</span>')
        rows += (
            f'<div style="{_ROW}">'
            f'  <div>'
            f'    <a href="{d.get("url","#")}" style="{_LINK}">{d.get("topic","")}</a>{badge}'
            f'  </div>'
            f'  <p style="{_META}">{d.get("source","")}</p>'
            + (f'  <p style="{_BODY}">{d["key_points"]}</p>' if d.get("key_points") else "")
            + "</div>"
        )
    return _card("Community Pulse", rows)


def _render_papers(papers: list[dict]) -> str:
    if not papers:
        return _card("Research Papers", _empty("No new papers today."))
    rows = ""
    for p in papers:
        rows += (
            f'<div style="{_ROW}">'
            f'  <a href="{p.get("url","#")}" style="{_LINK}">{p.get("title","")}</a>'
            + (f'  <p style="{_BODY}">{p["plain_english"]}</p>' if p.get("plain_english") else "")
            + (f'  <p style="{_BODY}"><strong>Key contribution:</strong> {p["key_contribution"]}</p>' if p.get("key_contribution") else "")
            + "</div>"
        )
    return _card("Research Papers (Plain English)", rows)


def _render_techniques(techniques: list[dict]) -> str:
    if not techniques:
        return _card("Techniques & Approaches", _empty("No new techniques today."))
    rows = ""
    for t in techniques:
        rows += (
            f'<div style="{_ROW}">'
            f'  <a href="{t.get("url","#")}" style="{_LINK}">{t.get("name","")}</a>'
            + (f'  <p style="{_BODY}">{t["what_it_does"]}</p>' if t.get("what_it_does") else "")
            + (f'  <p style="{_BODY}"><strong>Improvement:</strong> {t["improvement_over_before"]}</p>' if t.get("improvement_over_before") else "")
            + "</div>"
        )
    return _card("Techniques & Approaches", rows)


def _render_topics(topics: list[str]) -> str:
    if not topics:
        return _card("Trending Topics", _empty("No trending topics today."))
    tags = "".join(f'<span style="{_TAG}">{t}</span>' for t in topics)
    return _card("Trending Topics", f'<div style="margin-top:4px;">{tags}</div>')


# ── Public API ──────────────────────────────────────────────────────────────

def format_morning(digest: dict) -> str:
    """
    Build the morning email: all 7 sections in the order defined in CLAUDE.md.
    Morning is the comprehensive edition — covers everything from the past 12 hours.
    """
    sections = ""
    if digest.get("digest_summary"):
        sections += _banner(digest["digest_summary"])

    sections += _render_top_stories(digest.get("top_stories", []))
    sections += _render_new_models(digest.get("new_models", []))
    sections += _render_tools(digest.get("new_tools_frameworks", []))
    sections += _render_community(digest.get("community_discussions", []))
    sections += _render_papers(digest.get("research_papers", []))
    sections += _render_techniques(digest.get("techniques_approaches", []))
    sections += _render_topics(digest.get("trending_topics", []))

    return _shell(sections, "Morning")


def format_evening(digest: dict) -> str:
    """
    Build the evening email: 4 focused sections.
    Evening is the catch-up edition — what changed since the morning digest.
    """
    sections = ""

    # Section 1 — New Since Morning (reuse top_stories, framed as updates)
    stories = digest.get("top_stories", [])
    if stories:
        rows = ""
        for s in stories[:5]:
            rows += (
                f'<div style="{_ROW}">'
                f'  <a href="{s.get("url","#")}" style="{_LINK}">{s.get("title","")}</a>'
                f'  <p style="{_META}">{s.get("source","")}</p>'
                + (f'  <p style="{_BODY}">{s["what_changed"]}</p>' if s.get("what_changed") else "")
                + "</div>"
            )
        sections += _card("New Since Morning", rows)
    else:
        sections += _card("New Since Morning", _empty("Nothing new since the morning digest."))

    # Section 2 — Community Pulse Evening Update
    sections += _render_community(digest.get("community_discussions", []))

    # Section 3 — Trending Today
    sections += _render_topics(digest.get("trending_topics", []))

    # Section 4 — What to Watch Tomorrow (forward-looking: techniques + papers)
    tomorrow = digest.get("techniques_approaches", []) + digest.get("research_papers", [])
    if tomorrow:
        rows = ""
        for item in tomorrow[:4]:
            title = item.get("name") or item.get("title", "")
            body  = item.get("improvement_over_before") or item.get("key_contribution") or item.get("plain_english", "")
            rows += (
                f'<div style="{_ROW}">'
                f'  <a href="{item.get("url","#")}" style="{_LINK}">{title}</a>'
                + (f'  <p style="{_BODY}">{body}</p>' if body else "")
                + "</div>"
            )
        sections += _card("What to Watch Tomorrow", rows)

    return _shell(sections, "Evening")
