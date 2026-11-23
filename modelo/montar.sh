#!/bin/bash
# Uso: bash modelo/montar.sh <pasta_do_produto_com_1-foto.jpg_4-avaliacao.jpg_info.json> <saida.mp4>
# Roda a partir da raiz do repositorio radar-de-preco-videos.
set -e
PROD="$1"; OUT="$2"; M="$(cd "$(dirname "$0")" && pwd)"; TMP="$(mktemp -d)"
python3 "$M/render.py" "$PROD" "$M/clipes/surpresa.mp4" "$M/clipes/apontando.mp4" "$TMP/video.mp4" 2>/dev/null | grep -q "^ok"
python3 "$M/music.py" 18.4 "$TMP/music.wav"
ffmpeg -v error -y -i "$TMP/video.mp4" -i "$TMP/music.wav" -i "$TMP/music_fx.wav" -i "$M/clipes/surpresa.mp4" -i "$M/clipes/apontando.mp4" \
 -filter_complex "[3:a]atrim=0:3.2,afade=t=out:st=3.0:d=0.2,asetpts=PTS-STARTPTS,volume=1.1[va];[4:a]atrim=0:7,asetpts=PTS-STARTPTS,adelay=11400|11400,volume=1.1[vb];[1:a]volume='if(lt(t,3.2)+gte(t,11.4),0.35,0.8)':eval=frame[m];[m][2:a][va][vb]amix=inputs=4:duration=first:normalize=0,alimiter=limit=0.95[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -t 18.4 "$OUT"
ffmpeg -v error -y -i "$OUT" -vf "select='eq(n\,45)+eq(n\,250)+eq(n\,320)+eq(n\,500)',scale=270:480,tile=4x1" -frames:v 1 "${OUT%.mp4}_conferir.jpg"
python3 "$M/capa.py" "$PROD" "$M/clipes/surpresa.mp4" "${OUT%.mp4}_capa.jpg" >/dev/null
rm -rf "$TMP"; echo "pronto: $OUT e ${OUT%.mp4}_capa.jpg"
