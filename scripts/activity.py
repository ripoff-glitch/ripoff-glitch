import json
import os
import sys
import urllib.request
from datetime import date, timedelta

user, out = sys.argv[1], sys.argv[2]
days = 31

query = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
    headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
)
weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
counts = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}

today = date.today()
series = [(today - timedelta(days=i)) for i in range(days - 1, -1, -1)]
values = [counts.get(d.isoformat(), 0) for d in series]

W, H = 900, 320
L, R, T, B = 60, 30, 60, 50
pw, ph = W - L - R, H - T - B
top = max(max(values), 4)
step = -(-top // 4)
top = step * 4

def x(i): return L + pw * i / (days - 1)
def y(v): return T + ph * (1 - v / top)

pts = [(x(i), y(v)) for i, v in enumerate(values)]
line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
area = f"M{L},{T + ph} L" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + f" L{L + pw},{T + ph} Z"

grid = "".join(
    f'<line x1="{L}" y1="{y(v):.1f}" x2="{L + pw}" y2="{y(v):.1f}" class="g"/>'
    f'<text x="{L - 12}" y="{y(v) + 4:.1f}" text-anchor="end" class="t">{v}</text>'
    for v in range(0, top + 1, step)
)
xlabels = "".join(
    f'<text x="{x(i):.1f}" y="{T + ph + 22}" text-anchor="middle" class="t">{d.day}</text>'
    for i, d in enumerate(series)
)
dots = "".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" class="p"/>' for px, py in pts)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.t{{font:12px 'JetBrains Mono',monospace;fill:#00ffd5;opacity:.75}}
.h{{font:600 18px 'JetBrains Mono',monospace;fill:#00ffd5}}
.g{{stroke:#00ffd5;stroke-opacity:.08}}
.p{{fill:#ffffff;stroke:#6e00ff;stroke-width:2}}
.l{{fill:none;stroke:#6e00ff;stroke-width:3;stroke-linejoin:round;stroke-dasharray:4000;stroke-dashoffset:4000;animation:d 2.5s ease-out forwards}}
.a{{fill:url(#f);opacity:0;animation:o 1.5s 1s forwards}}
@keyframes d{{to{{stroke-dashoffset:0}}}}
@keyframes o{{to{{opacity:1}}}}
</style>
<defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6e00ff" stop-opacity=".55"/><stop offset="1" stop-color="#6e00ff" stop-opacity="0"/></linearGradient></defs>
<rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>
<text x="{W / 2}" y="34" text-anchor="middle" class="h">&gt; {user} :: last {days} days</text>
{grid}{xlabels}
<path d="{area}" class="a"/>
<polyline points="{line}" class="l"/>
{dots}
</svg>'''
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(svg)
print(f"{out}: {sum(values)} contributions")
