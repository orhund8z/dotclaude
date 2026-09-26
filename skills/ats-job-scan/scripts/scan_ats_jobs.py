#!/usr/bin/env python3
"""scan_ats_jobs.py — find matching jobs across every Ashby and Greenhouse job board we can discover.

    python3 scripts/scan_ats_jobs.py                 # full scan (~30 min first time), writes a dated report
    python3 scripts/scan_ats_jobs.py --rescore       # re-filter/re-score the last scan's cache (seconds)

Pipeline
  1. DISCOVER company board slugs
       - Common Crawl CDX index (jobs.ashbyhq.com, job-boards[.eu].greenhouse.io, boards.greenhouse.io)
         over the N most recent crawls
       - ashby/greenhouse links found under `link_roots` (local.json)
       - names of sub-folders of `company_dirs` (guessed as slugs; wrong guesses just 404)
       - `extra_slugs_file` (optional, one "ashby:slug" or "greenhouse:slug" per line)
     Slugs are cached (see `cache_dir`) and refreshed every 14 days (--refresh-slugs to force).
  2. FETCH each board through the public JSON APIs, rate-limited per host, with retries/backoff:
       Greenhouse  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
       Ashby       https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true
  3. FILTER by location  (Munich in any work model, or remote that is open to Germany/Europe/worldwide)
     and by title (Staff/Principal/Senior SRE, platform, architect, engineering manager, ...).
  4. SCORE (title + skills + pay vs. the EUR threshold + freshness - penalties).
  5. REPORT to <output_dir>/ats-scan-<date>.md, optionally publish it (`publish_cmd`), and print a JSON
     summary on stdout (progress and logs go to stderr).

Tunables (terms, weights, thresholds) live in config.json; machine-specific paths in local.json
(both are gitignored; config.example.json / local.example.json are the committed templates).
Only the Python 3 standard library is used (Python 3.9+).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import html as htmllib
import http.client
import json
import os
import random
import re
import shlex
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(SKILL_DIR, "config.json")
EXAMPLE_CONFIG = os.path.join(SKILL_DIR, "config.example.json")
LOCAL_SETTINGS = os.path.join(SKILL_DIR, "local.json")

# Machine-specific settings; overridden from local.json / CLI in main().
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "ats-job-scan")
OUT_DIR = os.path.join(SKILL_DIR, "reports")
EXTRA_SLUGS_PATH = ""
COMPANY_DIRS: List[str] = []
LINK_ROOTS: List[str] = []
PUBLISH_CMD = ""
PUBLISH_CWD = ""
UA = "ats-job-scan/1.0 (personal job search)"

CDX_PATTERNS = {
    "ashby": ["jobs.ashbyhq.com/*"],
    "greenhouse": ["job-boards.greenhouse.io/*", "job-boards.eu.greenhouse.io/*", "boards.greenhouse.io/*"],
}
RESERVED_SLUGS = {
    "embed", "jobs", "job", "robots.txt", "favicon.ico", "sitemap.xml", "static", "assets", "api", "apply",
    "application", "careers", "login", "signin", "_next", "cdn-cgi", "docs", "health", "status", "v1", "null",
    "undefined", "js", "css", "images", "img", "fonts", "public", "widget", "sso", "oauth", "auth", "cookie",
}
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------- config
def compile_terms(terms: List[str], flags: int = re.I) -> Optional["re.Pattern[str]"]:
    parts = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        if t.startswith("re:"):
            parts.append("(?:%s)" % t[3:])
        else:
            parts.append(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(t))
    return re.compile("|".join(parts), flags) if parts else None


class Config:
    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self.raw = raw
        loc, ti, sk = raw["location"], raw["title"], raw["skills"]
        self.munich_re = compile_terms(loc["munich_terms"])
        self.remote_re = compile_terms(loc["remote_terms"])
        weak = [t.lower() for t in loc.get("weak_region_terms", [])]
        self.region_strong_re = compile_terms([t for t in loc["region_terms_in_location"] if t.lower() not in weak])
        self.region_weak_re = compile_terms(weak)
        self.title_restrict_re = compile_terms(loc.get("title_region_restrictions", []))
        self.region_head_re = compile_terms(loc["region_regexes_in_description_head"])
        self.unspec_exclude_re = compile_terms(loc["unspecified_remote_exclude_regexes"])
        self.head_chars = int(loc.get("head_chars", 900))
        self.role_strong_re = compile_terms(ti["role_strong"])
        self.role_generic_re = compile_terms(ti["role_generic"])
        self.sen_high_re = compile_terms(ti["seniority_high"])
        self.sen_mid_re = compile_terms(ti["seniority_mid"])
        self.sen_optional_re = compile_terms(ti["seniority_not_needed"])
        self.title_exclude_re = compile_terms(ti["exclude"])
        self.junior_re = compile_terms(ti["junior"])
        self.tpts = ti["points"]
        self.skills = [(s["name"], int(s["weight"]), compile_terms(s["terms"])) for s in sk["items"]]
        self.skills_cap = int(sk["cap"])
        self.penalties = [
            (p["label"], int(p["points"]), compile_terms(p["terms"]), compile_terms(p.get("unless", [])))
            for p in raw["penalties"]
        ]
        self.comp = raw["compensation"]
        self.fresh = raw["freshness"]
        self.scoring = raw["scoring"]


# ------------------------------------------------------------------- rate-limited HTTP
class FetchError(Exception):
    pass


class HostLimiter:
    """Per-host pacing: at most `rps` requests/second across all threads.

    Adaptive: a 429 doubles the spacing (capped at 10 s) and pauses the host for Retry-After;
    50 consecutive successes shrink the spacing back toward the base rate. 15 consecutive
    server/network failures trip a circuit breaker so one dead host cannot stall the run.
    """

    def __init__(self, name: str, rps: float):
        self.name = name
        self.base = 1.0 / rps
        self.interval = self.base
        self.next_slot = 0.0
        self.ok_streak = 0
        self.fail_streak = 0
        self.aborted = False
        self.throttles = 0
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.monotonic()
            slot = max(now, self.next_slot)
            self.next_slot = slot + self.interval
            wait = slot - now
        if wait > 0:
            time.sleep(wait)

    def on_success(self) -> None:
        with self.lock:
            self.fail_streak = 0
            self.ok_streak += 1
            if self.ok_streak >= 50 and self.interval > self.base:
                self.interval = max(self.base, self.interval * 0.8)
                self.ok_streak = 0

    def on_throttle(self, retry_after: Optional[float]) -> None:
        with self.lock:
            self.throttles += 1
            self.ok_streak = 0
            self.interval = min(self.interval * 2, 10.0)
            pause = retry_after if retry_after else self.interval * 2
            self.next_slot = max(self.next_slot, time.monotonic() + min(pause, 120.0))

    def on_error(self) -> None:
        with self.lock:
            self.ok_streak = 0
            self.fail_streak += 1
            if self.fail_streak >= 15 and not self.aborted:
                self.aborted = True
                log("!! circuit breaker: too many consecutive failures on %s — skipping the rest of that host" % self.name)


def http_get(url: str, lim: HostLimiter, retries: int = 4, timeout: int = 40) -> Optional[str]:
    """GET -> text. Returns None for 404/410 (permanent 'no such board'). Raises FetchError after retries."""
    last: Optional[BaseException] = None
    for attempt in range(retries + 1):
        if lim.aborted:
            raise FetchError("host %s aborted" % lim.name)
        lim.acquire()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            lim.on_success()
            return body
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                lim.on_success()
                return None
            if e.code == 429:
                ra = e.headers.get("Retry-After") if e.headers else None
                lim.on_throttle(float(ra) if ra and ra.replace(".", "", 1).isdigit() else None)
            elif e.code >= 500:
                lim.on_error()
            else:
                raise FetchError("HTTP %s for %s" % (e.code, url))
            last = e
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError) as e:
            lim.on_error()
            last = e
        time.sleep(min(2 ** attempt + random.random(), 20))
    raise FetchError("%s: %s" % (url, last))


# ------------------------------------------------------------------------- discovery
def valid_slug(s: str) -> Optional[str]:
    s = urllib.parse.unquote(s or "").strip()
    if not SLUG_RE.match(s) or s.lower() in RESERVED_SLUGS or s.lower().endswith((".js", ".css", ".png", ".ico", ".json", ".xml", ".txt")):
        return None
    return s


def cdx_slugs(cdx_api: str, pattern: str, lim: HostLimiter, max_pages: int) -> List[str]:
    base = "%s?url=%s&output=json&filter=status:200" % (cdx_api, urllib.parse.quote(pattern, safe="*/"))
    meta = http_get(base + "&showNumPages=true", lim)
    if not meta:
        return []
    pages = int(json.loads(meta.strip().splitlines()[0]).get("pages", 0))
    out: List[str] = []
    for p in range(min(pages, max_pages)):
        txt = http_get("%s&fl=url&page=%d" % (base, p), lim)
        for line in (txt or "").splitlines():
            try:
                u = json.loads(line)["url"]
            except (ValueError, KeyError):
                continue
            m = re.match(r"https?://[^/]+/([^/?#]+)", u)
            if m:
                out.append(m.group(1))
    return out


def seed_slugs() -> Dict[str, set]:
    found: Dict[str, set] = {"ashby": set(), "greenhouse": set()}
    pats = {
        "ashby": re.compile(r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
        "greenhouse": re.compile(r"(?:job-boards(?:\.eu)?|boards)\.greenhouse\.io/([A-Za-z0-9_.%-]+)"),
    }
    skip = {".git", "html", "node_modules", ".ats_cache", ".claude", "__pycache__"}
    for base in LINK_ROOTS:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip and os.path.abspath(os.path.join(root, d)) != os.path.abspath(OUT_DIR)]
            for fn in files:
                if not fn.endswith((".md", ".txt", ".csv", ".json")):
                    continue
                try:
                    with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except OSError:
                    continue
                for ats, rx in pats.items():
                    for m in rx.finditer(text):
                        s = valid_slug(m.group(1))
                        if s:
                            found[ats].add(s)
    # sub-folders of company_dirs are guessed as slugs on both ATSs (wrong guesses just 404)
    for cdir in COMPANY_DIRS:
        if not os.path.isdir(cdir):
            continue
        for d in os.listdir(cdir):
            s = valid_slug(d)
            if s and os.path.isdir(os.path.join(cdir, d)):
                for ats in found:
                    found[ats].add(s)
    if EXTRA_SLUGS_PATH and os.path.exists(EXTRA_SLUGS_PATH):
        with open(EXTRA_SLUGS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.split("#")[0].strip()
                if ":" in line:
                    ats, slug = line.split(":", 1)
                    s = valid_slug(slug)
                    if ats.strip() in found and s:
                        found[ats.strip()].add(s)
    return found


def discover_slugs(args, cdx_lim: HostLimiter) -> Dict[str, Dict[str, str]]:
    """Returns {ats: {lowercase_slug: original_case_slug}}."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, "slugs.json")
    cached: Dict[str, List[str]] = {"ashby": [], "greenhouse": []}
    age_days = 1e9
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        cached = blob["slugs"]
        age_days = (time.time() - blob["updated_epoch"]) / 86400.0
    stale = args.refresh_slugs or age_days > 14
    if stale and not args.seeds_only:
        log("[discover] Common Crawl: last %d crawls (rate %.1f req/s, max %d pages/pattern)" % (args.crawls, args.rps_cdx, args.max_cdx_pages))
        info = http_get("https://index.commoncrawl.org/collinfo.json", cdx_lim)
        crawls = [c["cdx-api"] for c in json.loads(info or "[]")][: args.crawls]
        fresh: Dict[str, set] = {"ashby": set(), "greenhouse": set()}
        for ci, api in enumerate(crawls, 1):
            for ats, patterns in CDX_PATTERNS.items():
                for pat in patterns:
                    try:
                        got = cdx_slugs(api, pat, cdx_lim, args.max_cdx_pages)
                    except (FetchError, ValueError) as e:
                        log("  ! %s %s skipped: %s" % (api.rsplit("/", 1)[-1], pat, str(e)[:100]))
                        continue
                    for g in got:
                        s = valid_slug(g)
                        if s:
                            fresh[ats].add(s)
            log("  crawl %d/%d done — ashby=%d greenhouse=%d slugs so far" % (ci, len(crawls), len(fresh["ashby"]), len(fresh["greenhouse"])))
        for ats in fresh:
            cached[ats] = sorted(set(cached.get(ats, [])) | fresh[ats], key=str.lower)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"updated_epoch": time.time(), "updated": dt.datetime.now().isoformat(timespec="seconds"), "slugs": cached}, f)
    else:
        log("[discover] using cached slug list (%.1f days old)" % age_days if age_days < 1e8 else "[discover] no cache and --seeds-only: seeds only")
    seeds = seed_slugs()
    out: Dict[str, Dict[str, str]] = {"ashby": {}, "greenhouse": {}}
    for ats in out:
        for s in list(cached.get(ats, [])) + sorted(seeds[ats]):
            out[ats].setdefault(s.lower(), s)
    for spec in args.slug or []:
        ats, _, slug = spec.partition(":")
        if ats in out and valid_slug(slug):
            out[ats].setdefault(slug.lower(), slug)
    return out


# --------------------------------------------------------------------------- normalise
@dataclass
class Job:
    ats: str
    slug: str
    company: str
    job_id: str
    title: str
    url: str
    locations: List[str]
    remote: bool
    workplace: str  # "Remote" | "Hybrid" | "OnSite" | ""
    description: str
    published: str
    departments: List[str] = field(default_factory=list)
    comp_min: Optional[float] = None
    comp_max: Optional[float] = None
    comp_cur: str = ""


def clean_html(s: str) -> str:
    s = htmllib.unescape(s or "")
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


def pretty_company(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).strip().title() if slug else slug


def parse_greenhouse(slug: str, data: dict) -> List[Job]:
    jobs = []
    for j in data.get("jobs", []):
        # NB: Greenhouse `offices` lists every office of the department, not just this job's — using it
        # blindly makes an "Ireland (Remote)" job look like "Germany (Remote)". Trust `location` first and
        # fall back to offices only when it is empty or vague.
        primary = ((j.get("location") or {}).get("name") or "").strip()
        locs = [primary]
        if not primary or re.search(r"(?i)multiple|various|several|flexible|anywhere|see (description|posting)", primary):
            for o in j.get("offices") or []:
                locs.append((o.get("name") or "").strip())
                locs.append((o.get("location") or "").strip())
        locs = list(dict.fromkeys(x for x in locs if x))
        jobs.append(Job(
            ats="greenhouse", slug=slug, company=j.get("company_name") or pretty_company(slug), job_id=str(j.get("id")),
            title=(j.get("title") or "").strip(), url=j.get("absolute_url") or "", locations=locs, remote=False,
            workplace="", description=clean_html(j.get("content", "")),
            published=j.get("first_published") or j.get("updated_at") or "",
            departments=[d.get("name", "") for d in j.get("departments") or []],
        ))
    return jobs


def parse_ashby(slug: str, data: dict) -> List[Job]:
    jobs = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [(j.get("location") or "").strip()]
        for s in j.get("secondaryLocations") or []:
            locs.append((s.get("location") or "").strip())
        addr = ((j.get("address") or {}).get("postalAddress") or {})
        locs.append((addr.get("addressLocality") or "").strip())
        locs.append((addr.get("addressCountry") or "").strip())
        locs = list(dict.fromkeys(x for x in locs if x))
        cmin = cmax = None
        ccur = ""
        for tier in (j.get("compensation") or {}).get("compensationTiers") or []:
            for c in tier.get("components") or []:
                if c.get("compensationType") == "Salary" and (c.get("interval") or "").upper().endswith("YEAR") and c.get("maxValue"):
                    lo, hi = float(c.get("minValue") or 0), float(c["maxValue"])
                    cmin = lo if cmin is None else min(cmin, lo)
                    cmax = hi if cmax is None else max(cmax, hi)
                    ccur = c.get("currencyCode") or ccur
        jobs.append(Job(
            ats="ashby", slug=slug, company=pretty_company(slug), job_id=str(j.get("id")), title=(j.get("title") or "").strip(),
            url=j.get("jobUrl") or "", locations=locs, remote=bool(j.get("isRemote")) or j.get("workplaceType") == "Remote",
            workplace=j.get("workplaceType") or "", description=(j.get("descriptionPlain") or clean_html(j.get("descriptionHtml", ""))),
            published=j.get("publishedAt") or "", departments=[x for x in [j.get("department"), j.get("team")] if x],
            comp_min=cmin, comp_max=cmax, comp_cur=ccur,
        ))
    return jobs


# -------------------------------------------------------------------------- filtering
@dataclass
class Match:
    job: Job
    bucket: str  # munich | remote-eu | remote-unspecified
    where: str
    score: int = 0
    signals: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    pay: str = ""
    company_key: str = ""


def is_remote_job(job: Job, cfg: Config) -> bool:
    loc_text = " | ".join(job.locations)
    return job.remote or bool(cfg.remote_re.search(loc_text)) or bool(cfg.remote_re.search(job.title))


def classify_location(job: Job, cfg: Config, allow_unspecified: bool) -> Optional[Tuple[str, str]]:
    loc_text = " | ".join(job.locations)
    head = job.description[: cfg.head_chars]
    model = {"Remote": "Remote", "Hybrid": "Hybrid", "OnSite": "On-site"}.get(job.workplace, "")
    if not model:
        blob = (loc_text + " " + job.title).lower()
        model = "Hybrid" if "hybrid" in blob else ("Remote" if cfg.remote_re.search(blob) else "")
    if cfg.munich_re.search(loc_text) or cfg.munich_re.search(job.title):
        return "munich", "Munich · %s" % (model or "on-site/hybrid?")
    if not is_remote_job(job, cfg):
        return None
    # A title like "Staff Engineer (LATAM)" / "- US" contradicts weak evidence ("Global", or "Europe" somewhere
    # in the posting text), so weak evidence is ignored for those. Explicit Germany/Europe/EMEA/EU in the
    # location field is trusted.
    restricted = bool(cfg.title_restrict_re and cfg.title_restrict_re.search(job.title))
    strong = cfg.region_strong_re.search(loc_text) or cfg.region_strong_re.search(job.title)
    if strong:
        name = strong.group(0)
        name = name.upper() if name.lower() in ("eu", "emea", "dach", "cet", "cest") else name.title()
        return "remote-eu", "Remote · %s" % name
    if not restricted:
        weak = cfg.region_weak_re.search(loc_text) if cfg.region_weak_re else None
        if weak:
            return "remote-eu", "Remote · %s" % weak.group(0).title()
        if cfg.region_head_re.search(head):
            return "remote-eu", "Remote · Europe (per posting text)"
        if allow_unspecified and not cfg.unspec_exclude_re.search(loc_text + " " + head):
            return "remote-unspecified", "Remote · region unspecified"
    return None


def classify_title(title: str, cfg: Config) -> Optional[Tuple[int, List[str]]]:
    if cfg.title_exclude_re.search(title) or cfg.junior_re.search(title):
        return None
    strong = bool(cfg.role_strong_re.search(title))
    generic = bool(cfg.role_generic_re.search(title))
    if not (strong or generic):
        return None
    high = bool(cfg.sen_high_re.search(title))
    mid = bool(cfg.sen_mid_re.search(title))
    optional = bool(cfg.sen_optional_re.search(title))
    p = cfg.tpts
    pts, tags = 0, []
    if strong:
        pts += p["strong"]
    else:
        pts += p["generic"]
    if high:
        pts += p["high"]
    elif mid or optional:
        pts += p["mid"]
    else:
        if generic and not strong:
            return None  # plain "Software Engineer" etc. — mid-level, not our target
        pts += p["unclear_level_penalty"]
        tags.append("level?")
    return pts, tags


FX_SYM = {"€": "EUR", "eur": "EUR", "$": "USD", "usd": "USD", "£": "GBP", "gbp": "GBP", "chf": "CHF"}
_NUM = r"(\d{1,3}(?:[.,]\d{3})+|\d{2,3}(?:\.\d)?\s?[kK])"
RANGE_PRE = re.compile(r"(€|\$|£|EUR|USD|GBP|CHF)\s?%s\s?(?:-|–|—|to)\s?(?:€|\$|£|EUR|USD|GBP|CHF)?\s?%s(?![\d,.]\d)" % (_NUM, _NUM), re.I)
RANGE_POST = re.compile(r"%s\s?(?:-|–|—|to)\s?%s\s?(€|\$|£|EUR|USD|GBP|CHF)" % (_NUM, _NUM), re.I)


def _num(s: str) -> float:
    s = s.strip().lower().replace(" ", "")
    if s.endswith("k"):
        return float(s[:-1]) * 1000
    return float(re.sub(r"[.,]", "", s))


def parse_pay(job: Job, cfg: Config) -> Tuple[str, Optional[float]]:
    """Returns (display string, max-in-EUR or None)."""
    fx = cfg.comp["fx_to_eur"]
    if job.comp_max:
        cur = job.comp_cur or "USD"
        hi = job.comp_max * fx.get(cur, 1.0)
        return "%s%s–%s" % (cur + " ", _k(job.comp_min or 0), _k(job.comp_max)), hi
    text = job.description
    for rx, order in ((RANGE_PRE, "pre"), (RANGE_POST, "post")):
        for m in rx.finditer(text):
            g = m.groups()
            cur_sym = (g[0] if order == "pre" else g[2]).lower()
            lo_s, hi_s = (g[1], g[2]) if order == "pre" else (g[0], g[1])
            try:
                lo, hi = _num(lo_s), _num(hi_s)
            except ValueError:
                continue
            if 30000 <= lo <= hi <= 1_000_000:
                cur = FX_SYM.get(cur_sym, "EUR")
                return "%s %s–%s" % (cur, _k(lo), _k(hi)), hi * fx.get(cur, 1.0)
    return "", None


def _k(v: float) -> str:
    return "%dk" % round(v / 1000)


def days_old(published: str) -> Optional[int]:
    if not published:
        return None
    try:
        d = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
        return max(0, (dt.datetime.now(dt.timezone.utc) - (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc))).days)
    except ValueError:
        return None


def score_match(m: Match, cfg: Config, title_pts: int) -> None:
    j = m.job
    desc = j.description
    score = title_pts
    hits = []
    sk_pts = 0
    for name, weight, rx in cfg.skills:
        if rx.search(desc) or rx.search(j.title):
            sk_pts += weight
            hits.append(name)
    score += min(sk_pts, cfg.skills_cap)
    m.signals = hits[:6]
    for label, pts, rx, unless in cfg.penalties:
        if rx.search(desc) and not (unless and unless.search(desc)):
            score += pts
            m.flags.append(label)
    pay_str, hi_eur = parse_pay(j, cfg)
    m.pay = pay_str
    if hi_eur is not None:
        if hi_eur >= cfg.comp["threshold_eur"]:
            score += cfg.comp["above_points"]
        else:
            score += cfg.comp["below_points"]
            m.flags.append("pay < €%dk?" % (cfg.comp["threshold_eur"] // 1000))
    age = days_old(j.published)
    fr = cfg.fresh
    if age is not None:
        if age <= fr["fresh_days"]:
            score += fr["fresh_points"]
        elif age >= fr["stale_days"]:
            score += fr["stale_points"]
            m.flags.append("open %dd" % age)
    if m.bucket == "remote-unspecified":
        score += cfg.scoring["unspecified_remote_penalty"]
    m.score = max(0, min(100, score))


# ---------------------------------------------------------------------------- pipeline
class Stats:
    def __init__(self):
        self.lock = threading.Lock()
        self.boards_total = 0
        self.boards_done = 0
        self.boards_ok = 0
        self.boards_missing = 0
        self.boards_skipped_cache = 0
        self.boards_error = 0
        self.jobs_seen = 0
        self.jobs_candidates = 0   # title/seniority OK and (Munich or remote)
        self.jobs_location = 0     # ... and eligible for someone in Munich (strict location filter)
        self.unspecified_remote_skipped = 0


def process_board(ats: str, slug: str, lims: Dict[str, HostLimiter], cfg: Config, stats: Stats) -> Tuple[str, str, List[Job], int]:
    """Fetch one board; keep only 'candidates' (title/seniority OK and Munich-or-remote).

    Candidates are cached so scoring/location rules can be re-tuned offline with --rescore.
    """
    lim = lims[ats]
    if ats == "greenhouse":
        url = "https://boards-api.greenhouse.io/v1/boards/%s/jobs?content=true" % urllib.parse.quote(slug)
    else:
        url = "https://api.ashbyhq.com/posting-api/job-board/%s?includeCompensation=true" % urllib.parse.quote(slug)
    body = http_get(url, lim)
    if body is None:
        return "missing", "%s:%s" % (ats, slug.lower()), [], 0
    data = json.loads(body)
    jobs = parse_greenhouse(slug, data) if ats == "greenhouse" else parse_ashby(slug, data)
    cands: List[Job] = []
    for j in jobs:
        if classify_title(j.title, cfg) is None:
            continue
        loc_text = " | ".join(j.locations)
        if cfg.munich_re.search(loc_text) or cfg.munich_re.search(j.title) or is_remote_job(j, cfg):
            j.description = j.description[:12000]
            cands.append(j)
    with stats.lock:
        stats.jobs_seen += len(jobs)
        stats.jobs_candidates += len(cands)
    return "ok", "%s:%s" % (ats, slug.lower()), cands, len(jobs)


def select_matches(cands: List[Job], cfg: Config, args, stats: Stats) -> List[Match]:
    """Apply the strict location filter, title scoring and thresholds to cached candidates."""
    matches: List[Match] = []
    stats.jobs_location = 0
    stats.unspecified_remote_skipped = 0
    for j in cands:
        t = classify_title(j.title, cfg)
        loc = classify_location(j, cfg, True)
        if not t or not loc:
            continue
        bucket, where = loc
        if bucket == "remote-unspecified" and not args.include_unspecified_remote:
            stats.unspecified_remote_skipped += 1
            continue
        stats.jobs_location += 1
        m = Match(job=j, bucket=bucket, where=where, flags=list(t[1]))
        score_match(m, cfg, t[0])
        matches.append(m)
    return matches


def save_candidates(cands: List[Job], stats: Stats, partial: bool) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    blob = {"saved": dt.datetime.now().isoformat(timespec="seconds"), "partial": partial,
            "stats": {k: getattr(stats, k) for k in ("boards_total", "boards_done", "boards_ok", "boards_missing", "boards_skipped_cache", "boards_error", "jobs_seen", "jobs_candidates")},
            "jobs": [asdict(j) for j in cands]}
    with open(os.path.join(CACHE_DIR, "candidates.json"), "w", encoding="utf-8") as f:
        json.dump(blob, f)


def load_candidates(stats: Stats) -> Tuple[List[Job], bool, str]:
    path = os.path.join(CACHE_DIR, "candidates.json")
    if not os.path.exists(path):
        raise SystemExit("no cached candidates — run a normal scan first (without --rescore)")
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    for k, v in blob["stats"].items():
        setattr(stats, k, v)
    return [Job(**d) for d in blob["jobs"]], bool(blob.get("partial")), blob["saved"]


def load_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def run_scan(slugs: Dict[str, Dict[str, str]], lims: Dict[str, HostLimiter], cfg: Config, args, stats: Stats) -> Tuple[List[Job], bool]:
    state_path = os.path.join(CACHE_DIR, "boards.json")
    state: Dict[str, dict] = load_json(state_path, {})
    today = dt.date.today()
    tasks: List[Tuple[str, str]] = []
    for ats in ("ashby", "greenhouse"):
        for low, orig in slugs[ats].items():
            st = state.get("%s:%s" % (ats, low))
            if st and not args.recheck:
                age = (today - dt.date.fromisoformat(st["checked"])).days
                if (st["status"] == "missing" and age < 30) or (st["status"] == "ok" and st.get("jobs", 1) == 0 and age < 7):
                    stats.boards_skipped_cache += 1
                    continue
            tasks.append((ats, orig))
    random.Random(7).shuffle(tasks)  # spread load across both hosts
    if args.max_boards:
        tasks = tasks[: args.max_boards]
    stats.boards_total = len(tasks)
    log("[fetch] %d boards to fetch (%d skipped via cache) — workers=%d, ashby %.1f rps, greenhouse %.1f rps" % (
        len(tasks), stats.boards_skipped_cache, args.workers, args.rps_ashby, args.rps_greenhouse))
    all_cands: List[Job] = []
    partial = False
    started = time.time()
    ex = cf.ThreadPoolExecutor(max_workers=args.workers)
    futs = {ex.submit(process_board, ats, slug, lims, cfg, stats): (ats, slug) for ats, slug in tasks}
    try:
        for fut in cf.as_completed(futs):
            ats, slug = futs[fut]
            key = "%s:%s" % (ats, slug.lower())
            stats.boards_done += 1
            try:
                status, _, ms, n = fut.result()
            except (FetchError, ValueError) as e:
                stats.boards_error += 1
                state[key] = {"status": "error", "checked": today.isoformat(), "jobs": 0}
                if stats.boards_error <= 5:
                    log("  ! %s: %s" % (key, str(e)[:120]))
                continue
            if status == "missing":
                stats.boards_missing += 1
            else:
                stats.boards_ok += 1
                all_cands.extend(ms)
            state[key] = {"status": status, "checked": today.isoformat(), "jobs": n}
            if stats.boards_done % 100 == 0 or stats.boards_done == stats.boards_total:
                el = time.time() - started
                eta = el / stats.boards_done * (stats.boards_total - stats.boards_done)
                log("  %d/%d boards (ok=%d missing=%d err=%d) jobs=%d → candidates=%d · %.0fs elapsed, ~%.0fs left" % (
                    stats.boards_done, stats.boards_total, stats.boards_ok, stats.boards_missing, stats.boards_error,
                    stats.jobs_seen, stats.jobs_candidates, el, eta))
    except KeyboardInterrupt:
        partial = True
        log("!! interrupted — writing a PARTIAL report from what has been fetched")
        ex.shutdown(wait=False, cancel_futures=True)
    else:
        ex.shutdown(wait=True)
    finally:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    return all_cands, partial


def dedupe(matches: List[Match]) -> List[Match]:
    best: Dict[Tuple[str, str, str], Match] = {}
    for m in matches:
        k = (m.job.company.lower(), re.sub(r"\W+", " ", m.job.title.lower()).strip(), m.bucket)
        if k not in best or m.score > best[k].score:
            best[k] = m
    return list(best.values())


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def evaluated_companies() -> List[str]:
    out: List[str] = []
    for d in COMPANY_DIRS:
        if os.path.isdir(d):
            out += [norm_key(x) for x in os.listdir(d)
                    if os.path.isdir(os.path.join(d, x)) and x != os.path.basename(OUT_DIR)]
    return out


# ------------------------------------------------------------------------------ report
def esc(s: str) -> str:
    return (s or "").replace("|", "/").replace("\n", " ").strip()


def render_table(rows: List[Match], seen_first: Dict[str, str], baseline: bool, today: str) -> List[str]:
    out = ["| # | Score | Company | Role | Where | Pay | Fit signals | Link |", "|---|-------|---------|------|-------|-----|-------------|------|"]
    for i, m in enumerate(rows, 1):
        j = m.job
        badges = []
        if not baseline and seen_first.get("%s:%s:%s" % (j.ats, j.slug.lower(), j.job_id)) == today:
            badges.append("🆕")
        if m.company_key:
            badges.append("📁")
        sig = ", ".join(m.signals) if m.signals else "—"
        if m.flags:
            sig += " · ⚠ " + ", ".join(m.flags)
        out.append("| %d | **%d** | %s%s | %s | %s | %s | %s | [%s](%s) |" % (
            i, m.score, " ".join(badges) + " " if badges else "", esc(j.company), esc(j.title), esc(m.where), esc(m.pay) or "—",
            esc(sig), "Ashby" if j.ats == "ashby" else "Greenhouse", j.url))
    return out


def write_report(matches: List[Match], cfg: Config, args, stats: Stats, partial: bool, baseline: bool, seen_first: Dict[str, str], report_date: str = "") -> str:
    today = report_date or dt.date.today().isoformat()
    sc = cfg.scoring
    matches = [m for m in matches if m.score >= sc["min_score"]]
    matches.sort(key=lambda m: (-m.score, m.job.company.lower()))
    top = [m for m in matches if m.score >= sc["tier_top"]]
    good = [m for m in matches if sc["tier_good"] <= m.score < sc["tier_top"]]
    maybe = [m for m in matches if m.score < sc["tier_good"]]
    maybe_shown = maybe[: sc["max_rows_maybe"]]
    n_mun = sum(1 for m in matches if m.bucket == "munich")
    n_rem = sum(1 for m in matches if m.bucket == "remote-eu")
    n_unspec = sum(1 for m in matches if m.bucket == "remote-unspecified")
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    L: List[str] = []
    L.append("# 🔎 ATS Job Scan — Ashby + Greenhouse (%s)%s" % (today, " — PARTIAL" if partial else ""))
    L.append("")
    L.append("**📇 Künye:** Generated %s by the `ats-job-scan` skill (`scripts/scan_ats_jobs.py`) · Sources: Ashby posting API, Greenhouse boards API · Filter: Munich (on-site/hybrid/remote) **or** remote open to Germany/Europe/worldwide · Config: `config.json`" % now)
    L.append("")
    if partial:
        L.append("> ⚠️ **Partial run** — interrupted before all boards were fetched. Re-run to continue (finished boards are cached).")
        L.append("")
    L.append("## ⚡ Summary")
    L.append("")
    L.append("| | Count |")
    L.append("|---|---|")
    L.append("| 🔥 Top matches (score ≥ %d) | **%d** |" % (sc["tier_top"], len(top)))
    L.append("| ✅ Good matches (%d–%d) | **%d** |" % (sc["tier_good"], sc["tier_top"] - 1, len(good)))
    L.append("| 🤔 Worth a glance (%d–%d) | %d (showing %d) |" % (sc["min_score"], sc["tier_good"] - 1, len(maybe), len(maybe_shown)))
    L.append("| 📍 Munich / 🌍 Remote (Germany/Europe/worldwide)%s | %d / %d%s |" % (" / region unspecified" if n_unspec else "", n_mun, n_rem, " / %d" % n_unspec if n_unspec else ""))
    L.append("")
    L.append("Legend: 🆕 first seen in this run · 📁 company already has a folder in your company directory · ⚠ flags = things to check (level unclear, German required?, pay below threshold, stale posting, off-stack). "
             "Pay shown only when the posting states it (Ashby structured data or a parsed range); the threshold is €%dk base." % (cfg.comp["threshold_eur"] // 1000))
    if baseline:
        L.append("")
        L.append("_First run: no 🆕 markers yet — this run is the baseline for future \"new since last run\" tracking._")
    L.append("")
    for title, rows in (("## 🔥 Top matches", top), ("## ✅ Good matches", good)):
        if not rows:
            continue
        L.append(title)
        L.append("")
        mun = [m for m in rows if m.bucket == "munich"]
        rem = [m for m in rows if m.bucket != "munich"]
        if mun:
            L.append("### 📍 Munich (%d)" % len(mun))
            L.append("")
            L += render_table(mun, seen_first, baseline, today)
            L.append("")
        if rem:
            L.append("### 🌍 Remote — Germany / Europe / worldwide (%d)" % len(rem))
            L.append("")
            L += render_table(rem, seen_first, baseline, today)
            L.append("")
    if maybe_shown:
        L.append("## 🤔 Worth a glance")
        L.append("")
        L += render_table(maybe_shown, seen_first, baseline, today)
        L.append("")
    if not matches:
        L.append("_No jobs matched. Try lowering `scoring.min_score`, widening `title.role_*` terms, or `--include-unspecified-remote`._")
        L.append("")
    by_co: Dict[str, int] = {}
    for m in matches:
        by_co[m.job.company] = by_co.get(m.job.company, 0) + 1
    multi = sorted(((c, n) for c, n in by_co.items() if n > 1), key=lambda x: -x[1])[:15]
    if multi:
        L.append("## 🏢 Companies with several matching roles")
        L.append("")
        L.append("| Company | Matching roles |")
        L.append("|---|---|")
        for c, n in multi:
            L.append("| %s | %d |" % (esc(c), n))
        L.append("")
    L.append("## 🧪 How this run went")
    L.append("")
    L.append("| Stage | Count |")
    L.append("|---|---|")
    L.append("| Board slugs known (Ashby + Greenhouse) | %d |" % (stats.boards_total + stats.boards_skipped_cache))
    L.append("| Boards fetched this run | %d (ok %d · not found %d · errors %d) |" % (stats.boards_done, stats.boards_ok, stats.boards_missing, stats.boards_error))
    L.append("| Boards skipped (known-dead / empty, cached) | %d |" % stats.boards_skipped_cache)
    L.append("| Job postings seen | %d |" % stats.jobs_seen)
    L.append("| … with a matching title/seniority (Staff/Principal/Senior SRE, platform, architect, EM, …) in Munich or remote | %d |" % stats.jobs_candidates)
    L.append("| … also eligible from Munich (Munich, or remote open to Germany/Europe/worldwide) | %d |" % stats.jobs_location)
    L.append("| … in the report (score ≥ %d, de-duplicated) | %d |" % (sc["min_score"], len(matches)))
    if stats.unspecified_remote_skipped and not args.include_unspecified_remote:
        L.append("| Remote jobs skipped because the region is unspecified (re-run with `--include-unspecified-remote`) | %d |" % stats.unspecified_remote_skipped)
    L.append("")
    L.append("**Coverage caveat:** company boards are *discovered*, not enumerated — Ashby and Greenhouse publish no company index. "
             "Discovery uses Common Crawl, links already in this repo, and interview folder names, so companies that were never crawled are invisible. "
             "Add known companies to the extra-slugs file (`extra_slugs_file` in `local.json`; lines like `ashby:slug` / `greenhouse:slug`) to close gaps.")
    L.append("")
    L.append("**Next step:** run the top rows through `/job-evaluator` — this scan scores fit from the posting text only (no reviews, funding or layoffs).")
    L.append("")
    L.append("**Re-run:** `python3 scripts/scan_ats_jobs.py` from the skill folder (add `--refresh-slugs` to re-crawl for new companies, `--recheck` to ignore the dead-board cache).")
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "ats-scan-%s.md" % today)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return path


# -------------------------------------------------------------------------------- main
def expand(p: Optional[str]) -> str:
    return os.path.abspath(os.path.expanduser(p)) if p else ""


def apply_local_settings(args) -> None:
    """local.json (gitignored) holds machine-specific paths; CLI flags win over it."""
    global CACHE_DIR, OUT_DIR, EXTRA_SLUGS_PATH, COMPANY_DIRS, LINK_ROOTS, PUBLISH_CMD, PUBLISH_CWD, UA
    loc = load_json(args.local or LOCAL_SETTINGS, {})
    if loc.get("cache_dir"):
        CACHE_DIR = expand(loc["cache_dir"])
    if loc.get("output_dir"):
        OUT_DIR = expand(loc["output_dir"])
    EXTRA_SLUGS_PATH = expand(loc.get("extra_slugs_file"))
    COMPANY_DIRS = [expand(d) for d in loc.get("company_dirs", [])]
    LINK_ROOTS = [expand(d) for d in loc.get("link_roots", [])]
    PUBLISH_CMD = loc.get("publish_cmd") or ""
    PUBLISH_CWD = expand(loc.get("publish_cwd")) if loc.get("publish_cwd") else ""
    if loc.get("contact"):
        UA = "ats-job-scan/1.0 (personal job search; contact %s)" % loc["contact"]
    if args.output_dir:
        OUT_DIR = expand(args.output_dir)
    if args.cache_dir:
        CACHE_DIR = expand(args.cache_dir)


def summary_row(m: Match, seen_first: Dict[str, str], baseline: bool, scan_date: str) -> dict:
    j = m.job
    return {
        "score": m.score, "company": j.company, "title": j.title, "where": m.where, "pay": m.pay or None,
        "url": j.url, "signals": m.signals, "flags": m.flags, "evaluated_before": bool(m.company_key),
        "new": (not baseline) and seen_first.get("%s:%s:%s" % (j.ats, j.slug.lower(), j.job_id)) == scan_date,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="filter/scoring config (default: config.json, else config.example.json)")
    ap.add_argument("--local", default=None, help="machine-specific settings (default: local.json next to the skill)")
    ap.add_argument("--output-dir", default=None, help="where ats-scan-<date>.md is written (overrides local.json)")
    ap.add_argument("--cache-dir", default=None, help="slug/board/candidate cache (overrides local.json)")
    ap.add_argument("--refresh-slugs", action="store_true", help="re-crawl Common Crawl for company slugs now")
    ap.add_argument("--rescore", action="store_true", help="skip discovery+fetching; re-filter/re-score the candidates cached by the last scan (seconds)")
    ap.add_argument("--seeds-only", action="store_true", help="skip Common Crawl; use cached + seed slugs + --slug only")
    ap.add_argument("--crawls", type=int, default=12, help="how many recent Common Crawl crawls to read (default 12)")
    ap.add_argument("--max-cdx-pages", type=int, default=20, help="max CDX result pages per pattern per crawl")
    ap.add_argument("--recheck", action="store_true", help="ignore the dead/empty-board cache")
    ap.add_argument("--slug", action="append", metavar="ATS:SLUG", help="extra board to scan, e.g. ashby:nango (repeatable)")
    ap.add_argument("--max-boards", type=int, default=0, help="limit boards fetched (testing)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rps-ashby", type=float, default=4.0, help="max requests/second to api.ashbyhq.com")
    ap.add_argument("--rps-greenhouse", type=float, default=4.0, help="max requests/second to boards-api.greenhouse.io")
    ap.add_argument("--rps-cdx", type=float, default=1.0, help="max requests/second to index.commoncrawl.org")
    ap.add_argument("--min-score", type=int, default=None)
    ap.add_argument("--include-unspecified-remote", action="store_true", help="also list remote jobs whose region is not stated")
    ap.add_argument("--no-publish", action="store_true", help="write the markdown only; skip publish_cmd")
    args = ap.parse_args()

    apply_local_settings(args)
    cfg_path = args.config or (DEFAULT_CONFIG if os.path.exists(DEFAULT_CONFIG) else EXAMPLE_CONFIG)
    cfg = Config(cfg_path)
    if args.min_score is not None:
        cfg.scoring["min_score"] = args.min_score
    os.makedirs(CACHE_DIR, exist_ok=True)
    log("[setup] config=%s output=%s cache=%s" % (cfg_path, OUT_DIR, CACHE_DIR))
    lims = {
        "ashby": HostLimiter("api.ashbyhq.com", args.rps_ashby),
        "greenhouse": HostLimiter("boards-api.greenhouse.io", args.rps_greenhouse),
    }
    cdx_lim = HostLimiter("index.commoncrawl.org", args.rps_cdx)
    stats = Stats()
    today = dt.date.today().isoformat()
    scan_date = today
    if args.rescore:
        cands, partial, saved = load_candidates(stats)
        scan_date = saved[:10]  # the data is from that day, so the report is dated by it
        log("[rescore] %d cached candidates from the scan saved %s" % (len(cands), saved))
    else:
        slugs = discover_slugs(args, cdx_lim)
        log("[discover] %d ashby + %d greenhouse candidate slugs" % (len(slugs["ashby"]), len(slugs["greenhouse"])))
        cands, partial = run_scan(slugs, lims, cfg, args, stats)
        save_candidates(cands, stats, partial)
        for ats, lim in lims.items():
            if lim.throttles:
                log("[rate] %s throttled (HTTP 429) %d time(s); pacing adapted automatically" % (lim.name, lim.throttles))
    matches = select_matches(cands, cfg, args, stats)
    matches = dedupe(matches)
    ev = evaluated_companies()
    for m in matches:
        ck = norm_key(m.job.slug)
        m.company_key = ck if any(len(e) >= 4 and (e == ck or ck.startswith(e) or e.startswith(ck)) for e in ev) and len(ck) >= 4 else ""

    # seen.json maps "<ats>:<slug>:<job id>" -> the date of the scan that first saw the posting, plus a
    # "__baseline__" entry: the date of the very first scan. The baseline scan has no 🆕 markers; in a later
    # scan 🆕 means "first seen in this scan". Every candidate posting is tracked (not just this run's
    # matches), so a rule change alone never produces 🆕. A rescore never adds entries, except to create
    # the first baseline.
    seen_path = os.path.join(CACHE_DIR, "seen.json")
    seen_first: Dict[str, str] = load_json(seen_path, {})
    base_date = seen_first.get("__baseline__") or (min(seen_first.values()) if seen_first else None)
    first_run = base_date is None
    if first_run:
        base_date = scan_date
    baseline = base_date == scan_date
    if not args.rescore or first_run:
        for j in cands:
            seen_first.setdefault("%s:%s:%s" % (j.ats, j.slug.lower(), j.job_id), scan_date)
        seen_first["__baseline__"] = base_date
        with open(seen_path, "w", encoding="utf-8") as f:
            json.dump(seen_first, f)

    path = write_report(matches, cfg, args, stats, partial, baseline, seen_first, scan_date)
    log("[report] %s" % path)
    published = False
    rc = 0
    if PUBLISH_CMD and not args.no_publish:
        cwd = PUBLISH_CWD or os.path.dirname(path)
        rel = os.path.relpath(path, cwd) if path.startswith(cwd + os.sep) else path
        cmd = [part.replace("{file}", rel) for part in shlex.split(PUBLISH_CMD)]
        rc = subprocess.call(cmd, cwd=cwd, stdout=sys.stderr)
        published = rc == 0
        log("[publish] %s" % ("ok: " + " ".join(cmd) if published else "!! exited with %d — markdown is written, publish step failed" % rc))

    mun = [m for m in matches if m.bucket == "munich"]
    rem = [m for m in matches if m.bucket != "munich"]
    ordered = lambda ms: sorted([m for m in ms if m.score >= cfg.scoring["min_score"]], key=lambda m: (-m.score, m.job.company.lower()))
    tiers = cfg.scoring
    kept = [m for m in matches if m.score >= tiers["min_score"]]
    summary = {
        "report": path, "scan_date": scan_date, "partial": partial, "baseline_run": baseline, "published": published,
        "counts": {
            "boards_fetched": stats.boards_done, "boards_ok": stats.boards_ok, "boards_error": stats.boards_error,
            "jobs_seen": stats.jobs_seen, "candidates": stats.jobs_candidates, "eligible": stats.jobs_location,
            "in_report": len(kept), "top": sum(1 for m in kept if m.score >= tiers["tier_top"]),
            "good": sum(1 for m in kept if tiers["tier_good"] <= m.score < tiers["tier_top"]),
            "munich": sum(1 for m in kept if m.bucket == "munich"), "remote": sum(1 for m in kept if m.bucket != "munich"),
            "new": 0 if baseline else sum(1 for m in kept if seen_first.get("%s:%s:%s" % (m.job.ats, m.job.slug.lower(), m.job.job_id)) == scan_date),
        },
        "top_munich": [summary_row(m, seen_first, baseline, scan_date) for m in ordered(mun)[:10]],
        "top_remote": [summary_row(m, seen_first, baseline, scan_date) for m in ordered(rem)[:10]],
    }
    print(json.dumps(summary, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
