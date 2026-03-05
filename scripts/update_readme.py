#!/usr/bin/env python3
"""Update README.md with visual pin cards for external contributions."""

import json
import os
import re
import subprocess
import sys

GITHUB_USERNAME = "benthamite"
EXCLUDE_OWNERS = {"benthamite", "tlon-team", "fstafforini"}
README_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
START_MARKER = "<!-- CONTRIBUTIONS:START -->"
END_MARKER = "<!-- CONTRIBUTIONS:END -->"
CARD_BASE = "https://github-readme-stats.vercel.app/api/pin/"
MAX_CARDS = 10

QUERY = """
{
  user(login: "%s") {
    repositoriesContributedTo(first: 100, contributionTypes: [COMMIT, PULL_REQUEST]) {
      nodes {
        nameWithOwner
        stargazerCount
        url
      }
    }
  }
}
""" % GITHUB_USERNAME


def fetch_contributions():
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    repos = data["data"]["user"]["repositoriesContributedTo"]["nodes"]

    external = [
        r
        for r in repos
        if r["nameWithOwner"].split("/")[0] not in EXCLUDE_OWNERS
        and r["stargazerCount"] > 0
    ]

    external.sort(key=lambda r: r["stargazerCount"], reverse=True)
    return external[:MAX_CARDS]


def format_cards(repos):
    lines = ["<p>"]
    for r in repos:
        owner, repo = r["nameWithOwner"].split("/")
        url = r["url"]
        card_url = f"{CARD_BASE}?username={owner}&repo={repo}&hide_border=true&theme=transparent"
        lines.append(
            f'  <a href="{url}"><img width="400" src="{card_url}" /></a>'
        )
    lines.append("</p>")
    return "\n".join(lines)


def update_readme(cards):
    with open(README_PATH) as f:
        content = f.read()

    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL
    )
    replacement = f"{START_MARKER}\n{cards}\n{END_MARKER}"
    new_content = pattern.sub(replacement, content)

    if content == new_content:
        print("No changes needed.")
        return False

    with open(README_PATH, "w") as f:
        f.write(new_content)
    print("README.md updated.")
    return True


def main():
    repos = fetch_contributions()
    cards = format_cards(repos)
    update_readme(cards)


if __name__ == "__main__":
    main()
