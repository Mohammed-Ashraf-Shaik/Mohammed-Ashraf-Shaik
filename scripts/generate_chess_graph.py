import urllib.request
import json
import datetime
import os

USERNAME = "ashumm"
ARCHIVES_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Chess-Graph/1.0 (Python)"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def downsample(points, target=120):
    """Keep ~target evenly-spaced points + always keep first, last, and peak."""
    if len(points) <= target:
        return points
    ratings = [p["r"] for p in points]
    peak_idx = ratings.index(max(ratings))
    step = len(points) / target
    kept = set()
    kept.add(0)
    kept.add(len(points) - 1)
    kept.add(peak_idx)
    i = 0.0
    while i < len(points):
        kept.add(int(i))
        i += step
    return [points[i] for i in sorted(kept)]

def build_smooth_path(pts_xy):
    """Build a smooth cubic bezier path through points."""
    if len(pts_xy) < 2:
        return ""
    cmds = [f"M {pts_xy[0][0]:.1f} {pts_xy[0][1]:.1f}"]
    for i in range(1, len(pts_xy)):
        x0, y0 = pts_xy[i-1]
        x1, y1 = pts_xy[i]
        cx = (x0 + x1) / 2
        cmds.append(f"C {cx:.1f} {y0:.1f} {cx:.1f} {y1:.1f} {x1:.1f} {y1:.1f}")
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
                        r = w.get("rating")
                        opp = b.get("username", "Opponent")
                        res = w.get("result", "")
                    elif b.get("username", "").lower() == USERNAME.lower():
                        r = b.get("rating")
                        opp = w.get("username", "Opponent")
                        res = b.get("result", "")
                    else:
                        continue
                    if t and r:
                        all_points.append({"t": t, "r": r, "opp": opp, "res": res})
        except Exception as e:
            print(f"Error fetching {archive_url}: {e}")
            
    if not all_points:
        print("No rapid points found.")
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
    
    # Downsample to ~120 points for SVG rendering
    svg_points = downsample(all_points, target=120)
    print(f"Total games: {total_games}, SVG points: {len(svg_points)}")

    timestamps = [p["t"] for p in svg_points]
    t_min = all_points[0]["t"]
    t_max = all_points[-1]["t"]
    if t_min == t_max:
        t_max += 1

    # Dimensions
    svg_w = 880
    svg_h = 390
    m_left = 65
    m_right = 35
    m_top = 110
    m_bottom = 55
    chart_w = svg_w - m_left - m_right
    chart_h = svg_h - m_top - m_bottom
    y_min_val = max(200, r_start - 100)
    y_max_val = r_peak + 120
    bottom_y = m_top + chart_h

    def get_x(t):
        return m_left + ((t - t_min) / (t_max - t_min)) * chart_w
    def get_y(r):
        return (m_top + chart_h) - ((r - y_min_val) / (y_max_val - y_min_val)) * chart_h

    pts_xy = [(get_x(p["t"]), get_y(p["r"])) for p in svg_points]

    # Smooth bezier path
    line_path = build_smooth_path(pts_xy)

    # Closed area path
    first_x = pts_xy[0][0]
    last_x = pts_xy[-1][0]
    area_path = f"{line_path} L {last_x:.1f} {bottom_y:.1f} L {first_x:.1f} {bottom_y:.1f} Z"

    # Path length estimate (for dasharray)
    path_len = int(chart_w * 1.5)

    # Grid lines
    y_grid_values = []
    step = (y_max_val - y_min_val) / 5
    for i in range(6):
        val = int(y_min_val + i * step)
        y_grid_values.append(val)

    y_grid_lines = []
    for val in y_grid_values:
        yp = get_y(val)
        y_grid_lines.append(f"""
        <line x1="{m_left}" y1="{yp:.1f}" x2="{m_left + chart_w}" y2="{yp:.1f}" stroke="#2d333b" stroke-width="1" stroke-dasharray="4 4" />
        <text x="{m_left - 10}" y="{yp + 4:.1f}" text-anchor="end" fill="#768390" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="11" font-weight="600">{val}</text>
        """)

    x_grid_lines = []
    for step_i in range(7):
        tick_t = t_min + (t_max - t_min) * (step_i / 6)
        tick_x = get_x(tick_t)
        dt = datetime.datetime.fromtimestamp(tick_t, datetime.timezone.utc)
        date_str = dt.strftime("%b '%y")
        x_grid_lines.append(f"""
        <line x1="{tick_x:.1f}" y1="{m_top}" x2="{tick_x:.1f}" y2="{bottom_y:.1f}" stroke="#21262d" stroke-width="1" />
        <text x="{tick_x:.1f}" y="{bottom_y + 22:.1f}" text-anchor="middle" fill="#768390" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="10" font-weight="600">{date_str}</text>
        """)

    # Key points
    peak_x = get_x(peak_t)
    peak_y = get_y(r_peak)
    curr_x = get_x(all_points[-1]["t"])
    curr_y = get_y(r_curr)
    start_x = pts_xy[0][0]
    start_y = pts_xy[0][1]

    # Callout badge positions
    peak_bw, peak_bh = 104, 24
    peak_bx = max(m_left + 5, min(peak_x - 120, svg_w - peak_bw - 10))
    peak_by = max(m_top - 5, peak_y - 48)

    curr_bw, curr_bh = 96, 24
    curr_bx = max(m_left + 5, min(curr_x - 110, svg_w - curr_bw - 10))
    curr_by = min(bottom_y - 32, curr_y + 38)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%">
    <defs>
        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#81b64c" stop-opacity="0.45" />
            <stop offset="60%" stop-color="#81b64c" stop-opacity="0.10" />
            <stop offset="100%" stop-color="#81b64c" stop-opacity="0.0" />
        </linearGradient>
        <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#3e7d27" />
            <stop offset="50%" stop-color="#81b64c" />
            <stop offset="100%" stop-color="#a3d160" />
        </linearGradient>
        <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="115%">
            <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity="0.4" />
        </filter>
    </defs>

    <!-- Background -->
    <rect width="{svg_w}" height="{svg_h}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.2" filter="url(#cardShadow)" />

    <!-- Title -->
    <g transform="translate(22, 28)">
        <text font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif" font-weight="700" font-size="17" fill="#f0f6fc">&#9822;&#65039; Chess.com All-Time Rating Progression</text>
        <text font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif" font-weight="500" font-size="12" fill="#8b949e" y="20">Rapid history across {total_games:,} games  |  @{USERNAME}</text>
    </g>

    <!-- KPI Badges -->
    <g transform="translate({svg_w - 470}, 16)">
        <g>
            <rect width="105" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text font-family="-apple-system,sans-serif" font-size="10" font-weight="600" fill="#8b949e" x="12" y="17">CURRENT</text>
            <text font-family="-apple-system,sans-serif" font-size="16" font-weight="800" fill="#81b64c" x="12" y="38">{r_curr}</text>
        </g>
        <g transform="translate(115, 0)">
            <rect width="105" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text font-family="-apple-system,sans-serif" font-size="10" font-weight="600" fill="#8b949e" x="12" y="17">PEAK &#127942;</text>
            <text font-family="-apple-system,sans-serif" font-size="16" font-weight="800" fill="#f1e05a" x="12" y="38">{r_peak}</text>
        </g>
        <g transform="translate(230, 0)">
            <rect width="110" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text font-family="-apple-system,sans-serif" font-size="10" font-weight="600" fill="#8b949e" x="12" y="17">GAIN &#128200;</text>
            <text font-family="-apple-system,sans-serif" font-size="16" font-weight="800" fill="#58a6ff" x="12" y="38">+{r_gain}</text>
        </g>
        <g transform="translate(350, 0)">
            <rect width="105" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text font-family="-apple-system,sans-serif" font-size="10" font-weight="600" fill="#8b949e" x="12" y="17">GAMES</text>
            <text font-family="-apple-system,sans-serif" font-size="16" font-weight="800" fill="#f0f6fc" x="12" y="38">{total_games:,}</text>
        </g>
    </g>

    <!-- Grid -->
    {''.join(y_grid_lines)}
    {''.join(x_grid_lines)}

    <!-- Baseline -->
    <line x1="{m_left}" y1="{bottom_y}" x2="{m_left + chart_w}" y2="{bottom_y}" stroke="#30363d" stroke-width="1.2" />

    <!-- Static ghost trace (always visible) -->
    <path d="{line_path}" fill="none" stroke="#213524" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.4" />

    <!-- Animated area fill -->
    <path d="{area_path}" fill="url(#chartGradient)">
        <animate attributeName="opacity" dur="5s" repeatCount="indefinite"
            keyTimes="0; 0.2; 0.55; 0.85; 0.95; 1"
            values="0; 0.15; 1; 1; 0; 0"
            calcMode="linear" />
    </path>

    <!-- Animated wave line -->
    <path d="{line_path}" fill="none" stroke="url(#lineGradient)" stroke-width="2.8"
          stroke-linecap="round" stroke-linejoin="round"
          stroke-dasharray="{path_len}" stroke-dashoffset="{path_len}">
        <animate attributeName="stroke-dashoffset" dur="5s" repeatCount="indefinite"
            keyTimes="0; 0.5; 0.85; 0.95; 1"
            values="{path_len}; 0; 0; {path_len}; {path_len}"
            keySplines="0.22 1 0.36 1; 0 0 1 1; 0.8 0 1 1; 0 0 1 1"
            calcMode="spline" />
    </path>

    <!-- Start dot -->
    <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="4" fill="#4e8d35" stroke="#0d1117" stroke-width="2" />
    <rect x="{start_x + 7:.1f}" y="{start_y - 12:.1f}" width="72" height="20" rx="5" fill="#161b22" stroke="#30363d" stroke-width="1" />
    <text x="{start_x + 13:.1f}" y="{start_y + 2:.1f}" fill="#8b949e" font-family="-apple-system,sans-serif" font-size="10" font-weight="700">Start: {r_start}</text>

    <!-- Peak badge (fades in with animation) -->
    <g>
        <animate attributeName="opacity" dur="5s" repeatCount="indefinite"
            keyTimes="0; 0.35; 0.5; 0.85; 0.95; 1"
            values="0; 0; 1; 1; 0; 0" />
        <line x1="{peak_bx + peak_bw:.1f}" y1="{peak_by + peak_bh / 2:.1f}" x2="{peak_x:.1f}" y2="{peak_y:.1f}"
              stroke="#f1e05a" stroke-width="1" stroke-dasharray="3 3" opacity="0.7" />
        <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="6" fill="#f1e05a" stroke="#0d1117" stroke-width="2" filter="url(#glow)" />
        <rect x="{peak_bx:.1f}" y="{peak_by:.1f}" width="{peak_bw}" height="{peak_bh}" rx="6"
              fill="#1f1e14" stroke="#f1e05a" stroke-width="1.4" />
        <text x="{peak_bx + peak_bw / 2:.1f}" y="{peak_by + 16:.1f}" text-anchor="middle"
              fill="#f1e05a" font-family="-apple-system,sans-serif" font-size="11" font-weight="800">Peak: {r_peak} &#127942;</text>
    </g>

    <!-- Current badge (fades in slightly after peak) -->
    <g>
        <animate attributeName="opacity" dur="5s" repeatCount="indefinite"
            keyTimes="0; 0.45; 0.55; 0.85; 0.95; 1"
            values="0; 0; 1; 1; 0; 0" />
        <line x1="{curr_bx + curr_bw:.1f}" y1="{curr_by + curr_bh / 2:.1f}" x2="{curr_x:.1f}" y2="{curr_y:.1f}"
              stroke="#81b64c" stroke-width="1" stroke-dasharray="3 3" opacity="0.7" />
        <circle cx="{curr_x:.1f}" cy="{curr_y:.1f}" r="5.5" fill="#a3d160" stroke="#0d1117" stroke-width="2" filter="url(#glow)" />
        <rect x="{curr_bx:.1f}" y="{curr_by:.1f}" width="{curr_bw}" height="{curr_bh}" rx="6"
              fill="#102419" stroke="#81b64c" stroke-width="1.4" />
        <text x="{curr_bx + curr_bw / 2:.1f}" y="{curr_by + 16:.1f}" text-anchor="middle"
              fill="#a3d160" font-family="-apple-system,sans-serif" font-size="11" font-weight="800">Now: {r_curr}</text>
    </g>

</svg>"""

    # Save SVG
    out_dir = os.path.dirname(__file__)
    svg_path = os.path.abspath(os.path.join(out_dir, "..", "chess_rating_graph.svg"))
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"SVG saved: {svg_path}  ({len(svg_content)//1024}KB, {len(svg_points)} points)")

    # Save full data for interactive dashboard
    data_path = os.path.abspath(os.path.join(out_dir, "..", "chess_data.json"))
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "username": USERNAME,
            "total_games": total_games,
            "peak": r_peak,
            "current": r_curr,
            "start": r_start,
            "gain": r_gain,
            "points": all_points
        }, f)
    print(f"Data saved: {data_path}  ({os.path.getsize(data_path)//1024}KB)")

if __name__ == "__main__":
    main()
