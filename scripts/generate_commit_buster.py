import os
import math
import random
import urllib.request
import re
from PIL import Image, ImageDraw, ImageFont

# ==================== CONFIGURATION ====================
WIDTH = 890
HEIGHT = 285
FPS = 25
TOTAL_FRAMES = 115

# GitHub Dark Theme Colors
BG_COLOR    = (13, 17, 23)
CARD_BORDER = (48, 54, 61)
HEADER_LINE = (33, 38, 45)
EMPTY_CELL  = (22, 27, 34)
EMPTY_BORDER= (33, 38, 45)

GREEN_LEVELS = [
    (22, 27, 34),     # 0: empty
    (14, 68, 41),     # 1: dark green
    (0, 109, 50),     # 2: medium green
    (38, 166, 65),    # 3: light green
    (57, 211, 83)     # 4: bright green
]

HOT_GREEN   = (0, 255, 136)
CYAN_ACCENT = (0, 229, 255)
GOLD_ACCENT = (255, 215, 0)
WHITE       = (240, 246, 252)
MUTED       = (110, 118, 129)
FLASH_WHITE = (255, 255, 255)
FLASH_YELLOW= (255, 230, 50)
FLASH_ORANGE= (255, 110, 20)

# ==================== FONTS ====================
def get_font(size, bold=False):
    font_names = ['segoeuib.ttf' if bold else 'segoeui.ttf', 'arialbd.ttf' if bold else 'arial.ttf', 'consola.ttf']
    for name in font_names:
        p = os.path.join('C:\\Windows\\Fonts', name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

FONT_TITLE   = get_font(13, bold=True)
FONT_SUB     = get_font(10, bold=False)
FONT_HUD_LBL = get_font(9, bold=True)
FONT_HUD_VAL = get_font(12, bold=True)
FONT_LABEL   = get_font(9, bold=False)
FONT_POPUP   = get_font(11, bold=True)
FONT_VICTORY = get_font(13, bold=True)

# ==================== SCRAPE CONTRIBUTIONS ====================
def fetch_contributions(username="Mohammed-Ashraf-Shaik"):
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            matches = re.findall(r'data-level="(\d+)"[^>]*data-date="([^"]+)"', html)
            if not matches:
                matches = re.findall(r'data-date="([^"]+)"[^>]*data-level="(\d+)"', html)
                matches = [(m[1], m[0]) for m in matches]
            if matches:
                levels = [int(m[0]) for m in matches]
                if len(levels) >= 371:
                    return levels[-371:]
                return levels
    except Exception as e:
        print("Fetch error, using fallback calendar:", e)

    random.seed(1337)
    grid = []
    for _ in range(53 * 7):
        grid.append(random.choice([1, 2, 3, 4]) if random.random() > 0.86 else 0)
    return grid

# ==================== PARTICLE & EXPLOSION SYSTEM ====================
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

class Bullet:
    def __init__(self, x0, y0, x1, y1, duration=3):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.duration = duration
        self.progress = 0
        self.alive = True

    def update(self):
        self.progress += 1
        if self.progress >= self.duration:
            self.alive = False

    def draw(self, draw):
        t = self.progress / float(self.duration)
        prev_t = max(0.0, (self.progress - 0.9) / float(self.duration))
        curr_x = self.x0 + (self.x1 - self.x0) * t
        curr_y = self.y0 + (self.y1 - self.y0) * t
        tail_x = self.x0 + (self.x1 - self.x0) * prev_t
        tail_y = self.y0 + (self.y1 - self.y0) * prev_t

        draw.line([(tail_x, tail_y), (curr_x, curr_y)], fill=CYAN_ACCENT, width=4)
        draw.line([(tail_x, tail_y), (curr_x, curr_y)], fill=FLASH_WHITE, width=2)
        draw.ellipse([curr_x - 3, curr_y - 3, curr_x + 3, curr_y + 3], fill=FLASH_WHITE)

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 18

    def update(self):
        self.y -= 1.3
        self.life -= 1

    def draw(self, draw, font):
        if self.life > 0:
            draw.text((self.x + 1, self.y + 1), self.text, fill=(0, 0, 0), font=font, anchor="mm")
            draw.text((self.x, self.y), self.text, fill=self.color, font=font, anchor="mm")

# ==================== PIXEL ART HELPERS ====================
def draw_pixel_star(draw, cx, cy, r=6, col=GOLD_ACCENT):
    """Draws a 5-point vector star at (cx, cy)."""
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * (math.pi / 5)
        cur_r = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * cur_r, cy + math.sin(a) * cur_r))
    draw.polygon(pts, fill=col)

def draw_muzzle_flash(draw, fx, fy, aim_angle):
    """Draws a multi-spike energetic starburst muzzle flash."""
    spikes = [
        (0.0, 20, FLASH_WHITE, 4),
        (0.35, 15, FLASH_YELLOW, 2),
        (-0.35, 15, FLASH_YELLOW, 2),
        (0.7, 11, FLASH_ORANGE, 2),
        (-0.7, 11, FLASH_ORANGE, 2),
        (1.1, 7, FLASH_ORANGE, 1),
        (-1.1, 7, FLASH_ORANGE, 1),
    ]
    for a_off, length, col, w in spikes:
        a = aim_angle + a_off
        ex = fx + math.cos(a) * length
        ey = fy + math.sin(a) * length
        draw.line([(fx, fy), (ex, ey)], fill=col, width=w)
    draw.ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=FLASH_WHITE, outline=FLASH_YELLOW)

def draw_hero_sprite(draw, x, y, aim_angle=-math.pi/4, firing=False, recoil=0, run_frame=0, victory=False, charge_glow=False):
    HELMET_DARK = (20, 24, 30)
    HELMET_MID  = (36, 44, 56)
    HELMET_LIGHT= (55, 65, 81)
    VISOR_CORE  = (220, 255, 255)
    VISOR_CYAN  = (0, 229, 255)

    SKIN        = (215, 160, 120)
    ARMOR_DARK  = (25, 30, 40)
    ARMOR_MID   = (40, 50, 68)
    CORE_GLOW   = (0, 255, 136)

    BELT        = (18, 22, 28)
    POUCHES     = (50, 60, 75)
    PANTS_DARK  = (22, 28, 38)
    PANTS_MID   = (35, 45, 60)
    KNEE_PAD    = (50, 60, 75)
    BOOTS       = (12, 16, 22)

    CANNON_DARK = (20, 24, 32)
    CANNON_METAL= (60, 72, 90)
    CANNON_LIGHT= (90, 105, 130)
    CANNON_NEON = (255, 220, 0) if charge_glow else (0, 240, 255)

    head_y = y - 50
    neck_y = y - 38
    chest_y = y - 36
    waist_y = y - 22
    knees_y = y - 11

    # 1. Jetpack
    jp_x = x - 12
    draw.rounded_rectangle([jp_x - 5, chest_y - 2, jp_x + 3, waist_y + 2], radius=2, fill=HELMET_DARK, outline=HELMET_MID)
    draw.polygon([(jp_x - 4, waist_y + 2), (jp_x + 2, waist_y + 2), (jp_x - 1, waist_y + 7)], fill=HELMET_MID)
    if run_frame > 0 or firing:
        flame_len = 9 if firing else 6
        draw.polygon([(jp_x - 3, waist_y + 3), (jp_x + 1, waist_y + 3), (jp_x - 1, waist_y + 3 + flame_len)], fill=FLASH_ORANGE)
        draw.polygon([(jp_x - 2, waist_y + 3), (jp_x, waist_y + 3), (jp_x - 1, waist_y + 3 + flame_len - 2)], fill=FLASH_YELLOW)

    # 2. Legs & Feet
    if victory:
        draw.rectangle([x - 11, waist_y, x - 4, knees_y], fill=PANTS_MID)
        draw.rectangle([x + 4, waist_y, x + 11, knees_y], fill=PANTS_MID)
        draw.rectangle([x - 12, knees_y, x - 3, y - 5], fill=PANTS_DARK)
        draw.rectangle([x + 3, knees_y, x + 12, y - 5], fill=PANTS_DARK)
        draw.rounded_rectangle([x - 14, y - 5, x - 2, y], radius=2, fill=BOOTS)
        draw.rounded_rectangle([x + 2, y - 5, x + 14, y], radius=2, fill=BOOTS)
    elif run_frame > 0:
        cycle = run_frame % 4
        if cycle == 0:
            draw.line([(x - 6, waist_y), (x - 15, knees_y), (x - 18, y)], fill=PANTS_MID, width=7)
            draw.line([(x + 6, waist_y), (x + 11, knees_y), (x + 15, y - 2)], fill=PANTS_DARK, width=7)
            draw.rounded_rectangle([x - 22, y - 4, x - 11, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([x + 9, y - 6, x + 20, y - 2], radius=2, fill=BOOTS)
        elif cycle == 1:
            draw.line([(x - 6, waist_y), (x - 7, knees_y), (x - 9, y)], fill=PANTS_MID, width=7)
            draw.line([(x + 6, waist_y), (x + 7, knees_y), (x + 9, y)], fill=PANTS_DARK, width=7)
            draw.rounded_rectangle([x - 13, y - 4, x - 3, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([x + 3, y - 4, x + 13, y], radius=2, fill=BOOTS)
        elif cycle == 2:
            draw.line([(x - 6, waist_y), (x + 10, knees_y), (x + 15, y - 2)], fill=PANTS_DARK, width=7)
            draw.line([(x + 6, waist_y), (x - 13, knees_y), (x - 17, y)], fill=PANTS_MID, width=7)
            draw.rounded_rectangle([x + 9, y - 6, x + 19, y - 2], radius=2, fill=BOOTS)
            draw.rounded_rectangle([x - 21, y - 4, x - 10, y], radius=2, fill=BOOTS)
        else:
            draw.line([(x - 6, waist_y), (x + 5, knees_y), (x + 7, y)], fill=PANTS_DARK, width=7)
            draw.line([(x + 6, waist_y), (x - 5, knees_y), (x - 7, y)], fill=PANTS_MID, width=7)
            draw.rounded_rectangle([x + 3, y - 4, x + 12, y], radius=2, fill=BOOTS)
            draw.rounded_rectangle([x - 12, y - 4, x - 3, y], radius=2, fill=BOOTS)
    else:
        rc_shift = int(recoil * 0.8)
        draw.line([(x - 6 - rc_shift, waist_y), (x - 12 - rc_shift, knees_y), (x - 15 - rc_shift, y)], fill=PANTS_MID, width=7)
        draw.line([(x + 6 - rc_shift, waist_y), (x + 10 - rc_shift, knees_y), (x + 14 - rc_shift, y)], fill=PANTS_DARK, width=7)
        draw.rectangle([x - 15 - rc_shift, knees_y - 3, x - 9 - rc_shift, knees_y + 3], fill=KNEE_PAD)
        draw.rectangle([x + 7 - rc_shift, knees_y - 3, x + 13 - rc_shift, knees_y + 3], fill=KNEE_PAD)
        draw.rounded_rectangle([x - 20 - rc_shift, y - 5, x - 8 - rc_shift, y], radius=2, fill=BOOTS)
        draw.rounded_rectangle([x + 8 - rc_shift, y - 5, x + 20 - rc_shift, y], radius=2, fill=BOOTS)

    # 3. Torso & Armor
    rc_shift = int(recoil)
    tx = x - rc_shift
    draw.rounded_rectangle([tx - 10, chest_y, tx + 10, waist_y], radius=3, fill=ARMOR_MID, outline=ARMOR_DARK)
    draw.rounded_rectangle([tx - 8, chest_y + 2, tx + 8, waist_y - 4], radius=2, fill=ARMOR_DARK)
    draw.rounded_rectangle([tx - 4, chest_y + 5, tx + 4, chest_y + 11], radius=2, fill=CORE_GLOW)
    draw.rectangle([tx - 2, chest_y + 7, tx + 2, chest_y + 9], fill=FLASH_WHITE)
    draw.rectangle([tx - 11, waist_y - 4, tx + 11, waist_y], fill=BELT)
    draw.rectangle([tx - 9, waist_y - 3, tx - 5, waist_y + 1], fill=POUCHES)
    draw.rectangle([tx + 5, waist_y - 3, tx + 9, waist_y + 1], fill=POUCHES)

    # 4. Head & Helmet
    hx = tx
    draw.rounded_rectangle([hx - 9, head_y, hx + 9, neck_y], radius=4, fill=HELMET_MID, outline=HELMET_DARK)
    draw.rounded_rectangle([hx - 2, head_y + 4, hx + 10, head_y + 9], radius=2, fill=VISOR_CYAN)
    draw.line([(hx + 1, head_y + 5), (hx + 9, head_y + 5)], fill=VISOR_CORE, width=2)
    draw.rectangle([hx - 9, head_y + 3, hx - 6, head_y + 9], fill=HELMET_LIGHT)
    draw.line([(hx - 7, head_y), (hx - 7, head_y - 6)], fill=CANNON_METAL, width=2)
    draw.point((hx - 7, head_y - 6), fill=CORE_GLOW)

    # 5. Weapon
    if victory:
        # Cannon held up in right hand
        draw.rounded_rectangle([tx + 8, chest_y - 28, tx + 16, chest_y + 6], radius=2, fill=CANNON_DARK)
        draw.line([(tx + 12, chest_y - 28), (tx + 12, chest_y - 38)], fill=CANNON_METAL, width=5)
        draw.rectangle([tx + 10, chest_y - 38, tx + 14, chest_y - 34], fill=CANNON_NEON)
        # Smoke wisp from muzzle
        draw.line([(tx + 12, chest_y - 39), (tx + 14, chest_y - 44)], fill=(130, 145, 165), width=2)
        draw.line([(tx + 14, chest_y - 44), (tx + 12, chest_y - 48)], fill=(100, 115, 135), width=1)
        # Left arm raised fist pump
        draw.line([(tx - 8, chest_y + 4), (tx - 16, chest_y - 6), (tx - 14, chest_y - 18)], fill=ARMOR_MID, width=5)
        draw.rectangle([tx - 18, chest_y - 22, tx - 12, chest_y - 17], fill=SKIN)
        return (tx + 12, chest_y - 38)

    shoulder_x = tx + 4 - int(math.cos(aim_angle) * recoil * 1.5)
    shoulder_y = chest_y + 6 - int(math.sin(aim_angle) * recoil * 1.5)

    cannon_len = 34
    barrel_x = shoulder_x + math.cos(aim_angle) * cannon_len
    barrel_y = shoulder_y + math.sin(aim_angle) * cannon_len

    nx = -math.sin(aim_angle) * 3
    ny =  math.cos(aim_angle) * 3

    p1 = (shoulder_x + nx, shoulder_y + ny)
    p2 = (barrel_x + nx, barrel_y + ny)
    p3 = (barrel_x - nx, barrel_y - ny)
    p4 = (shoulder_x - nx, shoulder_y - ny)
    draw.polygon([p1, p2, p3, p4], fill=CANNON_DARK)
    draw.line([(shoulder_x + nx*1.3, shoulder_y + ny*1.3), (barrel_x + nx*1.3, barrel_y + ny*1.3)], fill=CANNON_METAL, width=3)

    for coil_i in [0.35, 0.55, 0.75]:
        cx = shoulder_x + math.cos(aim_angle) * (cannon_len * coil_i)
        cy = shoulder_y + math.sin(aim_angle) * (cannon_len * coil_i)
        draw.line([(cx + nx*1.8, cy + ny*1.8), (cx - nx*1.8, cy - ny*1.8)], fill=CANNON_NEON, width=2)

    draw.line([(barrel_x + nx*1.6, barrel_y + ny*1.6), (barrel_x - nx*1.6, barrel_y - ny*1.6)], fill=CANNON_LIGHT, width=3)

    grip1_x = shoulder_x + math.cos(aim_angle) * 10
    grip1_y = shoulder_y + math.sin(aim_angle) * 10
    grip2_x = shoulder_x + math.cos(aim_angle) * 22
    grip2_y = shoulder_y + math.sin(aim_angle) * 22

    draw.line([(tx - 6, chest_y + 4), (grip2_x, grip2_y)], fill=ARMOR_MID, width=5)
    draw.rectangle([grip2_x - 2, grip2_y - 2, grip2_x + 2, grip2_y + 2], fill=SKIN)
    draw.line([(tx + 4, chest_y + 4), (grip1_x, grip1_y)], fill=ARMOR_MID, width=5)
    draw.rectangle([grip1_x - 2, grip1_y - 2, grip1_x + 2, grip1_y + 2], fill=SKIN)

    if firing:
        draw_muzzle_flash(draw, barrel_x, barrel_y, aim_angle)

    return (barrel_x, barrel_y)

# ==================== MAIN GENERATOR ====================
def main():
    print("Fetching actual contributions for Mohammad-Ashraf-Shaik...")
    raw_levels = fetch_contributions("Mohammed-Ashraf-Shaik")
    grid_cells = raw_levels[:371]
    if len(grid_cells) < 371:
        grid_cells += [0] * (371 - len(grid_cells))

    green_indices = [i for i, lvl in enumerate(grid_cells) if lvl > 0]
    print(f"Total green commits: {len(green_indices)}")

    def pick_nearest(target_idx):
        if not green_indices:
            return target_idx
        return min(green_indices, key=lambda x: abs(x - target_idx))

    t1 = pick_nearest(76)   # Feb
    t2 = pick_nearest(206)  # Mid year
    t3 = pick_nearest(336)  # Late Aug
    t4 = pick_nearest(348)  # Early Sep
    t5 = pick_nearest(366)  # Mid Sep latest

    chosen_targets = []
    for t in [t1, t2, t3, t4, t5]:
        if t not in chosen_targets:
            chosen_targets.append(t)
    while len(chosen_targets) < 5:
        avail = [idx for idx in green_indices if idx not in chosen_targets]
        if avail:
            chosen_targets.append(avail[0])
        else:
            chosen_targets.append(len(chosen_targets) * 60)

    print("Targets for destruction:", chosen_targets)

    CELL_SIZE = 10
    CELL_GAP = 3
    GRID_X = 64
    GRID_Y = 68
    GROUND_Y = 244

    def get_cell_coord(idx):
        w = idx // 7
        d = idx % 7
        cx = GRID_X + w * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        cy = GRID_Y + d * (CELL_SIZE + CELL_GAP) + CELL_SIZE // 2
        return (cx, cy)

    target_coords = {t: get_cell_coord(t) for t in chosen_targets}

    MONTH_NAMES = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    day_map = [("Mon", 1), ("Wed", 3), ("Fri", 5)]

    shots = [
        (20, chosen_targets[0], "+100 PTS", 100),
        (44, chosen_targets[1], "CRITICAL! +250", 250),
        (66, chosen_targets[2], "COMBO x3! +200", 200),
        (74, chosen_targets[3], "COMBO x4! +300", 300),
        (82, chosen_targets[4], "OBLITERATED! +500", 500)
    ]

    active_grid = list(grid_cells)
    destroyed_cells = set()
    explosions = []
    floating_texts = []
    bullets = []
    frames = []

    current_score = 1200

    print(f"Rendering {TOTAL_FRAMES} frames...")
    for f in range(TOTAL_FRAMES):
        shake_x, shake_y = 0, 0
        for shot_f, _, _, _ in shots:
            if f == shot_f + 3:
                shake_x = random.choice([-2, 2])
                shake_y = random.choice([-1, 1])

        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. Outer Card Border
        draw.rounded_rectangle([2, 2, WIDTH - 3, HEIGHT - 3], radius=12, fill=BG_COLOR, outline=CARD_BORDER, width=1)

        # 2. Header Bar
        draw.rounded_rectangle([18, 10, 82, 28], radius=4, fill=(30, 41, 59), outline=CARD_BORDER)
        draw.text((50, 19), "ARCADE", fill=CYAN_ACCENT, font=FONT_HUD_LBL, anchor="mm")

        draw.text((92, 19), "COMMIT BUSTER // CONTRIBUTION ANNIHILATOR", fill=GOLD_ACCENT, font=FONT_TITLE, anchor="lm")
        draw.text((18, 36), "Target: Green Commit Boxes  •  Operator: @Mohammed-Ashraf-Shaik  •  Defense: ACTIVE", fill=MUTED, font=FONT_SUB)

        # Header Right Badges
        draw.rectangle([WIDTH - 275, 10, WIDTH - 170, 42], fill=(22, 27, 34), outline=CARD_BORDER)
        draw.text((WIDTH - 267, 14), "SCORE", fill=MUTED, font=FONT_HUD_LBL)
        draw.text((WIDTH - 267, 26), f"{current_score:05d}", fill=GOLD_ACCENT, font=FONT_HUD_VAL)

        status_text = "ANNIHILATING..." if f < 90 else "CLEARED! [PERFECT]"
        status_color = CYAN_ACCENT if f < 90 else HOT_GREEN
        draw.rectangle([WIDTH - 160, 10, WIDTH - 18, 42], fill=(22, 27, 34), outline=(35, 134, 54) if f >= 90 else CARD_BORDER)
        draw.text((WIDTH - 152, 14), "STATUS", fill=MUTED, font=FONT_HUD_LBL)
        draw.text((WIDTH - 152, 26), status_text, fill=status_color, font=FONT_HUD_VAL)

        draw.line([(15, 48), (WIDTH - 15, 48)], fill=HEADER_LINE, width=1)

        # 3. Month Labels
        for mi, mname in enumerate(MONTH_NAMES):
            col_x = GRID_X + mi * int(53 / 12 * (CELL_SIZE + CELL_GAP)) + shake_x
            draw.text((col_x, GRID_Y - 13 + shake_y), mname, fill=MUTED, font=FONT_LABEL)

        # Day Labels
        for dname, drow in day_map:
            dy = GRID_Y + drow * (CELL_SIZE + CELL_GAP) + 1 + shake_y
            draw.text((GRID_X - 28 + shake_x, dy), dname, fill=MUTED, font=FONT_LABEL)

        # 4. Contribution Grid
        for idx in range(371):
            w = idx // 7
            d = idx % 7
            cx = GRID_X + w * (CELL_SIZE + CELL_GAP) + shake_x
            cy = GRID_Y + d * (CELL_SIZE + CELL_GAP) + shake_y

            if idx in destroyed_cells:
                draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=(18, 22, 28), outline=(28, 33, 40))
            else:
                lvl = active_grid[idx]
                col = GREEN_LEVELS[min(lvl, 4)]
                outl = EMPTY_BORDER if lvl == 0 else col
                draw.rounded_rectangle([cx, cy, cx + CELL_SIZE, cy + CELL_SIZE], radius=2, fill=col, outline=outl)

        # Target Crosshair Lock Reticle
        active_shot = None
        for shot_f, t_idx, txt, pts in shots:
            if f < shot_f and (shot_f - f) <= 10:
                active_shot = (shot_f, t_idx)
                break

        if active_shot:
            tx, ty = target_coords[active_shot[1]]
            tx += shake_x
            ty += shake_y
            pulse = (f % 4 < 2)
            ret_col = (255, 60, 60) if pulse else GOLD_ACCENT
            sz = 9
            draw.line([(tx - sz, ty - sz), (tx - sz + 4, ty - sz)], fill=ret_col, width=1)
            draw.line([(tx - sz, ty - sz), (tx - sz, ty - sz + 4)], fill=ret_col, width=1)
            draw.line([(tx + sz, ty - sz), (tx + sz - 4, ty - sz)], fill=ret_col, width=1)
            draw.line([(tx + sz, ty - sz), (tx + sz, ty - sz + 4)], fill=ret_col, width=1)
            draw.line([(tx - sz, ty + sz), (tx - sz + 4, ty + sz)], fill=ret_col, width=1)
            draw.line([(tx - sz, ty + sz), (tx - sz, ty - sz + 4)], fill=ret_col, width=1)
            draw.line([(tx + sz, ty + sz), (tx + sz - 4, ty + sz)], fill=ret_col, width=1)
            draw.line([(tx + sz, ty + sz), (tx + sz, ty + sz - 4)], fill=ret_col, width=1)

        # 5. Cyber Platform Walkway
        draw.line([(15, GROUND_Y), (WIDTH - 15, GROUND_Y)], fill=(40, 50, 65), width=2)
        for px in range(20, WIDTH - 20, 24):
            draw.line([(px, GROUND_Y), (px + 12, GROUND_Y + 12)], fill=(22, 28, 38), width=1)
        draw.line([(15, GROUND_Y + 14), (WIDTH - 15, GROUND_Y + 14)], fill=HEADER_LINE, width=1)

        # Footer Status & Legend
        leg_x = WIDTH - 215
        leg_y = GROUND_Y + 20
        draw.text((leg_x - 30, leg_y), "Less", fill=MUTED, font=FONT_LABEL)
        for li in range(5):
            lx = leg_x + li * 14
            draw.rounded_rectangle([lx, leg_y, lx + 10, leg_y + 10], radius=2, fill=GREEN_LEVELS[li])
        draw.text((leg_x + 5 * 14 + 6, leg_y), "More", fill=MUTED, font=FONT_LABEL)

        draw.text((20, leg_y), "AUTOMATIC GREEN BLOCK ANNIHILATOR  •  FIRE-ON-SIGHT PROTOCOL", fill=MUTED, font=FONT_LABEL)

        # 6. Commando Movement & Action
        soldier_x = 135
        run_cycle = 0
        firing_now = False
        is_victory = (f >= 90)
        charge_glow = False

        if f < 14:
            t = f / 14.0
            soldier_x = 40 + t * (135 - 40)
            run_cycle = f
        elif f < 28:
            soldier_x = 135
        elif f < 40:
            t = (f - 28) / 12.0
            soldier_x = 135 + t * (370 - 135)
            run_cycle = f
        elif f < 54:
            soldier_x = 370
            charge_glow = (40 <= f < 44)
        elif f < 64:
            t = (f - 54) / 10.0
            soldier_x = 370 + t * (610 - 370)
            run_cycle = f
        else:
            soldier_x = 610

        if f < 30:
            cur_target_idx = chosen_targets[0]
        elif f < 55:
            cur_target_idx = chosen_targets[1]
        elif f < 70:
            cur_target_idx = chosen_targets[2]
        elif f < 78:
            cur_target_idx = chosen_targets[3]
        else:
            cur_target_idx = chosen_targets[4]

        tgt_x, tgt_y = target_coords[cur_target_idx]

        dx = tgt_x - (soldier_x + 4)
        dy = tgt_y - (GROUND_Y - 30)
        aim_angle = math.atan2(dy, dx)

        if active_shot and not is_victory and run_cycle == 0:
            bx_est = soldier_x + 4 + math.cos(aim_angle) * 34
            by_est = (GROUND_Y - 30) + math.sin(aim_angle) * 34
            dist = math.hypot(tgt_x - bx_est, tgt_y - by_est)
            steps = max(2, int(dist / 8))
            for si in range(0, steps, 2):
                p_start = (bx_est + (tgt_x - bx_est) * (si / steps), by_est + (tgt_y - by_est) * (si / steps))
                p_end   = (bx_est + (tgt_x - bx_est) * (min(si + 1, steps) / steps), by_est + (tgt_y - by_est) * (min(si + 1, steps) / steps))
                draw.line([p_start, p_end], fill=CYAN_ACCENT, width=1)

        recoil = 0
        for shot_f, t_idx, txt, pts in shots:
            if f == shot_f:
                firing_now = True
                recoil = 5
                bx_est = soldier_x + 4 + math.cos(aim_angle) * 34
                by_est = (GROUND_Y - 30) + math.sin(aim_angle) * 34
                dest_x, dest_y = target_coords[t_idx]
                bullets.append(Bullet(bx_est, by_est, dest_x, dest_y, duration=3))

            if f == shot_f + 3:
                dest_x, dest_y = target_coords[t_idx]
                lvl = active_grid[t_idx]
                explosions.append(EpicExplosion(dest_x, dest_y, lvl if lvl > 0 else 4))
                destroyed_cells.add(t_idx)
                floating_texts.append(FloatingText(dest_x, dest_y - 8, txt, GOLD_ACCENT))
                current_score += pts

        draw_hero_sprite(
            draw,
            int(soldier_x),
            GROUND_Y,
            aim_angle=aim_angle,
            firing=firing_now,
            recoil=recoil,
            run_frame=run_cycle,
            victory=is_victory,
            charge_glow=charge_glow
        )

        # 7. Bullets
        for b in bullets:
            b.update()
            if b.alive:
                b.draw(draw)
        bullets = [b for b in bullets if b.alive]

        # 8. Explosions
        for exp in explosions:
            exp.update()
            exp.draw(draw)
        explosions = [exp for exp in explosions if exp.age <= exp.max_age]

        # 9. Floating Texts
        for ft in floating_texts:
            ft.update()
            ft.draw(draw, FONT_POPUP)
        floating_texts = [ft for ft in floating_texts if ft.life > 0]

        # 10. Victory Banner with clean pixel stars
        if is_victory:
            banner_y = GROUND_Y - 45
            draw.text((WIDTH // 2, banner_y), "ALL COMMITS DESTROYED // STREAK DEFENDED!", fill=GOLD_ACCENT, font=FONT_VICTORY, anchor="mm")
            # Draw flanking gold pixel stars
            draw_pixel_star(draw, WIDTH // 2 - 188, banner_y, r=6, col=GOLD_ACCENT)
            draw_pixel_star(draw, WIDTH // 2 + 188, banner_y, r=6, col=GOLD_ACCENT)

        frames.append(img)

    print(f"Rendered {len(frames)} frames. Quantizing and encoding GIF...")

    sample_frame = frames[77]
    palette_img = sample_frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT)

    opt_frames = []
    for fr in frames:
        q = fr.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
        opt_frames.append(q)

    repo_scripts_dir = os.path.join("Mohammed-Ashraf-Shaik", "scripts")
    os.makedirs(repo_scripts_dir, exist_ok=True)

    out_paths = [
        "commit_buster.gif",
        os.path.join("Mohammed-Ashraf-Shaik", "commit_buster.gif")
    ]

    for p in out_paths:
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
