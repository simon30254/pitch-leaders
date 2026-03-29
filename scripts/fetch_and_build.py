import requests, csv, io, json, os
from datetime import datetime

PITCH_TYPES = [
    ("FF", "四縫線快速球"),
    ("SI", "伸卡球"),
    ("FC", "切球"),
    ("SL", "滑球"),
    ("SW", "掃球"),
    ("CU", "曲球"),
    ("CH", "變速球"),
    ("FS", "指叉球"),
]

YEAR = datetime.now().year
if datetime.now().month < 3:
    YEAR -= 1  # 賽季未開打前用上一年

def fetch_pitch_data(pitch_type, year):
    url = (
        f"https://baseballsavant.mlb.com/leaderboard/pitch-movement"
        f"?year={year}&min=q&pitch_type={pitch_type}&hand=&csv=true"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    return rows

def build_html(all_data):
    tabs_html = ""
    panels_html = ""

    for i, (code, name) in enumerate(PITCH_TYPES):
        rows = all_data.get(code, [])
        active = "active" if i == 0 else ""

        tabs_html += f'<button class="tab-btn {active}" onclick="showTab(\'{code}\')" id="btn-{code}">{name}<span class="code">({code})</span></button>\n'

        # 排序：依 diff_z (Vertical Drop vs Comparable) 降冪，沒有就跳過
        def sort_key(r):
            try: return float(r.get("diff_z") or r.get("diff_x") or 0)
            except: return 0

        rows_sorted = sorted(rows, key=sort_key, reverse=True)[:15]

        rows_html = ""
        for rank, r in enumerate(rows_sorted, 1):
            name_val = (
    r.get("last_name, first_name") or
    r.get("player_name") or
    r.get("name_display_first_last") or
    "—"
)
            diff_z = r.get("diff_z", "—")
            diff_x = r.get("diff_x", "—")
            velocity = r.get("velocity", r.get("avg_speed", "—"))
            hand = r.get("p_throws", r.get("pitch_hand", ""))
            try:
                diff_z_f = float(diff_z)
                diff_z_display = f"+{diff_z_f:.1f}" if diff_z_f > 0 else f"{diff_z_f:.1f}"
                color = "#22c55e" if diff_z_f > 0 else "#ef4444"
            except:
                diff_z_display = diff_z
                color = "#888"

            medal = ["🥇","🥈","🥉"][rank-1] if rank <= 3 else f"{rank}"

            rows_html += f"""
            <tr>
              <td class="rank">{medal}</td>
              <td class="player">{name_val} <span class="hand">{hand}</span></td>
              <td class="stat" style="color:{color}">{diff_z_display}"</td>
              <td class="stat">{diff_x}"</td>
              <td class="stat">{float(velocity):.1f} mph</td>
            </tr>"""

        no_data = "" if rows_sorted else '<tr><td colspan="5" style="text-align:center;padding:2rem;color:#888">本球種本季無符合資格投手</td></tr>'

        panels_html += f"""
        <div class="tab-panel {'active' if i==0 else ''}" id="panel-{code}">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>投手</th>
                <th>垂直位移 vs 同儕</th>
                <th>水平位移 vs 同儕</th>
                <th>球速</th>
              </tr>
            </thead>
            <tbody>{rows_html or no_data}</tbody>
          </table>
        </div>"""

    updated = datetime.now().strftime("%Y-%m-%d")
    year_display = YEAR

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MLB 各球種最強投手排行 {year_display}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; padding: 1rem; }}
  h1 {{ font-size: 1.2rem; font-weight: 700; color: #f8fafc; margin-bottom: .25rem; }}
  .subtitle {{ font-size: .8rem; color: #64748b; margin-bottom: 1rem; }}
  .tabs {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: 1rem; }}
  .tab-btn {{ background: #1e293b; border: 1px solid #334155; color: #94a3b8;
              padding: .4rem .75rem; border-radius: 6px; cursor: pointer;
              font-size: .8rem; transition: all .2s; }}
  .tab-btn:hover {{ background: #334155; color: #f1f5f9; }}
  .tab-btn.active {{ background: #3b82f6; border-color: #3b82f6; color: #fff; font-weight: 600; }}
  .code {{ opacity: .6; font-size: .7rem; margin-left: .25rem; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  thead {{ background: #1e293b; }}
  th {{ padding: .6rem .75rem; text-align: left; color: #64748b;
        font-size: .75rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: .05em; border-bottom: 1px solid #334155; }}
  td {{ padding: .55rem .75rem; border-bottom: 1px solid #1e293b; }}
  tr:hover td {{ background: #1e293b88; }}
  .rank {{ font-weight: 700; font-size: .95rem; width: 2.5rem; }}
  .player {{ font-weight: 600; color: #f1f5f9; }}
  .hand {{ font-size: .7rem; color: #64748b; margin-left: .3rem; }}
  .stat {{ font-family: monospace; font-size: .9rem; }}
  .footer {{ margin-top: 1rem; font-size: .7rem; color: #475569; text-align: right; }}
  .footer a {{ color: #3b82f6; text-decoration: none; }}
</style>
</head>
<body>
<h1>⚾ MLB 各球種最強投手 {year_display}</h1>
<p class="subtitle">依各球種 垂直位移 vs 同速段投手 排行｜資料來源：Baseball Savant</p>
<div class="tabs">{tabs_html}</div>
{panels_html}
<p class="footer">最後更新：{updated}｜<a href="https://baseballsavant.mlb.com/leaderboard/pitch-movement" target="_blank">原始資料</a></p>
<script>
function showTab(code) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + code).classList.add('active');
  document.getElementById('btn-' + code).classList.add('active');
}}
</script>
</body>
</html>"""

def main():
    all_data = {}
    for code, name in PITCH_TYPES:
        print(f"抓取 {name} ({code})...")
        try:
            rows = fetch_pitch_data(code, YEAR)
            all_data[code] = rows
            print(f"  → {len(rows)} 筆")
        except Exception as e:
            print(f"  → 失敗: {e}")
            all_data[code] = []

    html = build_html(all_data)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ 已生成 docs/index.html")

if __name__ == "__main__":
    main()
