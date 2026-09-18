import urllib.request
import json
import datetime
import math
import os

USERNAME = "ashumm"
ARCHIVES_URL = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Chess-Graph/1.0 (Python)"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    print(f"Fetching archives for {USERNAME}...")
    archives_data = fetch_json(ARCHIVES_URL)
    archives = archives_data.get("archives", [])
    
    points = [] # list of dicts: {"t": timestamp, "r": rating, "opp": opponent, "res": result}
    
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
                        points.append({"t": t, "r": r, "opp": opp, "res": res})
        except Exception as e:
            print(f"Error fetching {archive_url}: {e}")
            
    if not points:
        print("No rapid points found.")
        return

    # Sort chronologically
    points.sort(key=lambda x: x["t"])
    
    timestamps = [p["t"] for p in points]
    ratings = [p["r"] for p in points]
    
    t_min = timestamps[0]
    t_max = timestamps[-1]
    if t_min == t_max:
        t_max += 1

    r_curr = ratings[-1]
    r_peak = max(ratings)
    r_start = ratings[0]
    r_gain = r_curr - r_start
    total_games = len(points)
    
    # Peak point
    peak_idx = ratings.index(r_peak)
    peak_t = timestamps[peak_idx]

    # Dimensions
    svg_w = 880
    svg_h = 390
    m_left = 65
    m_right = 35
    m_top = 110
    m_bottom = 55
    
    chart_w = svg_w - m_left - m_right
    chart_h = svg_h - m_top - m_bottom
    
    y_min_val = 200
    y_max_val = 1300
    
    def get_x(t):
        return m_left + ((t - t_min) / (t_max - t_min)) * chart_w
        
    def get_y(r):
        return (m_top + chart_h) - ((r - y_min_val) / (y_max_val - y_min_val)) * chart_h

    # Build line path and area path
    path_commands = []
    for i, p in enumerate(points):
        x = get_x(p["t"])
        y = get_y(p["r"])
        cmd = "M" if i == 0 else "L"
        path_commands.append(f"{cmd} {x:.1f} {y:.1f}")
        
    line_path = " ".join(path_commands)
    
    first_x = get_x(points[0]["t"])
    last_x = get_x(points[-1]["t"])
    bottom_y = m_top + chart_h
    area_path = f"{line_path} L {last_x:.1f} {bottom_y:.1f} L {first_x:.1f} {bottom_y:.1f} Z"

    # Rating Grid Lines (Y-Axis)
    y_grid_lines = []
    for val in [200, 400, 600, 800, 1000, 1200]:
        y_pos = get_y(val)
        y_grid_lines.append(f"""
        <line x1="{m_left}" y1="{y_pos:.1f}" x2="{m_left + chart_w}" y2="{y_pos:.1f}" stroke="#2d333b" stroke-width="1" stroke-dasharray="4 4" />
        <text x="{m_left - 12}" y="{y_pos + 4:.1f}" text-anchor="end" fill="#768390" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="11" font-weight="600">{val}</text>
        """)

    # Date Grid Lines (X-Axis)
    x_grid_lines = []
    num_ticks = 6
    for step in range(num_ticks + 1):
        tick_t = t_min + (t_max - t_min) * (step / num_ticks)
        tick_x = get_x(tick_t)
        dt = datetime.datetime.fromtimestamp(tick_t, datetime.timezone.utc)
        date_str = dt.strftime("%b '%y")
        x_grid_lines.append(f"""
        <line x1="{tick_x:.1f}" y1="{m_top}" x2="{tick_x:.1f}" y2="{bottom_y:.1f}" stroke="#21262d" stroke-width="1" />
        <text x="{tick_x:.1f}" y="{bottom_y + 24:.1f}" text-anchor="middle" fill="#768390" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="11" font-weight="600">{date_str}</text>
        """)

    peak_x = get_x(peak_t)
    peak_y = get_y(r_peak)
    curr_x = get_x(timestamps[-1])
    curr_y = get_y(r_curr)
    start_x = get_x(timestamps[0])
    start_y = get_y(r_start)

    # Calculate callout positions to completely prevent overlap:
    peak_box_w = 100
    peak_box_h = 24
    peak_box_x = max(m_left + 10, min(peak_x - 110, svg_w - peak_box_w - 20))
    peak_box_y = max(m_top - 15, peak_y - 45)

    curr_box_w = 92
    curr_box_h = 24
    curr_box_x = max(m_left + 10, min(curr_x - 105, svg_w - curr_box_w - 20))
    curr_box_y = min(bottom_y - 30, curr_y + 35)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%">
    <defs>
        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#81b64c" stop-opacity="0.45" />
            <stop offset="60%" stop-color="#81b64c" stop-opacity="0.12" />
            <stop offset="100%" stop-color="#81b64c" stop-opacity="0.0" />
        </linearGradient>
        <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#4e8d35" />
            <stop offset="50%" stop-color="#81b64c" />
            <stop offset="100%" stop-color="#a3d160" />
        </linearGradient>
        <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="115%">
            <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.4" />
        </filter>
    </defs>

    <style>
        .title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 700; font-size: 17px; fill: #f0f6fc; }}
        .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 500; font-size: 12px; fill: #8b949e; }}
        .badge-title {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 10px; font-weight: 600; text-transform: uppercase; fill: #8b949e; letter-spacing: 0.5px; }}
        .badge-value {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 800; }}
        
        /* Direct SMIL & CSS Fallback Animation */
        @keyframes pulseGlow {{
            0% {{ r: 5px; opacity: 0.9; }}
            50% {{ r: 14px; opacity: 0.2; }}
            100% {{ r: 18px; opacity: 0; }}
        }}
        .beacon {{
            animation: pulseGlow 2s ease-out infinite;
            transform-origin: {curr_x:.1f}px {curr_y:.1f}px;
        }}
    </style>

    <!-- Background Card -->
    <rect width="{svg_w}" height="{svg_h}" rx="12" fill="#0d1117" stroke="#30363d" stroke-width="1.2" filter="url(#cardShadow)" />

    <!-- Top Left Title -->
    <g transform="translate(25, 30)">
        <text class="title" x="0" y="0">♟️ Chess.com All-Time Rating Progression</text>
        <text class="subtitle" x="0" y="20">Rapid Rating History across all {total_games:,} games • Player: @{USERNAME}</text>
    </g>

    <!-- Top Stat KPI Badges -->
    <g transform="translate({svg_w - 475}, 18)">
        <!-- Current -->
        <g transform="translate(0, 0)">
            <rect width="105" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text class="badge-title" x="12" y="18">Current</text>
            <text class="badge-value" x="12" y="38" fill="#81b64c">{r_curr}</text>
            <circle cx="88" cy="30" r="4" fill="#81b64c" />
        </g>
        <!-- Peak -->
        <g transform="translate(115, 0)">
            <rect width="105" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text class="badge-title" x="12" y="18">Peak 🏆</text>
            <text class="badge-value" x="12" y="38" fill="#f1e05a">{r_peak}</text>
        </g>
        <!-- Gain -->
        <g transform="translate(230, 0)">
            <rect width="110" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text class="badge-title" x="12" y="18">Gain 📈</text>
            <text class="badge-value" x="12" y="38" fill="#58a6ff">+{r_gain}</text>
        </g>
        <!-- Games -->
        <g transform="translate(350, 0)">
            <rect width="100" height="48" rx="8" fill="#161b22" stroke="#30363d" stroke-width="1" />
            <text class="badge-title" x="12" y="18">Games</text>
            <text class="badge-value" x="12" y="38" fill="#f0f6fc">{total_games:,}</text>
        </g>
    </g>

    <!-- Chart Grid -->
    {''.join(y_grid_lines)}
    {''.join(x_grid_lines)}

    <!-- Baseline Axis -->
    <line x1="{m_left}" y1="{bottom_y}" x2="{m_left + chart_w}" y2="{bottom_y}" stroke="#30363d" stroke-width="1.2" />

    <!-- Subtle Guide Trace (Always Visible Underneath) -->
    <path d="{line_path}" fill="none" stroke="#213524" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.35" />

    <!-- Animated Area Fill (Fades In In Sync With Wave) -->
    <path d="{area_path}" fill="url(#chartGradient)" opacity="1">
        <animate attributeName="opacity" dur="6.5s" repeatCount="indefinite"
            keyTimes="0; 0.25; 0.45; 0.88; 0.95; 1"
            values="0; 0.2; 1; 1; 0; 0"
            calcMode="linear" />
    </path>

    <!-- Live Rating Trajectory Wave Line (Pure SMIL Animation - Zero ClipPath Dependency) -->
    <path d="{line_path}" fill="none" stroke="url(#lineGradient)" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="5000" stroke-dashoffset="5000">
        <animate attributeName="stroke-dashoffset" dur="6.5s" repeatCount="indefinite"
            keyTimes="0; 0.42; 0.88; 0.96; 1"
            values="5000; 0; 0; 5000; 5000"
            keySplines="0.22 1 0.36 1; 0 0 1 1; 0.22 1 0.36 1; 0 0 1 1"
            calcMode="spline" />
    </path>

    <!-- ==================== MILESTONE MARKERS (NO OVERLAP) ==================== -->

    <!-- 1. Start Point Indicator -->
    <g>
        <circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="4.5" fill="#4e8d35" stroke="#0d1117" stroke-width="2" />
        <rect x="{start_x + 8:.1f}" y="{start_y - 12:.1f}" width="72" height="22" rx="5" fill="#161b22" stroke="#30363d" stroke-width="1" />
        <text x="{start_x + 14:.1f}" y="{start_y + 3:.1f}" fill="#8b949e" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="10" font-weight="700">Start: {r_start}</text>
    </g>

    <!-- 2. Peak Point Indicator (Positioned ABOVE-LEFT with Gold Pin Line) -->
    <g>
        <animate attributeName="opacity" dur="6.5s" repeatCount="indefinite"
            keyTimes="0; 0.30; 0.42; 0.88; 0.95; 1"
            values="0; 0; 1; 1; 0; 0" />
        <!-- Connecting leader line -->
        <line x1="{peak_box_x + peak_box_w:.1f}" y1="{peak_box_y + peak_box_h:.1f}" x2="{peak_x:.1f}" y2="{peak_y:.1f}" stroke="#f1e05a" stroke-width="1.2" stroke-dasharray="2 2" />
        <!-- Glowing peak point -->
        <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="6.5" fill="#f1e05a" stroke="#0d1117" stroke-width="2.5" filter="url(#glow)" />
        <!-- Badge Box -->
        <rect x="{peak_box_x:.1f}" y="{peak_box_y:.1f}" width="{peak_box_w}" height="{peak_box_h}" rx="6" fill="#1f1e14" stroke="#f1e05a" stroke-width="1.4" filter="url(#cardShadow)" />
        <text x="{peak_box_x + (peak_box_w / 2):.1f}" y="{peak_box_y + 16:.1f}" text-anchor="middle" fill="#f1e05a" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="11" font-weight="800">Peak: {r_peak} 🏆</text>
    </g>

    <!-- 3. Current Point Indicator (Positioned BELOW-LEFT with Emerald Pin Line) -->
    <g>
        <animate attributeName="opacity" dur="6.5s" repeatCount="indefinite"
            keyTimes="0; 0.34; 0.44; 0.88; 0.95; 1"
            values="0; 0; 1; 1; 0; 0" />
        <!-- Pulse ring behind point -->
        <circle class="beacon" cx="{curr_x:.1f}" cy="{curr_y:.1f}" r="6" fill="#81b64c" />
        <!-- Connecting leader line -->
        <line x1="{curr_box_x + curr_box_w:.1f}" y1="{curr_box_y:.1f}" x2="{curr_x:.1f}" y2="{curr_y:.1f}" stroke="#81b64c" stroke-width="1.2" stroke-dasharray="2 2" />
        <!-- Current point dot -->
        <circle cx="{curr_x:.1f}" cy="{curr_y:.1f}" r="5.5" fill="#a3d160" stroke="#0d1117" stroke-width="2" filter="url(#glow)" />
        <!-- Badge Box -->
        <rect x="{curr_box_x:.1f}" y="{curr_box_y:.1f}" width="{curr_box_w}" height="{curr_box_h}" rx="6" fill="#102419" stroke="#81b64c" stroke-width="1.4" filter="url(#cardShadow)" />
        <text x="{curr_box_x + (curr_box_w / 2):.1f}" y="{curr_box_y + 16:.1f}" text-anchor="middle" fill="#a3d160" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif" font-size="11" font-weight="800">Now: {r_curr}</text>
    </g>
</svg>"""

    output_path = os.path.join(os.path.dirname(__file__), "..", "chess_rating_graph.svg")
    output_path = os.path.abspath(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    print(f"Generated graph successfully at: {output_path}")

    # Also save points data for interactive HTML dashboard
    data_path = os.path.join(os.path.dirname(__file__), "..", "chess_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "username": USERNAME,
            "total_games": total_games,
            "peak": r_peak,
            "current": r_curr,
            "start": r_start,
            "gain": r_gain,
            "points": points
        }, f)
    print(f"Saved interactive data at: {data_path}")

if __name__ == "__main__":
    main()
