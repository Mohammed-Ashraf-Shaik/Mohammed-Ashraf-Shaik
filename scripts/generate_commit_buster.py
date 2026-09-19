import os
import math
import random
import urllib.request
import re
from PIL import Image, ImageDraw, ImageFont

# ==================== CONFIGURATION ====================
WIDTH = 890
HEIGHT = 210
FPS = 14
FRAME_DURATION = 70
TOTAL_FRAMES = 180

# GitHub Dark Theme Colors
BG_COLOR    = (13, 17, 23)
CARD_BORDER = (48, 54, 61)
HEADER_LINE = (33, 38, 45)
EMPTY_CELL  = (22, 27, 34)
EMPTY_BORDER= (33, 38, 45)

# GitHub Official Contribution Greens
GREEN_LEVELS = [
    (22, 27, 34),     # 0: empty
    (14, 68, 41),     # 1: dark green (#0e4429)
    (0, 109, 50),     # 2: medium green (#006d32)
    (38, 166, 65),    # 3: light green (#26a641)
    (57, 211, 83)     # 4: bright green (#39d353)
]

HOT_GREEN   = (0, 255, 136)
CYAN_ACCENT = (0, 229, 255)
GOLD_ACCENT = (255, 215, 0)
WHITE       = (240, 246, 252)
MUTED       = (110, 118, 129)
FLASH_WHITE = (255, 255, 255)
FLASH_YELLOW= (255, 230, 50)
FLASH_ORANGE= (255, 110, 20)

def get_font(size, bold=False):
    font_candidates = [
        'C:\\Windows\\Fonts\\segoeuib.ttf' if bold else 'C:\\Windows\\Fonts\\segoeui.ttf',
        'C:\\Windows\\Fonts\\arialbd.ttf' if bold else 'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\consola.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

FONT_HEADER = get_font(12, bold=True)
FONT_SUB    = get_font(10, bold=False)
FONT_LABEL  = get_font(9, bold=False)

# ==================== PARSE EXACT 2D GITHUB CONTRIBUTIONS ====================
def fetch_real_contributions(username="Mohammed-Ashraf-Shaik"):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            tbody_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
            if tbody_match:
                tbody = tbody_match.group(1)
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
                grid_2d = [] # 7 rows (Sunday to Saturday) x 53 cols (weeks)
                for r in rows:
                    cells = re.findall(r'data-date="([^"]+)"[^>]*data-level="(\d+)"', r)
                    if not cells:
                        cells = re.findall(r'data-level="(\d+)"[^>]*data-date="([^"]+)"', r)
                        cells = [(c[1], c[0]) for c in cells]
                    grid_2d.append([int(lvl) for d, lvl in cells])
                
                if len(grid_2d) == 7 and len(grid_2d[0]) >= 52:
                    return grid_2d
    except Exception as e:
        print("Scrape error, using fallback:", e)

    # Fallback realistic 7x53
    random.seed(1337)
    return [[random.choice([1, 2, 3, 4]) if random.random() > 0.85 else 0 for _ in range(53)] for _ in range(7)]

# ==================== CRISP BOX SHATTER SYSTEM ====================
class BoxShatter:
    def __init__(self, cx, cy, level=2):
        self.cx = cx
        self.cy = cy
        self.level = level
        self.age = 0
        self.max_age = 7  # Quick, localized to the 10x10 box

        box_color = GREEN_LEVELS[min(max(1, level), 4)]
        bright_color = HOT_GREEN

        # 6 small green pixel fragments of the 10x10 box
        self.shards = []
        angles = [0.4, 1.2, 2.1, 3.3, 4.3, 5.3]
        for a in angles:
            spd = random.uniform(1.2, 2.5)
            vx = math.cos(a) * spd
            vy = math.sin(a) * spd - 1.0
            sz = random.uniform(2.0, 3.0)
            col = box_color if random.random() > 0.3 else bright_color
            self.shards.append({
                'x': cx + math.cos(a) * 1.5,
                'y': cy + math.sin(a) * 1.5,
                'vx': vx,
                'vy': vy,
                'size': sz,
                'color': col
            })

        # 4 tiny pinpoint spark dots (NO giant fireball, NO smoke cloud)
        self.sparks = []
        for _ in range(4):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(1.8, 3.5)
            self.sparks.append({
                'x': cx,
                'y': cy,
                'vx': math.cos(ang) * spd,
                'vy': math.sin(ang) * spd,
                'life': random.randint(2, 4)
            })

    def update(self):
        self.age += 1
        for s in self.shards:
            s['x'] += s['vx']
            s['y'] += s['vy']
            s['vy'] += 0.32  # gentle gravity pulling shards down
            s['vx'] *= 0.90
        for sp in self.sparks:
            sp['x'] += sp['vx']
            sp['y'] += sp['vy']
            sp['life'] -= 1

    def draw(self, draw):
        # 1. Direct impact flash on the 10x10 box itself
        if self.age <= 1:
            draw.rectangle([self.cx - 5, self.cy - 5, self.cx + 5, self.cy + 5], fill=FLASH_WHITE)
            draw.line([(self.cx - 6, self.cy), (self.cx + 6, self.cy)], fill=CYAN_ACCENT, width=1)
            draw.line([(self.cx, self.cy - 6), (self.cx, self.cy + 6)], fill=CYAN_ACCENT, width=1)
        elif self.age <= 3:
            r = 3 + self.age
            draw.ellipse([self.cx - r, self.cy - r, self.cx + r, self.cy + r], outline=CYAN_ACCENT, width=1)

        # 2. Green debris shards falling away
        for s in self.shards:
            hw = s['size'] / 2.0
            draw.rectangle([s['x'] - hw, s['y'] - hw, s['x'] + hw, s['y'] + hw], fill=s['color'])

        # 3. Pinpoint spark dots
        for sp in self.sparks:
            if sp['life'] > 0:
                draw.point((int(sp['x']), int(sp['y'])), fill=FLASH_WHITE)

# ==================== BATARANG PROJECTILE ====================
class Batarang:
    def __init__(self, x0, y0, x1, y1, duration=3):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.duration = duration
        self.progress = 0
        self.alive = True
        self.rot = 0.0

    def update(self):
        self.progress += 1
        self.rot += 1.2 # fast spin
        if self.progress >= self.duration:
            self.alive = False

    def draw(self, draw):
        t = self.progress / float(self.duration)
        prev_t = max(0.0, (self.progress - 0.9) / float(self.duration))
        curr_x = self.x0 + (self.x1 - self.x0) * t
        curr_y = self.y0 + (self.y1 - self.y0) * t
        tail_x = self.x0 + (self.x1 - self.x0) * prev_t
        tail_y = self.y0 + (self.y1 - self.y0) * prev_t

        # Glowing blue kinetic trail
        draw.line([(tail_x, tail_y), (curr_x, curr_y)], fill=(0, 200, 255), width=3)
        draw.line([(tail_x, tail_y), (curr_x, curr_y)], fill=(255, 255, 255), width=1)

        # Spinning Batarang
        r = 6.0
        cos_a = math.cos(self.rot)
        sin_a = math.sin(self.rot)
        # Bat wings contour
        local_pts = [
            (0, -r * 0.35),
            (-r * 0.6, -r * 0.9),
            (-r, -r * 0.3),
            (-r * 0.7, 0),
            (-r, r * 0.5),
            (0, r * 0.2),
            (r, r * 0.5),
            (r * 0.7, 0),
            (r, -r * 0.3),
            (r * 0.6, -r * 0.9)
        ]
        rot_pts = [
            (curr_x + px * cos_a - py * sin_a, curr_y + px * sin_a + py * cos_a)
            for px, py in local_pts
        ]
        draw.polygon(rot_pts, fill=(10, 14, 20), outline=(0, 240, 255))

# ==================== BATMAN SPRITE RENDERER ====================
def draw_batman(draw, x, y, aim_angle=-math.pi/4, firing=False, recoil=0, run_frame=0, victory=False):
    """
    Renders Batman at platform position (x, y). Height ~54px.
    """
    COWL_BLACK  = (10, 12, 16)
    COWL_DARK   = (18, 22, 28)
    COWL_MID    = (30, 36, 46)
    EYES_WHITE  = (240, 250, 255)
    EYES_CYAN   = (180, 230, 255)
    JAW_SKIN    = (210, 160, 120)

    SUIT_DARK   = (22, 26, 34)
    SUIT_MID    = (35, 42, 54)
    BAT_INSIGNIA= (8, 10, 14)

    UTILITY_GOLD= (235, 170, 20)
    BELT_DARK   = (160, 110, 10)

    CAPE_BLACK  = (8, 10, 14)
    CAPE_MID    = (16, 20, 26)
    CAPE_HIGHLIGHT = (28, 35, 48)

    GAUNTLET    = (14, 17, 22)
    BOOTS       = (10, 12, 16)

    head_y   = y - 50
    neck_y   = y - 38
    cowl_top = y - 53
    chest_y  = y - 36
    waist_y  = y - 22
    knees_y  = y - 11

    rc_shift = int(recoil)
    bx = x - rc_shift

    # 1. BILLOWING BAT CAPE (Drawn behind body)
    if victory:
        # Cape spreading out wide like bat wings
        pts = [
            (bx - 4, chest_y), (bx - 26, knees_y), (bx - 32, y + 2),
            (bx - 20, y - 4), (bx - 10, y + 1), (bx, y - 3),
            (bx + 10, y + 1), (bx + 20, y - 4), (bx + 32, y + 2),
            (bx + 26, knees_y), (bx + 4, chest_y)
        ]
        draw.polygon(pts, fill=CAPE_BLACK)
        draw.line([(bx - 4, chest_y), (bx - 32, y + 2)], fill=CAPE_HIGHLIGHT, width=2)
        draw.line([(bx + 4, chest_y), (bx + 32, y + 2)], fill=CAPE_HIGHLIGHT, width=2)
    elif run_frame > 0:
        # Flowing gently back in the wind
        flutter = ((run_frame // 2) % 3) * 2
        draw.polygon([
            (bx - 4, chest_y),
            (bx - 24 - flutter, knees_y - 4),
            (bx - 34 - flutter, y - 8),
            (bx - 26 - flutter, y - 2),
            (bx - 18, y),
            (bx - 2, waist_y)
        ], fill=CAPE_BLACK)
        draw.line([(bx - 4, chest_y), (bx - 34 - flutter, y - 8)], fill=CAPE_MID, width=2)
    else:
        # Heavy dark cape hanging
        draw.polygon([
            (bx - 6, chest_y + 2),
            (bx - 20, knees_y),
            (bx - 24, y),
            (bx - 15, y - 3),
            (bx - 8, y),
            (bx, waist_y)
        ], fill=CAPE_BLACK)
        draw.line([(bx - 6, chest_y + 2), (bx - 24, y)], fill=CAPE_MID, width=2)

    # 2. LEGS & COMBAT BOOTS
    if victory:
        draw.rectangle([bx - 10, waist_y, bx - 3, knees_y], fill=SUIT_MID)
        draw.rectangle([bx + 3, waist_y, bx + 10, knees_y], fill=SUIT_MID)
        draw.rectangle([bx - 11, knees_y, bx - 2, y - 5], fill=SUIT_DARK)
        draw.rectangle([bx + 2, knees_y, bx + 11, y - 5], fill=SUIT_DARK)
        draw.rounded_rectangle([bx - 13, y - 5, bx - 1, y], radius=2, fill=BOOTS)
        draw.rounded_rectangle([bx + 1, y - 5, bx + 13, y], radius=2, fill=BOOTS)
    elif run_frame > 0:
        cycle = (run_frame // 2) % 4
        if cycle == 0:
            draw.line([(bx - 5, waist_y), (bx - 14, knees_y), (bx - 17, y)], fill=SUIT_MID, width=7)
            draw.line([(bx + 5, waist_y), (bx + 10, knees_y), (bx + 14, y - 2)], fill=SUIT_DARK, width=7)
            draw.rounded_rectangle([bx - 21, y - 4, bx - 10, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([bx + 8, y - 6, bx + 19, y - 2], radius=2, fill=BOOTS)
        elif cycle == 1:
            draw.line([(bx - 5, waist_y), (bx - 6, knees_y), (bx - 8, y)], fill=SUIT_MID, width=7)
            draw.line([(bx + 5, waist_y), (bx + 6, knees_y), (bx + 8, y)], fill=SUIT_DARK, width=7)
            draw.rounded_rectangle([bx - 12, y - 4, bx - 2, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([bx + 2, y - 4, bx + 12, y], radius=2, fill=BOOTS)
        elif cycle == 2:
            draw.line([(bx - 5, waist_y), (bx + 9, knees_y), (bx + 14, y - 2)], fill=SUIT_DARK, width=7)
            draw.line([(bx + 5, waist_y), (bx - 12, knees_y), (bx - 16, y)], fill=SUIT_MID, width=7)
            draw.rounded_rectangle([bx + 8, y - 6, bx + 18, y - 2], radius=2, fill=BOOTS)
            draw.rounded_rectangle([bx - 20, y - 4, bx - 9, y], radius=2, fill=BOOTS)
        else:
            draw.line([(bx - 5, waist_y), (bx + 4, knees_y), (bx + 6, y)], fill=SUIT_DARK, width=7)
            draw.line([(bx + 5, waist_y), (bx - 4, knees_y), (bx - 6, y)], fill=SUIT_MID, width=7)
            draw.rounded_rectangle([bx + 2, y - 4, bx + 11, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([bx - 11, y - 4, bx - 2, y], radius=2, fill=BOOTS)
    else:
        draw.line([(bx - 5, waist_y), (bx - 11, knees_y), (bx - 14, y)], fill=SUIT_MID, width=7)
        draw.line([(bx + 5, waist_y), (bx + 9, knees_y), (bx + 13, y)], fill=SUIT_DARK, width=7)
        draw.rounded_rectangle([bx - 18, y - 5, bx - 7, y], radius=2, fill=BOOTS)
        draw.rounded_rectangle([bx + 7, y - 5, bx + 18, y], radius=2, fill=BOOTS)

    # 3. TORSO & BAT-ARMOR
    draw.rounded_rectangle([bx - 10, chest_y, bx + 10, waist_y], radius=3, fill=SUIT_MID, outline=COWL_BLACK)
    draw.line([(bx, chest_y + 3), (bx, waist_y - 4)], fill=COWL_DARK, width=1)

    # BAT-SYMBOL
    draw.polygon([
        (bx, chest_y + 8),
        (bx - 3, chest_y + 4),
        (bx - 7, chest_y + 3),
        (bx - 8, chest_y + 6),
        (bx - 5, chest_y + 9),
        (bx - 3, chest_y + 11),
        (bx, chest_y + 13),
        (bx + 3, chest_y + 11),
        (bx + 5, chest_y + 9),
        (bx + 8, chest_y + 6),
        (bx + 7, chest_y + 3),
        (bx + 3, chest_y + 4),
    ], fill=BAT_INSIGNIA)
    draw.line([(bx - 1, chest_y + 3), (bx - 1, chest_y + 2)], fill=BAT_INSIGNIA, width=1)
    draw.line([(bx + 1, chest_y + 3), (bx + 1, chest_y + 2)], fill=BAT_INSIGNIA, width=1)

    # GOLD UTILITY BELT
    draw.rectangle([bx - 10, waist_y - 4, bx + 10, waist_y], fill=UTILITY_GOLD)
    draw.rectangle([bx - 2, waist_y - 5, bx + 2, waist_y + 1], fill=BELT_DARK, outline=UTILITY_GOLD)
    draw.rectangle([bx - 8, waist_y - 4, bx - 5, waist_y], fill=BELT_DARK)
    draw.rectangle([bx + 5, waist_y - 4, bx + 8, waist_y], fill=BELT_DARK)

    # 4. BAT-COWL & FACE
    draw.rounded_rectangle([bx - 8, head_y, bx + 8, neck_y], radius=3, fill=COWL_DARK, outline=COWL_BLACK)
    draw.polygon([
        (bx - 4, neck_y - 4), (bx + 4, neck_y - 4),
        (bx + 3, neck_y), (bx - 3, neck_y)
    ], fill=JAW_SKIN)
    draw.line([(bx - 2, neck_y - 2), (bx + 2, neck_y - 2)], fill=(160, 110, 80), width=1)

    # BAT EARS
    draw.polygon([(bx - 8, head_y + 4), (bx - 8, head_y - 7), (bx - 4, head_y + 1)], fill=COWL_BLACK)
    draw.polygon([(bx + 4, head_y + 1), (bx + 8, head_y - 7), (bx + 8, head_y + 4)], fill=COWL_BLACK)
    draw.line([(bx - 8, head_y - 7), (bx - 5, head_y + 2)], fill=COWL_MID, width=1)
    draw.line([(bx + 8, head_y - 7), (bx + 5, head_y + 2)], fill=COWL_MID, width=1)

    # GLOWING WHITE SLIT EYES
    draw.polygon([(bx - 6, head_y + 5), (bx - 2, head_y + 7), (bx - 6, head_y + 7)], fill=EYES_WHITE)
    draw.polygon([(bx + 2, head_y + 7), (bx + 6, head_y + 5), (bx + 6, head_y + 7)], fill=EYES_WHITE)
    draw.point((bx - 4, head_y + 6), fill=EYES_CYAN)
    draw.point((bx + 4, head_y + 6), fill=EYES_CYAN)

    # 5. WEAPON & BAT-GAUNTLETS
    if victory:
        # Stoic Dark Knight victory pose
        draw.line([(bx - 6, chest_y + 4), (bx - 14, chest_y - 10), (bx - 10, chest_y - 24)], fill=SUIT_MID, width=5)
        draw.rectangle([bx - 12, chest_y - 26, bx - 8, chest_y - 22], fill=GAUNTLET)
        draw.polygon([(bx - 16, chest_y - 28), (bx - 10, chest_y - 24), (bx - 4, chest_y - 28), (bx - 10, chest_y - 22)], fill=COWL_BLACK)
        draw.polygon([(bx - 13, chest_y - 12), (bx - 17, chest_y - 10), (bx - 12, chest_y - 8)], fill=COWL_BLACK)
        draw.polygon([(bx - 12, chest_y - 16), (bx - 16, chest_y - 14), (bx - 11, chest_y - 12)], fill=COWL_BLACK)
        return (bx - 10, chest_y - 26)

    shoulder_x = bx + 4 - int(math.cos(aim_angle) * recoil * 1.5)
    shoulder_y = chest_y + 6 - int(math.sin(aim_angle) * recoil * 1.5)

    gun_len = 30
    barrel_x = shoulder_x + math.cos(aim_angle) * gun_len
    barrel_y = shoulder_y + math.sin(aim_angle) * gun_len

    nx = -math.sin(aim_angle) * 3
    ny =  math.cos(aim_angle) * 3

    p1 = (shoulder_x + nx, shoulder_y + ny)
    p2 = (barrel_x + nx, barrel_y + ny)
    p3 = (barrel_x - nx, barrel_y - ny)
    p4 = (shoulder_x - nx, shoulder_y - ny)
    draw.polygon([p1, p2, p3, p4], fill=COWL_BLACK)
    draw.line([(shoulder_x + nx, shoulder_y + ny), (barrel_x + nx, barrel_y + ny)], fill=COWL_MID, width=2)

    # Bat-fins on weapon
    draw.polygon([
        (shoulder_x + math.cos(aim_angle)*14 + nx*1.8, shoulder_y + math.sin(aim_angle)*14 + ny*1.8),
        (shoulder_x + math.cos(aim_angle)*18 + nx*3.0, shoulder_y + math.sin(aim_angle)*18 + ny*3.0),
        (shoulder_x + math.cos(aim_angle)*22 + nx*1.8, shoulder_y + math.sin(aim_angle)*22 + ny*1.8)
    ], fill=COWL_BLACK)

    draw.line([(bx - 6, chest_y + 4), (shoulder_x + math.cos(aim_angle)*20, shoulder_y + math.sin(aim_angle)*20)], fill=SUIT_MID, width=5)
    draw.line([(bx + 4, chest_y + 4), (shoulder_x + math.cos(aim_angle)*8, shoulder_y + math.sin(aim_angle)*8)], fill=SUIT_MID, width=5)

    # 3 Bat-fins on forearm gauntlet
    arm_mid_x = bx - 2
    arm_mid_y = chest_y + 8
    draw.polygon([(arm_mid_x, arm_mid_y), (arm_mid_x - 5, arm_mid_y - 3), (arm_mid_x - 2, arm_mid_y + 2)], fill=COWL_BLACK)
    draw.polygon([(arm_mid_x + 3, arm_mid_y + 3), (arm_mid_x - 2, arm_mid_y), (arm_mid_x + 1, arm_mid_y + 5)], fill=COWL_BLACK)

    if firing:
        spikes = [
            (0.0, 18, (255, 255, 255), 3),
            (0.35, 14, (100, 220, 255), 2),
            (-0.35, 14, (100, 220, 255), 2),
            (0.7, 10, (0, 140, 255), 2),
            (-0.7, 10, (0, 140, 255), 2),
        ]
        for a_off, length, col, w in spikes:
            a = aim_angle + a_off
            ex = barrel_x + math.cos(a) * length
            ey = barrel_y + math.sin(a) * length
            draw.line([(barrel_x, barrel_y), (ex, ey)], fill=col, width=w)
        draw.ellipse([barrel_x - 3, barrel_y - 3, barrel_x + 3, barrel_y + 3], fill=(255, 255, 255))

    return (barrel_x, barrel_y)

# ==================== MAIN GENERATOR ====================
def main():
    print("Fetching REAL 2D contribution grid for Mohammed-Ashraf-Shaik...")
    grid_2d = fetch_real_contributions("Mohammed-Ashraf-Shaik")
    
    # Calculate total active commits
    total_active_count = sum(sum(1 for lvl in row if lvl > 0) for row in grid_2d)
    print(f"Verified live contribution data: 7 rows x {len(grid_2d[0])} cols, {total_active_count} active commit days.")

    # Find ALL real green commit coordinates: (week, day, level)
    active_commit_cells = []
    for d in range(7):
        for w in range(len(grid_2d[d])):
            lvl = grid_2d[d][w]
            if lvl > 0:
                active_commit_cells.append((w, d, lvl))

    # Sort chronologically by week (left to right), then day
    active_commit_cells.sort(key=lambda item: (item[0], item[1]))
    N = len(active_commit_cells)
    print(f"Batman will target and CLEAR ALL {N} active contributions!")

    # Layout dimensions matching clean seamless widget (like Awaiz snake)
    CELL_SIZE = 10
    CELL_GAP  = 3
    GRID_X    = (WIDTH - (53 * (CELL_SIZE + CELL_GAP) - CELL_GAP)) // 2  # 102 (centered)
    GRID_Y    = 24
    GROUND_Y  = 176

    def get_cell_coord(w, d):
        cx = GRID_X + w * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        cy = GRID_Y + d * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        return (cx, cy)

    target_coords = {(w, d): get_cell_coord(w, d) for w, d, lvl in active_commit_cells}

    # Schedule shots for ALL N active contributions with comfortable pacing
    START_SHOOT = 16
    END_SHOOT = 150
    shot_map = {}
    hit_map = {}
    for i in range(N):
        sf = int(START_SHOOT + i * (END_SHOOT - START_SHOOT) / float(N))
        hf = sf + 4
        shot_map.setdefault(sf, []).append(active_commit_cells[i])
        hit_map.setdefault(hf, []).append(active_commit_cells[i])

    # Active grid state
    active_grid = [list(row) for row in grid_2d]
    destroyed_cells = set()
    explosions = []
    batarangs = []
    frames = []

    bat_x = 130.0
    run_cycle = 0

    print(f"Rendering {TOTAL_FRAMES} frames...")
    for f in range(TOTAL_FRAMES):
        # Zero screen shake: rock solid clarity
        shake_x = 0
        shake_y = 0

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. EXACT REAL CONTRIBUTION GRID (Seamless, centered, NO card borders, NO extra words)
        for d in range(7):
            for w in range(len(active_grid[d])):
                cx = GRID_X + w * (CELL_SIZE + CELL_GAP)
                cy = GRID_Y + d * (CELL_SIZE + CELL_GAP)

                if (w, d) in destroyed_cells:
                    # Scorched/empty cell slot
                    draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=(16, 20, 26), outline=(26, 32, 40))
                else:
                    lvl = active_grid[d][w]
                    col = GREEN_LEVELS[min(lvl, 4)]
                    outl = EMPTY_BORDER if lvl == 0 else col
                    draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=col, outline=outl)

        # 2. Clean Ground Line
        draw.line([(40, GROUND_Y), (WIDTH - 40, GROUND_Y)], fill=(30, 36, 46), width=1)

        # 3. Bottom Gradient Scale (Matching Awaiz snake structure at bottom-left)
        bar_w = 40
        bar_h = 6
        bar_y = GROUND_Y + 14
        for i, col in enumerate(GREEN_LEVELS[1:]):
            draw.rounded_rectangle([GRID_X + i * bar_w, bar_y, GRID_X + (i + 1) * bar_w, bar_y + bar_h], radius=2, fill=col)

        # 6. Batman Movement & Action
        upcoming_targets = [c for c in active_commit_cells if (c[0], c[1]) not in destroyed_cells]
        is_victory = (f >= 156)
        firing_now = (f in shot_map)
        recoil = 2 if firing_now else 0

        if upcoming_targets:
            cur_target = upcoming_targets[0]
            tgt_x, tgt_y = target_coords[(cur_target[0], cur_target[1])]
            
            # Subtle cyan target lock reticle on the active upcoming target
            if not is_victory and f >= START_SHOOT - 2:
                sz = 7
                tx, ty = tgt_x, tgt_y
                draw.line([(tx - sz, ty - sz), (tx - sz + 3, ty - sz)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx - sz, ty - sz), (tx - sz, ty - sz + 3)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx + sz, ty - sz), (tx + sz - 3, ty - sz)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx + sz, ty - sz), (tx + sz, ty - sz + 3)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx - sz, ty + sz), (tx - sz + 3, ty + sz)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx - sz, ty + sz), (tx - sz, ty + sz - 3)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx + sz, ty + sz), (tx + sz - 3, ty + sz)], fill=CYAN_ACCENT, width=1)
                draw.line([(tx + sz, ty + sz), (tx + sz, ty + sz - 3)], fill=CYAN_ACCENT, width=1)
        else:
            cur_target = active_commit_cells[-1]
            tgt_x, tgt_y = target_coords[(cur_target[0], cur_target[1])]

        # Dynamic positioning of Batman with smooth walk speed limit
        MAX_WALK_SPEED = 3.0
        if f < START_SHOOT:
            first_tgt_x = target_coords[(active_commit_cells[0][0], active_commit_cells[0][1])][0]
            desired_x = max(110, min(first_tgt_x - 65, 730))
            diff = desired_x - bat_x
            move = math.copysign(min(abs(diff) * 0.12, MAX_WALK_SPEED), diff)
            bat_x += move
            if abs(move) > 0.3:
                run_cycle += 1
            else:
                run_cycle = 0
        elif f <= END_SHOOT:
            desired_x = max(110, min(tgt_x - 60, 730))
            diff = desired_x - bat_x
            move = math.copysign(min(abs(diff) * 0.12, MAX_WALK_SPEED), diff)
            bat_x += move
            if abs(move) > 0.3:
                run_cycle += 1
            else:
                run_cycle = 0
        else:
            # End sequence: walk calmly to victory mark
            desired_x = min(730, target_coords[(active_commit_cells[-1][0], active_commit_cells[-1][1])][0] - 40)
            diff = desired_x - bat_x
            move = math.copysign(min(abs(diff) * 0.10, MAX_WALK_SPEED * 0.6), diff)
            bat_x += move
            run_cycle = 0

        dx = tgt_x - (bat_x + 4)
        dy = tgt_y - (GROUND_Y - 30)
        aim_angle = math.atan2(dy, dx)

        # Fire Batarangs (4-frame flight duration for clear trajectory tracking)
        if f in shot_map:
            for w_s, d_s, lvl_s in shot_map[f]:
                bx_est = bat_x + 4 + math.cos(aim_angle) * 28
                by_est = (GROUND_Y - 30) + math.sin(aim_angle) * 28
                dest_x, dest_y = target_coords[(w_s, d_s)]
                batarangs.append(Batarang(bx_est, by_est, dest_x, dest_y, duration=4))

        # Handle Hits: Shatter box cleanly with 100% localized debris chips
        if f in hit_map:
            for w_h, d_h, lvl_h in hit_map[f]:
                dest_x, dest_y = target_coords[(w_h, d_h)]
                explosions.append(BoxShatter(dest_x, dest_y, lvl_h if lvl_h > 0 else 2))
                destroyed_cells.add((w_h, d_h))

        # Draw Batman
        draw_batman(
            draw,
            int(bat_x),
            GROUND_Y,
            aim_angle=aim_angle,
            firing=firing_now,
            recoil=recoil,
            run_frame=run_cycle,
            victory=is_victory
        )

        # 7. Batarangs
        for b in batarangs:
            b.update()
            if b.alive:
                b.draw(draw)
        batarangs = [b for b in batarangs if b.alive]

        # 8. Box Shatter Particles
        for exp in explosions:
            exp.update()
            exp.draw(draw)
        explosions = [exp for exp in explosions if exp.age <= exp.max_age]

        frames.append(img)

    print(f"Rendered {len(frames)} frames. Quantizing and encoding GIF...")

    sample_frame = frames[77]
    palette_img = sample_frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT)

    opt_frames = []
    for fr in frames:
        q = fr.quantize(palette=palette_img, dither=Image.Dither.NONE)
        opt_frames.append(q)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    primary_out = os.path.join(repo_root, "commit_buster.gif")
    
    out_paths = [primary_out]
    if os.path.abspath(os.getcwd()) != repo_root:
        out_paths.append(os.path.join(os.getcwd(), "commit_buster.gif"))

    for p in set(out_paths):
        opt_frames[0].save(
            p,
            save_all=True,
            append_images=opt_frames[1:],
            duration=FRAME_DURATION,
            loop=0,
            optimize=True
        )
        print(f"Saved {p}: {os.path.getsize(p) // 1024} KB")
        print(f"Saved {p}: {os.path.getsize(p) // 1024} KB")

if __name__ == "__main__":
    main()
