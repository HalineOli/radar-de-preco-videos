# Rotina diária – Radar de Preço (TikTok)

Objetivo: todo dia, olhar os produtos que o robô Ofertou exporta, escolher SÓ os que têm mais chance de viralizar e agendar no TikTok pelo Metricool, publicando automaticamente (a dona aprovou o modelo e pode apagar posts no Metricool antes do horário de publicação).

**Limite do plano grátis do Metricool: 20 posts publicados por mês** (zera no dia 1º). A dona não vai pagar plano. Por isso a rotina posta no máximo 1 vídeo por dia (2 só em dia excepcional) e nunca passa de 20 no mês. O controle fica no arquivo `publicados.csv`, na raiz deste repositório.

## 1. Pegar os dados
- Fuso: America/Sao_Paulo. HOJE = data de hoje (AAAA-MM-DD).
- Repositório de produtos (privado, só leitura): `HalineOli/radar-de-preco-feed`, pasta `HOJE/`.
  - `produtos.json` + uma pasta por produto (`<id>/1-foto.jpg`, `2-vertical.jpg`, `3-preco.jpg`, `4-avaliacao.jpg`).
- Repositório de vídeos (público, escrita): `HalineOli/radar-de-preco-videos`. Modelo em `modelo/`.
- Se a pasta `HOJE/` não existir no feed, NÃO invente produtos: avise a dona que o robô não exportou hoje e pare.

## 2. Conferir o saldo do mês
- Abra `publicados.csv` (colunas: `data,horario,id,produto,preco,status`). `status` = `agendado`, `publicado` ou `erro`.
- Atualize os status antigos: chame getScheduledPosts (brandId 8258136, do dia 1º do mês até hoje, fuso America/Sao_Paulo). Post que aparece com status ERROR → `erro` (e anote o motivo para avisar a dona). Post com data já passada que não aparece mais como pendente/erro → `publicado`.
- `USADOS` = linhas do mês atual com status `agendado` ou `publicado` (as de `erro` não contam). Linhas com id `limite-metricool` contam como 20 de uma vez (o mês já esgotou).
- `META` = arredondar para cima (20 × dias de seg a sex do mês até hoje, contando hoje ÷ total de dias de seg a sex do mês). Ex.: 10º dia útil de um mês com 21 dias úteis → META 10. (A cota é pensada para os dias úteis, que têm mais visualização.)
- Se `USADOS` ≥ 20: não monte vídeo, não agende nada e pare sem avisar (a cota do mês acabou; volta no dia 1º).
- Se algum post deu ERROR com "account limit" e o mês ainda não tinha 20 no registro, acrescente uma linha `limite-metricool` no mês, avise a dona e pare.

## 3. Escolher o produto do dia
Use só produtos com `desconto_verificado: true`. Escolha pelo que chama mais atenção e tem mais chance de viralizar, pensando como quem rola o TikTok:
- **Preço que choca**: desconto alto (quanto maior, melhor) e/ou preço final baixo para o que o produto é (ex.: eletrônico por menos de R$ 50, item de beleza por menos de R$ 20).
- **Desejo e apelo visual**: produto que muita gente quer e que fica bonito na foto (eletrônicos, cozinha, beleza, casa, gadgets). Item sem graça ou muito específico vale menos.
- **Prova social**: muitas vendas e nota alta (≥ 4,7).
- Use `a_partir_de: true` com cuidado: o preço "a partir de" é só da versão mais barata, então pese menos esse preço.

Classifique o melhor do dia:
- **Excepcional**: desconto ≥ 50%; ou preço ≤ R$ 20 com desconto ≥ 35%; ou produto de muito desejo com desconto ≥ 45% e ≥ 1.000 vendas.
- **Forte**: desconto ≥ 40%; ou preço ≤ R$ 30 com desconto ≥ 25%; ou ≥ 1.000 vendas, nota ≥ 4,7 e desconto ≥ 30%.
- **Fraco**: o resto.

## 3b. Dia e hora que mais dão visualização (prioridade)
Os posts vão para os dias e horários com mais audiência. Nenhuma regra de escolha pode colocar um post fora deles, a não ser o produto excepcional no fim de semana.
- **Dias**: segunda a sexta são os dias prioritários. Quarta e quinta são os melhores. Sábado e domingo têm cerca de metade da audiência: só posta no fim de semana se o produto for **excepcional**.
- **Horário**: a cada rodada, chame getBestTimeToPostByNetwork (brandId 8258136, rede tiktok, de hoje 00:00 a hoje 23:59, fuso America/Sao_Paulo). Use o dia da semana de hoje e escolha a hora com maior valor entre 9h e 21h. Isso costuma dar 10h, 12h ou 18h. Se houver 2º post, ele vai na 2ª melhor hora que esteja a pelo menos 4 horas de distância da 1ª.
- **Dados do próprio perfil**: chame getAnalyticsDataByMetrics (brandId 8258136, métricas TKPO02 = data/hora em UTC, some -3h para Brasília, e TKPO07 = visualizações) para os últimos 60 dias. Quando houver pelo menos 20 vídeos com dados, calcule a média de visualizações por dia da semana e por faixa de horário. Se algum dia ou horário tiver média pelo menos 30% acima dos outros, dê prioridade a ele no lugar do que o Metricool sugere (e conte isso para a dona na próxima mensagem).

Quantos postar hoje:
- Sábado ou domingo → só posta se o melhor do dia for **excepcional** e `USADOS` < `META` + 1.
- Segunda a sexta:
  - Melhor do dia **fraco** → não posta hoje.
  - Melhor do dia **forte** → posta 1, só se `USADOS` < `META`. Em quarta e quinta, posta também se `USADOS` = `META` (são os melhores dias).
  - Melhor do dia **excepcional** → posta 1 mesmo que `USADOS` ≥ `META`, desde que `USADOS` < `META` + 2. Se houver um 2º produto também excepcional e ainda sobrar cota dentro dessa regra, pode postar 2.
- Nunca mais de 2 por dia e nunca passar de 20 no mês.

Horários: o 1º escolhido vai na melhor hora do dia (veja 3b); o 2º, se houver, na 2ª melhor. Se o horário já passou quando a rotina rodar, pule esse post.

## 4. Montar cada vídeo
Monte vídeo SÓ dos produtos escolhidos. Para cada um, crie uma pasta de trabalho com `1-foto.jpg` e um `info.json`:
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
- `data`: dia/mês de hoje. `data_iso`: HOJE. `n`: posição do vídeo no dia (1 = o 1º escolhido, 2 = o 2º).
- O estilo visual (A a E: cores, ordem das cenas, clipes da personagem, música e capa) é escolhido sozinho pelo `n` + data, então os vídeos mudam de um dia para o outro. Não force o mesmo estilo.
- Os gatilhos ("APROVEITE AGORA", "PREÇO PODE SUBIR A QUALQUER MOMENTO", "LINK NA BIO", "COMENTA QUERO" etc.) já estão no modelo; não acrescente outros.

Rodar, a partir da raiz do repositório de vídeos:
```
bash modelo/montar.sh <pasta_do_produto> videos/HOJE/<n>-<id>.mp4
```
O script também gera a capa `<n>-<id>_capa.jpg` (mantenha-a no repositório) e já coloca essa capa no primeiro meio segundo do vídeo, porque a conta do TikTok é pessoal e usa o 1º quadro como capa. Depois, abra o `_conferir.jpg` e a `_capa.jpg` geradas e confira se nenhum texto saiu cortado ou por cima de algo. Se saiu, encurte o texto e monte de novo. Apague os `_conferir.jpg` antes de salvar.

## 5. Publicar o vídeo
- Salve os mp4 em `videos/HOJE/`, faça commit e push na branch `main`.
- Apague pastas em `videos/` com mais de 7 dias (exceto `teste/`) para o repositório não crescer demais.
- URL pública: `https://raw.githubusercontent.com/HalineOli/radar-de-preco-videos/main/videos/HOJE/<arquivo>.mp4`

## 6. Agendar no Metricool
Marca (blogId): `8258136`. Ferramenta: createScheduledPost, uma por vídeo, `draft: false`, `autoPublish: true`.
- `providers`: `[{"network":"tiktok"}]`
- `videoThumbnailUrl`: URL pública da capa (`.../videos/HOJE/<n>-<id>_capa.jpg`). Se o Metricool recusar por causa da capa, agende de novo sem `videoThumbnailUrl` e avise a dona.
- `tiktokData`: `{"title": "<até 90 caracteres>", "privacyOption":"PUBLIC_TO_EVERYONE", "commercialContentThirdParty": true, "commercialContentOwnBrand": false, "isAigc": true, "disableComment": false, "disableDuet": false, "disableStitch": false, "autoAddMusic": false}` (o title é obrigatório)
- `text` (legenda), modelo:
  `<Produto> de R$ X por R$ Y 😱 <1 frase com 1-2 características reais> e nota <nota> de quem já comprou. Link na bio 🔗 ou comenta QUERO que a gente te manda! Preço consultado em <dd/mm>, pode mudar.`
  + linha em branco + 6 a 8 hashtags: sempre `#achadinhos #achadinhosshopee #shopee #radardepreco` + 2 a 4 do tema do produto.
- `publicationDate`: `{"dateTime":"HOJET HH:00:00","timezone":"America/Sao_Paulo"}`
- Depois de agendar, acrescente uma linha por post em `publicados.csv` com status `agendado` e faça commit e push junto com os vídeos.

## 7. Avisar a dona
- Se agendou: mensagem curta com o produto (ou os 2), horário, preço "de/por", por que foi escolhido (1 frase), quantos posts do mês já foram usados (ex.: 8 de 20) e o link do calendário
  https://app.metricool.com/planner/calendar?blogId=8258136, lembrando que dá para apagar antes do horário do post.
- Se não postou porque nenhum produto foi forte o bastante ou porque está à frente da META: não precisa avisar.
- Se algo falhar (robô sem exportação, GitHub, Metricool, limite atingido), diga exatamente o que falhou e o que foi ou não agendado.
