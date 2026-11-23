"""Monta o video (sem audio) de um produto num dos 5 estilos.
Uso: python3 render.py <pasta_produto> <pasta_clipes> <saida_video.mp4> <saida_timeline.json>
info.json do produto precisa de: de, por, pct, vendas, nota, data, hook, chips, porlbl, n (1..5), data_iso (AAAA-MM-DD)."""
import sys, os, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estilos import estilo_do_video, NAVY, WHITE, YEL, RED

PROD, CLIPS, OUT, TL = sys.argv[1:5]
W, H, FPS = 1080, 1920, 30
MONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
EMO = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

info = json.load(open(f"{PROD}/info.json"))
idx, EST, TM, TOPO_TXT, ALERTA_TXT = estilo_do_video(info["n"], info["data_iso"])
if "estilo" in info: idx = info["estilo"]; from estilos import ESTILOS, TEMAS, TOPO, ALERTA; EST = ESTILOS[idx]; TM = TEMAS[EST["tema"]]
STROKE = TM["contorno"]

def font(size, w="Black"):
    f = ImageFont.truetype(MONT, size); f.set_variation_by_name(w); return f

def emoji(ch, size):
    f = ImageFont.truetype(EMO, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def sticker(parts, bg, fg=WHITE, size=60, pad=(34, 22), radius=999, stroke=None, weight="Black"):
    f = font(size, weight); pieces = []
    for p in parts:
        if p.startswith("[") and p.endswith("]"):
            pieces.append(emoji(p[1:-1], int(size * 1.05)))
        else:
            bb = f.getbbox(p)
            im = Image.new("RGBA", (bb[2] - bb[0] + 4, int(size * 1.25)), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((-bb[0] + 2, int(size * 0.12) - bb[1]), p, font=f, fill=fg)
            pieces.append(im)
    gap = int(size * 0.3)
    tw = sum(p.width for p in pieces) + gap * (len(pieces) - 1); th = max(p.height for p in pieces)
    bw, bh = tw + 2 * pad[0], th + 2 * pad[1]
    out = Image.new("RGBA", (bw + 16, bh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(out); r = min(radius, bh // 2)
    d.rounded_rectangle([8, 14, 8 + bw, 14 + bh], r, fill=(0, 0, 0, 110))
    d.rounded_rectangle([8, 6, 8 + bw, 6 + bh], r, fill=tuple(bg) + (255,), outline=stroke, width=5 if stroke else 0)
    x = 8 + pad[0]
    for p in pieces:
        out.alpha_composite(p, (x, 6 + pad[1] + (th - p.height) // 2)); x += p.width + gap
    return out

def fit(st, maxw=1000):
    if st.width <= maxw: return st
    return st.resize((maxw, int(st.height * maxw / st.width)), Image.LANCZOS)

def text_block(lines, size, fill=WHITE, sw=10, weight="Black", spacing=8):
    f = font(size, weight); ims = []
    for l in lines:
        if not l: continue
        bb = f.getbbox(l, stroke_width=sw)
        im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((-bb[0] + 4, -bb[1] + 4), l, font=f, fill=fill, stroke_width=sw, stroke_fill=STROKE)
        ims.append(im)
    w = max(i.width for i in ims); h = sum(i.height for i in ims) + spacing * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in ims: out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + spacing
    return fit(out)

def ease_back(x):
    x = max(0, min(1, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

POPS = []
def place(frame, st, cx, cy, t, t0, t1=1e9, dur=0.28, pulse=0, wobble=0, slide=0, pop=True):
    if t < t0 or t > t1: return
    if pop and abs(t - t0) < 0.5 / FPS: POPS.append(round(t0, 2))
    s = ease_back((t - t0) / dur)
    if pulse: s *= 1 + pulse * math.sin((t - t0) * 2 * math.pi * 1.6)
    if s <= 0.02: return
    im = st.resize((max(1, int(st.width * s)), max(1, int(st.height * s))), Image.BILINEAR)
    if wobble: im = im.rotate(wobble * math.sin((t - t0) * 2 * math.pi * 1.3), expand=True, resample=Image.BICUBIC)
    dx = int(slide * (1 - min(1, (t - t0) / dur)))
    frame.alpha_composite(im, (int(cx - im.width / 2) + dx, int(cy - im.height / 2)))

def bg_tema():
    g = np.zeros((H, W, 3), np.uint8); yy = np.linspace(0, 1, H)[:, None]
    for i in range(3): g[..., i] = (TM["top"][i] * (1 - yy) + TM["bot"][i] * yy).astype(np.uint8)
    im = Image.fromarray(g).convert("RGBA")
    for r, a in ((620, 40), (420, 50)):
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([W / 2 - r, 900 - r, W / 2 + r, 900 + r], fill=tuple(TM["glow"]) + (a,))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    return im

def card(size):
    p = Image.open(f"{PROD}/1-foto.jpg").convert("RGBA").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size, size], 48, fill=255)
    c = Image.new("RGBA", (size, size), (0, 0, 0, 0)); c.paste(p, (0, 0), m); return c

BG = bg_tema(); CARD_BIG = card(860); CARD_MD = card(720); CARD_SM = card(600)
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
de, por, pct, nota, vendas = info["de"], info["por"], info["pct"], info["nota"], info["vendas"]
vend_txt = f"{vendas/1000:.1f} MIL".replace(".", ",").replace(",0 MIL", " MIL") if vendas >= 1000 else str(vendas)

S = {}
S["gancho1"] = text_block(EST["gancho"], 104, fill=YEL if EST["tema"] != "vermelho" else WHITE)
S["gancho2"] = text_block(info["hook"], 60, fill=WHITE, sw=9)
S["topo"] = sticker(["[⚡]", TOPO_TXT], TM["topo_bg"], fg=TM["topo_fg"], size=46)
S["chips"] = [sticker([c], TM["top"], fg=TM["chip"], size=50, stroke=TM["chip"]) for c in info["chips"]]
S["de"] = text_block([f"DE {brl(de)}"], 70, fill=(205, 208, 216), sw=6, weight="Bold")
S["porlbl"] = text_block([info.get("porlbl", "POR APENAS")], 58, fill=WHITE, sw=6, weight="ExtraBold")
S["por"] = text_block([brl(por)], 170, fill=TM["preco"], sw=12)
S["pct"] = sticker([f"-{pct}%"], TM["badge_bg"], fg=TM["badge_fg"], size=86, pad=(36, 26))
S["alerta"] = fit(sticker(["[⏰]", ALERTA_TXT], TM["alerta_bg"], fg=TM["alerta_fg"], size=38, radius=20, pad=(26, 18)), 1020)
S["nota"] = text_block([f"{nota:.1f}".replace(".", ",")], 150, fill=WHITE, sw=10)
S["estrela"] = emoji("⭐", 130)
S["vendidos"] = text_block([f"{vend_txt} VENDIDOS"], 72, fill=TM["preco"], sw=8)
S["aprovou"] = sticker(["[🔥]", "QUEM COMPROU APROVOU"], RED, size=54)
S["bio"] = sticker(["[🔗]", "O LINK TÁ NA BIO!"], TM["cta_bg"], fg=TM["cta_fg"], size=66)
S["coment1"] = text_block(["OU COMENTA"], 72, fill=WHITE)
S["quero"] = sticker(["[💬]", "QUERO"], YEL, fg=NAVY, size=96, pad=(40, 24))
S["coment2"] = text_block(["QUE A GENTE TE MANDA!"], 60, fill=WHITE)
S["seta"] = emoji("👇", 120)
S["aviso"] = sticker([f"Preço consultado em {info['data']}, pode mudar"], (0, 0, 0), size=28, weight="SemiBold", pad=(20, 10))
S["check"] = emoji("✅", 90)
S["motivos"] = [sticker([c], TM["cta_bg"], fg=TM["cta_fg"], size=64, radius=24, pad=(36, 24)) for c in info["chips"][:2]] + \
               [sticker(["[⭐]", f"NOTA {nota:.1f}".replace(".", ",")], TM["cta_bg"], fg=TM["cta_fg"], size=64, radius=24, pad=(36, 24))]
S["reacao"] = text_block(["ATÉ EU FIQUEI", "CHOCADA!"], 96, fill=YEL)

# ---------- cenas ----------
def zoomed(im, z):
    w, h = int(W / z), int(H / z); x, y = (W - w) // 2, (H - h) // 2
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)

def cena_heroi(f, lt, d, t, t0, papel):
    sc = 1 + 0.05 * lt
    c = CARD_BIG.resize((int(860 * sc), int(860 * sc)), Image.BILINEAR)
    f.alpha_composite(c, ((W - c.width) // 2, 880 - c.height // 2 + int(80 * (1 - ease_back(lt / 0.35)))))
    if papel == "gancho":
        place(f, S["gancho1"], W / 2, 260, t, t0 + 0.05, pulse=0.04, wobble=3)
        place(f, S["gancho2"], W / 2, 1450, t, t0 + 0.5)
        place(f, S["pct"], W / 2 + 300, 470, t, t0 + 1.0, wobble=8)
    else:
        xs = [(W / 2 - 270, 1450, -200), (W / 2 + 230, 1450, 200), (W / 2, 1580, 0)]
        for i, (st, (x, y, sl)) in enumerate(zip(S["chips"], xs)):
            place(f, st, x, y, t, t0 + 0.35 + 0.3 * i, slide=sl)

def cena_preco(f, lt, d, t, t0):
    f.alpha_composite(CARD_SM, ((W - 600) // 2, 330))
    place(f, S["de"], W / 2, 1060, t, t0 + 0.2)
    if lt > 0.55:
        k = min(1, (lt - 0.55) / 0.25); dw = S["de"].width
        ImageDraw.Draw(f).line([(W / 2 - dw / 2, 1065), (W / 2 - dw / 2 + dw * k, 1055)], fill=RED + (255,), width=12)
    place(f, S["porlbl"], W / 2, 1170, t, t0 + 0.95)
    place(f, S["por"], W / 2, 1320, t, t0 + 1.15, dur=0.35, pulse=0.035)
    place(f, S["pct"], W / 2 + 280, 400, t, t0 + 1.5, wobble=8)
    place(f, S["alerta"], W / 2, 1560, t, t0 + 2.0, pulse=0.04)

def cena_aval(f, lt, d, t, t0):
    f.alpha_composite(CARD_MD, ((W - 720) // 2, 280))
    place(f, S["estrela"], W / 2 - 150, 1150, t, t0 + 0.2)
    place(f, S["nota"], W / 2 + 70, 1150, t, t0 + 0.3)
    place(f, S["vendidos"], W / 2, 1320, t, t0 + 0.6)
    place(f, S["aprovou"], W / 2, 1480, t, t0 + 0.9, pulse=0.04, wobble=3)

def cena_lista(f, lt, d, t, t0):
    f.alpha_composite(CARD_SM, ((W - 600) // 2, 300))
    for i, st in enumerate(S["motivos"]):
        y = 1040 + i * 190; ti = t0 + 0.4 + 1.2 * i
        place(f, st, W / 2 + 50, y, t, ti, slide=300)
        place(f, S["check"], W / 2 - st.width / 2 - 40, y, t, ti + 0.2)

def overlays_clip(f, papel, t, t0, d):
    if papel == "gancho":
        place(f, S["gancho1"], W / 2, 300, t, t0 + 0.15, pulse=0.03)
        place(f, S["gancho2"], W / 2, 510, t, t0 + 0.9)
    elif papel == "reacao":
        place(f, S["reacao"], W / 2, 330, t, t0 + 0.1, pulse=0.04, wobble=3)
    elif papel == "final":
        place(f, S["bio"], W / 2, 260, t, t0 + 0.15, pulse=0.04)
        place(f, S["coment1"], W / 2, 1270, t, t0 + 2.2)
        place(f, S["quero"], W / 2, 1420, t, t0 + 2.5, pulse=0.06, wobble=4)
        place(f, S["coment2"], W / 2, 1570, t, t0 + 2.8)
        if t > t0 + 3.0:
            off = int(18 * abs(math.sin((t - t0) * 2 * math.pi * 1.5)))
            f.alpha_composite(S["seta"], ((W - S["seta"].width) // 2, 1660 + off))
        place(f, S["aviso"], W / 2, 1860, t, t0 + 0.5, pop=False)

def clip_reader(path, start):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-vf", f"scale={W}:{H},fps={FPS}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: last = Image.fromarray(np.frombuffer(b, np.uint8).reshape(H, W, 3)).convert("RGBA")
        if last is None: raise RuntimeError("clipe vazio " + path)
        yield last

# ---------- linha do tempo ----------
plan, t = [], 0.0
for c in EST["cenas"]:
    d = c[3] if c[0] == "clip" else c[1]
    plan.append((t, d, c)); t += d
TOTAL = t
N = int(round(TOTAL * FPS))
voz = [dict(arquivo=c[1] + ".mp4", ini_origem=c[2], ini=t0, dur=d) for t0, d, c in plan if c[0] == "clip"]
cuts = [t0 for t0, d, c in plan[1:]]

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
readers = {}
for n in range(N):
    t = n / FPS
    for t0, d, c in plan:
        if t0 <= t < t0 + d or (n == N - 1 and t0 + d >= TOTAL - 1e-6): break
    lt = t - t0; kind = c[0]
    if kind == "clip":
        key = (c[1], c[2], t0)
        if key not in readers: readers[key] = clip_reader(f"{CLIPS}/{c[1]}.mp4", c[2])
        f = next(readers[key]).copy()
        if c[4] == "gancho": f = zoomed(f, 1 + 0.06 * min(1, lt / d))
        overlays_clip(f, c[4], t, t0, d)
    else:
        f = BG.copy()
        if kind == "heroi": cena_heroi(f, lt, d, t, t0, c[2] if len(c) > 2 else "")
        elif kind == "preco": cena_preco(f, lt, d, t, t0)
        elif kind == "aval": cena_aval(f, lt, d, t, t0)
        elif kind == "lista": cena_lista(f, lt, d, t, t0)
        if not (kind == "heroi" and len(c) > 2):
            place(f, S["topo"], W / 2, 150, t, t0 + 0.05, pulse=0.05, pop=False)
    for cu in cuts:
        if 0 <= t - cu < 0.13:
            f.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - (t - cu) / 0.13)))))
    enc.stdin.write(f.convert("RGB").tobytes())
enc.stdin.close(); enc.wait()
preco_t = [t0 + 1.15 for t0, d, c in plan if c[0] == "preco"]
json.dump(dict(estilo=EST["nome"], tema=EST["tema"], dur=round(TOTAL, 3), bpm=EST["bpm"], tom=EST["tom"], cortes=cuts,
               pops=sorted(set(POPS)), ding=preco_t, voz=voz), open(TL, "w"), ensure_ascii=False, indent=1)
print("ok", EST["nome"], round(TOTAL, 2))
