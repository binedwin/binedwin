#!/usr/bin/env python3
import json, os, urllib.request, random
from collections import Counter
from pathlib import Path

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "binedwin")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "binedwin-profile-assets",
}
OUT = Path("output")
OUT.mkdir(exist_ok=True)

def request_json(url, data=None, extra_headers=None):
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def graphql(query, variables):
    payload = json.dumps({"query": query, "variables": variables}).encode()
    return request_json(
        "https://api.github.com/graphql",
        data=payload,
        extra_headers={"Content-Type": "application/json"},
    )["data"]

def generate_galaxy():
    query = '''
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
    '''
    cal = graphql(query, {"login": USERNAME})["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]

    left, top, right = 74, 105, 1120
    xgap = (right-left) / max(len(weeks)-1, 1)
    ygap = 35
    levels = {"NONE":0,"FIRST_QUARTILE":1,"SECOND_QUARTILE":2,"THIRD_QUARTILE":3,"FOURTH_QUARTILE":4}
    colors = ["#263244","#67E8F9","#7DD3FC","#A78BFA","#F8FAFC"]
    radii = [1.3,2.3,3.0,3.7,4.6]

    stars = []
    active = []
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            lvl = levels.get(day["contributionLevel"], 0)
            x = left + wi*xgap
            y = top + di*ygap
            cnt = day["contributionCount"]
            opacity = 0.22 if lvl == 0 else 0.72 + lvl*0.06
            stars.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radii[lvl]}" fill="{colors[lvl]}" opacity="{opacity:.2f}">'
                f'<title>{day["date"]} - {cnt} contributions</title></circle>'
            )
            if lvl > 0:
                active.append((x,y))

    lines = []
    for i in range(len(active)-1):
        x1,y1 = active[i]
        x2,y2 = active[i+1]
        d = ((x2-x1)**2 + (y2-y1)**2)**0.5
        if d < 58 and len(lines) < 90:
            lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#7DD3FC" stroke-opacity=".12" stroke-width=".8"/>')

    random.seed(73)
    bg = []
    for _ in range(60):
        x = random.randint(20,1180)
        y = random.randint(18,372)
        r = random.choice([0.55,0.7,0.9,1.1])
        op = random.choice([0.14,0.18,0.24,0.32])
        bg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" opacity="{op}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="390" viewBox="0 0 1200 390">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#030712"/><stop offset=".58" stop-color="#0B1020"/><stop offset="1" stop-color="#111827"/>
</linearGradient>
<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#7DD3FC" stop-opacity="0"/><stop offset=".72" stop-color="#7DD3FC" stop-opacity=".5"/><stop offset="1" stop-color="#FFFFFF"/>
</linearGradient>
</defs>
<rect width="1200" height="390" rx="24" fill="url(#sky)"/>
{''.join(bg)}
<text x="74" y="48" fill="#F8FAFC" font-family="Arial,sans-serif" font-size="24" font-weight="700">CONTRIBUTION GALAXY</text>
<text x="74" y="73" fill="#94A3B8" font-family="monospace" font-size="12">{USERNAME} - {total} contributions in the last year</text>
<g>{''.join(lines)}</g>
<g>{''.join(stars)}</g>
<g>
  <animateTransform attributeName="transform" type="translate" values="-250 -40;1330 330;1330 330" keyTimes="0;0.16;1" dur="12s" begin="3s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.03;.16;1" dur="12s" begin="3s" repeatCount="indefinite"/>
  <line x1="0" y1="0" x2="190" y2="0" stroke="url(#trail)" stroke-width="3" stroke-linecap="round"/>
  <circle cx="190" cy="0" r="3.4" fill="#FFFFFF"/>
</g>
<text x="1125" y="362" text-anchor="end" fill="#64748B" font-family="monospace" font-size="11">Every commit becomes a star.</text>
</svg>'''
    (OUT/"contribution-galaxy.svg").write_text(svg, encoding="utf-8")
    return total

def generate_signals(total):
    profile = request_json(f"https://api.github.com/users/{USERNAME}")
    repos = request_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&sort=updated")

    stars = sum(r.get("stargazers_count",0) for r in repos)
    forks = sum(r.get("forks_count",0) for r in repos)
    langs = Counter()

    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            langs.update(request_json(repo["languages_url"]))
        except Exception:
            pass

    total_lang = sum(langs.values()) or 1
    top = langs.most_common(5)
    palette = ["#7DD3FC","#A78BFA","#34D399","#F59E0B","#FB7185"]

    x = 72
    segments = []
    labels = []
    for i,(lang,count) in enumerate(top):
        pct = count/total_lang
        w = max(4,500*pct)
        segments.append(f'<rect x="{x:.1f}" y="232" width="{w:.1f}" height="12" rx="6" fill="{palette[i]}"/>')
        lx = 72 + (i%3)*185
        ly = 272 + (i//3)*28
        labels.append(f'<circle cx="{lx}" cy="{ly-4}" r="5" fill="{palette[i]}"/><text x="{lx+12}" y="{ly}" fill="#CBD5E1" font-family="Arial,sans-serif" font-size="12">{lang} {pct*100:.1f}%</text>')
        x += w

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="330" viewBox="0 0 1200 330">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#030712"/><stop offset=".6" stop-color="#0B1020"/><stop offset="1" stop-color="#111827"/></linearGradient></defs>
<rect width="1200" height="330" rx="24" fill="url(#bg)"/>
<text x="72" y="54" fill="#F8FAFC" font-family="Arial,sans-serif" font-size="25" font-weight="700">GITHUB SIGNALS</text>
<text x="72" y="78" fill="#94A3B8" font-family="monospace" font-size="12">Generated directly from GitHub API</text>
<rect x="72" y="112" width="240" height="78" rx="15" fill="#111827" stroke="#1E293B"/>
<text x="92" y="140" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">PUBLIC REPOSITORIES</text>
<text x="92" y="174" fill="#7DD3FC" font-family="Arial,sans-serif" font-size="30" font-weight="700">{profile.get("public_repos",0)}</text>
<rect x="330" y="112" width="240" height="78" rx="15" fill="#111827" stroke="#1E293B"/>
<text x="350" y="140" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">CONTRIBUTIONS / YEAR</text>
<text x="350" y="174" fill="#A78BFA" font-family="Arial,sans-serif" font-size="30" font-weight="700">{total}</text>
<rect x="588" y="112" width="240" height="78" rx="15" fill="#111827" stroke="#1E293B"/>
<text x="608" y="140" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">FOLLOWERS</text>
<text x="608" y="174" fill="#34D399" font-family="Arial,sans-serif" font-size="30" font-weight="700">{profile.get("followers",0)}</text>
<rect x="846" y="112" width="282" height="78" rx="15" fill="#111827" stroke="#1E293B"/>
<text x="866" y="140" fill="#94A3B8" font-family="Arial,sans-serif" font-size="12">STARS / FORKS</text>
<text x="866" y="174" fill="#F8FAFC" font-family="Arial,sans-serif" font-size="26" font-weight="700">{stars} stars   {forks} forks</text>
<text x="72" y="220" fill="#F8FAFC" font-family="Arial,sans-serif" font-size="14" font-weight="700">Language Orbit</text>
<rect x="72" y="232" width="500" height="12" rx="6" fill="#1E293B"/>
{''.join(segments)}
{''.join(labels)}
<text x="1128" y="303" text-anchor="end" fill="#64748B" font-family="monospace" font-size="11">Self-hosted - no external stats service</text>
</svg>'''
    (OUT/"github-signals.svg").write_text(svg, encoding="utf-8")

if __name__ == "__main__":
    total = generate_galaxy()
    generate_signals(total)
    print("updated profile assets")
