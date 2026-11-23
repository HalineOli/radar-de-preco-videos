"""Capa 1080x1920 do video. Uso: python3 capa.py <pasta_produto_com_info.json_e_1-foto.jpg> <clipe_surpresa.mp4> <saida.jpg>
Conteudo importante fica na faixa central 3:4 (y 240..1680), que e o recorte do grid do perfil."""
import sys, json, subprocess, io
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
sys.argv, ARGS = sys.argv[:1], sys.argv[1:]
PROD, CLIP, OUT = ARGS
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estilos import estilo_do_video
from PIL import ImageFont
MONT = "/usr/share/fonts/truetype/google-fonts/ofl/montserrat/Montserrat[wght].ttf"
EMO = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
W, H = 1080, 1920
NAVY = (11, 18, 32); GREEN = (46, 230, 140); YEL = (255, 206, 40); RED = (255, 59, 59); WHITE = (255, 255, 255)
def font(s, w="Black"):
    f = ImageFont.truetype(MONT, s); f.set_variation_by_name(w); return f
def txt(lines, size, fill, sw=10, w="Black"):
    f = font(size, w); ims = []
    for l in lines:
        bb = f.getbbox(l, stroke_width=sw)
        im = Image.new("RGBA", (bb[2]-bb[0]+8, bb[3]-bb[1]+8), (0,0,0,0))
        ImageDraw.Draw(im).text((-bb[0]+4, -bb[1]+4), l, font=f, fill=fill, stroke_width=sw, stroke_fill=NAVY)
        ims.append(im)
    out = Image.new("RGBA", (max(i.width for i in ims), sum(i.height for i in ims)+8*(len(ims)-1)), (0,0,0,0)); y = 0
    for i in ims: out.alpha_composite(i, ((out.width-i.width)//2, y)); y += i.height+8
    return out
def pill(text, bg, fg, size, emoji=None, pad=(34, 20)):
    f = font(size); bb = f.getbbox(text)
    e = None
    if emoji:
        ef = ImageFont.truetype(EMO, 109); ei = Image.new("RGBA", (160,160), (0,0,0,0))
        ImageDraw.Draw(ei).text((10,10), emoji, font=ef, embedded_color=True); ei = ei.crop(ei.getbbox())
        e = ei.resize((int(size*1.05), int(size*1.05*ei.height/ei.width)))
    tw = bb[2]-bb[0] + (e.width + int(size*0.3) if e else 0); th = int(size*1.2)
    im = Image.new("RGBA", (tw+2*pad[0]+12, th+2*pad[1]+14), (0,0,0,0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 12, 6+tw+2*pad[0], 12+th+2*pad[1]-2], 999, fill=(0,0,0,110))
    d.rounded_rectangle([6, 4, 6+tw+2*pad[0], 4+th+2*pad[1]-2], 999, fill=bg+(255,))
    x = 6+pad[0]
    if e: im.alpha_composite(e, (x, 4+pad[1]+(th-e.height)//2)); x += e.width+int(size*0.3)
    d.text((x-bb[0], 4+pad[1]+(th-(bb[3]-bb[1]))//2-bb[1]), text, font=f, fill=fg)
    return im
info = json.load(open(f"{PROD}/info.json"))
_i, _E, TM, _t, _a = estilo_do_video(info["n"], info["data_iso"])
TOPO_CAPA = {"A": "ACHADO DO DIA", "B": "OLHA ESSE ACHADO", "C": "OLHA O QUE EU ACHEI", "D": "PARA TUDO!", "E": "CORRE QUE TÁ BARATO"}[_E["nome"]]
GREEN = TM["preco"]
brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
# fundo: personagem surpresa (mao na boca), escurecida e desfocada
raw = subprocess.run(["ffmpeg","-v","error","-ss","2.9","-i",CLIP,"-frames:v","1","-vf",f"scale={W}:{H}","-f","image2pipe","-vcodec","png","-"], capture_output=True).stdout
bg = Image.open(io.BytesIO(raw)).convert("RGBA")
face = bg.copy()
bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(18))).enhance(0.45)
c = Image.new("RGBA", (W, H), (0,0,0,0))
c.alpha_composite(bg)
c.alpha_composite(Image.new("RGBA", (W, H), tuple(TM["top"]) + (120,)))
# personagem nitida no rodape, em circulo
fc = face.crop((230, 400, 850, 1020)).resize((340, 340))
m = Image.new("L", (340, 340), 0); ImageDraw.Draw(m).ellipse([0,0,340,340], fill=255)
ring = Image.new("RGBA", (364, 364), (0,0,0,0)); ImageDraw.Draw(ring).ellipse([0,0,364,364], fill=tuple(TM["badge_bg"])+(255,))
# produto
p = Image.open(f"{PROD}/1-foto.jpg").convert("RGBA").resize((700, 700))
pm = Image.new("L", (700, 700), 0); ImageDraw.Draw(pm).rounded_rectangle([0,0,700,700], 50, fill=255)
card = Image.new("RGBA", (700, 700), (0,0,0,0)); card.paste(p, (0,0), pm)
sh = Image.new("RGBA", (W, H), (0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([190, 470, 890, 1170], 50, fill=(0,0,0,160))
c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(25)))
c.alpha_composite(card, (190, 440))
top = txt([TOPO_CAPA], 92, YEL if _E["tema"] != "vermelho" else (255, 255, 255))
if top.width > 1000: top = top.resize((1000, int(top.height * 1000 / top.width)))
c.alpha_composite(top, ((W-top.width)//2, 270))
badge = pill(f"-{info['pct']}%", TM["badge_bg"], TM["badge_fg"], 96)
badge = badge.rotate(-10, expand=True, resample=Image.BICUBIC)
c.alpha_composite(badge, (720, 380))
lbl = txt([info.get("porlbl", "POR APENAS")], 56, WHITE, sw=7, w="ExtraBold")
c.alpha_composite(lbl, ((W-lbl.width)//2, 1190))
pr = txt([brl(info["por"])], 190, GREEN, sw=14)
c.alpha_composite(pr, ((W-pr.width)//2, 1260))
de = txt([f"antes {brl(info['de'])}"], 50, (210, 214, 222), sw=6, w="Bold")
c.alpha_composite(de, ((W-de.width)//2, 1490))
d = ImageDraw.Draw(c); d.line([((W-de.width)//2+150, 1520), ((W+de.width)//2-8, 1516)], fill=RED+(255,), width=8)
c.alpha_composite(ring, (60, 1560)); c.paste(fc, (72, 1572), m)
cta = pill("LINK NA BIO", TM["cta_bg"], TM["cta_fg"], 58, emoji="🔗")
c.alpha_composite(cta, (460, 1690))
c.convert("RGB").save(OUT, quality=92)
print("ok")
