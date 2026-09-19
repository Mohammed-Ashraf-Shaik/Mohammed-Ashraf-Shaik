import os
from PIL import Image, ImageDraw, ImageFont

def generate_name_gif(output_path='name_animation.gif'):
    font_candidates = [
        'C:\\Windows\\Fonts\\consolab.ttf',
        'C:\\Windows\\Fonts\\consola.ttf',
        'C:\\Windows\\Fonts\\segoeuib.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ]
    font = None
    for p in font_candidates:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, 28)
                break
            except:
                pass
    if not font:
        font = ImageFont.load_default()

    text = "Hi there, I'm Mohammad Ashraf Shaik"
    m_idx = text.find('Mohammad')
    a_idx = text.find('Ashraf')

    char_w = font.getlength('M') if hasattr(font, 'getlength') else 15.0
    total_w = char_w * len(text)

    WIDTH = 680
    HEIGHT = 50
    start_x = (WIDTH - total_w) / 2
    y = (HEIGHT - 28) / 2 - 2

    BG_COLOR = (13, 17, 23)   # #0d1117 (GitHub Dark)
    GREEN = (57, 211, 83)      # #39d353
    WHITE = (255, 255, 255)    # pure white for M and A

    frames = []
    blank_img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    frames.append(blank_img)

    # Type letter by letter
    for count in range(1, len(text) + 1):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        for i in range(count):
            ch = text[i]
            col = WHITE if i in (m_idx, a_idx) else GREEN
            draw.text((start_x + i * char_w, y), ch, fill=col, font=font)
        frames.append(img)

    # Hold complete text for 22 frames (22 * 75ms = ~1.65 seconds)
    full_img = frames[-1]
    for _ in range(22):
        frames.append(full_img)

    # Blank pause at end before looping (4 frames * 75ms = 0.3s)
    for _ in range(4):
        frames.append(blank_img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=75,
        loop=0,
        optimize=True
    )
    print(f"Generated {output_path}: {len(frames)} frames, {os.path.getsize(output_path)//1024} KB")

if __name__ == '__main__':
    generate_name_gif('name_animation.gif')
