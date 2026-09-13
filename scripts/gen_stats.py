#!/usr/bin/env python3
"""
gen_stats.py — generate data-driven SVG cards for the profile README.

Data sources (all live GitHub API, no third-party services):
  - repos / stars / PR counts / primary languages
  - contribution calendar (last 12 months)

Outputs into assets/: stats.svg, langs.svg, contrib.svg
Runs locally with GH_TOKEN, in Actions with GITHUB_TOKEN.
"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    sys.exit("GH_TOKEN or GITHUB_TOKEN required")

USER = "Moseyuh333"
API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# ---------------------------------------------------------------- API helpers
def gh_get(path):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "stats-gen",
                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gh_graphql(query):
    req = urllib.request.Request(
        f"{API}/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "stats-gen",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
        if "errors" in d:
            raise RuntimeError(d["errors"])
        return d["data"]

# ---------------------------------------------------------------- fetch
def fetch_data():
    u = gh_get("/user")
    data = {"repos": u["public_repos"], "followers": u["followers"],
            "stars": 0, "pr_open": 0, "pr_merged": 0,
            "lang_counts": {}, "weekly": [], "contrib_total": 0}

    q = '''query {
      user(login: "%s") {
        repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
          nodes { stargazers { totalCount } primaryLanguage { name } }
        }
      }
    }''' % USER
    for rp in gh_graphql(q)["user"]["repositories"]["nodes"]:
        data["stars"] += rp["stargazers"]["totalCount"]
        lang = (rp.get("primaryLanguage") or {}).get("name")
        if lang:
            data["lang_counts"][lang] = data["lang_counts"].get(lang, 0) + 1

    data["pr_merged"] = gh_get(
        "/search/issues?q=author%3A{}%20type%3Apr%20is%3Amerged&per_page=1".format(USER))["total_count"]
    data["pr_open"] = gh_get(
        "/search/issues?q=author%3A{}%20type%3Apr%20is%3Aopen&per_page=1".format(USER))["total_count"]

    since = (datetime.now(timezone.utc) - timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z")
    q2 = '''query {
      user(login: "%s") {
        contributionsCollection(from: "%s") {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { contributionCount } }
          }
        }
      }
    }''' % (USER, since)
    cal = gh_graphql(q2)["user"]["contributionsCollection"]["contributionCalendar"]
    data["contrib_total"] = cal["totalContributions"]
    data["weekly"] = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
    return data

# ---------------------------------------------------------------- SVG helpers
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


FONT = "Segoe UI, -apple-system, Arial, sans-serif"

HEADER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">
<defs>
  <linearGradient id="cardbg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#0a0e16"/>
  </linearGradient>
</defs>
<rect width="{w}" height="{h}" rx="14" fill="url(#cardbg)"/>
<rect x="0.5" y="0.5" width="{w1}" height="{h1}" rx="13.5" fill="none" stroke="#30363d"/>
<text x="24" y="34" font-family="{font}" font-size="14.5" font-weight="600" fill="#c9d1d9">{title}</text>
<text x="{tx}" y="34" font-family="{font}" font-size="11" fill="#8b949e" text-anchor="end">{sub}</text>
<rect x="24" y="44" width="46" height="3" rx="1.5" fill="{accent}"/>
'''


def svg_open(w, h, title, sub, accent):
    return HEADER.format(w=w, h=h, w1=w - 1, h1=h - 1, font=FONT,
                         title=esc(title), sub=esc(sub), tx=w - 24, accent=accent)

# ---------------------------------------------------------------- cards
def gen_stats(d):
    w, h = 800, 128
    s = svg_open(w, h, "GITHUB METRICS", "auto-refreshed daily", "#ff7ad9")
    blocks = [("35" if not d["repos"] else str(d["repos"]), "public repositories", "#3be8ff"),
              (str(d["stars"]), "stars earned", "#ff7ad9"),
              (str(d["pr_merged"]), "PRs merged", "#52f0a8"),
              (str(d["contrib_total"]), "contributions / 12 mo", "#a78bfa")]
    for i, (val, label, color) in enumerate(blocks):
        x = 24 + i * 189
        s += f'<rect x="{x}" y="68" width="4" height="40" rx="2" fill="{color}" opacity="0.85"/>'
        s += f'<text x="{x + 16}" y="98" font-family="{FONT}" font-size="28" font-weight="700" fill="#ffffff">{val}</text>'
        s += f'<text x="{x + 16}" y="118" font-family="{FONT}" font-size="11.5" fill="#8b949e">{label}</text>'
    return s + "</svg>"


def gen_langs(d, n=6):
    colors = {"Python": "#3572A5", "Java": "#b07219", "HTML": "#e34c26", "JavaScript": "#f1e05a",
              "TypeScript": "#3178c6", "PLpgSQL": "#336790", "Kotlin": "#A97BFF", "C": "#555555",
              "GDScript": "#355570", "Assembly": "#6E4C13", "Rust": "#dea584", "Shell": "#89e051",
              "CSS": "#663399", "PowerShell": "#012456", "Dockerfile": "#384d54", "YARA": "#220000"}
    items = sorted(d["lang_counts"].items(), key=lambda x: -x[1])[:n]
    total = sum(d["lang_counts"].values()) or 1
    w, h = 800, 56 + 40 * len(items)
    s = svg_open(w, h, "PRIMARY LANGUAGE", "repositories owned (non-fork)", "#3be8ff")
    for i, (lang, cnt) in enumerate(items):
        y = 74 + i * 40
        pct = cnt / total * 100
        color = colors.get(lang, "#8b949e")
        s += f'<text x="24" y="{y + 12}" font-family="{FONT}" font-size="13" fill="#c9d1d9">{esc(lang)}</text>'
        s += f'<rect x="150" y="{y}" width="470" height="14" rx="7" fill="#161b22"/>'
        s += f'<rect x="150" y="{y}" width="{max(8, int(470 * cnt / max(i2[1] for i2 in items)))}" height="14" rx="7" fill="{color}"/>'
        s += f'<text x="640" y="{y + 12}" font-family="{FONT}" font-size="12.5" font-weight="600" fill="#ffffff">{cnt}</text>'
        s += f'<text x="668" y="{y + 12}" font-family="{FONT}" font-size="11.5" fill="#8b949e">{pct:.0f}%</text>'
    return s + "</svg>"


def gen_contrib(d):
    weeks = d["weekly"][-52:]
    w, h = 800, 176
    s = svg_open(w, h, "CONTRIBUTION PULSE", "last 52 weeks", "#52f0a8")
    if weeks:
        m = max(weeks)
        bw, gap = 13.4, 1.2
        for i, v in enumerate(weeks):
            x = 24 + i * (bw + gap)
            bh = max(2, int(v / m * 96)) if m else 2
            col = "#52f0a8" if v >= m * 0.7 else ("#3be8ff" if v >= m * 0.4 else "#243156")
            s += (f'<rect x="{x:.1f}" y="{140 - bh}" width="{bw:.1f}" height="{bh}" rx="2.5" fill="{col}">'
                  f'<title>{v} contributions</title></rect>')
        s += f'<text x="24" y="162" font-family="{FONT}" font-size="11.5" fill="#8b949e">peak week: {m}</text>'
        s += f'<text x="500" y="162" font-family="{FONT}" font-size="11.5" fill="#8b949e">total: {d["contrib_total"]}</text>'
    return s + "</svg>"


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    data = fetch_data()
    os.makedirs(ASSETS, exist_ok=True)
    out = {"stats.svg": gen_stats(data), "langs.svg": gen_langs(data), "contrib.svg": gen_contrib(data)}
    changed = []
    for fname, content in out.items():
        p = os.path.join(ASSETS, fname)
        old = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        if old != content:
            open(p, "w", encoding="utf-8").write(content)
            changed.append(fname)
    print(json.dumps({"changed": changed,
                      "repos": data["repos"], "stars": data["stars"],
                      "pr_merged": data["pr_merged"], "pr_open": data["pr_open"],
                      "contrib_total": data["contrib_total"],
                      "langs": data["lang_counts"]}, indent=2))
