#!/usr/bin/env python3
import json, os, urllib.request, random
from pathlib import Path

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "binedwin")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path("output/contribution-galaxy.svg")
OUT.parent.mkdir(parents=True, exist_ok=True)

QUERY = """
query($login:String!) {
  user(login:$login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
            date
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "contribution-galaxy-generator",
    },
)
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.load(r)

if data.get("errors"):
    raise RuntimeError(data["errors"])

cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
total = cal["totalContributions"]

left, top, ygap = 72, 96, 34
xgap = 1000 / max(len(weeks) - 1, 1)
levels = {"NONE":0, "FIRST_QUARTILE":1, "SECOND_QUARTILE":2, "THIRD_QUARTILE":3, "FOURTH_QUARTILE":4}
colors = ["#334155","#67E8F9","#7DD3FC","#A78BFA","#F8FAFC"]
radii = [1.2,2.2,2.8,3.5,4.3]

nodes, lines = [], []
active_by_row = {}

for wi, week in enumerate(weeks):
    for di, day in enumerate(week["contributionDays"]):
        level = levels.get(day["contributionLevel"], 0)
        count = day["contributionCount"]
        x = left + wi * xgap
        y = top + di * ygap
        opacity = 0.18 if level == 0 else min(0.55 + level * 0.1, 1)
        nodes.append(
            f'<circle class="cstar l{level}" cx="{x:.1f}" cy="{y:.1f}" r="{radii[level]}" '
            f'fill="{colors[level]}" opacity="{opacity:.2f}"><title>{day["date"]} · {count} contributions</title></circle>'
        )
        if level:
            active_by_row.setdefault(di, []).append((x, y))

for row, pts in active_by_row.items():
    pts.sort()
    for a, b in zip(pts, pts[1:]):
        if b[0] - a[0] <= xgap * 3.2:
            lines.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')

random.seed(42)
bg = []
for _ in range(90):
    x = random.randint(20,1180)
    y = random.randint(20,410)
    r = random.choice([0.6,0.8,1.0,1.2])
    bg.append(f'<circle class="bg" cx="{x}" cy="{y}" r="{r}"/>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="430" viewBox="0 0 1200 430">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#030712"/><stop offset=".55" stop-color="#0B1020"/><stop offset="1" stop-color="#111827"/></linearGradient>
<style>
.bg{{fill:#fff;opacity:.22;animation:tw 5s ease-in-out infinite}}
.cstar{{animation:pulse 5.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
.l0{{animation:none}}
.links{{stroke:#7DD3FC;stroke-width:.65;stroke-opacity:.13}}
.meteor{{animation:shoot 11s linear infinite;transform-box:view-box;transform-origin:center}}
@keyframes tw{{0%,100%{{opacity:.10}}50%{{opacity:.5}}}}
@keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.22)}}}}
@keyframes shoot{{0%,70%{{transform:translate(-420px,-120px);opacity:0}}73%{{opacity:1}}83%{{transform:translate(1320px,370px);opacity:0}}100%{{transform:translate(1320px,370px);opacity:0}}}}
</style>
</defs>
<rect width="1200" height="430" rx="24" fill="url(#sky)"/>
{''.join(bg)}
<text x="72" y="48" fill="#F8FAFC" font-family="Arial" font-size="24" font-weight="700">CONTRIBUTION GALAXY</text>
<text x="72" y="72" fill="#94A3B8" font-family="monospace" font-size="12">{USERNAME} · {total} contributions in the last year</text>
<g class="links">{''.join(lines)}</g>
<g>{''.join(nodes)}</g>
<g class="meteor"><line x1="0" y1="0" x2="210" y2="0" stroke="#7DD3FC" stroke-opacity=".65" stroke-width="3"/><circle cx="210" cy="0" r="3.5" fill="#fff"/></g>
<text x="1128" y="402" text-anchor="end" fill="#64748B" font-family="monospace" font-size="11">Every commit becomes a star.</text>
</svg>"""

OUT.write_text(svg, encoding="utf-8")
print(f"updated {OUT}")
