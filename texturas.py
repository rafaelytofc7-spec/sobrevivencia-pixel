# -*- coding: utf-8 -*-
"""
texturas.py - Texturas do chão (geradas por código) e o desenho do chão dos chunks.

- 8 variações por tipo de chão, com manchas, tufos, pedrinhas, flores...
- Cores mudam com a ESTAÇÃO (outono amarelado, inverno coberto de neve).
- Transições (autotiling): o chão "mais alto" na ordem PRIORIDADE invade a
  borda do vizinho com um recorte irregular, então biomas e margens de água
  ficam arredondadas em vez de quadradas. A água ganha espuma na margem.
- Ondas animadas são desenhadas por cima da água a cada quadro (o resto do
  chão fica guardado em cache por chunk).
"""
import math
import random
import pygame

from config import (TILE, TAMANHO_CHUNK, AGUA_FUNDA, AGUA_RASA, LAMA, AREIA, GRAMA,
                    GRAMA_FLORESTA, GRAMA_PANTANO, NEVE, ROCHA, CHAO_AGUA)
from ruido import ruido

CH = TAMANHO_CHUNK
N_VARIANTES = 8
PRIORIDADE = {AGUA_FUNDA: 0, AGUA_RASA: 1, LAMA: 2, AREIA: 3, GRAMA_PANTANO: 4,
              GRAMA: 5, GRAMA_FLORESTA: 6, ROCHA: 7, NEVE: 8}
ESPUMA = (226, 242, 252, 255)
ESPUMA_2 = (176, 216, 246, 255)


def _limitar(c):
    return max(0, min(255, int(c)))


def _misturar(a, b, t):
    return tuple(_limitar(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ruido_tile(x, y, escala, semente):
    """Ruído que 'emenda' com ele mesmo nas bordas do tile."""
    fx, fy = x / TILE, y / TILE
    return (ruido(x / escala, y / escala, semente) * (1 - fx) * (1 - fy)
            + ruido((x - TILE) / escala, y / escala, semente) * fx * (1 - fy)
            + ruido(x / escala, (y - TILE) / escala, semente) * (1 - fx) * fy
            + ruido((x - TILE) / escala, (y - TILE) / escala, semente) * fx * fy)


def _tile_base(paleta, semente, escala=5.0, granulado=0.10):
    """Tile com manchas suaves (ruído) + granulado. paleta = (escuro, médio, claro)."""
    rng = random.Random(semente)
    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    esc, med, cla = paleta
    base_ruido = semente // 100 * 100 + semente % 3       # 3 padrões de manchas por tipo
    for y in range(TILE):
        for x in range(TILE):
            # ruído periódico no tile (para não aparecer emenda)
            n = _ruido_tile(x, y, escala, base_ruido)
            r = rng.random()
            if r < granulado:
                cor = esc
            elif r < granulado * 1.6:
                cor = cla
            elif n < 0.36:
                cor = _misturar(med, esc, 0.3)
            elif n > 0.66:
                cor = _misturar(med, cla, 0.28)
            else:
                cor = med
            s.set_at((x, y), cor)
    return s, rng


def _tufos(s, rng, n, cor_esc, cor_cla):
    for _ in range(n):
        x, y = rng.randrange(1, 15), rng.randrange(3, 15)
        s.set_at((x, y), cor_esc)
        s.set_at((x, y - 1), cor_esc)
        s.set_at((x + 1, y), cor_cla)
        if rng.random() < 0.5:
            s.set_at((x - 1, y - 1), cor_cla)


def _pedrinhas(s, rng, n, cor=(150, 146, 136), sombra=(96, 92, 86)):
    for _ in range(n):
        x, y = rng.randrange(1, 14), rng.randrange(1, 14)
        s.set_at((x, y), cor)
        s.set_at((x + 1, y), cor)
        s.set_at((x, y + 1), sombra)
        s.set_at((x + 1, y + 1), sombra)


# ---------------------------------------------------------------
# Cada tipo de chão
# ---------------------------------------------------------------
def tile_grama(semente, estacao):
    pal = {"primavera": ((84, 160, 64), (110, 188, 78), (146, 210, 98)),
           "verao": ((76, 146, 62), (96, 168, 72), (124, 192, 90)),
           "outono": ((130, 124, 52), (160, 148, 64), (190, 172, 84)),
           "inverno": ((76, 146, 62), (96, 168, 72), (124, 192, 90))}[estacao]
    s, rng = _tile_base(pal, semente)
    _tufos(s, rng, 5, _misturar(pal[0], (0, 0, 0), 0.15), pal[2])
    flores = {"primavera": 0.8, "verao": 0.35, "outono": 0.1, "inverno": 0.0}[estacao]
    while rng.random() < flores:
        flores -= 0.3
        x, y = rng.randrange(2, 14), rng.randrange(2, 14)
        cor = rng.choice([(250, 240, 120), (240, 120, 160), (250, 250, 250), (170, 150, 250)])
        s.set_at((x, y), cor)
        s.set_at((x, y + 1), (60, 120, 50))
    if rng.random() < 0.2:
        _pedrinhas(s, rng, 1)
    if estacao == "outono":
        for _ in range(3):
            s.set_at((rng.randrange(16), rng.randrange(16)), rng.choice([(200, 110, 40), (180, 70, 40)]))
    if estacao == "inverno":
        _cobrir_neve(s, rng, semente, 0.78)
    return s


def tile_floresta(semente, estacao):
    pal = {"primavera": ((52, 116, 50), (70, 140, 60), (96, 166, 76)),
           "verao": ((46, 102, 46), (62, 128, 56), (84, 150, 68)),
           "outono": ((120, 72, 34), (150, 96, 42), (188, 128, 56)),
           "inverno": ((46, 102, 46), (62, 128, 56), (84, 150, 68))}[estacao]
    s, rng = _tile_base(pal, semente, escala=4.0, granulado=0.14)
    folhas = [(140, 100, 50), (120, 86, 44)] if estacao != "outono" else \
        [(220, 120, 40), (200, 70, 40), (230, 170, 60)]
    for _ in range(4 if estacao != "outono" else 10):
        x, y = rng.randrange(16), rng.randrange(16)
        cor = rng.choice(folhas)
        s.set_at((x, y), cor)
        if rng.random() < 0.4 and x < 15:
            s.set_at((x + 1, y), cor)
    _tufos(s, rng, 2, _misturar(pal[0], (0, 0, 0), 0.2), pal[2])
    if estacao == "inverno":
        _cobrir_neve(s, rng, semente, 0.7)
    return s


def tile_pantano(semente, estacao):
    pal = ((74, 92, 54), (92, 112, 62), (112, 132, 74))
    if estacao == "outono":
        pal = ((96, 92, 50), (116, 110, 58), (138, 130, 72))
    s, rng = _tile_base(pal, semente, escala=3.5, granulado=0.14)
    if rng.random() < 0.6:  # pocinha
        x, y = rng.randrange(2, 10), rng.randrange(2, 12)
        pygame.draw.ellipse(s, (64, 90, 96), (x, y, 5, 3))
        s.set_at((x + 1, y + 1), (110, 140, 140))
    _tufos(s, rng, 3, (60, 80, 44), (130, 150, 80))
    if estacao == "inverno":
        _cobrir_neve(s, rng, semente, 0.55)
    return s


def tile_neve(semente, estacao):
    s, rng = _tile_base(((206, 218, 236), (232, 238, 248), (255, 255, 255)), semente, escala=4.0, granulado=0.08)
    for _ in range(2):
        s.set_at((rng.randrange(16), rng.randrange(16)), (180, 200, 230))
    if rng.random() < 0.3:
        x, y = rng.randrange(2, 13), rng.randrange(3, 13)
        s.set_at((x, y), (90, 110, 80))   # graminha aparecendo
        s.set_at((x, y - 1), (110, 130, 96))
    return s


def tile_rocha(semente, estacao):
    s, rng = _tile_base(((100, 98, 98), (126, 122, 118), (154, 150, 144)), semente, escala=3.0, granulado=0.12)
    x, y = rng.randrange(1, 11), rng.randrange(2, 12)
    for i in range(rng.randrange(3, 6)):     # rachadura
        s.set_at((x + i, y + (i % 2)), (80, 76, 76))
        s.set_at((x + i, y + (i % 2) + 1), (160, 156, 150))
    _pedrinhas(s, rng, 2, (160, 156, 150), (90, 86, 84))
    if estacao == "inverno":
        _cobrir_neve(s, rng, semente, 0.25)
    return s


def tile_areia(semente, estacao):
    s, rng = _tile_base(((206, 182, 120), (226, 204, 140), (240, 224, 170)), semente, escala=6.0, granulado=0.07)
    for _ in range(2):                       # ondinhas de areia
        x0, y0 = rng.randrange(0, 10), rng.randrange(2, 14)
        for x in range(x0, x0 + rng.randrange(3, 6)):
            s.set_at((x, y0 + (1 if (x - x0) % 4 == 2 else 0)), (208, 184, 122))
    if rng.random() < 0.2:
        x, y = rng.randrange(2, 13), rng.randrange(2, 13)
        s.set_at((x, y), (250, 236, 220))    # conchinha
        s.set_at((x + 1, y), (230, 190, 170))
    return s


def tile_lama(semente, estacao):
    s, rng = _tile_base(((100, 74, 50), (122, 92, 62), (146, 114, 80)), semente, escala=4.0, granulado=0.12)
    x, y = rng.randrange(1, 10), rng.randrange(1, 12)
    for i in range(6):                       # rachaduras de lama seca
        s.set_at((x + i, y + (i % 2)), (80, 58, 40))
        if i == 3:
            s.set_at((x + i, y + 2), (80, 58, 40))
    if rng.random() < 0.5:
        pygame.draw.ellipse(s, (92, 70, 52), (rng.randrange(2, 10), rng.randrange(2, 12), 4, 2))
    return s


def tile_agua(semente, funda):
    if funda:
        pal = ((34, 74, 152), (42, 88, 174), (56, 104, 192))
    else:
        pal = ((66, 132, 200), (80, 148, 212), (98, 166, 224))
    s, rng = _tile_base(pal, semente, escala=5.0, granulado=0.03)
    return s


def _cobrir_neve(s, rng, semente, quanto):
    """Cobre o tile com neve; só um pouco do chão de baixo aparece (quanto = fração de neve)."""
    original = s.copy()
    for y in range(TILE):
        for x in range(TILE):
            n = _ruido_tile(x, y, 4.0, semente % 3 + 900)
            r = rng.random()
            cor = (232, 238, 248) if n > 0.4 else (216, 226, 242)
            if r < 0.05:
                cor = (255, 255, 255)
            s.set_at((x, y), cor)
    # pedacinhos do chão aparecendo
    for _ in range(int((1 - quanto) * 14)):
        x, y = rng.randrange(1, 15), rng.randrange(1, 15)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if rng.random() < 0.8:
                s.set_at((x + dx, y + dy), original.get_at((x + dx, y + dy)))
        s.set_at((x, y - 1), (200, 212, 232))


FABRICAS = {GRAMA: tile_grama, GRAMA_FLORESTA: tile_floresta, GRAMA_PANTANO: tile_pantano,
            NEVE: tile_neve, ROCHA: tile_rocha, AREIA: tile_areia, LAMA: tile_lama}


# ---------------------------------------------------------------
# Máscaras das transições
# ---------------------------------------------------------------
def _mascara_borda(lado, variante):
    """Conjunto de pixels de uma faixa irregular encostada no lado ('n','s','e','w')."""
    rng = random.Random(77 + variante * 13 + "nsew".index(lado))
    prof = []
    d = 3
    for i in range(TILE):
        if i in (0, TILE - 1):
            d = 3
        else:
            d = max(2, min(5, d + rng.choice((-1, 0, 0, 1))))
        prof.append(d)
    pts = set()
    for i in range(TILE):
        for k in range(prof[i]):
            if lado == "n":
                pts.add((i, k))
            elif lado == "s":
                pts.add((i, TILE - 1 - k))
            elif lado == "w":
                pts.add((k, i))
            else:
                pts.add((TILE - 1 - k, i))
    return pts


def _mascara_canto(canto, variante):
    rng = random.Random(311 + variante * 7 + ["ne", "nw", "se", "sw"].index(canto))
    r = 3.6 + rng.random() * 0.8
    pts = set()
    for y in range(6):
        for x in range(6):
            if math.hypot(x + 0.5, y + 0.5) <= r + rng.uniform(-0.4, 0.4):
                X = x if "w" in canto else TILE - 1 - x
                Y = y if "n" in canto else TILE - 1 - y
                pts.add((X, Y))
    return pts


DIRECOES = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}
CANTOS = {"nw": (-1, -1), "ne": (1, -1), "sw": (-1, 1), "se": (1, 1)}


class Texturas:
    def __init__(self):
        self.mascaras = {}
        for v in range(2):
            for lado in "nsew":
                self.mascaras[(lado, v)] = _mascara_borda(lado, v)
            for canto in CANTOS:
                self.mascaras[(canto, v)] = _mascara_canto(canto, v)
        self._tiles = {}           # estacao -> {tipo: [variantes]}
        self._sobreposicoes = {}   # (estacao, tipo, mascara) -> Surface
        self._espumas = {}
        self.agua = {AGUA_RASA: [tile_agua(70 + i, False) for i in range(N_VARIANTES)],
                     AGUA_FUNDA: [tile_agua(80 + i, True) for i in range(N_VARIANTES)]}
        self.ondas = self._criar_ondas()

    # ---------------- tiles ----------------
    def tiles(self, estacao):
        if estacao not in self._tiles:
            d = {}
            for tipo, fab in FABRICAS.items():
                d[tipo] = [fab(100 * tipo + i, estacao) for i in range(N_VARIANTES)]
            d.update(self.agua)
            self._tiles[estacao] = d
        return self._tiles[estacao]

    def sobreposicao(self, estacao, tipo, mascara):
        k = (estacao, tipo, mascara)
        if k not in self._sobreposicoes:
            base = self.tiles(estacao)[tipo][mascara[1] * 3 % N_VARIANTES]
            s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pts = self.mascaras[mascara]
            for (x, y) in pts:
                s.set_at((x, y), base.get_at((x, y)))
            # rochas e neve ganham uma bordinha (cara de relevo)
            if tipo in (ROCHA, NEVE):
                borda = (92, 88, 86) if tipo == ROCHA else (196, 208, 228)
                for (x, y) in pts:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        q = (x + dx, y + dy)
                        if 0 <= q[0] < TILE and 0 <= q[1] < TILE and q not in pts:
                            s.set_at((x, y), borda)
                            break
            self._sobreposicoes[k] = s
        return self._sobreposicoes[k]

    def espuma(self, mascara):
        if mascara not in self._espumas:
            pts = self.mascaras[mascara]
            s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            for (x, y) in pts:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if 0 <= q[0] < TILE and 0 <= q[1] < TILE and q not in pts:
                        s.set_at(q, ESPUMA if (q[0] + q[1]) % 3 else ESPUMA_2)
            self._espumas[mascara] = s
        return self._espumas[mascara]

    # ---------------- ondas animadas ----------------
    def _criar_ondas(self):
        quadros = {AGUA_RASA: [], AGUA_FUNDA: []}
        for tipo, cor in ((AGUA_RASA, (160, 206, 244, 255)), (AGUA_FUNDA, (96, 146, 220, 255))):
            for q in range(4):
                lista = []
                for v in range(4):
                    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                    rng = random.Random(v * 31 + tipo)
                    for _ in range(2):
                        x0, y0 = rng.randrange(4, 9), rng.randrange(5, 11)
                        fase = (q + rng.randrange(4)) % 4
                        comp = [2, 3, 4, 2][fase]
                        for i in range(comp):
                            s.set_at((x0 + i + (fase // 2), y0), cor)
                        if fase == 2:
                            s.set_at((x0 + 1, y0 - 1), cor)
                    lista.append(s)
                quadros[tipo].append(lista)
        return quadros

    # ---------------- chunk ----------------
    def desenhar_chunk(self, sup, ch, mundo, estacao):
        """Pinta o chão de um chunk (com transições) na superfície 'sup' (256x256)."""
        tiles = self.tiles(estacao)
        chao = ch.chao
        x0, y0 = ch.cx * CH, ch.cy * CH

        def tipo_em(i, j):
            if 0 <= i < CH and 0 <= j < CH:
                return chao[j * CH + i]
            return mundo.tipo_chao(x0 + i, y0 + j)

        prio = PRIORIDADE
        for j in range(CH):
            for i in range(CH):
                tipo = chao[j * CH + i]
                tx, ty = x0 + i, y0 + j
                h = (tx * 73856093) ^ (ty * 19349663)
                var = (h >> 3) % N_VARIANTES
                px, py = i * TILE, j * TILE
                sup.blit(tiles[tipo][var], (px, py))
                p = prio[tipo]
                mv = (h >> 7) & 1
                # vizinhos "mais altos" invadem a borda
                lados = []
                for lado, (dx, dy) in DIRECOES.items():
                    v = tipo_em(i + dx, j + dy)
                    if prio[v] > p:
                        lados.append((prio[v], v, (lado, mv)))
                for canto, (dx, dy) in CANTOS.items():
                    v = tipo_em(i + dx, j + dy)
                    if prio[v] > p:
                        # só se os dois lados vizinhos do canto não forem desse tipo (senão a borda já cobre)
                        a = tipo_em(i + dx, j)
                        b = tipo_em(i, j + dy)
                        if prio[a] < prio[v] and prio[b] < prio[v]:
                            lados.append((prio[v], v, (canto, mv)))
                if not lados:
                    continue
                lados.sort(key=lambda e: e[0])
                agua = tipo in CHAO_AGUA
                if agua:
                    for _, v, m in lados:
                        if v not in CHAO_AGUA:
                            sup.blit(self.espuma(m), (px, py))
                for _, v, m in lados:
                    sup.blit(self.sobreposicao(estacao, v, m), (px, py))

    def desenhar_ondas(self, cena, mundo, cam_x, cam_y, largura, altura, tempo):
        """Ondinhas animadas nos blocos de água visíveis."""
        q = int(tempo * 2.5)
        tx0, ty0 = cam_x // TILE, cam_y // TILE
        tx1, ty1 = (cam_x + largura) // TILE, (cam_y + altura) // TILE
        ondas = self.ondas
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                t = mundo.tipo_chao(tx, ty)
                if t in CHAO_AGUA:
                    h = (tx * 92837111) ^ (ty * 689287499)
                    if h % 3 == 0:
                        continue
                    lista = ondas[t][(q + h) % 4]
                    cena.blit(lista[(h >> 4) % 4], (tx * TILE - cam_x, ty * TILE - cam_y))
