import urllib.request
import json
import datetime
import os
import math

USERNAME = "ashumm"
ARCHIVES_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Chess-Graph/1.0 (Python)"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def downsample(points, target=150):
    if len(points) <= target:
        return points
    ratings = [p["r"] for p in points]
    peak_idx = ratings.index(max(ratings))
    step = len(points) / target
    kept = set([0, len(points)-1, peak_idx])
    i = 0.0
    while i < len(points):
        kept.add(int(i))
        i += step
    return [points[i] for i in sorted(kept)]

def catmull_rom_to_bezier(pts_xy):
    """Convert Catmull-Rom spline to SVG cubic bezier path — ultra-smooth curves."""
    if len(pts_xy) < 2:
        return ""
    n = len(pts_xy)
    cmds = [f"M {pts_xy[0][0]:.2f} {pts_xy[0][1]:.2f}"]
    for i in range(n - 1):
        p0 = pts_xy[max(i-1, 0)]
        p1 = pts_xy[i]
        p2 = pts_xy[i+1]
        p3 = pts_xy[min(i+2, n-1)]
        tension = 0.4
        cp1x = p1[0] + (p2[0] - p0[0]) * tension
        cp1y = p1[1] + (p2[1] - p0[1]) * tension
        cp2x = p2[0] - (p3[0] - p1[0]) * tension
        cp2y = p2[1] - (p3[1] - p1[1]) * tension
        cmds.append(f"C {cp1x:.2f} {cp1y:.2f} {cp2x:.2f} {cp2y:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    return " ".join(cmds)

def main():
    print(f"Fetching archives for {USERNAME}...")
    archives_data = fetch_json(ARCHIVES_URL)
    archives = archives_data.get("archives", [])
    all_points = []

    for archive_url in archives:
        try:
            month_data = fetch_json(archive_url)
            for g in month_data.get("games", []):
                if g.get("time_class") == "rapid":
                    t = g.get("end_time")
                    w = g.get("white", {})
                    b = g.get("black", {})
                    if w.get("username", "").lower() == USERNAME.lower():
                        r, opp, res = w.get("rating"), b.get("username","Opp"), w.get("result","")
                    elif b.get("username", "").lower() == USERNAME.lower():
                        r, opp, res = b.get("rating"), w.get("username","Opp"), b.get("result","")
                    else:
                        continue
                    if t and r:
                        all_points.append({"t": t, "r": r, "opp": opp, "res": res})
        except Exception as e:
            print(f"Skip {archive_url}: {e}")

    if not all_points:
        print("No points found.")
        return

    all_points.sort(key=lambda x: x["t"])
    total_games = len(all_points)
    ratings_all = [p["r"] for p in all_points]
    r_curr = ratings_all[-1]
    r_peak = max(ratings_all)
    r_start = ratings_all[0]
    r_gain = r_curr - r_start
    peak_idx_full = ratings_all.index(r_peak)
    peak_t = all_points[peak_idx_full]["t"]

    svg_points = downsample(all_points, target=150)
    print(f"Total games: {total_games} -> SVG pts: {len(svg_points)}")

    # --- Layout ---
    W, H = 900, 420
    ML, MR, MT, MB = 70, 40, 120, 60
    CW = W - ML - MR
    CH = H - MT - MB
    BY = MT + CH  # bottom Y

    t_min = all_points[0]["t"]
    t_max = all_points[-1]["t"]
    if t_min == t_max: t_max += 1

    r_lo = max(100, r_start - 80)
    r_hi = r_peak + 150

    def gx(t): return ML + (t - t_min) / (t_max - t_min) * CW
    def gy(r): return BY - (r - r_lo) / (r_hi - r_lo) * CH

    pts_xy = [(gx(p["t"]), gy(p["r"])) for p in svg_points]
    line_path = catmull_rom_to_bezier(pts_xy)
    area_path = f"{line_path} L {pts_xy[-1][0]:.2f} {BY} L {pts_xy[0][0]:.2f} {BY} Z"
    path_len = int(CW * 2.2)

    # Key coords
    peak_x, peak_y = gx(peak_t), gy(r_peak)
    curr_x, curr_y = gx(all_points[-1]["t"]), gy(r_curr)
    start_x, start_y = pts_xy[0]

    # Date labels
    dates = []
    for i in range(7):
        tick_t = t_min + (t_max - t_min) * i / 6
        tx = gx(tick_t)
        dt = datetime.datetime.fromtimestamp(tick_t, datetime.timezone.utc)
        dates.append((tx, dt.strftime("%b'%y")))

    # Y grid
    y_ticks = []
    step_r = (r_hi - r_lo) / 5
    for i in range(6):
        val = int(r_lo + i * step_r)
        y_ticks.append((val, gy(val)))

    # Callout boxes (ensure no overlap)
    pbw, pbh = 112, 26
    pbx = max(ML + 5, min(peak_x - 125, W - pbw - 8))
    pby = max(MT + 2, peak_y - 52)

    cbw, cbh = 100, 26
    cbx = max(ML + 5, min(curr_x - 115, W - cbw - 8))
    cby = min(BY - 34, curr_y + 40)
    # if callouts overlap vertically, push current down
    if abs(pby - cby) < 35 and abs(pbx - cbx) < 120:
        cby = pby + 48

    # Build chess-board tile pattern (subtle)
    tile_size = 22
    tiles = []
    for row in range(int(H / tile_size) + 1):
        for col in range(int(W / tile_size) + 1):
            if (row + col) % 2 == 0:
                tx = col * tile_size
                ty = row * tile_size
                tiles.append(f'<rect x="{tx}" y="{ty}" width="{tile_size}" height="{tile_size}" fill="white" />')
    tile_svg = "\n        ".join(tiles)

    # Y grid SVG
    y_grid_svg = ""
    for val, yp in y_ticks:
        y_grid_svg += f"""
    <line x1="{ML}" y1="{yp:.1f}" x2="{ML+CW}" y2="{yp:.1f}" stroke="#ffffff" stroke-width="0.6" stroke-dasharray="4 6" stroke-opacity="0.08" />
    <text x="{ML-10}" y="{yp+4:.1f}" text-anchor="end" fill="#6e7681" font-size="11" font-family="'Segoe UI',system-ui,sans-serif" font-weight="600">{val}</text>"""

    # X date SVG
    x_date_svg = ""
    for i, (tx, label) in enumerate(dates):
        x_date_svg += f"""
    <line x1="{tx:.1f}" y1="{MT}" x2="{tx:.1f}" y2="{BY}" stroke="#ffffff" stroke-width="0.5" stroke-opacity="0.06" />
    <text x="{tx:.1f}" y="{BY+22:.1f}" text-anchor="middle" fill="#6e7681" font-size="10" font-family="'Segoe UI',system-ui,sans-serif" font-weight="600">{label}</text>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" height="auto" style="max-width:900px">
  <defs>

    <!-- Chess tile background pattern -->
    <pattern id="chessPattern" x="0" y="0" width="{tile_size*2}" height="{tile_size*2}" patternUnits="userSpaceOnUse">
      <rect width="{tile_size*2}" height="{tile_size*2}" fill="transparent"/>
      <rect width="{tile_size}" height="{tile_size}" fill="#ffffff" fill-opacity="0.018"/>
      <rect x="{tile_size}" y="{tile_size}" width="{tile_size}" height="{tile_size}" fill="#ffffff" fill-opacity="0.018"/>
    </pattern>

    <!-- Chart area fill gradient -->
    <linearGradient id="fillGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#00d26a" stop-opacity="0.35"/>
      <stop offset="40%"  stop-color="#81b64c" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0"/>
    </linearGradient>

    <!-- Line stroke gradient -->
    <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#3ecf8e"/>
      <stop offset="35%"  stop-color="#81b64c"/>
      <stop offset="70%"  stop-color="#a8d660"/>
      <stop offset="100%" stop-color="#58f0a0"/>
    </linearGradient>

    <!-- Background card gradient -->
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0.3" y2="1">
      <stop offset="0%"   stop-color="#161b22"/>
      <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>

    <!-- Glow filter for peak/curr dots -->
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>

    <!-- Stronger glow for peak -->
    <filter id="peakGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>

    <!-- Soft shadow for card -->
    <filter id="shadow" x="-4%" y="-4%" width="108%" height="116%">
      <feDropShadow dx="0" dy="8" stdDeviation="14" flood-color="#000" flood-opacity="0.55"/>
    </filter>

    <!-- Line glow -->
    <filter id="lineGlow" x="-5%" y="-50%" width="110%" height="200%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>

  </defs>

  <!-- ── CARD BACKGROUND ── -->
  <rect width="{W}" height="{H}" rx="16" fill="url(#bgGrad)" stroke="#30363d" stroke-width="1.2" filter="url(#shadow)"/>

  <!-- Chess tile texture overlay -->
  <rect width="{W}" height="{H}" rx="16" fill="url(#chessPattern)"/>

  <!-- Accent top border strip -->
  <rect x="0" y="0" width="{W}" height="3" rx="2" fill="url(#lineGrad)" opacity="0.9"/>

  <!-- ── HEADER ── -->
  <!-- Chess icon circle -->
  <circle cx="34" cy="46" r="18" fill="#1c2128" stroke="#30363d" stroke-width="1.2"/>
  <text x="34" y="52" text-anchor="middle" font-size="18" fill="white">♟</text>

  <!-- Title text -->
  <text x="62" y="38" font-family="'Segoe UI',system-ui,-apple-system,sans-serif"
        font-size="18" font-weight="700" fill="#f0f6fc" letter-spacing="-0.3">Chess.com Rating Progression</text>
  <text x="62" y="57" font-family="'Segoe UI',system-ui,sans-serif"
        font-size="12" fill="#6e7681">Rapid · {total_games:,} games · @{USERNAME} · Aug 2025 – Sep 2026</text>

  <!-- ── KPI BADGE ROW ── -->
  <!-- Current Rating -->
  <g transform="translate({W-430}, 14)">
    <rect width="96" height="56" rx="10" fill="#1c2128" stroke="#238636" stroke-width="1.2"/>
    <text x="48" y="20" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="9" font-weight="700" fill="#3fb950" letter-spacing="0.8">CURRENT</text>
    <text x="48" y="42" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="22" font-weight="900" fill="#3fb950">{r_curr}</text>
  </g>

  <!-- Peak Rating -->
  <g transform="translate({W-324}, 14)">
    <rect width="96" height="56" rx="10" fill="#1c2128" stroke="#9e6a03" stroke-width="1.2"/>
    <text x="48" y="20" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="9" font-weight="700" fill="#d29922" letter-spacing="0.8">PEAK &#9813;</text>
    <text x="48" y="42" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="22" font-weight="900" fill="#d29922">{r_peak}</text>
  </g>

  <!-- Total Gain -->
  <g transform="translate({W-218}, 14)">
    <rect width="96" height="56" rx="10" fill="#1c2128" stroke="#1f6feb" stroke-width="1.2"/>
    <text x="48" y="20" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="9" font-weight="700" fill="#58a6ff" letter-spacing="0.8">GAIN &#128200;</text>
    <text x="48" y="42" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="22" font-weight="900" fill="#58a6ff">+{r_gain}</text>
  </g>

  <!-- Games -->
  <g transform="translate({W-112}, 14)">
    <rect width="96" height="56" rx="10" fill="#1c2128" stroke="#6e40c9" stroke-width="1.2"/>
    <text x="48" y="20" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="9" font-weight="700" fill="#bc8cff" letter-spacing="0.8">GAMES</text>
    <text x="48" y="42" text-anchor="middle" font-family="'Segoe UI',sans-serif"
          font-size="22" font-weight="900" fill="#bc8cff">{total_games:,}</text>
  </g>

  <!-- ── GRID ── -->
  {y_grid_svg}
  {x_date_svg}

  <!-- Baseline -->
  <line x1="{ML}" y1="{BY}" x2="{ML+CW}" y2="{BY}" stroke="#30363d" stroke-width="1.5"/>
  <line x1="{ML}" y1="{MT}" x2="{ML}" y2="{BY}" stroke="#30363d" stroke-width="1"/>

  <!-- ── CHART ── -->

  <!-- Ghost/static trace (always visible, very faint) -->
  <path d="{line_path}" fill="none" stroke="#3fb950" stroke-width="1.2"
        stroke-linecap="round" stroke-linejoin="round" opacity="0.15"/>

  <!-- Animated area fill -->
  <path d="{area_path}" fill="url(#fillGrad)">
    <animate attributeName="opacity" dur="4.5s" repeatCount="indefinite"
      keyTimes="0;0.15;0.55;0.82;0.94;1"
      values="0;0.1;1;1;0;0" calcMode="linear"/>
  </path>

  <!-- Animated glow duplicate line (blurred, wider) -->
  <path d="{line_path}" fill="none" stroke="#3ecf8e" stroke-width="5"
        stroke-linecap="round" stroke-linejoin="round"
        stroke-dasharray="{path_len}" stroke-dashoffset="{path_len}"
        opacity="0.35" filter="url(#lineGlow)">
    <animate attributeName="stroke-dashoffset" dur="4.5s" repeatCount="indefinite"
      keyTimes="0;0.55;0.82;0.93;1"
      values="{path_len};0;0;{path_len};{path_len}"
      keySplines="0.16 1 0.3 1;0 0 1 1;0.7 0 1 1;0 0 1 1"
      calcMode="spline"/>
  </path>

  <!-- Main animated wave line -->
  <path d="{line_path}" fill="none" stroke="url(#lineGrad)" stroke-width="2.8"
        stroke-linecap="round" stroke-linejoin="round"
        stroke-dasharray="{path_len}" stroke-dashoffset="{path_len}">
    <animate attributeName="stroke-dashoffset" dur="4.5s" repeatCount="indefinite"
      keyTimes="0;0.55;0.82;0.93;1"
      values="{path_len};0;0;{path_len};{path_len}"
      keySplines="0.16 1 0.3 1;0 0 1 1;0.7 0 1 1;0 0 1 1"
      calcMode="spline"/>
  </path>

  <!-- ── START DOT ── -->
  <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="4" fill="#6e7681" stroke="#0d1117" stroke-width="2"/>
  <rect x="{start_x+7:.1f}" y="{start_y-11:.1f}" width="64" height="20" rx="5"
        fill="#1c2128" stroke="#30363d" stroke-width="0.8"/>
  <text x="{start_x+39:.1f}" y="{start_y+3:.1f}" text-anchor="middle"
        fill="#8b949e" font-family="'Segoe UI',sans-serif" font-size="10" font-weight="700">Start: {r_start}</text>

  <!-- ── PEAK BADGE (animated) ── -->
  <g>
    <animate attributeName="opacity" dur="4.5s" repeatCount="indefinite"
      keyTimes="0;0.38;0.52;0.82;0.93;1"
      values="0;0;1;1;0;0"/>
    <!-- leader line -->
    <line x1="{pbx+pbw:.1f}" y1="{pby+pbh/2:.1f}" x2="{peak_x:.1f}" y2="{peak_y:.1f}"
          stroke="#d29922" stroke-width="1" stroke-dasharray="3 4" opacity="0.7"/>
    <!-- glow ring -->
    <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="11" fill="#d29922" fill-opacity="0.15" filter="url(#peakGlow)"/>
    <!-- outer ring -->
    <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="7.5" fill="none" stroke="#d29922" stroke-width="1.5" opacity="0.6"/>
    <!-- core dot -->
    <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="5" fill="#d29922" stroke="#0d1117" stroke-width="2" filter="url(#glow)"/>
    <!-- badge box -->
    <rect x="{pbx:.1f}" y="{pby:.1f}" width="{pbw}" height="{pbh}" rx="7"
          fill="#1a1700" stroke="#d29922" stroke-width="1.5"/>
    <text x="{pbx+pbw/2:.1f}" y="{pby+17:.1f}" text-anchor="middle"
          fill="#d29922" font-family="'Segoe UI',sans-serif" font-size="11.5" font-weight="800">Peak {r_peak} &#9813;</text>
  </g>

  <!-- ── CURRENT BADGE (animated) ── -->
  <g>
    <animate attributeName="opacity" dur="4.5s" repeatCount="indefinite"
      keyTimes="0;0.44;0.57;0.82;0.93;1"
      values="0;0;1;1;0;0"/>
    <!-- leader line -->
    <line x1="{cbx+cbw:.1f}" y1="{cby+cbh/2:.1f}" x2="{curr_x:.1f}" y2="{curr_y:.1f}"
          stroke="#3fb950" stroke-width="1" stroke-dasharray="3 4" opacity="0.7"/>
    <!-- pulse ring -->
    <circle cx="{curr_x:.1f}" cy="{curr_y:.1f}" r="10" fill="#3fb950" fill-opacity="0.12" filter="url(#glow)">
      <animate attributeName="r" dur="1.8s" repeatCount="indefinite" values="6;14;6"/>
      <animate attributeName="opacity" dur="1.8s" repeatCount="indefinite" values="0.5;0;0.5"/>
    </circle>
    <!-- core dot -->
    <circle cx="{curr_x:.1f}" cy="{curr_y:.1f}" r="5.5" fill="#3fb950" stroke="#0d1117" stroke-width="2.5" filter="url(#glow)"/>
    <!-- badge box -->
    <rect x="{cbx:.1f}" y="{cby:.1f}" width="{cbw}" height="{cbh}" rx="7"
          fill="#091e13" stroke="#238636" stroke-width="1.5"/>
    <text x="{cbx+cbw/2:.1f}" y="{cby+17:.1f}" text-anchor="middle"
          fill="#3fb950" font-family="'Segoe UI',sans-serif" font-size="11.5" font-weight="800">Now: {r_curr}</text>
  </g>

</svg>"""

    # Save SVG
    out_dir = os.path.dirname(__file__)
    svg_path = os.path.abspath(os.path.join(out_dir, "..", "chess_rating_graph.svg"))
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG saved: {svg_path}  ({len(svg)//1024}KB, {len(svg_points)} pts)")

    # Save full data for interactive dashboard
    data_path = os.path.abspath(os.path.join(out_dir, "..", "chess_data.json"))
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "username": USERNAME, "total_games": total_games,
            "peak": r_peak, "current": r_curr,
            "start": r_start, "gain": r_gain,
            "points": all_points
        }, f)
    print(f"Data saved: {data_path}")

if __name__ == "__main__":
    main()
