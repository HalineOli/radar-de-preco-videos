"""Estilos visuais do Radar de Preço. Cada video do dia usa um estilo diferente (rodizio por data)."""
import datetime

NAVY = (11, 18, 32); WHITE = (255, 255, 255); YEL = (255, 206, 40); RED = (255, 59, 59)

TEMAS = {
    "verde":   dict(top=(14, 22, 40), bot=(6, 10, 20), glow=(46, 230, 140), preco=(46, 230, 140), chip=(46, 230, 140),
                    cta_bg=(46, 230, 140), cta_fg=NAVY, badge_bg=YEL, badge_fg=NAVY, alerta_bg=YEL, alerta_fg=NAVY, topo_bg=RED, topo_fg=WHITE, contorno=NAVY),
    "rosa":    dict(top=(44, 12, 60), bot=(18, 6, 28), glow=(255, 79, 163), preco=(255, 214, 90), chip=(255, 120, 190),
                    cta_bg=(255, 79, 163), cta_fg=WHITE, badge_bg=(255, 214, 90), badge_fg=(44, 12, 60), alerta_bg=WHITE, alerta_fg=(150, 20, 90), topo_bg=(255, 79, 163), topo_fg=WHITE, contorno=(30, 6, 40)),
    "laranja": dict(top=(40, 20, 8), bot=(14, 7, 3), glow=(255, 122, 26), preco=(255, 176, 56), chip=(255, 150, 70),
                    cta_bg=(255, 122, 26), cta_fg=WHITE, badge_bg=WHITE, badge_fg=(200, 70, 0), alerta_bg=(255, 122, 26), alerta_fg=WHITE, topo_bg=WHITE, topo_fg=(200, 70, 0), contorno=(24, 10, 2)),
    "vermelho":dict(top=(52, 8, 14), bot=(20, 3, 6), glow=(255, 60, 60), preco=YEL, chip=YEL,
                    cta_bg=YEL, cta_fg=(52, 8, 14), badge_bg=WHITE, badge_fg=RED, alerta_bg=RED, alerta_fg=WHITE, topo_bg=YEL, topo_fg=(52, 8, 14), contorno=(24, 2, 4)),
    "azul":    dict(top=(8, 30, 62), bot=(3, 12, 30), glow=(0, 190, 255), preco=(0, 225, 255), chip=(0, 225, 255),
                    cta_bg=(0, 225, 255), cta_fg=NAVY, badge_bg=YEL, badge_fg=NAVY, alerta_bg=WHITE, alerta_fg=(0, 90, 170), topo_bg=RED, topo_fg=WHITE, contorno=NAVY),
}

# Gatilhos (todos verdadeiros para qualquer produto com desconto verificado)
TOPO = ["APROVEITE AGORA", "ACHADO DO DIA", "CORRE QUE TÁ BARATO", "PREÇO DE HOJE", "APROVEITE AGORA"]
ALERTA = ["PREÇO PODE SUBIR A QUALQUER MOMENTO", "NÃO DEIXA PRA DEPOIS", "GARANTE ANTES QUE O PREÇO MUDE",
          "PREÇO PODE SUBIR A QUALQUER MOMENTO", "NÃO DEIXA PRA DEPOIS"]

ESTILOS = [
    # A: personagem surpresa abre -> produto -> preco -> avaliacao -> ela aponta (link)
    dict(nome="A", tema="verde", gancho=["GENTE, OLHA", "ESSE PREÇO!"], bpm=118, tom=0,
         cenas=[("clip", "surpresa", 0.0, 3.2, "gancho"), ("heroi", 2.0), ("preco", 4.0), ("aval", 2.2), ("clip", "apontando", 0.0, 7.0, "final")]),
    # B: segredo -> preco primeiro -> produto -> avaliacao -> joia
    dict(nome="B", tema="rosa", gancho=["VEM CÁ QUE EU", "VOU TE CONTAR"], bpm=104, tom=5,
         cenas=[("clip", "convite_segredo", 0.0, 5.6, "gancho"), ("preco", 4.0), ("heroi", 2.2), ("aval", 2.0), ("clip", "joia", 0.6, 5.6, "final")]),
    # C: ela falando -> produto -> avaliacao -> preco -> aponta
    dict(nome="C", tema="laranja", gancho=["OLHA O QUE", "EU ACHEI!"], bpm=124, tom=2,
         cenas=[("clip", "selfie_falando", 0.0, 3.6, "gancho"), ("heroi", 2.4), ("aval", 2.0), ("preco", 4.0), ("clip", "apontando", 0.0, 6.6, "final")]),
    # D: produto primeiro com PARA TUDO -> reacao dela -> preco -> avaliacao -> joia
    dict(nome="D", tema="vermelho", gancho=["PARA TUDO!", ""], bpm=128, tom=7,
         cenas=[("heroi", 2.6, "gancho"), ("clip", "surpresa", 1.4, 2.6, "reacao"), ("preco", 4.0), ("aval", 2.0), ("clip", "joia", 0.6, 5.6, "final")]),
    # E: 3 motivos -> lista -> preco -> aponta
    dict(nome="E", tema="azul", gancho=["3 MOTIVOS PRA", "GARANTIR JÁ"], bpm=112, tom=9,
         cenas=[("clip", "selfie_falando", 0.0, 3.4, "gancho"), ("lista", 5.0), ("preco", 3.8), ("clip", "apontando", 0.0, 6.6, "final")]),
]

def estilo_do_video(n, data_iso):
    """n = posicao do video no dia (1..5). Gira o estilo por dia para nao repetir a mesma combinacao."""
    d = datetime.date.fromisoformat(data_iso).toordinal()
    i = (n - 1 + d) % len(ESTILOS)
    return i, ESTILOS[i], TEMAS[ESTILOS[i]["tema"]], TOPO[(i + d) % len(TOPO)], ALERTA[(i + d) % len(ALERTA)]
