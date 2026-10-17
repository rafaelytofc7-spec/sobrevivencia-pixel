# -*- coding: utf-8 -*-
"""
estruturas.py - ESTRUTURAS geradas pela semente: vilas, cidadelas, castelos,
entradas de masmorra, ruínas e baús de tesouro.

Como funciona (compatível com o mundo infinito em chunks):
1. O mundo é dividido numa grade GROSSA de regiões (REGIAO x REGIAO blocos).
2. Cada região sorteia (com a semente + coordenadas da região) se tem uma
   estrutura, qual tipo e onde. A estrutura cabe INTEIRA dentro da região,
   então duas estruturas nunca se encostam.
3. A planta da estrutura (pisos, paredes, objetos, NPCs, baús) é montada uma
   vez e guardada em cache, em coordenadas do mundo.
4. Quando um chunk é gerado, carimbar() copia para ele só o pedaço da planta
   que cai dentro do chunk. Assim uma estrutura que ocupa vários chunks
   aparece certinha, não importa a ordem em que os chunks carregam.

Regras de bioma: nada em cima de lago/rio (o lugar é recusado se tiver água
demais, e o chão embaixo das construções é "aterrado" para não alagar na
chuva); vilas do deserto usam arenito, as da neve usam madeira escura;
castelos não são feitos no pântano; vilas não são feitas na montanha.
"""
import random
import zlib

from config import TAMANHO_CHUNK, CHAO_AGUA, LAMA
import dados_estruturas as DE      # noqa: F401  (registra itens/objetos/criaturas novos)
import arte_estruturas             # noqa: F401  (ícones dos itens novos)

CH = TAMANHO_CHUNK
REGIAO = 96              # tamanho (em blocos) de cada região da grade grossa
ATERRO = 0.06            # quanto acima do nível da água o chão das construções fica

# Chance de cada tipo por região (o que sobrar = região vazia)
CHANCES = [("vila", 0.20), ("cidadela", 0.07), ("castelo", 0.06), ("masmorra", 0.14),
           ("ruina", 0.20), ("tesouro", 0.10)]

BIOMAS_PERMITIDOS = {
    "vila":     {"planicie", "floresta", "deserto", "neve", "pantano"},
    "cidadela": {"planicie", "floresta", "deserto", "neve"},
    "castelo":  {"planicie", "floresta", "deserto", "neve", "montanha"},
    "masmorra": {"planicie", "floresta", "deserto", "neve", "montanha", "pantano"},
    "ruina":    {"planicie", "floresta", "deserto", "neve", "montanha", "pantano"},
    "tesouro":  {"planicie", "floresta", "deserto", "neve", "montanha", "pantano"},
}
AGUA_MAXIMA = {"vila": 0.20, "cidadela": 0.15, "castelo": 0.15, "masmorra": 0.25,
               "ruina": 0.30, "tesouro": 0.0}
NOMES_ESTRUTURAS = {"vila": "uma vila", "cidadela": "uma cidadela", "castelo": "um castelo",
                    "masmorra": "a entrada de uma masmorra", "ruina": "ruínas antigas",
                    "tesouro": "um baú de tesouro"}

# Materiais por bioma: (parede, variante), (piso da casa, variante), variante do caminho
MATERIAIS = {
    "planicie": {"parede": ("parede_madeira", 0), "piso": ("piso", 0), "caminho": 0},
    "floresta": {"parede": ("parede_madeira", 0), "piso": ("piso", 0), "caminho": 0},
    "pantano":  {"parede": ("parede_madeira", 0), "piso": ("piso", 0), "caminho": 0},
    "neve":     {"parede": ("parede_madeira", 1), "piso": ("piso", 0), "caminho": 2},
    "deserto":  {"parede": ("parede_pedra", 1), "piso": ("piso_arenito", 0), "caminho": 1},
    "montanha": {"parede": ("parede_pedra", 0), "piso": ("piso_pedra", 0), "caminho": 0},
}
PEDRA_CIDADE = {"parede": ("parede_pedra", 0), "piso": ("piso_pedra", 0), "caminho": 0}
PEDRA_DESERTO = {"parede": ("parede_pedra", 1), "piso": ("piso_arenito", 0), "caminho": 1}


def numero(*partes):
    """Número fixo a partir de qualquer coisa (semente, região, texto...)."""
    return zlib.crc32(repr(partes).encode("utf-8")) & 0x7FFFFFFF


# ===============================================================
# Planta de uma estrutura
# ===============================================================
class Estrutura:
    def __init__(self, tipo, ident, bioma, x0, y0, largura, altura):
        self.tipo = tipo
        self.id = ident                 # texto único, ex.: "vila:3,-2"
        self.bioma = bioma
        self.caixa = (x0, y0, x0 + largura - 1, y0 + altura - 1)
        self.pisos = {}                 # (x, y) -> (tipo, variante)
        self.objetos = {}               # (x, y) -> (tipo, variante)
        self.area = set()               # blocos aterrados + limpos de árvores/pedras
        self.npcs = []                  # dicts: id, tipo, x, y (blocos), raio, extra
        self.baus = {}                  # (x, y) -> nível do tesouro (1..3)

    # --- ferramentas de construção ---
    def chao(self, x, y, tipo, var=0):
        self.pisos[(x, y)] = (tipo, var)
        self.area.add((x, y))

    def obj(self, x, y, tipo, var=0):
        self.objetos[(x, y)] = (tipo, var)
        self.area.add((x, y))

    def tirar(self, x, y):
        self.objetos.pop((x, y), None)

    def limpo(self, x, y):
        self.area.add((x, y))

    def bau(self, x, y, nivel, ouro=False):
        self.obj(x, y, "bau_tesouro", 1 if ouro else 0)
        self.baus[(x, y)] = nivel

    def npc(self, tipo, x, y, raio=5, **extra):
        n = len(self.npcs)
        self.npcs.append({"id": f"{self.id}#{n}", "tipo": tipo, "x": x, "y": y, "raio": raio,
                          "estrutura": self.id, "bioma": self.bioma, **extra})

    def retangulo_area(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.area.add((x, y))

    def contem(self, tx, ty, folga=0):
        x0, y0, x1, y1 = self.caixa
        return x0 - folga <= tx <= x1 + folga and y0 - folga <= ty <= y1 + folga

    @property
    def centro(self):
        x0, y0, x1, y1 = self.caixa
        return ((x0 + x1) // 2, (y0 + y1) // 2)


# ===============================================================
# Peças reutilizáveis
# ===============================================================
def casa(est, x, y, w, h, mat, lado_porta, rng, mobilia=True, nivel_bau=1):
    """Casa com paredes, piso, porta e mobília. Retorna o bloco logo fora da porta."""
    parede, pvar = mat["parede"]
    piso, svar = mat["piso"]
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            borda = xx in (x, x + w - 1) or yy in (y, y + h - 1)
            if borda:
                est.obj(xx, yy, parede, pvar)
            else:
                est.chao(xx, yy, piso, svar)
    if lado_porta == "baixo":
        px, py, fora = x + w // 2, y + h - 1, (x + w // 2, y + h)
    elif lado_porta == "cima":
        px, py, fora = x + w // 2, y, (x + w // 2, y - 1)
    elif lado_porta == "esquerda":
        px, py, fora = x, y + h // 2, (x - 1, y + h // 2)
    else:
        px, py, fora = x + w - 1, y + h // 2, (x + w, y + h // 2)
    est.chao(px, py, piso, svar)
    est.obj(px, py, "porta")
    if mobilia:
        dentro = [(xx, yy) for yy in range(y + 1, y + h - 1) for xx in range(x + 1, x + w - 1)
                  if abs(xx - px) + abs(yy - py) > 1]
        rng.shuffle(dentro)
        cantos = sorted(dentro, key=lambda p: -(min(p[0] - x, x + w - 1 - p[0]) == 1) -
                        (min(p[1] - y, y + h - 1 - p[1]) == 1))
        coisas = ["cama"]
        if rng.random() < 0.45:
            coisas.append("bau")
        if rng.random() < 0.30:
            coisas.append("bancada")
        for coisa, (cx, cy) in zip(coisas, cantos):
            if coisa == "bau":
                est.bau(cx, cy, nivel_bau)
            else:
                est.obj(cx, cy, coisa)
    est.area.add(fora)
    return fora, ((x + w // 2), (y + h // 2))


def muralha(est, x0, y0, x1, y1, parede, var, portoes, torres=True, tam_torre=3):
    """Muro em volta do retângulo, com torres nos cantos e portões (lista de (x, y, largura, 'h'/'v'))."""
    buracos = set()
    for (gx, gy, larg, orient) in portoes:
        for i in range(larg):
            buracos.add((gx + i, gy) if orient == "h" else (gx, gy + i))
    for x in range(x0, x1 + 1):
        for y in (y0, y1):
            if (x, y) not in buracos:
                est.obj(x, y, parede, var)
    for y in range(y0, y1 + 1):
        for x in (x0, x1):
            if (x, y) not in buracos:
                est.obj(x, y, parede, var)
    for b in buracos:
        est.chao(b[0], b[1], "caminho", 0)
    if torres:
        t = tam_torre
        for (cx, cy) in ((x0, y0), (x1 - t + 1, y0), (x0, y1 - t + 1), (x1 - t + 1, y1 - t + 1)):
            for yy in range(cy, cy + t):
                for xx in range(cx, cx + t):
                    est.obj(xx, yy, parede, var)
    return buracos


def vila(est, ox, oy, rng, mat, aldeoes=True, nivel_bau=1, comerciantes=False):
    """Vila em grade 3x3 de lotes: praça com poço no meio, casas e plantações em volta."""
    LW, LH, P = 10, 9, 2
    largura, altura = 3 * LW + 2 * P, 3 * LH + 2 * P
    cv = mat["caminho"]
    # caminhos (linhas entre os lotes)
    for k in (1, 2):
        xc = ox + k * LW + (k - 1) * P
        for y in range(oy, oy + altura):
            for xx in range(xc, xc + P):
                est.chao(xx, y, "caminho", cv)
        yc = oy + k * LH + (k - 1) * P
        for x in range(ox, ox + largura):
            for yy in range(yc, yc + P):
                est.chao(x, yy, "caminho", cv)
    lotes = [(gx, gy) for gy in range(3) for gx in range(3) if (gx, gy) != (1, 1)]
    rng.shuffle(lotes)
    usos = ["casa"] * 3 + [rng.choice(["casa", "casa", "plantacao", "vazio"]) for _ in range(5)]
    if "plantacao" not in usos:
        usos[3] = "plantacao"
    rng.shuffle(usos)
    casas = []
    for (gx, gy), uso in zip(lotes, usos):
        lx, ly = ox + gx * (LW + P), oy + gy * (LH + P)
        if uso == "casa":
            w, h = rng.randint(5, 8), rng.randint(5, 7)
            hx, hy = lx + rng.randint(0, LW - w), ly + rng.randint(0, LH - h)
            if gy == 0:
                lado = "baixo"
            elif gy == 2:
                lado = "cima"
            else:
                lado = "direita" if gx == 0 else "esquerda"
            fora, meio = casa(est, hx, hy, w, h, mat, lado, rng, nivel_bau=nivel_bau)
            # trilha da porta até o caminho
            dx, dy = {"baixo": (0, 1), "cima": (0, -1), "esquerda": (-1, 0), "direita": (1, 0)}[lado]
            x, y = fora
            for _ in range(LW + P):
                if (x, y) in est.pisos and est.pisos[(x, y)][0] == "caminho":
                    break
                est.chao(x, y, "caminho", cv)
                x, y = x + dx, y + dy
            casas.append(meio)
        elif uso == "plantacao":
            w, h = rng.randint(7, 9), rng.randint(5, 7)
            fx, fy = lx + rng.randint(0, LW - w), ly + rng.randint(0, LH - h)
            var = rng.randrange(2)
            abertura = (fx + w // 2, fy + h - 1 if gy == 0 else fy)
            for yy in range(fy, fy + h):
                for xx in range(fx, fx + w):
                    borda = xx in (fx, fx + w - 1) or yy in (fy, fy + h - 1)
                    if borda:
                        if (xx, yy) != abertura:
                            est.obj(xx, yy, "cerca")
                        else:
                            est.limpo(xx, yy)
                    else:
                        est.chao(xx, yy, "terra_arada")
                        if (yy - fy) % 2 == 1:
                            est.obj(xx, yy, ("plantacao_trigo", "plantacao_abobora")[var])
            if aldeoes and rng.random() < 0.6:
                est.npc("aldeao", fx + w // 2, fy + h + (0 if gy == 0 else -h - 1), raio=5,
                        comerciante=comerciantes)
        else:
            if rng.random() < 0.5:
                x, y = lx + rng.randint(2, LW - 3), ly + rng.randint(2, LH - 3)
                est.obj(x, y, "fogueira")
    # praça do meio
    px0, py0 = ox + LW + P, oy + LH + P
    for y in range(py0, py0 + LH):
        for x in range(px0, px0 + LW):
            est.chao(x, y, "caminho", cv)
    cx, cy = px0 + LW // 2, py0 + LH // 2
    est.obj(cx, cy, "poco")
    for (tx, ty) in ((px0, py0), (px0 + LW - 1, py0), (px0, py0 + LH - 1), (px0 + LW - 1, py0 + LH - 1)):
        est.obj(tx, ty, "tocha")
    if aldeoes:
        for (mx, my) in casas:
            est.npc("aldeao", mx, my, raio=6, comerciante=comerciantes)
        est.npc("aldeao", cx, cy + 2, raio=4, comerciante=comerciantes)
    return largura, altura, (cx, cy)


# ===============================================================
# Construtores de cada tipo
# ===============================================================
def construir_vila(est, ox, oy, rng):
    vila(est, ox, oy, rng, MATERIAIS[est.bioma])


def construir_cidadela(est, ox, oy, rng):
    mat = PEDRA_DESERTO if est.bioma == "deserto" else PEDRA_CIDADE
    m = 4                                   # espaço entre o muro e a vila
    larg, alt = 34 + 2 * m, 31 + 2 * m
    x1, y1 = ox + larg - 1, oy + alt - 1
    est.retangulo_area(ox, oy, x1, y1)
    # vila de pedra lá dentro (linhas de caminho em x = ox+m+10..11 e y = oy+m+9..10)
    vila(est, ox + m, oy + m, rng, mat, nivel_bau=2, comerciantes=True)
    gx, gy = ox + m + 10, oy + m + 9
    portoes = [(gx, oy, 2, "h"), (gx, y1, 2, "h"), (ox, gy, 2, "v"), (x1, gy, 2, "v")]
    muralha(est, ox, oy, x1, y1, mat["parede"][0], mat["parede"][1], portoes)
    # caminhos dos portões até a vila
    for i in range(m + 1):
        for k in range(2):
            est.chao(gx + k, oy + i, "caminho", mat["caminho"])
            est.chao(gx + k, y1 - i, "caminho", mat["caminho"])
            est.chao(ox + i, gy + k, "caminho", mat["caminho"])
            est.chao(x1 - i, gy + k, "caminho", mat["caminho"])
    # guardas nos portões e tochas
    for (px, py, dx, dy) in ((gx, oy + 1, 0, 1), (gx, y1 - 1, 0, -1), (ox + 1, gy, 1, 0), (x1 - 1, gy, -1, 0)):
        est.npc("guarda", px + dx, py + dy, raio=3)
        lado = (px - 1, py) if dy else (px, py - 1)
        est.obj(*lado, "tocha")
    est.npc("guarda", ox + larg // 2, oy + alt // 2 + 3, raio=8)
    est.npc("guarda", ox + larg // 2 - 6, oy + alt // 2 - 6, raio=8)
    # estandartes nos cantos de dentro
    for (bx, by) in ((ox + 4, oy + 1), (x1 - 4, oy + 1)):
        est.obj(bx, by + 0, "estandarte", 1)


def construir_castelo(est, ox, oy, rng):
    larg, alt = 40, 34
    x1, y1 = ox + larg - 1, oy + alt - 1
    parede = ("parede_pedra", 3)
    est.retangulo_area(ox, oy, x1, y1)
    # pátio
    for y in range(oy + 1, y1):
        for x in range(ox + 1, x1):
            est.chao(x, y, "piso_pedra", 0)
    gx = ox + larg // 2 - 1
    muralha(est, ox, oy, x1, y1, *parede, [(gx, y1, 2, "h")], tam_torre=4)
    # torre de vigia nos lados
    for yy in range(oy + alt // 2 - 1, oy + alt // 2 + 2):
        for xx in (ox + 1, x1 - 1):
            est.obj(xx, yy, *parede)
    # torre central (salão do trono)
    kx0, ky0, kx1, ky1 = ox + 8, oy + 4, x1 - 8, oy + 17
    for y in range(ky0, ky1 + 1):
        for x in range(kx0, kx1 + 1):
            if x in (kx0, kx1) or y in (ky0, ky1):
                est.obj(x, y, *parede)
            else:
                est.chao(x, y, "piso_pedra", 1)
    meio = (kx0 + kx1) // 2
    for x in (meio, meio + 1):              # porta dupla do salão
        est.tirar(x, ky1)
        est.chao(x, ky1, "tapete")
    for y in range(ky0 + 2, ky1):           # tapete até o trono
        est.chao(meio, y, "tapete")
        est.chao(meio + 1, y, "tapete")
    est.obj(meio, ky0 + 1, "trono")
    est.chao(meio + 1, ky0 + 1, "tapete")
    for x in (kx0 + 2, kx0 + 6, kx1 - 6, kx1 - 2):
        est.obj(x, ky0 + 1, "estandarte")
    for y in range(ky0 + 3, ky1 - 1, 4):
        est.obj(kx0 + 1, y, "tocha")
        est.obj(kx1 - 1, y, "tocha")
    # baús do tesouro do castelo
    est.bau(kx0 + 1, ky0 + 1, 3, ouro=True)
    est.bau(kx1 - 1, ky0 + 1, 3, ouro=True)
    est.bau(kx0 + 1, ky1 - 1, 2)
    est.bau(kx1 - 1, ky1 - 1, 2)
    # pátio: caminho do portão ao salão, poço, tochas
    for y in range(ky1 + 1, y1 + 1):
        est.chao(gx, y, "caminho", 0)
        est.chao(gx + 1, y, "caminho", 0)
    est.obj(ox + 5, y1 - 5, "poco")
    for x in range(ox + 6, x1 - 5, 7):
        est.obj(x, y1 - 1, "tocha")
    est.obj(gx - 1, y1 - 1, "tocha")
    est.obj(gx + 2, y1 - 1, "tocha")
    est.bau(x1 - 5, y1 - 4, 2)
    # defensores
    for _ in range(6):
        x, y = rng.randint(ox + 4, x1 - 4), rng.randint(ky1 + 2, y1 - 3)
        if (x, y) not in est.objetos:
            est.npc("cavaleiro", x, y, raio=9)
    for x in (meio - 3, meio + 4):
        est.npc("cavaleiro", x, ky0 + 6, raio=5)
    est.npc("senhor_castelo", meio + 1, ky0 + 3, raio=6, chefe=True)


def construir_masmorra(est, ox, oy, rng):
    """Entrada: anel de pedra quebrada com a escada no meio."""
    t = 9
    musgo = ("parede_pedra", 1 if est.bioma == "deserto" else 4)
    est.retangulo_area(ox, oy, ox + t - 1, oy + t - 1)
    meio = t // 2
    for y in range(oy, oy + t):
        for x in range(ox, ox + t):
            borda = x in (ox, ox + t - 1) or y in (oy, oy + t - 1)
            if borda:
                porta = (x == ox + meio and y == oy + t - 1)
                if not porta and rng.random() < 0.75:
                    est.obj(x, y, *musgo)
                else:
                    est.chao(x, y, "piso_pedra", 2)
            else:
                est.chao(x, y, "piso_pedra", 2 if rng.random() < 0.6 else 1)
    est.obj(ox + meio, oy + meio, "escada_descer")
    est.obj(ox + meio - 2, oy + meio - 1, "tocha")
    est.obj(ox + meio + 2, oy + meio - 1, "tocha")
    est.obj(ox + 1, oy + t - 2, "ossos")


def construir_ruina(est, ox, oy, rng):
    t = rng.randint(9, 13)
    var = 1 if est.bioma == "deserto" else 4
    for y in range(oy, oy + t):
        for x in range(ox, ox + t):
            borda = x in (ox, ox + t - 1) or y in (oy, oy + t - 1)
            if borda:
                if rng.random() < 0.55:
                    est.obj(x, y, "parede_pedra", var)
                else:
                    est.limpo(x, y)
            elif rng.random() < 0.65:
                est.chao(x, y, "piso_pedra", 2)
            else:
                est.limpo(x, y)
    for _ in range(rng.randint(1, 3)):          # pilares
        x, y = rng.randint(ox + 2, ox + t - 3), rng.randint(oy + 2, oy + t - 3)
        est.obj(x, y, "parede_pedra", var)
    cx, cy = ox + t // 2, oy + t // 2
    est.bau(cx, cy, 1)
    est.obj(cx + 1, cy + 1, "ossos")
    if rng.random() < 0.5:
        est.npc("esqueleto", cx - 2, cy, raio=5)


def construir_tesouro(est, ox, oy, rng):
    cx, cy = ox + 2, oy + 2
    for (x, y) in ((cx - 1, cy - 1), (cx + 1, cy - 1), (cx, cy), (cx - 1, cy + 1), (cx + 1, cy + 1)):
        est.chao(x, y, "caminho", 1 if est.bioma == "deserto" else 0)
    est.retangulo_area(ox, oy, ox + 4, oy + 4)
    est.bau(cx, cy, 1, ouro=rng.random() < 0.3)
    est.obj(cx - 2, cy - 2, "tocha")


CONSTRUTORES = {
    "vila": (construir_vila, 34, 31),
    "cidadela": (construir_cidadela, 42, 39),
    "castelo": (construir_castelo, 40, 34),
    "masmorra": (construir_masmorra, 9, 9),
    "ruina": (construir_ruina, 13, 13),
    "tesouro": (construir_tesouro, 5, 5),
}


# ===============================================================
# Planejador (uma por mundo; tudo determinístico pela semente)
# ===============================================================
class PlanoEstruturas:
    def __init__(self, semente, gerador):
        self.semente = semente
        self.gerador = gerador
        self._cache = {}               # (rx, ry) -> Estrutura ou None
        self.abertos = set()           # ids dos baús já abertos (preenchido pelo jogo)

    # ----- sorteio por região -----
    def regiao(self, rx, ry):
        k = (rx, ry)
        if k not in self._cache:
            self._cache[k] = self._planejar(rx, ry)
            if len(self._cache) > 400:     # não deixa o cache crescer sem fim
                for velho in list(self._cache)[:100]:
                    del self._cache[velho]
        return self._cache[k]

    def _amostrar(self, x0, y0, w, h, permitidos):
        """Bioma do centro, fração de água e fração de biomas proibidos (amostra a cada 3 blocos)."""
        g = self.gerador
        agua = proibido = total = 0
        for y in range(y0, y0 + h, 3):
            for x in range(x0, x0 + w, 3):
                b, alt, nb = g.dados_bloco(x, y)
                if g.classificar(b, alt, nb, 0.0) in CHAO_AGUA + (LAMA,):
                    agua += 1
                if b not in permitidos:
                    proibido += 1
                total += 1
        bioma = g.bioma(x0 + w // 2, y0 + h // 2)
        return bioma, agua / max(1, total), proibido / max(1, total)

    def _planejar(self, rx, ry):
        rng = random.Random(numero(self.semente, "regiao", rx, ry))
        sorteio = rng.random()
        tipo, acumulado = None, 0.0
        for t, chance in CHANCES:
            acumulado += chance
            if sorteio < acumulado:
                tipo = t
                break
        if tipo is None:
            return None
        if (rx, ry) == (0, 0) and tipo in ("castelo",):
            tipo = "ruina"              # nada perigoso demais perto do começo
        construtor, w, h = CONSTRUTORES[tipo]
        for _ in range(3):              # até 3 lugares diferentes dentro da região
            x0 = rx * REGIAO + rng.randint(4, REGIAO - w - 4)
            y0 = ry * REGIAO + rng.randint(4, REGIAO - h - 4)
            permitidos = BIOMAS_PERMITIDOS[tipo]
            bioma, agua, proibido = self._amostrar(x0, y0, w, h, permitidos)
            if bioma in permitidos and agua <= AGUA_MAXIMA[tipo] + 1e-9 and proibido <= 0.15:
                est = Estrutura(tipo, f"{tipo}:{rx},{ry}", bioma, x0, y0, w, h)
                construtor(est, x0, y0, random.Random(numero(self.semente, est.id)))
                return est
        return None

    # ----- consultas -----
    def estruturas_na_caixa(self, x0, y0, x1, y1):
        achou = []
        for ry in range(y0 // REGIAO, y1 // REGIAO + 1):
            for rx in range(x0 // REGIAO, x1 // REGIAO + 1):
                est = self.regiao(rx, ry)
                if est is None:
                    continue
                a, b, c, d = est.caixa
                if a <= x1 and c >= x0 and b <= y1 and d >= y0:
                    achou.append(est)
        return achou

    def estrutura_em(self, tx, ty, folga=0):
        est = self.regiao(tx // REGIAO, ty // REGIAO)
        if est and est.contem(tx, ty, folga):
            return est
        return None

    def por_id(self, ident):
        tipo, resto = ident.split(":", 1)
        rx, ry = (int(v) for v in resto.split(","))
        est = self.regiao(rx, ry)
        return est if est and est.id == ident else None

    @staticmethod
    def id_bau(tx, ty, prefixo=""):
        return f"{prefixo}{tx},{ty}"

    # ----- carimbo no chunk -----
    def carimbar(self, ch, classe_objeto):
        """Copia para o chunk a parte das estruturas que cai nele."""
        x0, y0 = ch.cx * CH, ch.cy * CH
        x1, y1 = x0 + CH - 1, y0 + CH - 1
        lista = self.estruturas_na_caixa(x0, y0, x1, y1)
        if not lista:
            return False
        for est in lista:
            for j in range(CH):
                ty = y0 + j
                for i in range(CH):
                    tx = x0 + i
                    p = (tx, ty)
                    if p in est.area:
                        k = j * CH + i
                        ch.alturas[k] = max(ch.alturas[k], ch.niveis[k] + ATERRO)
                        o = ch.objetos.get(p)
                        if o is not None and not o.construcao:
                            del ch.objetos[p]
                    if p in est.pisos:
                        t, v = est.pisos[p]
                        ch.pisos[p] = classe_objeto(t, tx, ty, v)
                    if p in est.objetos:
                        t, v = est.objetos[p]
                        if t == "bau_tesouro" and self.id_bau(tx, ty) in self.abertos:
                            t = "bau_tesouro_aberto"
                        ch.objetos[p] = classe_objeto(t, tx, ty, v)
        ch.recalcular_chao(0.0)
        ch.estruturas = [e.id for e in lista]
        return True
