#!/usr/bin/env python3
"""Private repolardaki test-hub sonuçlarını herkese açık rozet JSON'una çevirir.

shields.io "endpoint" rozeti bu JSON'u okur. GH_TOKEN, ilgili private
repolarda en az "Actions: read" izni olan bir token olmalı.
"""
import json
import os
import sys
import urllib.request

OWNER = "ferhanburak"
# rozet dosyası adı -> (repo, workflow dosyası)
BADGES = {
    "tracksnap-tests": ("carfollow", "test-hub.yml"),
}


def latest_conclusion(repo, workflow, token):
    url = (f"https://api.github.com/repos/{OWNER}/{repo}/actions/workflows/"
           f"{workflow}/runs?branch=main&status=completed&per_page=1")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as r:
        runs = json.load(r)["workflow_runs"]
    return runs[0]["conclusion"] if runs else None


def badge(conclusion):
    if conclusion == "success":
        return {"message": "passing", "color": "brightgreen"}
    if conclusion in ("failure", "timed_out"):
        return {"message": "failing", "color": "red"}
    return {"message": conclusion or "unknown", "color": "lightgrey"}


def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("GH_TOKEN yok, rozetler güncellenmedi.")
        return
    os.makedirs("assets", exist_ok=True)
    for name, (repo, wf) in BADGES.items():
        try:
            c = latest_conclusion(repo, wf, token)
        except Exception as e:  # erişim yoksa eski rozeti koru
            print(f"{repo}: okunamadı ({e}), atlandı", file=sys.stderr)
            continue
        # Same look as GitHub's own workflow badge (used for the public repos).
        data = {"schemaVersion": 1, "label": "test-hub", "namedLogo": "github", "logoColor": "white", **badge(c)}
        with open(f"assets/{name}.json", "w") as f:
            json.dump(data, f)
        print(f"{name}: {data['message']}")


if __name__ == "__main__":
    main()
