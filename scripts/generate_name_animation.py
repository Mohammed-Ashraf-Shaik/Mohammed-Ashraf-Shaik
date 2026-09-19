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

    BG_COLOR = (13, 17, 23)
    GREEN = (57, 211, 83)
    WHITE = (255, 255, 255)

    def make_frame(count):
        img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        for i in range(count):
            ch = text[i]
            col = WHITE if i in (m_idx, a_idx) else GREEN
            draw.text((start_x + i * char_w, y), ch, fill=col, font=font)
        return img

    frames = []
    durations = []

    # 1. Initial blank pause (350ms)
    frames.append(make_frame(0))
    durations.append(350)

    # 2. Type forward letter-by-letter (70ms per char)
    for count in range(1, len(text) + 1):
        frames.append(make_frame(count))
        durations.append(70)

    # 3. Hold complete text (1800ms)
    frames.append(make_frame(len(text)))
    durations.append(1800)

    # 4. Reverse backspace letter-by-letter (40ms per char)
    for count in range(len(text) - 1, -1, -1):
        frames.append(make_frame(count))
        durations.append(40)

    # disposal=2 ensures each frame fully replaces the previous one
    # so reverse frames actually remove characters visually
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2
    )
    print(f"Generated {output_path}: {len(frames)} frames, {os.path.getsize(output_path)//1024} KB")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    out = os.path.join(repo_root, 'name_animation.gif')
    generate_name_gif(out)
