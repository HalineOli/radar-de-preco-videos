# Rotina diária – Radar de Preço (TikTok)

Objetivo: todo dia, transformar os 5 produtos que o robô Ofertou exporta em 5 vídeos e agendar no TikTok pelo Metricool, publicando automaticamente (a dona aprovou o modelo e pode apagar posts no Metricool até as 10h).

## 1. Pegar os dados
- Fuso: America/Sao_Paulo. HOJE = data de hoje (AAAA-MM-DD).
- Repositório de produtos (privado, só leitura): `HalineOli/radar-de-preco-feed`, pasta `HOJE/`.
  - `produtos.json` + uma pasta por produto (`<id>/1-foto.jpg`, `2-vertical.jpg`, `3-preco.jpg`, `4-avaliacao.jpg`).
- Repositório de vídeos (público, escrita): `HalineOli/radar-de-preco-videos`. Modelo em `modelo/`.
- Se a pasta `HOJE/` não existir no feed, NÃO invente produtos: avise a dona que o robô não exportou hoje e pare.

## 2. Escolher e ordenar
- Use só produtos com `desconto_verificado: true`. Pule os outros (e diga quais pulou).
- Ordene do melhor para o pior (desconto real, vendas, nota) e distribua nos horários:
  1º melhor → 18:00 · 2º → 10:00 · 3º → 12:00 · 4º → 20:00 · 5º → 16:00
- Horário que já passou quando a rotina rodar: pule esse post.

## 3. Montar cada vídeo
Para cada produto, crie uma pasta de trabalho com `1-foto.jpg` e um `info.json`:
```json
{"de":129.90,"por":99.90,"pct":23,"vendas":605,"nota":4.9,"data":"22/11",
 "hook":["LIQUIDIFICADOR PHILCO 1200W","POR MENOS DE R$ 100"],
 "chips":["1200W","3 LITROS","12 VELOCIDADES"],
 "porlbl":"POR APENAS", "n":4, "data_iso":"2026-11-22"}
```
Regras do texto (verdade sempre, nada inventado):
- `hook`: 2 linhas em MAIÚSCULAS, no máximo ~28 caracteres cada. Linha 1 = o que é o produto (curto). Linha 2 = o gancho de preço, que precisa ser verdadeiro ("POR MENOS DE R$ 100" só se for menos de 100; senão "POR SÓ R$ 54,90").
- Se `a_partir_de` for true: `porlbl` = "A PARTIR DE" e o gancho também diz "A PARTIR DE".
- `chips`: 3 características curtas tiradas do NOME do produto (ex.: "KIT 5 POTES", "VIDRO", "COM TAMPA"). Nunca invente características.
- Proibido escrever "oferta relâmpago", "últimas unidades", contagem regressiva ou qualquer urgência que o robô não informou.
- `data`: dia/mês de hoje. `data_iso`: HOJE. `n`: posição do vídeo no dia (1 = o das 18h, 2 = 10h, 3 = 12h, 4 = 20h, 5 = 16h).
- O estilo visual (A a E: cores, ordem das cenas, clipes da personagem, música e capa) é escolhido sozinho pelo `n` + data, então os 5 vídeos do dia saem sempre diferentes entre si e mudam de um dia para o outro. Não force o mesmo estilo.
- Os gatilhos ("APROVEITE AGORA", "PREÇO PODE SUBIR A QUALQUER MOMENTO", "LINK NA BIO", "COMENTA QUERO" etc.) já estão no modelo; não acrescente outros.

Rodar, a partir da raiz do repositório de vídeos:
```
bash modelo/montar.sh <pasta_do_produto> videos/HOJE/<n>-<id>.mp4
```
O script também gera a capa `<n>-<id>_capa.jpg` (mantenha-a no repositório) e já coloca essa capa no primeiro meio segundo do vídeo, porque a conta do TikTok é pessoal e usa o 1º quadro como capa. Depois, abra o `_conferir.jpg` e a `_capa.jpg` geradas e confira se nenhum texto saiu cortado ou por cima de algo. Se saiu, encurte o texto e monte de novo. Apague os `_conferir.jpg` antes de salvar.

## 4. Publicar o vídeo
- Salve os mp4 em `videos/HOJE/`, faça commit e push na branch `main`.
- Apague pastas em `videos/` com mais de 7 dias (exceto `teste/`) para o repositório não crescer demais.
- URL pública: `https://raw.githubusercontent.com/HalineOli/radar-de-preco-videos/main/videos/HOJE/<arquivo>.mp4`

## 5. Agendar no Metricool
Marca (blogId): `8258136`. Ferramenta: createScheduledPost, uma por vídeo, `draft: false`, `autoPublish: true`.
- `providers`: `[{"network":"tiktok"}]`
- `videoThumbnailUrl`: URL pública da capa (`.../videos/HOJE/<n>-<id>_capa.jpg`). Se o Metricool recusar por causa da capa, agende de novo sem `videoThumbnailUrl` e avise a dona.
- `tiktokData`: `{"title": "<até 90 caracteres>", "privacyOption":"PUBLIC_TO_EVERYONE", "commercialContentThirdParty": true, "commercialContentOwnBrand": false, "isAigc": true, "disableComment": false, "disableDuet": false, "disableStitch": false, "autoAddMusic": false}` (o title é obrigatório)
- `text` (legenda), modelo:
  `<Produto> de R$ X por R$ Y 😱 <1 frase com 1-2 características reais> e nota <nota> de quem já comprou. Link na bio 🔗 ou comenta QUERO que a gente te manda! Preço consultado em <dd/mm>, pode mudar.`
  + linha em branco + 6 a 8 hashtags: sempre `#achadinhos #achadinhosshopee #shopee #radardepreco` + 2 a 4 do tema do produto.
- `publicationDate`: `{"dateTime":"HOJET HH:00:00","timezone":"America/Sao_Paulo"}`

## 6. Avisar a dona
Mande uma mensagem curta: os 5 produtos, horário de cada um, e o link do calendário
https://app.metricool.com/planner/calendar?blogId=8258136 — lembrando que dá para apagar até as 10h.
Se algo falhar (robô sem exportação, GitHub, Metricool), diga exatamente o que falhou e o que foi ou não agendado.
