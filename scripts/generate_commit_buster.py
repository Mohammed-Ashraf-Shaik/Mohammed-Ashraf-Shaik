import os
import math
import random
import urllib.request
import re
from PIL import Image, ImageDraw, ImageFont

# ==================== CONFIGURATION ====================
WIDTH = 890
HEIGHT = 270
FPS = 25
TOTAL_FRAMES = 115

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

# ==================== EXPLOSION SYSTEM ====================
class Shard:
    def __init__(self, x, y, vx, vy, color, size, rot_speed):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.angle = random.uniform(0, math.pi * 2)
        self.rot_speed = rot_speed
        self.life = random.randint(14, 20)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.28
        self.vx *= 0.94
        self.angle += self.rot_speed
        self.life -= 1

    def draw(self, draw):
        if self.life <= 0:
            return
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        hw = self.size / 2.0
        hh = (self.size * 1.3) / 2.0
        pts = [
            (self.x + cos_a * (-hw) - sin_a * (-hh), self.y + sin_a * (-hw) + cos_a * (-hh)),
            (self.x + cos_a * (hw)  - sin_a * (-hh), self.y + sin_a * (hw)  + cos_a * (-hh)),
            (self.x + cos_a * (hw)  - sin_a * (hh),  self.y + sin_a * (hw)  + cos_a * (hh)),
            (self.x + cos_a * (-hw) - sin_a * (hh),  self.y + sin_a * (-hw) + cos_a * (hh))
        ]
        draw.polygon(pts, fill=self.color)

class EpicExplosion:
    def __init__(self, x, y, level=4):
        self.x = x
        self.y = y
        self.level = level
        self.age = 0
        self.max_age = 20

        self.shards = []
        box_colors = [HOT_GREEN, (57, 211, 83), (38, 166, 65), (200, 255, 210), FLASH_YELLOW]
        for _ in range(24):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.5, 9.5)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 2.2
            c = random.choice(box_colors)
            sz = random.uniform(2.5, 5.2)
            rot_spd = random.uniform(-0.4, 0.4)
            self.shards.append(Shard(x, y, vx, vy, c, sz, rot_spd))

        self.sparks = []
        for _ in range(28):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(4.5, 12.5)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - 1.2
            c = random.choice([FLASH_WHITE, FLASH_YELLOW, (255, 180, 50), CYAN_ACCENT])
            self.sparks.append({
                'x': x, 'y': y, 'vx': vx, 'vy': vy, 'color': c,
                'life': random.randint(6, 12)
            })

    def update(self):
        self.age += 1
        for s in self.shards:
            s.update()
        for sp in self.sparks:
            sp['x'] += sp['vx']
            sp['y'] += sp['vy']
            sp['vx'] *= 0.92
            sp['vy'] *= 0.92
            sp['life'] -= 1

    def draw(self, draw):
        if self.age < 15:
            sw_r = self.age * 3.6
            factor = max(0.0, 1.0 - (self.age / 15.0))
            sw_col = (int(HOT_GREEN[0] * factor), int(HOT_GREEN[1] * factor), int(HOT_GREEN[2] * factor))
            if sw_r > 2:
                draw.ellipse([self.x - sw_r, self.y - sw_r, self.x + sw_r, self.y + sw_r], outline=sw_col, width=2)

        if 2 <= self.age < 11:
            sw2_r = (self.age - 2) * 2.8
            factor2 = max(0.0, 1.0 - ((self.age - 2) / 9.0))
            sw2_col = (int(FLASH_YELLOW[0] * factor2), int(FLASH_YELLOW[1] * factor2), int(FLASH_YELLOW[2] * factor2))
            if sw2_r > 2:
                draw.ellipse([self.x - sw2_r, self.y - sw2_r, self.x + sw2_r, self.y + sw2_r], outline=sw2_col, width=1)

        if self.age <= 3:
            r = max(5, int(self.age * 5.2))
            draw.ellipse([self.x - r - 2, self.y - r - 2, self.x + r + 2, self.y + r + 2], fill=HOT_GREEN)
            draw.ellipse([self.x - r, self.y - r, self.x + r, self.y + r], fill=FLASH_WHITE)
            star_len = r * 2.6
            draw.line([(self.x - star_len, self.y), (self.x + star_len, self.y)], fill=FLASH_WHITE, width=2)
            draw.line([(self.x, self.y - star_len), (self.x, self.y + star_len)], fill=FLASH_WHITE, width=2)
        elif self.age <= 8:
            fb_r = int(16 - (self.age - 3) * 1.6)
            lobes = [
                (self.x, self.y, fb_r + 2),
                (self.x - fb_r*0.6, self.y - fb_r*0.4, fb_r * 0.8),
                (self.x + fb_r*0.6, self.y - fb_r*0.4, fb_r * 0.8),
                (self.x - fb_r*0.5, self.y + fb_r*0.5, fb_r * 0.7),
                (self.x + fb_r*0.5, self.y + fb_r*0.5, fb_r * 0.7)
            ]
            for lx, ly, lr in lobes:
                draw.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=FLASH_ORANGE)
            for lx, ly, lr in lobes:
                draw.ellipse([lx - lr*0.6, ly - lr*0.6, lx + lr*0.6, ly + lr*0.6], fill=FLASH_YELLOW)
        elif self.age <= 14:
            sm_y = self.y - (self.age - 8) * 1.5
            sm_r = int(11 + (self.age - 8) * 1.2)
            alpha_sm = max(0.0, 1.0 - (self.age - 8) / 6.0)
            c = (int(50 * alpha_sm), int(60 * alpha_sm), int(75 * alpha_sm))
            draw.ellipse([self.x - sm_r, sm_y - sm_r, self.x + sm_r, sm_y + sm_r], fill=c)

        for s in self.shards:
            s.draw(draw)

        for sp in self.sparks:
            if sp['life'] > 0:
                sx, sy = sp['x'], sp['y']
                draw.line([(sx, sy), (sx - sp['vx']*0.8, sy - sp['vy']*0.8)], fill=sp['color'], width=1)
                draw.point((sx, sy), fill=FLASH_WHITE)

# ==================== BATARANG PROJECTILE ====================
class Batarang:
    def __init__(self, x0, y0, x1, y1, duration=4):
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
        # Flowing back in the wind
        flutter = (run_frame % 3) * 3
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
        cycle = run_frame % 4
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

    # Find all real green commit coordinates: (week, day, level)
    active_commit_cells = []
    for d in range(7):
        for w in range(len(grid_2d[d])):
            lvl = grid_2d[d][w]
            if lvl > 0:
                active_commit_cells.append((w, d, lvl))

    # Sort chronologically by week (left to right)
    active_commit_cells.sort(key=lambda item: (item[0], item[1]))

    # Select 5 real targets from the user's live commits across his active periods:
    # Target 1: Early in the year (e.g. around week 23, Feb 2026)
    # Target 2: Mid-year (e.g. around week 46, Aug 2026)
    # Target 3, 4, 5: Recent commits (weeks 50, 51, 52 - late Aug & Sep 2026)
    def find_best_commit(target_w):
        return min(active_commit_cells, key=lambda c: abs(c[0] - target_w))

    real_t1 = find_best_commit(23)
    real_t2 = find_best_commit(46)
    real_t3 = find_best_commit(50)
    real_t4 = find_best_commit(51)
    real_t5 = find_best_commit(52)

    chosen_targets = []
    for t in [real_t1, real_t2, real_t3, real_t4, real_t5]:
        if (t[0], t[1]) not in [(c[0], c[1]) for c in chosen_targets]:
            chosen_targets.append(t)
            
    while len(chosen_targets) < 5:
        avail = [c for c in active_commit_cells if (c[0], c[1]) not in [(x[0], x[1]) for x in chosen_targets]]
        if avail:
            chosen_targets.append(avail[0])
        else:
            break

    print(f"Batman will target the user's actual progress: {chosen_targets}")

    # Layout dimensions matching clean GitHub cards
    CELL_SIZE = 10
    CELL_GAP  = 3
    GRID_X    = 64
    GRID_Y    = 62
    GROUND_Y  = 238

    def get_cell_coord(w, d):
        cx = GRID_X + w * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        cy = GRID_Y + d * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        return (cx, cy)

    target_coords = {(w, d): get_cell_coord(w, d) for w, d, lvl in chosen_targets}

    MONTH_NAMES = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    day_map = [("Mon", 1), ("Wed", 3), ("Fri", 5)]

    # Clean shot sequence (NO combo text, NO score numbers!)
    shots = [
        (20, chosen_targets[0]),
        (44, chosen_targets[1]),
        (66, chosen_targets[2]),
        (74, chosen_targets[3]),
        (82, chosen_targets[4])
    ]

    # Active grid state
    active_grid = [list(row) for row in grid_2d]
    destroyed_cells = set()
    explosions = []
    batarangs = []
    frames = []

    print(f"Rendering {TOTAL_FRAMES} frames...")
    for f in range(TOTAL_FRAMES):
        shake_x, shake_y = 0, 0
        for shot_f, _ in shots:
            if f == shot_f + 4:
                shake_x = random.choice([-2, 2])
                shake_y = random.choice([-1, 1])

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. Outer Card Border
        draw.rounded_rectangle([2, 2, WIDTH - 3, HEIGHT - 3], radius=12, fill=BG_COLOR, outline=CARD_BORDER, width=1)

        # 2. CLEAN GITHUB HEADER (No arcade HUD, no scores, no badges!)
        # Sleek GitHub-style header with Batman symbol & clean title
        draw.text((22, 16), "Mohammed-Ashraf-Shaik / Contributions", fill=WHITE, font=FONT_HEADER)
        draw.text((22, 33), f"{total_active_count} contributions in the last year  •  The Dark Knight of Code", fill=MUTED, font=FONT_SUB)

        draw.line([(15, 48), (WIDTH - 15, 48)], fill=HEADER_LINE, width=1)

        # 3. Month Labels
        for mi, mname in enumerate(MONTH_NAMES):
            col_x = GRID_X + mi * int(53 / 12 * (CELL_SIZE + CELL_GAP)) + shake_x
            draw.text((col_x, GRID_Y - 13 + shake_y), mname, fill=MUTED, font=FONT_LABEL)

        # Day Labels (Mon, Wed, Fri)
        for dname, drow in day_map:
            dy = GRID_Y + drow * (CELL_SIZE + CELL_GAP) + 1 + shake_y
            draw.text((GRID_X - 28 + shake_x, dy), dname, fill=MUTED, font=FONT_LABEL)

        # 4. EXACT REAL CONTRIBUTION GRID (2D mapped: Row d, Col w)
        for d in range(7):
            for w in range(len(active_grid[d])):
                cx = GRID_X + w * (CELL_SIZE + CELL_GAP) + shake_x
                cy = GRID_Y + d * (CELL_SIZE + CELL_GAP) + shake_y

                if (w, d) in destroyed_cells:
                    # Scorched cell
                    draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=(18, 22, 28), outline=(28, 33, 40))
                else:
                    lvl = active_grid[d][w]
                    col = GREEN_LEVELS[min(lvl, 4)]
                    outl = EMPTY_BORDER if lvl == 0 else col
                    draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=col, outline=outl)

        # Subtle Bat-Targeting Lock on active upcoming target
        active_shot = None
        for shot_f, t_info in shots:
            if f < shot_f and (shot_f - f) <= 8:
                active_shot = (shot_f, t_info)
                break

        if active_shot:
            w_tgt, d_tgt, _ = active_shot[1]
            tx, ty = target_coords[(w_tgt, d_tgt)]
            tx += shake_x
            ty += shake_y
            sz = 8
            # Minimalist target reticle
            draw.line([(tx - sz, ty - sz), (tx - sz + 3, ty - sz)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx - sz, ty - sz), (tx - sz, ty - sz + 3)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx + sz, ty - sz), (tx + sz - 3, ty - sz)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx + sz, ty - sz), (tx + sz, ty - sz + 3)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx - sz, ty + sz), (tx - sz + 3, ty + sz)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx - sz, ty + sz), (tx - sz, ty + sz - 3)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx + sz, ty + sz), (tx + sz - 3, ty + sz)], fill=CYAN_ACCENT, width=1)
            draw.line([(tx + sz, ty + sz), (tx + sz, ty + sz - 3)], fill=CYAN_ACCENT, width=1)

        # 5. Clean Cyber Ground Line
        draw.line([(15, GROUND_Y), (WIDTH - 15, GROUND_Y)], fill=(30, 36, 46), width=1)

        # Clean Legend (Exact GitHub style)
        leg_x = WIDTH - 215
        leg_y = GROUND_Y + 14
        draw.text((leg_x - 30, leg_y), "Less", fill=MUTED, font=FONT_LABEL)
        for li in range(5):
            lx = leg_x + li * 14
            draw.rounded_rectangle([lx, leg_y, lx + 10, leg_y + 10], radius=2, fill=GREEN_LEVELS[li])
        draw.text((leg_x + 5 * 14 + 6, leg_y), "More", fill=MUTED, font=FONT_LABEL)

        # 6. Batman Movement & Action
        # Calculate X positions giving 45-degree heroic angles to the targets
        # Target 1 (week ~23) -> cx ~ 363 -> stand at ~ 290
        # Target 2 (week ~46) -> cx ~ 662 -> stand at ~ 580
        # Target 3,4,5 (weeks 50-52) -> cx ~ 714-740 -> stand at ~ 650
        bat_x = 290
        run_cycle = 0
        firing_now = False
        is_victory = (f >= 92)

        t1_x = target_coords[(chosen_targets[0][0], chosen_targets[0][1])][0]
        t2_x = target_coords[(chosen_targets[1][0], chosen_targets[1][1])][0]
        t3_x = target_coords[(chosen_targets[2][0], chosen_targets[2][1])][0]

        stand1 = max(60, t1_x - 70)
        stand2 = max(stand1 + 60, t2_x - 80)
        stand3 = max(stand2 + 50, t3_x - 75)

        if f < 14:
            t = f / 14.0
            bat_x = 60 + t * (stand1 - 60)
            run_cycle = f
        elif f < 28:
            bat_x = stand1
        elif f < 40:
            t = (f - 28) / 12.0
            bat_x = stand1 + t * (stand2 - stand1)
            run_cycle = f
        elif f < 54:
            bat_x = stand2
        elif f < 64:
            t = (f - 54) / 10.0
            bat_x = stand2 + t * (stand3 - stand2)
            run_cycle = f
        else:
            bat_x = stand3

        if f < 30:
            cur_target = chosen_targets[0]
        elif f < 55:
            cur_target = chosen_targets[1]
        elif f < 70:
            cur_target = chosen_targets[2]
        elif f < 78:
            cur_target = chosen_targets[3]
        else:
            cur_target = chosen_targets[4]

        tgt_x, tgt_y = target_coords[(cur_target[0], cur_target[1])]

        dx = tgt_x - (bat_x + 4)
        dy = tgt_y - (GROUND_Y - 30)
        aim_angle = math.atan2(dy, dx)

        recoil = 0
        for shot_f, t_info in shots:
            w_s, d_s, lvl_s = t_info
            if f == shot_f:
                firing_now = True
                recoil = 4
                bx_est = bat_x + 4 + math.cos(aim_angle) * 30
                by_est = (GROUND_Y - 30) + math.sin(aim_angle) * 30
                dest_x, dest_y = target_coords[(w_s, d_s)]
                batarangs.append(Batarang(bx_est, by_est, dest_x, dest_y, duration=4))

            if f == shot_f + 4:
                dest_x, dest_y = target_coords[(w_s, d_s)]
                lvl = active_grid[d_s][w_s]
                explosions.append(EpicExplosion(dest_x, dest_y, lvl if lvl > 0 else 4))
                destroyed_cells.add((w_s, d_s))

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

        # 8. Explosions (Big, dramatic debris & blast clouds)
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
        q = fr.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
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
            duration=40,
            loop=0,
            optimize=True
        )
        print(f"Saved {p}: {os.path.getsize(p) // 1024} KB")

if __name__ == "__main__":
    main()
