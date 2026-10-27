#!/usr/bin/env python3
"""Render the README's stat, language and pin cards as SVG files in cards/.

The cards used to be served by a public github-readme-stats instance, which
breaks whenever that instance runs out of quota. Rendering them here from the
GitHub API keeps the profile independent of any third-party service.

Pin cards are generated for every `cards/pin/OWNER/REPO.svg` the README refers
to, so adding a card to the README is enough to have it rendered.
"""

import json
import os
import re
import shutil
import subprocess
import textwrap
from html import escape

GITHUB_USERNAME = "benthamite"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(ROOT, "README.md")
CARDS_DIR = os.path.join(ROOT, "cards")
PIN_PATTERN = re.compile(r'src="cards/pin/([^/"]+)/([^/"]+)\.svg"')
LANGS_COUNT = 8

# Colours of github-readme-stats' "transparent" theme, which the cards imitated.
TITLE = "#006AFF"
TEXT = "#417E87"
ICON = "#0579C3"
FONT = "'Segoe UI', Ubuntu, Sans-Serif"

REPO_ICON = "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"
STAR_ICON = "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25zm0 2.445L6.615 5.5a.75.75 0 01-.564.41l-3.097.45 2.24 2.184a.75.75 0 01.216.664l-.528 3.084 2.769-1.456a.75.75 0 01.698 0l2.77 1.456-.53-3.084a.75.75 0 01.216-.664l2.24-2.183-3.096-.45a.75.75 0 01-.564-.41L8 2.694v.001z"
FORK_ICON = "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z"


def graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        args += ["-F", f"{name}={value}"]
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["data"]


def text_width(text, size):
    """Rough rendered width of TEXT at font SIZE, for laying out inline items."""
    return len(text) * size * 0.58


def svg(width, height, body):
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{ font: 600 18px {FONT}; fill: {TITLE} }}
    .description {{ font: 400 13px {FONT}; fill: {TEXT} }}
    .gray {{ font: 400 12px {FONT}; fill: {TEXT} }}
    .stat {{ font: 600 14px {FONT}; fill: {TEXT} }}
    .icon {{ fill: {ICON} }}
  </style>
{body}
</svg>
"""


def icon(path, x, y):
    return f'<svg class="icon" x="{x}" y="{y}" viewBox="0 0 16 16" width="16" height="16"><path fill-rule="evenodd" d="{path}"/></svg>'


# Pin cards

PIN_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    description
    stargazerCount
    forkCount
    primaryLanguage { name color }
  }
}
"""


def render_pin(repo):
    lines = textwrap.wrap(repo["description"] or "", 55)[:3] or [""]
    height = 120 + 18 * (len(lines) - 1)
    description = "".join(
        f'<tspan x="25" dy="{0 if i == 0 else 18}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    footer, x = [], 0
    language = repo["primaryLanguage"]
    if language:
        footer.append(
            f'<circle cx="{x}" cy="-5" r="6" fill="{language["color"] or TEXT}"/>'
            f'<text class="gray" x="{x + 15}">{escape(language["name"])}</text>'
        )
        x += 15 + text_width(language["name"], 12) + 20
    for path, count in ((STAR_ICON, repo["stargazerCount"]), (FORK_ICON, repo["forkCount"])):
        if count:
            footer.append(icon(path, x, -12) + f'<text class="gray" x="{x + 20}">{count}</text>')
            x += 20 + text_width(str(count), 12) + 25
    body = f"""  {icon(REPO_ICON, 25, 22)}
  <text class="header" x="50" y="35">{escape(repo["name"])}</text>
  <text class="description" y="68">{description}</text>
  <g transform="translate(30, {height - 20})">{"".join(footer)}</g>"""
    return svg(400, height, body)


# Stats and languages cards

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def render_stats(user):
    contributions = user["contributionsCollection"]
    rows = [
        ("Total stars earned", sum(r["stargazerCount"] for r in user["repositories"]["nodes"])),
        ("Commits (last year)", contributions["totalCommitContributions"] + contributions["restrictedContributionsCount"]),
        ("Total pull requests", user["pullRequests"]["totalCount"]),
        ("Total issues", user["issues"]["totalCount"]),
        ("Contributed to (last year)", user["repositoriesContributedTo"]["totalCount"]),
    ]
    body = [f'  <text class="header" x="25" y="35">{escape(GITHUB_USERNAME)}\'s GitHub stats</text>']
    for i, (label, value) in enumerate(rows):
        y = 75 + 25 * i
        body.append(f'  <text class="stat" x="25" y="{y}">{label}:</text><text class="stat" x="250" y="{y}">{value:,}</text>')
    return svg(400, 195, "\n".join(body))


def render_langs(user):
    sizes, colors = {}, {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or TEXT
    top = sorted(sizes.items(), key=lambda item: item[1], reverse=True)[:LANGS_COUNT]
    total = sum(size for _, size in top) or 1
    bar, x = [], 0.0
    for name, size in top:
        width = 250 * size / total
        bar.append(f'<rect x="{x:.2f}" y="0" width="{width:.2f}" height="8" fill="{colors[name]}"/>')
        x += width
    legend = []
    for i, (name, size) in enumerate(top):
        lx, ly = 150 * (i % 2), 25 * (i // 2)
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly + 6}" r="5" fill="{colors[name]}"/>'
            f'<text class="gray" x="{lx + 15}" y="{ly + 10}">{escape(name)} {100 * size / total:.2f}%</text>'
        )
    height = 105 + 25 * ((len(top) + 1) // 2)
    body = f"""  <text class="header" x="25" y="35">Most Used Languages</text>
  <mask id="bar"><rect x="0" y="0" width="250" height="8" fill="white" rx="5"/></mask>
  <g transform="translate(25, 55)"><g mask="url(#bar)">{"".join(bar)}</g></g>
  <g transform="translate(25, 80)">{"".join(legend)}</g>"""
    return svg(350, height, body)


def write(path, content):
    path = os.path.join(CARDS_DIR, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def main():
    with open(README_PATH) as f:
        pins = sorted(set(PIN_PATTERN.findall(f.read())))
    shutil.rmtree(os.path.join(CARDS_DIR, "pin"), ignore_errors=True)
    for owner, name in pins:
        repo = graphql(PIN_QUERY, owner=owner, name=name)["repository"]
        write(f"pin/{owner}/{name}.svg", render_pin(repo))
    user = graphql(STATS_QUERY, login=GITHUB_USERNAME)["user"]
    write("stats.svg", render_stats(user))
    write("top-langs.svg", render_langs(user))
    print(f"Rendered {len(pins)} pin cards, stats and languages.")


if __name__ == "__main__":
    main()
