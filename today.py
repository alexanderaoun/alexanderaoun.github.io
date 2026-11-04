"""Builds dark_mode.svg and light_mode.svg for the GitHub profile README.

Run by .github/workflows/build.yml once a day. Locally: python today.py
Set GITHUB_TOKEN (any token, or the Actions token) to fetch live stats;
without one it falls back to the public REST API.
"""
import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

USER = "alexanderaoun"
START = dt.date(2023, 9, 1)  # first semester of engineering at EPFL
WIDTH = 58                   # characters in the info column

ART = open(os.path.join(os.path.dirname(__file__), "art.txt"), encoding="utf-8").read().split("\n")

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", art="#5fa585", key="#6cc39d", value="#e6edf3",
                 dot="#3d4b44", head="#e6edf3", add="#3fb950"),
    "light": dict(bg="#f6f8fa", border="#d0d7de", art="#4f7d68", key="#0b6a4b", value="#1f2328",
                  dot="#b8c4bd", head="#1f2328", add="#1a7f37"),
}


def api(url, token, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-builder"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN")
    out = {"repos": "?", "stars": "?", "followers": "?", "commits": "?"}
    try:
        if token:
            q = """query($login:String!){ user(login:$login){
              followers{totalCount}
              repositories(ownerAffiliations:OWNER, first:100, privacy:PUBLIC){ totalCount nodes{ stargazerCount } }
              contributionsCollection{ totalCommitContributions }
            }}"""
            body = json.dumps({"query": q, "variables": {"login": USER}}).encode()
            u = api("https://api.github.com/graphql", token, body)["data"]["user"]
            out["repos"] = u["repositories"]["totalCount"]
            out["stars"] = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
            out["followers"] = u["followers"]["totalCount"]
            out["commits"] = u["contributionsCollection"]["totalCommitContributions"]
        else:
            u = api(f"https://api.github.com/users/{USER}", None)
            repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100", None)
            out["repos"] = u["public_repos"]
            out["followers"] = u["followers"]
            out["stars"] = sum(r["stargazers_count"] for r in repos)
    except Exception as e:  # keep the card building even if the API is unreachable
        print("stats unavailable:", e)
    return out


def uptime(today):
    months = (today.year - START.year) * 12 + today.month - START.month
    y, m = divmod(months, 12)
    return f"{y} year{'s' * (y != 1)}, {m} month{'s' * (m != 1)}"


def info_lines(s, today):
    """Each entry: ('kv', key, value) | ('head', title) | ('blank',) | ('pair', k1, v1, k2, v2)."""
    return [
        ("title", "alexander@aoun"),
        ("kv", "OS", "macOS, Linux, ESP32"),
        ("kv", "Uptime", uptime(today) + " of engineering"),
        ("kv", "Host", "ETH Zurich, MSc EEIT"),
        ("kv", "Kernel", "Biomedical Electronics"),
        ("kv", "IDE", "MATLAB, KiCad, Altium, Cadence"),
        ("blank",),
        ("kv", "Languages.Programming", "Python, C, C++, MATLAB"),
        ("kv", "Languages.Hardware", "SystemVerilog, SPICE"),
        ("kv", "Languages.Real", "French, English, Arabic, German"),
        ("blank",),
        ("kv", "Hobbies.Building", "Exoskeletons, drones, race cars"),
        ("kv", "Hobbies.Outdoor", "Scuba, skiing, trail running"),
        ("head", "Experience"),
        ("kv", "Sensors", "TE Connectivity, research intern"),
        ("kv", "Rocketry", "EPFL Rocket Team, electronics lead"),
        ("head", "Contact"),
        ("kv", "Email", "alexanderaoun0@gmail.com"),
        ("kv", "LinkedIn", "alexander-aoun"),
        ("kv", "Website", "alexanderaoun.github.io"),
    ]


def tspan(text, color):
    return f'<tspan fill="{color}">{escape(text)}</tspan>'


def render(s, theme, today):
    t = THEMES[theme]
    lh, fs = 20, 15
    lines = info_lines(s, today)
    rows = len(lines)
    height = 22 + rows * lh
    art_x, info_x = 22, 392
    out = []
    # strip blank rows at top and bottom, then fit the art to the height of the info column
    art = list(ART)
    while art and not art[0].strip(): art.pop(0)
    while art and not art[-1].strip(): art.pop()
    span = (len(lines) - 1) * lh
    alh = span / max(1, len(art) - 1)
    cols = max(len(r) for r in art)
    afs = round(min(alh * 0.82, (info_x - art_x - 18) / (cols * 0.602)), 2)
    for i, row in enumerate(art):
        y = round(30 + i * alh, 2)
        out.append(f'<text x="{art_x}" y="{y}" font-size="{afs}px" fill="{t["art"]}">{escape(row)}</text>')
    for i, ln in enumerate(lines):
        y = 30 + i * lh
        kind = ln[0]
        if kind == "title":
            rule = " " + "─" * (WIDTH - len(ln[1]) - 1)
            body = tspan(ln[1], t["head"]) + tspan(rule, t["dot"])
        elif kind == "head":
            rule = " " + "─" * (WIDTH - len(ln[1]) - 3)
            body = tspan("- ", t["dot"]) + tspan(ln[1], t["head"]) + tspan(rule, t["dot"])
        elif kind == "blank":
            body = tspan(".", t["dot"])
        elif kind == "kv":
            key, val = ln[1] + ":", ln[2]
            dots = WIDTH - 2 - len(key) - len(val) - 2
            body = tspan(". ", t["dot"]) + tspan(key, t["key"]) + tspan(" " + "." * max(1, dots) + " ", t["dot"]) + tspan(val, t["value"])
        else:  # pair
            half = (WIDTH - 5) // 2
            k1, v1, k2, v2 = ln[1] + ":", ln[2], ln[3] + ":", ln[4]
            d1 = half - len(k1) - len(v1) - 2
            d2 = half - len(k2) - len(v2) - 2
            body = (tspan(". ", t["dot"]) + tspan(k1, t["key"]) + tspan(" " + "." * max(1, d1) + " ", t["dot"]) + tspan(v1, t["add"])
                    + tspan(" | ", t["dot"]) + tspan(k2, t["key"]) + tspan(" " + "." * max(1, d2) + " ", t["dot"]) + tspan(v2, t["add"]))
        out.append(f'<text x="{info_x}" y="{y}">{body}</text>')
    width = info_x + int(WIDTH * fs * 0.6) + 24
    return f'''<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,'DejaVu Sans Mono','Courier New',monospace" width="{width}px" height="{height}px" font-size="{fs}px">
<style>text {{ white-space: pre; }} @font-face {{ font-family: ConsolasFallback; src: local('Consolas'), local('Menlo'); }}</style>
<rect width="{width}px" height="{height}px" fill="{t['bg']}" rx="0"/>
<rect x="0.5" y="0.5" width="{width - 1}px" height="{height - 1}px" fill="none" stroke="{t['border']}"/>
{chr(10).join(out)}
</svg>
'''


def main():
    today = dt.date.today()
    s = {}
    for theme in THEMES:
        with open(f"{theme}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(s, theme, today))
    print("built", s)


if __name__ == "__main__":
    main()
