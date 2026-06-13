#!/usr/bin/env python3
"""
Scrape Petri Kainulainen's blog (petrikainulainen.net) into per-post markdown-ish
text files, organized by category, for use as reference material in the
`javapaavi` Claude plugin.

Usage:
    python scrape_blog.py [--limit N] [--out DIR] [--only PATTERN]

The script:
  1. Pulls the WordPress/Yoast sitemap.
  2. Filters URLs to the topical categories we care about.
  3. Downloads each post with polite throttling.
  4. Extracts the post body, title, date, and tags.
  5. Writes one file per post under <out>/<category>/<slug>.md.
  6. Writes an index.json with metadata for downstream distillation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup

SITEMAP_INDEX = "https://www.petrikainulainen.net/sitemap_index.xml"
USER_AGENT = "javapaavi-scraper/1.0 (+https://github.com/local/claude-javapaavi)"
THROTTLE_SECONDS = 0.4
TIMEOUT = 20

# We keep these category prefixes (path[0]/path[1] from the URL). The rest
# (weekly roundups, etc.) are noisy link-dumps and add little signal for an
# opinionated coding agent.
KEEP_PREFIXES = {
    "programming/testing",
    "programming/spring-framework",
    "programming/unit-testing",
    "programming/tips-and-tricks",
    "programming/jooq",
    "programming/gradle",
    "programming/maven",
    "programming/solr",
    "software-development/processes",
    "software-development/design",
    "software-development/learning",
    "software-development/general",
    "software-development/technology-evaluation",
}


@dataclass
class Post:
    url: str
    slug: str
    category: str
    title: str = ""
    date: str = ""
    tags: list[str] = field(default_factory=list)
    body_markdown: str = ""
    word_count: int = 0


def fetch(url: str, session: requests.Session) -> str:
    r = session.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    return r.text


def list_post_urls(session: requests.Session) -> list[str]:
    index_xml = fetch(SITEMAP_INDEX, session)
    sub_sitemaps = re.findall(r"<loc>([^<]+)</loc>", index_xml)
    post_sitemap = next(s for s in sub_sitemaps if "post-sitemap" in s)
    posts_xml = fetch(post_sitemap, session)
    urls = re.findall(r"<loc>([^<]+)</loc>", posts_xml)
    return [u for u in urls if u.rstrip("/") != "https://www.petrikainulainen.net/blog"]


def url_category(url: str) -> str:
    parts = urllib.parse.urlparse(url).path.strip("/").split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0] if parts else "uncategorized"


def url_slug(url: str) -> str:
    parts = urllib.parse.urlparse(url).path.strip("/").split("/")
    return parts[-1] if parts else "post"


# ----- HTML -> Markdown-ish conversion -----------------------------------

INLINE_TAGS = {"em", "i", "strong", "b", "code", "a", "span"}


def _text(el) -> str:
    return el.get_text(" ", strip=True)


def html_to_markdown(node) -> str:
    """Walk a BeautifulSoup tree and emit a lightweight markdown rendering.

    We don't need perfect fidelity — we need readable, grep-able prose with
    code blocks intact so an LLM can use it as reference."""
    out: list[str] = []

    for child in node.children:
        name = getattr(child, "name", None)
        if name is None:
            text = str(child).strip()
            if text:
                out.append(text)
            continue
        if name in {"script", "style", "iframe", "noscript"}:
            continue
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            out.append(f"\n{'#' * level} {_text(child)}\n")
        elif name == "p":
            out.append("\n" + _render_inline(child) + "\n")
        elif name == "blockquote":
            inner = _render_inline(child).splitlines()
            out.append("\n" + "\n".join(f"> {l}" for l in inner if l) + "\n")
        elif name in {"ul", "ol"}:
            ordered = name == "ol"
            for idx, li in enumerate(child.find_all("li", recursive=False), 1):
                marker = f"{idx}." if ordered else "-"
                out.append(f"{marker} {_render_inline(li)}")
            out.append("")
        elif name == "pre":
            code = child.find("code")
            code_text = (code.get_text() if code else child.get_text()).rstrip()
            lang = ""
            if code and code.get("class"):
                for cls in code.get("class"):
                    if cls.startswith(("language-", "lang-")):
                        lang = cls.split("-", 1)[1]
                        break
                    if cls in {"java", "kotlin", "xml", "groovy", "bash", "sql"}:
                        lang = cls
                        break
            out.append(f"\n```{lang}\n{code_text}\n```\n")
        elif name == "figure":
            cap = child.find("figcaption")
            if cap:
                out.append(f"\n*Figure: {_text(cap)}*\n")
        elif name == "table":
            out.append("\n" + _render_table(child) + "\n")
        elif name in {"div", "section", "article", "aside"}:
            out.append(html_to_markdown(child))
        else:
            inline = _render_inline(child).strip()
            if inline:
                out.append(inline)

    return "\n".join(s for s in out if s is not None)


def _render_inline(el) -> str:
    pieces: list[str] = []
    for child in el.children:
        name = getattr(child, "name", None)
        if name is None:
            pieces.append(str(child))
            continue
        if name in {"strong", "b"}:
            pieces.append(f"**{_text(child)}**")
        elif name in {"em", "i"}:
            pieces.append(f"*{_text(child)}*")
        elif name == "code":
            pieces.append(f"`{_text(child)}`")
        elif name == "a":
            href = child.get("href", "")
            text = _text(child)
            pieces.append(f"[{text}]({href})" if href else text)
        elif name == "br":
            pieces.append("\n")
        elif name == "img":
            alt = child.get("alt", "image")
            pieces.append(f"![{alt}]")
        else:
            pieces.append(_render_inline(child))
    return re.sub(r"[ \t]+", " ", "".join(pieces)).strip()


def _render_table(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_text(c) for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(" | ".join(cells))
    if not rows:
        return ""
    sep = " | ".join("---" for _ in rows[0].split("|"))
    return rows[0] + "\n" + sep + "\n" + "\n".join(rows[1:])


# ----- Post extraction ----------------------------------------------------


def parse_post(url: str, html: str) -> Post:
    soup = BeautifulSoup(html, "lxml")
    post = Post(url=url, slug=url_slug(url), category=url_category(url))

    title_tag = soup.find("h1", class_=re.compile(r"entry-title|post-title|tve_p")) or soup.find("h1")
    if title_tag:
        post.title = _text(title_tag)

    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        post.date = time_tag["datetime"][:10]
    if not post.date:
        # Fallback: petrikainulainen.net renders the date as plain text inside
        # a `Published:\n<Month D, YYYY>` block in the post header.
        m = re.search(
            r"Published:\s*\n?\s*"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+(\d{1,2}),\s*(\d{4})",
            soup.get_text("\n"),
        )
        if m:
            months = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12,
            }
            try:
                from datetime import datetime as _dt
                post.date = _dt(int(m.group(3)), months[m.group(1)], int(m.group(2))).strftime("%Y-%m-%d")
            except ValueError:
                pass

    for tag_link in soup.select("a[rel~=tag], .tags-links a"):
        t = _text(tag_link)
        if t and t not in post.tags:
            post.tags.append(t)

    body = (
        soup.find("div", class_=re.compile(r"entry-content|post-content|tve-content-box-background"))
        or soup.find("article")
        or soup.find("main")
    )
    if body is None:
        return post

    for sel in [
        ".sharedaddy", ".jp-relatedposts", ".sd-sharing-enabled",
        ".wp-block-comments", ".comments-area", "#comments",
        ".tve-leads-conversion-object", ".thrv_wrapper.thrv-button",
        ".post-navigation", ".author-box", ".feedburner",
    ]:
        for el in body.select(sel):
            el.decompose()

    post.body_markdown = re.sub(r"\n{3,}", "\n\n", html_to_markdown(body)).strip()
    post.word_count = len(post.body_markdown.split())
    return post


# ----- Driver -------------------------------------------------------------


def scrape(out_dir: Path, limit: int | None, only: str | None) -> None:
    session = requests.Session()
    print("Fetching sitemap...", file=sys.stderr)
    all_urls = list_post_urls(session)
    print(f"  sitemap has {len(all_urls)} URLs", file=sys.stderr)

    targets = [u for u in all_urls if url_category(u) in KEEP_PREFIXES]
    if only:
        targets = [u for u in targets if only in u]
    if limit:
        targets = targets[:limit]
    print(f"  scraping {len(targets)} posts", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []

    def work(url: str) -> Post | None:
        try:
            html = fetch(url, session)
            time.sleep(THROTTLE_SECONDS)
            return parse_post(url, html)
        except Exception as e:  # noqa: BLE001 — scraper, log and continue
            print(f"  ! {url}: {e}", file=sys.stderr)
            return None

    # Modest concurrency — we still respect the throttle inside each worker.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(work, u): u for u in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            post = fut.result()
            if not post or not post.body_markdown:
                continue
            cat_dir = out_dir / post.category
            cat_dir.mkdir(parents=True, exist_ok=True)
            (cat_dir / f"{post.slug}.md").write_text(
                _format_post_file(post), encoding="utf-8"
            )
            index.append(
                {k: v for k, v in asdict(post).items() if k != "body_markdown"}
            )
            if i % 25 == 0:
                print(f"  ... {i}/{len(targets)}", file=sys.stderr)

    index.sort(key=lambda p: (p["category"], p["date"]))
    (out_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Done. {len(index)} posts written to {out_dir}", file=sys.stderr)


def _format_post_file(post: Post) -> str:
    header = [
        f"# {post.title}",
        "",
        f"- Source: {post.url}",
        f"- Date: {post.date}",
        f"- Category: {post.category}",
    ]
    if post.tags:
        header.append(f"- Tags: {', '.join(post.tags)}")
    header += ["", "---", ""]
    return "\n".join(header) + post.body_markdown + "\n"


def main(argv: Iterable[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="plugins/javapaavi/reference/posts")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", default=None,
                    help="substring filter applied to URLs (e.g. 'spring-framework')")
    args = ap.parse_args(list(argv))
    scrape(Path(args.out), args.limit, args.only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
