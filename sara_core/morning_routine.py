"""
CORE — Morning routine: news feeds, gig intake (e.g. Fiverr), similarity clustering,
and batched AI guidance so users refine many leads at once instead of one-by-one.

Data: ~/sara_nbs/morning_routine/{config.json,gigs.json,sessions.json}
"""

from __future__ import annotations

import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sara_core.network import extract_text, http_get

_BASE = os.path.join(os.path.expanduser("~"), "sara_nbs", "morning_routine")


def _path(name: str) -> str:
    os.makedirs(_BASE, exist_ok=True)
    return os.path.join(_BASE, name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(name: str, default: Any) -> Any:
    p = _path(name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(name: str, data: Any) -> None:
    p = _path(name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "feeds": [
        {"id": "example-tech", "title": "Hacker News", "url": "https://news.ycombinator.com/rss", "enabled": False},
    ],
    "news_search_queries": [],
    "fiverr_keywords": [],
    "fiverr_exclude": [],
    "gig_split_delimiter": "---",
    "notes": "Enable feeds you trust; add Fiverr-related keywords for filtering.",
}


def get_config() -> Dict[str, Any]:
    cfg = _load_json("config.json", {})
    if not cfg:
        cfg = dict(DEFAULT_CONFIG)
        _save_json("config.json", cfg)
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
    return {"success": True, "config": cfg}


def set_config(partial: Optional[Dict[str, Any]] = None, replace: bool = False) -> Dict[str, Any]:
    if replace and partial:
        cfg = dict(partial)
    else:
        cur = get_config()["config"]
        cfg = dict(cur)
        if partial:
            for k, v in partial.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    merged = dict(cfg[k])
                    merged.update(v)
                    cfg[k] = merged
                else:
                    cfg[k] = v
    cfg["updated"] = _now()
    _save_json("config.json", cfg)
    return {"success": True, "config": cfg}


def _tokenize(text: str) -> Set[str]:
    return {t for t in re.findall(r"[a-z0-9#+]{3,}", text.lower()) if len(t) <= 40}


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _localname(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_rss_atom(data: bytes, url: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return items

    def text_el(el: Optional[ET.Element]) -> str:
        if el is None or el.text is None:
            return ""
        return (el.text or "").strip()

    # Collect all <item> (RSS 2.0, namespaced) and <entry> (Atom)
    for node in root.iter():
        ln = _localname(node.tag)
        if ln != "item" and ln != "entry":
            continue
        title = link = desc = pub = ""
        for ch in node:
            t = _localname(ch.tag).lower()
            if t == "title":
                title = text_el(ch)
            elif t == "link":
                link = ch.attrib.get("href", "") or text_el(ch)
            elif t in ("description", "summary", "content"):
                piece = text_el(ch)
                if len(piece) > len(desc):
                    desc = piece
            elif t in ("pubdate", "published", "updated", "dc:date"):
                pub = text_el(ch)
        if not title and not desc:
            continue
        body = re.sub(r"<[^>]+>", " ", desc)
        items.append({"title": title or "(no title)", "link": link, "summary": body[:2000], "published": pub})
    return items


def fetch_feed(url: str, timeout: int = 20) -> Dict[str, Any]:
    try:
        data, ctype = http_get(url)
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}
    parsed = _parse_rss_atom(data, url)
    if parsed:
        return {"success": True, "url": url, "format": "rss_or_atom", "items": parsed[:50]}
    text, meta = extract_text(data, url, ctype)
    return {
        "success": True,
        "url": url,
        "format": "html_text",
        "items": [{"title": meta.get("domain", url), "link": url, "summary": text[:8000], "published": ""}],
    }


def fetch_all_feeds() -> Dict[str, Any]:
    cfg = get_config()["config"]
    results = []
    for feed in cfg.get("feeds", []):
        if not feed.get("enabled", False):
            continue
        u = str(feed.get("url", "")).strip()
        if not u:
            continue
        r = fetch_feed(u)
        r["feed_id"] = feed.get("id", "")
        r["feed_title"] = feed.get("title", "")
        results.append(r)
    return {"success": True, "fetched_at": _now(), "results": results}


def _load_gigs() -> List[Dict[str, Any]]:
    return list(_load_json("gigs.json", []))


def _save_gigs(gigs: List[Dict[str, Any]]) -> None:
    _save_json("gigs.json", gigs)


def add_gigs_from_text(raw: str, delimiter: Optional[str] = None) -> Dict[str, Any]:
    cfg = get_config()["config"]
    delim = delimiter or cfg.get("gig_split_delimiter") or "---"
    parts = [p.strip() for p in raw.split(delim) if p.strip()]
    if len(parts) == 1 and delim != "\n\n":
        parts = [p.strip() for p in re.split(r"\n{3,}", raw) if p.strip()]
    if len(parts) == 1:
        parts = [p.strip() for p in raw.split("\n---\n") if p.strip()]

    gigs = _load_gigs()
    keywords = [k.lower() for k in cfg.get("fiverr_keywords", []) if str(k).strip()]
    exclude = [k.lower() for k in cfg.get("fiverr_exclude", []) if str(k).strip()]

    added = 0
    for block in parts:
        low = block.lower()
        if keywords and not any(k in low for k in keywords):
            continue
        if exclude and any(k in low for k in exclude):
            continue
        gid = f"GIG-{uuid.uuid4().hex[:8].upper()}"
        title_line = block.split("\n", 1)[0].strip()[:200]
        gigs.append(
            {
                "gig_id": gid,
                "title": title_line,
                "body": block,
                "source": "paste",
                "created": _now(),
                "cluster_id": None,
            }
        )
        added += 1
    _save_gigs(gigs)
    return {"success": True, "added": added, "total_gigs": len(gigs)}


def add_gigs_from_list(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    gigs = _load_gigs()
    for it in items:
        gid = str(it.get("gig_id") or f"GIG-{uuid.uuid4().hex[:8].upper()}")
        gigs.append(
            {
                "gig_id": gid,
                "title": str(it.get("title", ""))[:200],
                "body": str(it.get("body", it.get("description", ""))),
                "url": str(it.get("url", "")),
                "budget": it.get("budget"),
                "source": str(it.get("source", "import")),
                "created": _now(),
                "cluster_id": None,
            }
        )
    _save_gigs(gigs)
    return {"success": True, "added": len(items), "total_gigs": len(gigs)}


def list_gigs() -> Dict[str, Any]:
    gigs = _load_gigs()
    return {"success": True, "count": len(gigs), "gigs": gigs}


def clear_gigs() -> Dict[str, Any]:
    _save_gigs([])
    return {"success": True, "cleared": True}


def cluster_gigs(threshold: float = 0.12, max_clusters: int = 40) -> Dict[str, Any]:
    gigs = _load_gigs()
    tokens = [_tokenize(g["title"] + " " + g.get("body", "")) for g in gigs]
    n = len(gigs)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(tokens[i], tokens[j]) >= threshold:
                union(i, j)

    roots: Dict[int, List[int]] = {}
    for i in range(n):
        r = find(i)
        roots.setdefault(r, []).append(i)

    clusters: List[Dict[str, Any]] = []
    cid = 0
    for members in sorted(roots.values(), key=len, reverse=True):
        if len(members) < 2:
            continue
        cid += 1
        if cid > max_clusters:
            break
        cname = f"CLU-{cid:02d}"
        for idx in members:
            gigs[idx]["cluster_id"] = cname
        sample_titles = [gigs[i]["title"] for i in members[:5]]
        clusters.append({"cluster_id": cname, "size": len(members), "sample_titles": sample_titles})

    for i, g in enumerate(gigs):
        if g.get("cluster_id") is None:
            g["cluster_id"] = f"SOLO-{i+1:04d}"

    _save_gigs(gigs)
    return {"success": True, "threshold": threshold, "clusters": clusters, "gigs": gigs}


def filter_gigs_by_keywords() -> Dict[str, Any]:
    cfg = get_config()["config"]
    keywords = [k.lower() for k in cfg.get("fiverr_keywords", []) if str(k).strip()]
    exclude = [k.lower() for k in cfg.get("fiverr_exclude", []) if str(k).strip()]
    gigs = _load_gigs()
    kept = []
    for g in gigs:
        blob = (g.get("title", "") + " " + g.get("body", "")).lower()
        if exclude and any(x in blob for x in exclude):
            g["filter_pass"] = False
        elif keywords and not any(k in blob for k in keywords):
            g["filter_pass"] = False
        else:
            g["filter_pass"] = True
            kept.append(g)
    _save_gigs(gigs)
    return {"success": True, "matched": len(kept), "total": len(gigs)}


def append_session_entry(entry: Dict[str, Any]) -> None:
    sess = list(_load_json("sessions.json", []))
    entry["at"] = _now()
    sess.append(entry)
    _save_json("sessions.json", sess[-500:])


def run_news_searches(num_results: int = 5) -> Dict[str, Any]:
    """Run DuckDuckGo-style searches from config `news_search_queries`."""
    try:
        from sara_core.google_services import web_search
    except Exception as e:
        return {"success": False, "error": str(e)}
    cfg = get_config()["config"]
    out: List[Dict[str, Any]] = []
    for q in cfg.get("news_search_queries", []):
        s = str(q).strip()
        if not s:
            continue
        out.append(web_search(query=s, num_results=int(num_results)))
    return {"success": True, "searched_at": _now(), "results": out}


def ai_batch_analyze(
    user_guidance: str,
    batch_size: int = 15,
    cluster_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Batched AI: each batch includes user guidance + a compact list of gigs.
    Later batches can build on prior output if caller passes prior_summary in guidance.
    """
    try:
        from sara_sdk.ai_backend_sdk import ai_backend
    except Exception as e:
        return {"success": False, "error": f"AI backend unavailable: {e}"}

    gigs = _load_gigs()
    if cluster_id:
        gigs = [g for g in gigs if g.get("cluster_id") == cluster_id]
    if not gigs:
        return {"success": False, "error": "No gigs to analyze (add gigs or adjust cluster filter)."}

    default_sys = (
        "You are SARA's morning-routine assistant. The user is scanning freelance leads (e.g. Fiverr). "
        "Group similarities, flag risks, estimate effort, and suggest a short next action per item. "
        "Be concise; use bullet clusters. Adapt tone to the user's guidance each batch."
    )
    sys_p = system_prompt or default_sys

    batches: List[Dict[str, Any]] = []
    prior_summary = ""

    for start in range(0, len(gigs), max(1, batch_size)):
        chunk = gigs[start : start + batch_size]
        lines = []
        for g in chunk:
            gid = g.get("gig_id", "")
            title = (g.get("title") or "")[:160]
            body = (g.get("body", "") or "")[:1200]
            lines.append(f"- [{gid}] {title}\n  {body.replace(chr(10), ' ')}")

        prompt = (
            f"USER GUIDANCE (follow closely):\n{user_guidance.strip()}\n\n"
            f"CONTEXT FROM PRIOR BATCHES (may be empty):\n{prior_summary[:2500]}\n\n"
            f"BATCH ({len(chunk)} listings):\n" + "\n".join(lines) + "\n\n"
            "Respond with: (1) Similarity groups inside this batch, (2) Top 3 cross-batch themes if any, "
            "(3) Suggested priority order, (4) One line 'next click' per gig id."
        )
        text = ai_backend.generate(prompt, {"system_prompt": sys_p, "max_tokens": 900, "temperature": 0.45})
        prior_summary = (prior_summary + "\n" + text)[-4000:]
        batches.append({"range": [start, start + len(chunk)], "gig_ids": [g.get("gig_id") for g in chunk], "analysis": text})
        append_session_entry({"type": "morning_routine_ai_batch", "batch": len(batches), "gig_ids": [g.get("gig_id") for g in chunk]})

    return {"success": True, "batches": len(batches), "results": batches, "backend": ai_backend.default_backend}
