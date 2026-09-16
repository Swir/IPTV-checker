from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "icon.ico"
SIZE = 512

im = Image.new("RGBA", (SIZE, SIZE), (5, 15, 27, 255))
for blur, alpha in ((24, 80), (12, 110)):
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((32, 32, 480, 480), radius=108, outline=(45, 155, 220, alpha), width=10)
    draw.rounded_rectangle((104, 174, 408, 392), radius=42, outline=(74, 210, 255, alpha), width=18)
    draw.line((166, 284, 224, 342, 350, 210), fill=(78, 225, 255, alpha), width=30, joint="curve")
    im = Image.alpha_composite(im, layer.filter(ImageFilter.GaussianBlur(blur)))

draw = ImageDraw.Draw(im)
draw.rounded_rectangle((28, 28, 484, 484), radius=108, fill=(7, 17, 31, 255), outline=(30, 96, 145, 255), width=12)
draw.line((172, 122, 256, 184, 340, 122), fill=(49, 127, 171, 255), width=18, joint="curve")
draw.rounded_rectangle((104, 174, 408, 392), radius=42, fill=(7, 24, 39, 255), outline=(71, 211, 255, 255), width=18)
draw.line((166, 284, 224, 342, 350, 210), fill=(88, 223, 255, 255), width=30, joint="curve")
draw.line((180, 430, 332, 430), fill=(88, 223, 255, 235), width=18)
OUT.parent.mkdir(parents=True, exist_ok=True)
im.save(OUT, sizes=[(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)])
print(f"Generated {OUT}")
