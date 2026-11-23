import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
PROD = sys.argv[1]          # pasta do produto
CLIP_A = sys.argv[2]        # surpresa
CLIP_B = sys.argv[3]        # apontando
OUT = sys.argv[4]           # video sem audio

MONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
EMO = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
NAVY = (11, 18, 32); GREEN = (46, 230, 140); YEL = (255, 206, 40); RED = (255, 59, 59); WHITE = (255, 255, 255)

def font(size, w="Black"):
    f = ImageFont.truetype(MONT, size); f.set_variation_by_name(w); return f

def emoji(ch, size):
    f = ImageFont.truetype(EMO, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def sticker(parts, bg, fg=WHITE, size=60, pad=(34, 22), radius=999, stroke=None, weight="Black"):
    """parts: lista de strings; strings entre [] sao emoji"""
    f = font(size, weight)
    pieces = []
    for p in parts:
        if p.startswith("[") and p.endswith("]"):
            pieces.append(emoji(p[1:-1], int(size * 1.05)))
        else:
            bb = f.getbbox(p)
            im = Image.new("RGBA", (bb[2] - bb[0] + 4, int(size * 1.25)), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((-bb[0] + 2, int(size * 0.12) - bb[1] + 0), p, font=f, fill=fg)
            pieces.append(im)
    gap = int(size * 0.3)
    tw = sum(p.width for p in pieces) + gap * (len(pieces) - 1)
    th = max(p.height for p in pieces)
    bw, bh = tw + 2 * pad[0], th + 2 * pad[1]
    out = Image.new("RGBA", (bw + 16, bh + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    r = min(radius, bh // 2)
    d.rounded_rectangle([8, 14, 8 + bw, 14 + bh], r, fill=(0, 0, 0, 110))  # sombra
    d.rounded_rectangle([8, 6, 8 + bw, 6 + bh], r, fill=bg + (255,), outline=stroke, width=5 if stroke else 0)
    x = 8 + pad[0]
    for p in pieces:
        out.alpha_composite(p, (x, 6 + pad[1] + (th - p.height) // 2)); x += p.width + gap
    return out

def text_block(lines, size, fill=WHITE, stroke=NAVY, sw=10, weight="Black", spacing=8):
    f = font(size, weight)
    ims = []
    for l in lines:
        bb = f.getbbox(l, stroke_width=sw)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 4, -bb[1] + 4), l, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
        ims.append(im)
    w = max(i.width for i in ims); h = sum(i.height for i in ims) + spacing * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + spacing
    return out

# ---------- animacoes ----------
def ease_back(x):
    x = max(0, min(1, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

def place(frame, st, cx, cy, t, t0, t1=99, dur=0.28, pulse=0, wobble=0, slide=0):
    if t < t0 or t > t1: return
    s = ease_back((t - t0) / dur)
    if pulse: s *= 1 + pulse * math.sin((t - t0) * 2 * math.pi * 1.6)
    if s <= 0.02: return
    im = st.resize((max(1, int(st.width * s)), max(1, int(st.height * s))), Image.BILINEAR)
    if wobble: im = im.rotate(wobble * math.sin((t - t0) * 2 * math.pi * 1.3), expand=True, resample=Image.BICUBIC)
    a = min(1, (t1 - t) / 0.15) if t1 < 99 else 1
    if a < 1:
        al = im.getchannel("A").point(lambda v: int(v * a)); im.putalpha(al)
    dx = int(slide * (1 - min(1, (t - t0) / dur)))
    frame.alpha_composite(im, (int(cx - im.width / 2) + dx, int(cy - im.height / 2)))

# ---------- fundos ----------
def bg_navy():
    g = np.zeros((H, W, 3), np.uint8)
    yy = np.linspace(0, 1, H)[:, None]
    for i, (a, b) in enumerate(zip((14, 22, 40), (6, 10, 20))):
        g[..., i] = (a * (1 - yy) + b * yy).astype(np.uint8)
    im = Image.fromarray(g).convert("RGBA")
    d = ImageDraw.Draw(im)
    for r, a in ((620, 35), (420, 45)):   # brilho verde atras do produto
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([W / 2 - r, 900 - r, W / 2 + r, 900 + r], fill=GREEN + (a,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    return im

def product_card(size):
    p = Image.open(f"{PROD}/1-foto.jpg").convert("RGBA").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size, size], 48, fill=255)
    card = Image.new("RGBA", (size, size), (0, 0, 0, 0)); card.paste(p, (0, 0), m)
    return card

NAV = bg_navy()
CARD_BIG = product_card(860)
CARD_SM = product_card(640)
AVAL = Image.open(f"{PROD}/4-avaliacao.jpg").convert("RGBA").resize((W, H))

info = json.load(open(f"{PROD}/info.json"))
de, por, pct, vendas, nota = info["de"], info["por"], info["pct"], info["vendas"], info["nota"]
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------- stickers ----------
S = {}
S["hook1"] = text_block(["GENTE, OLHA", "ESSE PREÇO!"], 104, fill=YEL)
S["hook2"] = text_block(info["hook"], 60, fill=WHITE, sw=9)
S["aproveite"] = sticker(["[⚡]", "APROVEITE AGORA"], RED, size=46)
S["chip1"] = sticker([info["chips"][0]], NAVY, fg=GREEN, size=50, stroke=GREEN)
S["chip2"] = sticker([info["chips"][1]], NAVY, fg=GREEN, size=50, stroke=GREEN)
S["chip3"] = sticker([info["chips"][2]], NAVY, fg=GREEN, size=50, stroke=GREEN)
S["de"] = text_block([f"DE {brl(de)}"], 70, fill=(200, 205, 215), stroke=NAVY, sw=6, weight="Bold")
S["porlbl"] = text_block([info.get("porlbl", "POR APENAS")], 58, fill=WHITE, sw=6, weight="ExtraBold")
S["por"] = text_block([brl(por)], 170, fill=GREEN, sw=12)
S["pct"] = sticker([f"-{pct}%"], YEL, fg=NAVY, size=86, pad=(36, 26))
S["subir"] = sticker(["[⏰]", "PREÇO PODE SUBIR A QUALQUER MOMENTO"], YEL, fg=NAVY, size=38, radius=20, pad=(26, 18))
S["compraram"] = sticker(["[🔥]", "QUEM COMPROU APROVOU"], RED, size=54)
S["bio"] = sticker(["[🔗]", "O LINK TÁ NA BIO!"], GREEN, fg=NAVY, size=66)
S["coment1"] = text_block(["OU COMENTA"], 72, fill=WHITE)
S["quero"] = sticker(["[💬]", "QUERO"], YEL, fg=NAVY, size=96, pad=(40, 24))
S["coment2"] = text_block(["QUE A GENTE TE MANDA!"], 60, fill=WHITE)
S["seta"] = emoji("👇", 120)
S["aviso"] = sticker([f"Preço consultado em {info['data']}, pode mudar"], (0, 0, 0), size=28, weight="SemiBold", pad=(20, 10))

# ---------- linha do tempo ----------
T = [0, 3.2, 5.2, 9.2, 11.4, 18.4]
CUTS = T[1:5]
N = int(T[-1] * FPS)

def clip_reader(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},fps={FPS}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield Image.fromarray(np.frombuffer(b, np.uint8).reshape(H, W, 3)).convert("RGBA")

ra, rb = clip_reader(CLIP_A), clip_reader(CLIP_B)
last = None
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", OUT],
                       stdin=subprocess.PIPE)

def zoomed(im, z, cx=W / 2, cy=H / 2):
    w, h = int(W / z), int(H / z)
    return im.crop((int(cx - w / 2), int(cy - h / 2), int(cx - w / 2) + w, int(cy - h / 2) + h)).resize((W, H), Image.BILINEAR)

for n in range(N):
    t = n / FPS
    if t < T[1]:                                  # 1) gancho com a personagem
        last = next(ra, last); f = last.copy()
        z = 1 + 0.06 * min(1, t / 3.2); f = zoomed(f, z)
        place(f, S["hook1"], W / 2, 300, t, 0.15, pulse=0.03)
        place(f, S["hook2"], W / 2, 510, t, 0.9)
    elif t < T[2]:                                # 2) produto em destaque
        lt = t - T[1]; f = NAV.copy()
        sc = 1 + 0.05 * lt
        c = CARD_BIG.resize((int(860 * sc), int(860 * sc)), Image.BILINEAR)
        f.alpha_composite(c, ((W - c.width) // 2, 860 - c.height // 2 + int(80 * (1 - ease_back(lt / 0.35)))))
        place(f, S["chip1"], W / 2 - 270, 1450, t, T[1] + 0.35, slide=-200)
        place(f, S["chip2"], W / 2 + 230, 1450, t, T[1] + 0.65, slide=200)
        place(f, S["chip3"], W / 2, 1580, t, T[1] + 0.95)
    elif t < T[3]:                                # 3) preco
        lt = t - T[2]; f = NAV.copy()
        f.alpha_composite(CARD_SM, ((W - 640) // 2, 330))
        place(f, S["de"], W / 2, 1080, t, T[2] + 0.2)
        if t > T[2] + 0.55:                       # risco animado
            k = min(1, (t - T[2] - 0.55) / 0.25); dw = S["de"].width
            ImageDraw.Draw(f).line([(W / 2 - dw / 2, 1085), (W / 2 - dw / 2 + dw * k, 1075)], fill=RED + (255,), width=12)
        place(f, S["porlbl"], W / 2, 1185, t, T[2] + 0.95)
        place(f, S["por"], W / 2, 1330, t, T[2] + 1.15, dur=0.35, pulse=0.035)
        place(f, S["pct"], W / 2 + 300, 420, t, T[2] + 1.5, wobble=8)
        place(f, S["subir"], W / 2, 1560, t, T[2] + 2.1, pulse=0.04)
    elif t < T[4]:                                # 4) prova social
        lt = t - T[3]; f = zoomed(AVAL, 1 + 0.04 * lt)
        place(f, S["compraram"], W / 2, 1640, t, T[3] + 0.3, pulse=0.04, wobble=3)
    else:                                         # 5) chamada final com a personagem
        last = next(rb, last); f = last.copy()
        place(f, S["bio"], W / 2, 260, t, T[4] + 0.15, pulse=0.04)
        place(f, S["coment1"], W / 2, 1270, t, T[4] + 2.4)
        place(f, S["quero"], W / 2, 1420, t, T[4] + 2.7, pulse=0.06, wobble=4)
        place(f, S["coment2"], W / 2, 1570, t, T[4] + 3.0)
        if t > T[4] + 3.2:
            off = int(18 * abs(math.sin((t - T[4]) * 2 * math.pi * 1.5)))
            f.alpha_composite(S["seta"], ((W - S["seta"].width) // 2, 1660 + off))
        place(f, S["aviso"], W / 2, 1860, t, T[4] + 0.5)
    if T[1] <= t < T[3]:
        place(f, S["aproveite"], W / 2, 150, t, T[1] + 0.05, pulse=0.05)
    for c in CUTS:                                # flash nas trocas de cena
        if 0 <= t - c < 0.13:
            a = int(200 * (1 - (t - c) / 0.13))
            f.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, a)))
    enc.stdin.write(f.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
print("ok", N)
