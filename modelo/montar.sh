#!/bin/bash
# Uso: bash modelo/montar.sh <pasta_do_produto> <saida.mp4>
# A pasta do produto precisa de 1-foto.jpg e info.json (com n e data_iso). Gera tambem <saida>_capa.jpg e <saida>_conferir.jpg.
set -e
PROD="$1"; OUT="$2"; M="$(cd "$(dirname "$0")" && pwd)"; TMP="$(mktemp -d)"
python3 "$M/render.py" "$PROD" "$M/clipes" "$TMP/video.mp4" "$TMP/tl.json" | grep "^ok"
python3 "$M/music.py" "$TMP/tl.json" "$TMP/music.wav"
python3 - "$TMP" "$M/clipes" "$OUT" <<'PY'
import json, sys, subprocess
tmp, clipes, out = sys.argv[1:4]
tl = json.load(open(f"{tmp}/tl.json"))
args = ["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/video.mp4", "-i", f"{tmp}/music.wav", "-i", f"{tmp}/music_fx.wav"]
fil, labels, duck = [], [], []
for k, v in enumerate(tl["voz"]):
    args += ["-i", f"{clipes}/{v['arquivo']}"]; i = 3 + k; ms = int(v["ini"] * 1000)
    fil.append(f"[{i}:a]atrim={v['ini_origem']}:{v['ini_origem'] + v['dur']},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,afade=t=out:st={max(0, v['dur'] - 0.15)}:d=0.15,adelay={ms}|{ms},volume=1.1[v{k}]")
    labels.append(f"[v{k}]"); duck.append(f"between(t,{v['ini']},{v['ini'] + v['dur']})")
fil.append(f"[1:a]volume='if({'+'.join(duck) or '0'},0.35,0.8)':eval=frame[m]")
fil.append(f"[m][2:a]{''.join(labels)}amix=inputs={2 + len(labels)}:duration=first:normalize=0,alimiter=limit=0.95[a]")
args += ["-filter_complex", ";".join(fil), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-t", str(tl["dur"]), out]
subprocess.run(args, check=True)
print("estilo", tl["estilo"], "tema", tl["tema"], "duracao", tl["dur"])
PY
python3 "$M/capa.py" "$PROD" "$M/clipes/surpresa.mp4" "${OUT%.mp4}_capa.jpg" >/dev/null
# capa como primeiro meio segundo do video (o TikTok de conta pessoal usa o 1o quadro como capa)
mv "$OUT" "$TMP/corpo.mp4"
ffmpeg -v error -y -loop 1 -framerate 30 -t 0.5 -i "${OUT%.mp4}_capa.jpg" -f lavfi -t 0.5 -i anullsrc=r=44100:cl=stereo -i "$TMP/corpo.mp4" \
  -filter_complex "[0:v]scale=1080:1920,format=yuv420p,setsar=1[cv];[2:v]setsar=1[bv];[cv][1:a][bv][2:a]concat=n=2:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart "$OUT"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
ffmpeg -v error -y -i "$OUT" -vf "fps=6/$D,scale=270:480,tile=6x1" -frames:v 1 "${OUT%.mp4}_conferir.jpg"
rm -rf "$TMP"; echo "pronto: $OUT"
