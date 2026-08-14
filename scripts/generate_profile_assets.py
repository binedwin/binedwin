#!/usr/bin/env python3
import json
import os
import random
import urllib.request
from collections import Counter
from html import escape
from pathlib import Path

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "binedwin")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

OUT = Path("output")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "binedwin-profile-assets",
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def request_json(url, data=None, extra_headers=None):
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def graphql(query, variables):
    if not TOKEN:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN is required for GitHub GraphQL")

    payload = json.dumps({
        "query": query,
        "variables": variables,
    }).encode("utf-8")

    result = request_json(
        "https://api.github.com/graphql",
        data=payload,
        extra_headers={"Content-Type": "application/json"},
    )

    if result.get("errors"):
        raise RuntimeError(result["errors"])

    return result["data"]


def get_contribution_calendar():
    query = '''
    query($login: String!) {
      user(login: $login) {
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

    return graphql(query, {"login": USERNAME})[
        "user"
    ]["contributionsCollection"]["contributionCalendar"]


def generate_pixel_robot_starfield():
    width = 1200
    height = 390

    left = 92
    top = 105
    cell = 12
    gap = 6
    pitch = cell + gap

    colors = [
        "#111827",
        "#164E63",
        "#0E7490",
        "#22D3EE",
        "#E0F2FE",
    ]

    grid_weeks = 53
    random.seed(20260814)
    cells = []

    for week_index in range(grid_weeks):
        for day_index in range(7):
            level = random.choices(
                range(5),
                weights=(50, 24, 14, 8, 4),
                k=1,
            )[0]

            x = left + week_index * pitch
            y = top + day_index * pitch

            duration = random.uniform(1.8, 5.2)
            delay = random.uniform(-5.0, 0.0)
            low_opacity = random.uniform(0.18, 0.38)
            high_opacity = random.uniform(0.72, 1.0)
            glow = ' filter="url(#cellGlow)"' if level >= 3 else ""

            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{colors[level]}"{glow} opacity="{low_opacity:.2f}">'
                f'<animate attributeName="opacity" '
                f'values="{low_opacity:.2f};{high_opacity:.2f};{low_opacity:.2f}" '
                f'dur="{duration:.2f}s" begin="{delay:.2f}s" '
                f'repeatCount="indefinite"/>'
                f'</rect>'
            )

    random.seed(2026)
    stars = []

    for _ in range(75):
        x = random.randint(25, 1175)
        y = random.randint(18, 360)
        radius = random.choice([0.55, 0.7, 0.9, 1.1])
        opacity = random.choice([0.12, 0.18, 0.25, 0.34])

        stars.append(
            f'<circle cx="{x}" cy="{y}" r="{radius}" '
            f'fill="#FFFFFF" opacity="{opacity}"/>'
        )

    robot_y = top + 7 * pitch + 38
    start_x = left - 10
    end_x = left + (grid_weeks - 1) * pitch + cell

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{width}" height="{height}" viewBox="0 0 {width} {height}">

<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#020617"/>
    <stop offset=".55" stop-color="#08111F"/>
    <stop offset="1" stop-color="#111827"/>
  </linearGradient>

  <linearGradient id="horizon" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>
    <stop offset=".5" stop-color="#22D3EE" stop-opacity=".28"/>
    <stop offset="1" stop-color="#A78BFA" stop-opacity="0"/>
  </linearGradient>

  <filter id="cellGlow" x="-200%" y="-200%" width="500%" height="500%">
    <feGaussianBlur stdDeviation="2.1" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>

  <filter id="robotGlow" x="-200%" y="-200%" width="500%" height="500%">
    <feGaussianBlur stdDeviation="2.8" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<rect width="{width}" height="{height}" rx="26" fill="url(#sky)"/>

{''.join(stars)}

<text x="72" y="46"
  fill="#F8FAFC"
  font-family="Arial,sans-serif"
  font-size="24"
  font-weight="700">
  PIXEL ROBOT STAR WALK
</text>

<text x="72" y="72"
  fill="#94A3B8"
  font-family="monospace"
  font-size="12">
  {escape(USERNAME)} - a randomly twinkling pixel night
</text>

<g>
  {''.join(cells)}
</g>

<line x1="70" y1="{robot_y + 24}" x2="1130" y2="{robot_y + 24}"
  stroke="url(#horizon)" stroke-width="1.4"/>

<g filter="url(#robotGlow)">

  <animateMotion
    path="M {start_x} {robot_y} L {end_x} {robot_y} L {start_x} {robot_y}"
    dur="26s"
    repeatCount="indefinite"
    calcMode="linear"/>

  <rect x="-2" y="-30" width="4" height="6" rx="1" fill="#94A3B8"/>
  <rect x="-3" y="-34" width="6" height="5" rx="2" fill="#22D3EE">
    <animate attributeName="opacity"
      values=".35;1;.35"
      dur="1.1s"
      repeatCount="indefinite"/>
  </rect>

  <rect x="-14" y="-25" width="28" height="20" rx="4"
    fill="#E2E8F0" stroke="#7DD3FC" stroke-width="1"/>

  <rect x="-8" y="-18" width="4" height="4" rx="1" fill="#0EA5E9"/>
  <rect x="4" y="-18" width="4" height="4" rx="1" fill="#0EA5E9"/>
  <rect x="-6" y="-10" width="12" height="2" rx="1" fill="#64748B"/>

  <rect x="-11" y="-3" width="22" height="18" rx="3"
    fill="#334155" stroke="#A78BFA" stroke-width="1"/>

  <rect x="-4" y="2" width="8" height="5" rx="1" fill="#22D3EE">
    <animate attributeName="opacity"
      values=".3;1;.3"
      dur=".9s"
      repeatCount="indefinite"/>
  </rect>

  <rect x="-18" y="-1" width="5" height="14" rx="2" fill="#94A3B8">
    <animate attributeName="y"
      values="-1;3;-1"
      dur=".48s"
      repeatCount="indefinite"/>
  </rect>

  <rect x="13" y="3" width="5" height="14" rx="2" fill="#94A3B8">
    <animate attributeName="y"
      values="3;-1;3"
      dur=".48s"
      repeatCount="indefinite"/>
  </rect>

  <rect x="-9" y="15" width="6" height="13" rx="2" fill="#CBD5E1">
    <animate attributeName="y"
      values="15;19;15"
      dur=".48s"
      repeatCount="indefinite"/>
  </rect>

  <rect x="3" y="19" width="6" height="13" rx="2" fill="#CBD5E1">
    <animate attributeName="y"
      values="19;15;19"
      dur=".48s"
      repeatCount="indefinite"/>
  </rect>

  <circle cx="-25" cy="22" r="2" fill="#67E8F9">
    <animate attributeName="opacity"
      values="0;.8;0"
      dur=".8s"
      repeatCount="indefinite"/>
  </circle>

  <circle cx="-35" cy="18" r="1.3" fill="#C4B5FD">
    <animate attributeName="opacity"
      values=".8;0;.8"
      dur="1.2s"
      repeatCount="indefinite"/>
  </circle>

</g>

<g opacity="0">
  <animateMotion
    path="M -160 45 L 1240 230"
    dur="10s"
    begin="2s"
    repeatCount="indefinite"/>

  <animate attributeName="opacity"
    values="0;1;0;0"
    keyTimes="0;.03;.16;1"
    dur="10s"
    begin="2s"
    repeatCount="indefinite"/>

  <line x1="0" y1="0" x2="120" y2="0"
    stroke="#7DD3FC"
    stroke-opacity=".55"
    stroke-width="2.5"/>

  <circle cx="120" cy="0" r="3" fill="#FFFFFF"/>
</g>

<text x="1125" y="365"
  text-anchor="end"
  fill="#64748B"
  font-family="monospace"
  font-size="11">
  Every commit becomes a step.
</text>

</svg>'''

    (OUT / "pixel-robot-contributions.svg").write_text(svg, encoding="utf-8")


def generate_github_signals(calendar):
    total_contributions = calendar["totalContributions"]

    profile = request_json(
        f"https://api.github.com/users/{USERNAME}"
    )

    repos = request_json(
        f"https://api.github.com/users/{USERNAME}/repos"
        "?per_page=100&type=owner&sort=updated"
    )

    total_stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repos
    )

    total_forks = sum(
        repo.get("forks_count", 0)
        for repo in repos
    )

    languages = Counter()

    for repo in repos:
        if repo.get("fork"):
            continue

        try:
            language_bytes = request_json(repo["languages_url"])
            languages.update(language_bytes)
        except Exception:
            pass

    language_total = sum(languages.values()) or 1
    top_languages = languages.most_common(5)

    palette = [
        "#7DD3FC",
        "#A78BFA",
        "#34D399",
        "#F59E0B",
        "#FB7185",
    ]

    language_segments = []
    language_labels = []

    current_x = 650
    bar_width = 430

    for index, (language, count) in enumerate(top_languages):
        ratio = count / language_total
        segment_width = max(4, bar_width * ratio)

        language_segments.append(
            f'<rect x="{current_x:.1f}" y="207" '
            f'width="{segment_width:.1f}" height="12" rx="6" '
            f'fill="{palette[index]}"/>'
        )

        label_y = 247 + index * 22

        language_labels.append(
            f'<circle cx="650" cy="{label_y - 4}" r="4.5" '
            f'fill="{palette[index]}"/>'
            f'<text x="663" y="{label_y}" '
            f'fill="#CBD5E1" font-family="Arial,sans-serif" '
            f'font-size="12">{escape(language)} {ratio * 100:.1f}%</text>'
        )

        current_x += segment_width

    if not top_languages:
        language_labels.append(
            '<text x="650" y="253" fill="#94A3B8" '
            'font-family="Arial,sans-serif" font-size="12">'
            'No public language data yet</text>'
        )

    metrics = [
        ("REPOSITORIES", profile.get("public_repos", 0), "#7DD3FC", 145),
        ("CONTRIBUTIONS", total_contributions, "#A78BFA", 300),
        ("FOLLOWERS", profile.get("followers", 0), "#34D399", 455),
    ]

    metric_nodes = []

    for label, value, color, x in metrics:
        metric_nodes.append(
            f'''
<g>
  <circle cx="{x}" cy="178" r="54"
    fill="#0F172A" stroke="{color}" stroke-opacity=".55"/>

  <circle cx="{x}" cy="178" r="54"
    fill="none" stroke="{color}" stroke-width="1.5" opacity=".45">
    <animate attributeName="r"
      values="54;64;54"
      dur="3.2s"
      repeatCount="indefinite"/>
    <animate attributeName="opacity"
      values=".5;0;.5"
      dur="3.2s"
      repeatCount="indefinite"/>
  </circle>

  <text x="{x}" y="172"
    text-anchor="middle"
    fill="{color}"
    font-family="Arial,sans-serif"
    font-size="27"
    font-weight="700">
    {value}
  </text>

  <text x="{x}" y="198"
    text-anchor="middle"
    fill="#94A3B8"
    font-family="Arial,sans-serif"
    font-size="10">
    {label}
  </text>
</g>'''
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="1200" height="340" viewBox="0 0 1200 340">

<defs>
  <linearGradient id="signalsBg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#020617"/>
    <stop offset=".55" stop-color="#08111F"/>
    <stop offset="1" stop-color="#111827"/>
  </linearGradient>

  <linearGradient id="scan" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#22D3EE" stop-opacity="0"/>
    <stop offset=".5" stop-color="#22D3EE" stop-opacity=".85"/>
    <stop offset="1" stop-color="#22D3EE" stop-opacity="0"/>
  </linearGradient>
</defs>

<rect width="1200" height="340" rx="26" fill="url(#signalsBg)"/>

<text x="72" y="50"
  fill="#F8FAFC"
  font-family="Arial,sans-serif"
  font-size="24"
  font-weight="700">
  GITHUB SIGNALS
</text>

<text x="72" y="75"
  fill="#94A3B8"
  font-family="monospace"
  font-size="12">
  Live profile data generated by my own GitHub Actions workflow
</text>

{''.join(metric_nodes)}

<g>
  <circle cx="570" cy="178" r="7" fill="#F8FAFC"/>
  <circle cx="570" cy="178" r="16" fill="none" stroke="#7DD3FC" opacity=".5">
    <animate attributeName="r"
      values="10;28;10"
      dur="2.4s"
      repeatCount="indefinite"/>
    <animate attributeName="opacity"
      values=".8;0;.8"
      dur="2.4s"
      repeatCount="indefinite"/>
  </circle>
</g>

<text x="650" y="155"
  fill="#F8FAFC"
  font-family="Arial,sans-serif"
  font-size="15"
  font-weight="700">
  LANGUAGE ORBIT
</text>

<text x="650" y="181"
  fill="#94A3B8"
  font-family="Arial,sans-serif"
  font-size="12">
  {total_stars} stars / {total_forks} forks
</text>

<rect x="650" y="207" width="430" height="12" rx="6" fill="#1E293B"/>

{''.join(language_segments)}

<rect x="650" y="202" width="50" height="22" rx="11" fill="url(#scan)" opacity=".45">
  <animate attributeName="x"
    values="650;1030;650"
    dur="5s"
    repeatCount="indefinite"/>
</rect>

{''.join(language_labels)}

<text x="1125" y="315"
  text-anchor="end"
  fill="#64748B"
  font-family="monospace"
  font-size="11">
  self-hosted SVG / no external stats service
</text>

</svg>'''

    (OUT / "github-signals.svg").write_text(svg, encoding="utf-8")


def main():
    calendar = get_contribution_calendar()

    generate_pixel_robot_starfield()
    generate_github_signals(calendar)

    print("Updated:")
    print(" - output/pixel-robot-contributions.svg")
    print(" - output/github-signals.svg")


if __name__ == "__main__":
    main()
