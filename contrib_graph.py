#!/usr/bin/env python3
"""GitHub katkı grafiğini SABİT eşiklerle SVG olarak çizer.

Kullanım:
    GH_TOKEN=... python contrib_graph.py <kullanici_adi> [cikti_klasoru]

Eşikleri aşağıdaki THRESHOLDS listesinden değiştir.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

# ---- AYARLAR -------------------------------------------------------------
# Her sayı bir tonun BAŞLANGICI: 1-3 -> ton 1, 4-9 -> ton 2, 10-19 -> ton 3, 20+ -> ton 4
THRESHOLDS = [1, 4, 10, 20]

THEMES = {
    "dark": {
        "bg": "#0d1117", "text": "#8b949e",
        "colors": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "bg": "#ffffff", "text": "#57606a",
        "colors": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}
CELL, GAP = 11, 3
LEFT, TOP = 32, 22
MONTHS_TR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
             "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
DAYS_TR = {1: "Pzt", 3: "Çar", 5: "Cum"}
# --------------------------------------------------------------------------

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GitHub API hatası: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]


def level(count):
    lv = 0
    for i, t in enumerate(THRESHOLDS, start=1):
        if count >= t:
            lv = i
    return lv


def legend_labels():
    labels = ["0"]
    for i, t in enumerate(THRESHOLDS):
        if i + 1 < len(THRESHOLDS):
            hi = THRESHOLDS[i + 1] - 1
            labels.append(str(t) if hi == t else f"{t}–{hi}")
        else:
            labels.append(f"{t}+")
    return labels


def render(total, weeks, theme):
    th = THEMES[theme]
    step = CELL + GAP
    width = LEFT + len(weeks) * step + 10
    height = TOP + 7 * step + 40
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" font-size="10">',
        f'<rect width="100%" height="100%" fill="{th["bg"]}" rx="6"/>',
    ]

    # Ay etiketleri: ayın ilk günü hangi haftadaysa oraya
    last_month = None
    for wi, week in enumerate(weeks):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month:
            if wi < len(weeks) - 2 or last_month is None:
                x = LEFT + wi * step
                out.append(f'<text x="{x}" y="{TOP - 8}" fill="{th["text"]}">{MONTHS_TR[first.month - 1]}</text>')
            last_month = first.month

    for wd, name in DAYS_TR.items():
        out.append(f'<text x="2" y="{TOP + wd * step + 9}" fill="{th["text"]}">{name}</text>')

    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            c = day["contributionCount"]
            x = LEFT + wi * step
            y = TOP + day["weekday"] * step
            color = th["colors"][level(c)]
            out.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}">'
                f'<title>{day["date"]}: {c} katkı</title></rect>'
            )

    # Alt satır: toplam + sabit eşikli lejant
    by = TOP + 7 * step + 18
    out.append(f'<text x="{LEFT}" y="{by}" fill="{th["text"]}">Son bir yılda {total} katkı</text>')
    labels = legend_labels()
    lx = width - 10 - len(labels) * 46
    for i, lab in enumerate(labels):
        x = lx + i * 46
        out.append(f'<rect x="{x}" y="{by - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{th["colors"][i]}"/>')
        out.append(f'<text x="{x + CELL + 3}" y="{by}" fill="{th["text"]}">{lab}</text>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit("Kullanım: python contrib_graph.py <kullanici_adi> [cikti_klasoru]")
    login = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN ortam değişkeni gerekli.")
    total, weeks = fetch(login, token)
    os.makedirs(out_dir, exist_ok=True)
    for theme in THEMES:
        path = os.path.join(out_dir, f"contrib-{theme}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(total, weeks, theme))
        print("yazıldı:", path)


if __name__ == "__main__":
    main()
