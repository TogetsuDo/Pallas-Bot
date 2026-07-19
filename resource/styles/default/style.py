"""帮助图背景：全不透明绘制，避免透明角在查看器中呈黑色。"""

from PIL import Image, ImageDraw

CANVAS = (250, 247, 243)
SURFACE = (255, 252, 249)
BORDER = (210, 202, 194)

FRAME_PAD = 20
RADIUS = 28


def draw_clarity_canvas(xs: int, ys: int) -> Image.Image:
    img = Image.new("RGB", (xs, ys), CANVAS)
    draw = ImageDraw.Draw(img)
    x1, y1 = FRAME_PAD, FRAME_PAD
    x2, y2 = max(x1 + 2, xs - FRAME_PAD), max(y1 + 2, ys - FRAME_PAD)
    draw.rounded_rectangle((x1, y1, x2, y2), radius=RADIUS, fill=SURFACE, outline=BORDER, width=2)
    return img.convert("RGBA")
