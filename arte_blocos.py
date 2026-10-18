# -*- coding: utf-8 -*-
"""
arte_blocos.py - Pixel art (feita por código) da v0.5: blocos em "cubinho"
(face de cima + 4 pixels de frente), minérios, chão de caverna e lava, buraco,
escada de mão, bichos novos (vaca, porco, ovelha, zumbi, esqueleto, Explosivo)
e os ícones dos itens novos.
"""
import math
import random
import pygame

from config import TILE, CAVERNA, LAVA
from sprites import (nova_superficie, contornar, bolha, pixels, retangulo, linha, escurecer,
                     tile_textura, _pernas, icone_machado, icone_picareta, icone_espada,
                     icone_capacete, icone_roupa, CABO, CABO_ESC, OLHO)

ALT_FRENTE = 4


# ===============================================================
# Blocos (16 x 20)
# ===============================================================
def _ruido_pixels(s, area, cores, chance, rng):
    x0, y0, w, h = area
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if rng.random() < chance:
                s.set_at((x, y), rng.choice(cores))


def cubo(topo, frente, frente_esc, semente=0, borda=True, detalhe_frente=None, base=None):
    """Junta a face de cima (16x16) com a frente (16x4)."""
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE + ALT_FRENTE)
    s.blit(topo, (0, 0))
    retangulo(s, 0, TILE, TILE, ALT_FRENTE, frente)
    _ruido_pixels(s, (0, TILE, TILE, ALT_FRENTE), [frente_esc, escurecer(frente, 1.08)], 0.25, rng)
    if detalhe_frente:
        detalhe_frente(s, rng)
    retangulo(s, 0, TILE + ALT_FRENTE - 1, TILE, 1, escurecer(frente_esc, 0.8))
    if borda:
        cor = base or tuple(topo.get_at((0, 8))[:3])
        claro = tuple(min(255, int(c * 1.12) + 8) for c in cor)
        esc = escurecer(cor, 0.72)
        retangulo(s, 0, 0, TILE, 1, claro)
        retangulo(s, 0, 0, 1, TILE, claro)
        retangulo(s, TILE - 1, 0, 1, TILE, esc)
        retangulo(s, 0, TILE - 1, TILE, 1, esc)
    return s


def topo_textura(base, escuro, claro, semente, pe=0.14, pc=0.08):
    return tile_textura(base, escuro, claro, semente, pe, pc)[0]


def _copia_alpha(sup):
    s = nova_superficie(TILE, TILE)
    s.blit(sup, (0, 0))
    return s


PEDRA = ((122, 122, 132), (100, 100, 112), (146, 146, 156))


def bloco_pedra(semente):
    t = topo_textura(*PEDRA, semente)
    rng = random.Random(semente + 5)
    base = PEDRA[0]
    for _ in range(3):
        x, y = rng.randrange(2, 12), rng.randrange(2, 13)
        linha(t, PEDRA[1], (x, y), (x + rng.randrange(2, 4), y + rng.choice((-1, 0, 1))))
    return cubo(t, (88, 88, 100), (70, 70, 82), semente, base=base)


def bloco_pedregulho(semente=1):
    t = nova_superficie(TILE, TILE)
    t.fill((96, 96, 104))
    rng = random.Random(semente)
    for (x, y, w, h) in ((1, 1, 5, 4), (7, 1, 4, 3), (12, 1, 3, 5), (1, 6, 3, 4), (5, 5, 6, 5),
                         (12, 7, 3, 4), (1, 11, 5, 4), (7, 11, 3, 4), (11, 12, 4, 3)):
        c = rng.choice(((140, 140, 150), (126, 126, 138), (154, 152, 160)))
        retangulo(t, x, y, w, h, c)
        retangulo(t, x, y, w, 1, escurecer(c, 1.15))
    return cubo(t, (90, 90, 100), (66, 66, 76), semente, base=(126, 126, 138))


def bloco_pedra_lisa():
    t = topo_textura((160, 160, 166), (146, 146, 154), (174, 174, 180), 21, 0.06, 0.04)
    pygame.draw.rect(t, (130, 130, 140), (2, 2, 12, 12), 1)
    return cubo(t, (122, 122, 130), (104, 104, 114), 21)


def bloco_terra():
    t = topo_textura((134, 94, 60), (110, 76, 48), (156, 114, 76), 31, 0.2, 0.1)
    return cubo(t, (104, 72, 44), (84, 58, 36), 31)


def bloco_areia():
    t = topo_textura((222, 204, 146), (204, 184, 128), (236, 222, 170), 41, 0.18, 0.1)
    return cubo(t, (194, 174, 118), (172, 152, 100), 41)


def bloco_tora():
    t = nova_superficie(TILE, TILE)
    t.fill((110, 74, 42))
    for r, c in ((7, (176, 132, 82)), (5, (196, 152, 98)), (3, (172, 128, 78)), (1, (150, 106, 62))):
        pygame.draw.circle(t, c, (8, 8), r)
    pygame.draw.circle(t, (110, 74, 42), (8, 8), 7, 1)

    def casca(s, rng):
        for x in range(0, TILE, 3):
            retangulo(s, x, TILE, 1, ALT_FRENTE, (70, 46, 26))
    return cubo(t, (104, 70, 40), (82, 54, 30), 51, detalhe_frente=casca, base=(150, 106, 62))


def bloco_tabuas():
    t = nova_superficie(TILE, TILE)
    t.fill((184, 140, 86))
    for y in (0, 4, 8, 12):
        retangulo(t, 0, y + 3, TILE, 1, (140, 100, 58))
        off = 5 if (y // 4) % 2 else 11
        retangulo(t, off, y, 1, 3, (150, 108, 64))
    pixels(t, [(3, 1), (12, 6), (6, 10), (14, 13)], (200, 158, 102))
    return cubo(t, (150, 108, 62), (126, 88, 50), 61)


def bloco_vidro():
    s = nova_superficie(TILE, TILE + ALT_FRENTE)
    vidro = (190, 226, 240)
    s.fill((*vidro, 60), (1, 1, TILE - 2, TILE - 2))
    pygame.draw.rect(s, (220, 244, 252, 255), (0, 0, TILE, TILE), 1)
    linha(s, (255, 255, 255, 230), (3, 4), (6, 1))
    linha(s, (255, 255, 255, 200), (4, 7), (9, 2))
    s.fill((150, 196, 214, 150), (0, TILE, TILE, ALT_FRENTE))
    pygame.draw.rect(s, (200, 232, 244, 255), (0, TILE, TILE, ALT_FRENTE), 1)
    return s


def bloco_minerio(semente, cores, brilho=None):
    t = topo_textura(*PEDRA, semente + 200)
    rng = random.Random(semente * 3 + 7)
    for _ in range(5):
        x, y = rng.randrange(1, 13), rng.randrange(1, 13)
        retangulo(t, x, y, 2, 2, cores[0])
        t.set_at((x, y), cores[1])
        if rng.random() < 0.6:
            t.set_at((x + 2, y + 1), cores[0])
    if brilho:
        for _ in range(3):
            t.set_at((rng.randrange(1, 15), rng.randrange(1, 15)), brilho)

    def pontos(s, rng2):
        for _ in range(3):
            x = rng2.randrange(1, 14)
            retangulo(s, x, TILE + 1, 2, 2, escurecer(cores[0], 0.8))
    return cubo(t, (88, 88, 100), (70, 70, 82), semente, detalhe_frente=pontos, base=PEDRA[0])


MINERIOS_CORES = {
    "min_carvao": ((34, 32, 38), (70, 66, 74), None),
    "min_ferro": ((214, 168, 128), (240, 206, 170), None),
    "min_ouro": ((246, 206, 60), (255, 246, 160), (255, 255, 210)),
    "min_cristal": ((220, 40, 70), (255, 120, 140), (255, 190, 200)),
    "min_diamante": ((80, 230, 226), (200, 255, 250), (255, 255, 255)),
}


def bloco_lampada():
    t = nova_superficie(TILE, TILE)
    t.fill((250, 226, 150))
    for i in (4, 8, 12):
        retangulo(t, i - 1, 0, 1, TILE, (200, 150, 80))
        retangulo(t, 0, i - 1, TILE, 1, (200, 150, 80))
    retangulo(t, 6, 6, 4, 4, (255, 252, 230))
    return cubo(t, (214, 170, 96), (180, 130, 70), 71, base=(240, 210, 130))


# ===============================================================
# Chão das cavernas, buraco e escada
# ===============================================================
def tile_caverna(semente):
    s, _ = tile_textura((72, 68, 72), (58, 54, 60), (90, 86, 92), semente + 300, 0.18, 0.08)
    rng = random.Random(semente)
    for _ in range(3):
        x, y = rng.randrange(1, 14), rng.randrange(1, 14)
        retangulo(s, x, y, 2, 1, (98, 94, 100))
    return s


def tile_lava(semente):
    s, _ = tile_textura((226, 92, 28), (184, 52, 20), (255, 170, 60), semente + 400, 0.2, 0.15)
    rng = random.Random(semente)
    for _ in range(3):
        x, y = rng.randrange(0, 13), rng.randrange(0, 14)
        retangulo(s, x, y, 3, 1, (255, 220, 110))
    return s


def sprite_buraco():
    s = nova_superficie(TILE, TILE)
    pygame.draw.ellipse(s, (96, 66, 40), (0, 1, 16, 14))
    pygame.draw.ellipse(s, (54, 36, 24), (1, 2, 14, 12))
    pygame.draw.ellipse(s, (14, 10, 12), (2, 3, 12, 10))
    pygame.draw.ellipse(s, (0, 0, 0), (4, 5, 8, 6))
    pixels(s, [(3, 3), (12, 4), (2, 10), (13, 11)], (130, 92, 58))
    return s


def sprite_escada():
    s = nova_superficie(TILE, TILE + 2)
    madeira, esc = (176, 128, 74), (120, 82, 44)
    retangulo(s, 3, 0, 2, TILE + 2, madeira)
    retangulo(s, 11, 0, 2, TILE + 2, madeira)
    retangulo(s, 4, 0, 1, TILE + 2, esc)
    retangulo(s, 12, 0, 1, TILE + 2, esc)
    for y in range(2, TILE + 1, 4):
        retangulo(s, 5, y, 6, 1, (196, 150, 92))
        retangulo(s, 5, y + 1, 6, 1, esc)
    return contornar(s)


def rachaduras_chao(estagio):
    """Rachaduras por cima do chão sendo cavado (estagio 1..3): terra revirada + fendas a partir do centro."""
    s = nova_superficie(TILE, TILE)
    rng = random.Random(11)
    # terra revirada no meio, cresce com o estágio
    r = 2 + estagio * 2
    pygame.draw.ellipse(s, (70, 48, 30, 90 + estagio * 40), (8 - r, 8 - r, r * 2, r * 2))
    pygame.draw.ellipse(s, (30, 20, 14, 70 + estagio * 50), (8 - r + 2, 8 - r + 2, r * 2 - 4, r * 2 - 4))
    # fendas retas saindo do centro (sem "patinhas")
    for n in range(3 + estagio * 2):
        ang = n * 2.399 + rng.random() * 0.5
        comp = 3 + estagio * 1.6 + rng.random() * 2
        x, y = 8.0, 8.0
        for _ in range(int(comp)):
            x += math.cos(ang); y += math.sin(ang)
            if 0 <= x < 16 and 0 <= y < 16:
                s.set_at((int(x), int(y)), (18, 12, 10, 235))
    # bordinha de alvo para mostrar o bloco
    pygame.draw.rect(s, (255, 255, 255, 70), (0, 0, TILE, TILE), 1)
    return s


def forno_apagado(img):
    s = img.copy()
    w, h = s.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = s.get_at((x, y))
            if a and r > 180 and b < 140 and r - b > 80:
                s.set_at((x, y), (44, 36, 36, a))
    return s


# ===============================================================
# Criaturas (olhando para a direita, 2 quadros)
# ===============================================================
def criatura_vaca(q):
    s = nova_superficie(TILE, TILE)
    _pernas(s, (3, 5, 9, 11), 11, 4, (60, 50, 46), q)
    bolha(s, 7, 8.5, 6, 3.5, ((190, 186, 180), (240, 236, 230), (255, 255, 255)))
    pixels(s, [(4, 7), (5, 7), (5, 8), (8, 9), (9, 9), (9, 8), (6, 10)], (40, 34, 34))
    bolha(s, 13, 6.5, 2.6, 2.4, ((50, 44, 40), (80, 70, 64), (110, 98, 90)))
    retangulo(s, 14, 7, 2, 2, (230, 170, 170))                     # focinho
    pixels(s, [(12, 3), (14, 3)], (236, 230, 210))                 # chifres
    s.set_at((13, 5), OLHO)
    linha(s, (60, 50, 46), (1, 6), (0, 9 - q))                     # rabo
    return contornar(s)


def criatura_porco(q):
    s = nova_superficie(TILE, TILE)
    rosa = ((200, 120, 130), (240, 160, 168), (255, 196, 200))
    _pernas(s, (4, 6, 9, 11), 12, 2, (200, 120, 130), q)
    bolha(s, 7.5, 9.5, 5.5, 3.2, rosa)
    bolha(s, 12.5, 8.5, 2.6, 2.4, rosa)
    retangulo(s, 14, 8, 2, 2, (220, 120, 130))                     # focinho
    s.set_at((15, 9), (150, 70, 80))
    s.set_at((12, 7), OLHO)
    pixels(s, [(11, 5), (12, 5)], (220, 130, 140))
    pixels(s, [(2, 8), (1, 7)], (220, 130, 140))
    return contornar(s)


def criatura_ovelha(q):
    s = nova_superficie(TILE, TILE)
    _pernas(s, (4, 6, 9, 11), 11, 4, (70, 66, 64), q)
    rng = random.Random(9)
    bolha(s, 7.5, 8.5, 6, 4, ((206, 204, 200), (236, 234, 230), (252, 252, 250)), rng, 0.3)
    bolha(s, 13, 7.5, 2.4, 2.2, ((60, 56, 54), (90, 86, 82), (120, 116, 110)))
    s.set_at((14, 7), (240, 240, 240))
    s.set_at((14, 6), OLHO)
    return contornar(s)


def _humanoide():
    from arte_estruturas import humanoide
    return humanoide


def criatura_zumbi(q):
    def bracos(s, q):
        retangulo(s, 10, 7 + q, 5, 2, (96, 150, 86))               # braços esticados
        s.set_at((14, 8 + q), (70, 120, 64))
    return _humanoide()(q, (96, 150, 86), (60, 116, 170), (70, 56, 140), cabelo=(50, 80, 46),
                        extra=bracos, olho=(20, 10, 10))


def criatura_esqueleto_arq(q):
    def arco(s, q):
        for y in (7, 9):
            linha(s, (150, 146, 136), (7, y), (10, y))
        pygame.draw.arc(s, (140, 96, 56), (10, 3, 6, 10), -1.4, 1.4, 1)
        linha(s, (230, 230, 230), (13, 4), (13, 12))
    return _humanoide()(q, (230, 226, 210), (210, 206, 190), (190, 186, 172), extra=arco,
                        olho=(30, 10, 10))


def criatura_explosivo(q):
    s = nova_superficie(TILE, TILE)
    verde = ((50, 120, 50), (80, 170, 70), (130, 210, 110))
    rng = random.Random(4)
    retangulo(s, 5, 1, 7, 11, verde[1])
    _ruido_pixels(s, (5, 1, 7, 11), [verde[0], verde[2]], 0.3, rng)
    pixels(s, [(6, 3), (7, 3), (9, 3), (10, 3), (8, 5), (7, 6), (8, 6), (9, 6), (7, 7), (9, 7)], (20, 26, 20))
    for n, x in enumerate((5, 7, 9, 11)):
        lev = (n + q) % 2
        retangulo(s, x, 12, 2 if x < 11 else 1, 3 - lev, verde[0])
    return contornar(s)


FABRICA = {"vaca": criatura_vaca, "porco": criatura_porco, "ovelha": criatura_ovelha,
           "zumbi": criatura_zumbi, "esqueleto_arq": criatura_esqueleto_arq, "explosivo": criatura_explosivo}


# ===============================================================
# Ícones
# ===============================================================
def icone_bloco(sprite):
    s = nova_superficie(TILE, TILE)
    mini = pygame.transform.scale(sprite, (12, 15))
    s.blit(mini, (2, 0))
    return contornar(s)


def icone_pa(cor):
    s = nova_superficie(TILE, TILE)
    for i in range(9):
        s.set_at((3 + i, 13 - i), CABO)
        s.set_at((4 + i, 13 - i), CABO_ESC)
    for (x, y) in ((11, 2), (12, 2), (13, 2), (10, 3), (11, 3), (12, 3), (13, 3), (14, 3), (10, 4), (11, 4),
                   (12, 4), (13, 4), (11, 5), (12, 5), (13, 1)):
        s.set_at((x, y), cor)
    pixels(s, [(12, 2), (13, 3)], escurecer(cor, 1.2))
    pixels(s, [(10, 4), (11, 5)], escurecer(cor, 0.75))
    return contornar(s)


def icone_graveto():
    s = nova_superficie(TILE, TILE)
    for i in range(10):
        s.set_at((3 + i, 13 - i), (150, 104, 60))
        s.set_at((4 + i, 13 - i), (110, 74, 40))
    return contornar(s)


def _gema(cor, claro, formato="losango"):
    s = nova_superficie(TILE, TILE)
    if formato == "losango":
        pygame.draw.polygon(s, cor, [(8, 2), (13, 7), (8, 14), (3, 7)])
        pygame.draw.polygon(s, claro, [(8, 3), (11, 7), (8, 7)])
    else:  # pó
        for (x, y) in ((5, 9), (7, 7), (9, 10), (10, 6), (6, 12), (11, 11), (8, 4)):
            retangulo(s, x, y, 2, 2, cor)
            s.set_at((x, y), claro)
    return contornar(s)


def icone_barra(cor, claro):
    s = nova_superficie(TILE, TILE)
    pygame.draw.polygon(s, cor, [(2, 11), (5, 6), (14, 6), (11, 11)])
    pygame.draw.polygon(s, escurecer(cor, 0.75), [(2, 11), (11, 11), (11, 13), (2, 13)])
    linha(s, claro, (6, 7), (12, 7))
    return contornar(s)


def icone_minerio(cor):
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 6, 5, ((100, 100, 112), (130, 130, 142), (160, 160, 172)))
    for (x, y) in ((5, 7), (9, 6), (7, 10), (11, 10)):
        retangulo(s, x, y, 2, 2, cor)
    return contornar(s)


def icone_la():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 6, 5, ((206, 204, 200), (236, 234, 230), (255, 255, 255)), random.Random(3), 0.3)
    return contornar(s)


def icone_carne_podre():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 5.5, 4, ((90, 110, 60), (130, 140, 80), (160, 170, 100)))
    pixels(s, [(6, 8), (9, 10), (10, 7)], (70, 50, 40))
    return contornar(s)


def icone_osso():
    s = nova_superficie(TILE, TILE)
    linha(s, (236, 232, 216), (4, 12), (12, 4))
    linha(s, (210, 206, 190), (5, 12), (12, 5))
    for (x, y) in ((3, 11), (4, 13), (11, 3), (13, 4)):
        retangulo(s, x, y, 2, 2, (236, 232, 216))
    return contornar(s)


def icone_polvora():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 11, 5.5, 3.2, ((60, 60, 64), (96, 96, 100), (130, 130, 136)))
    pixels(s, [(6, 7), (9, 6), (10, 8)], (110, 110, 116))
    return contornar(s)


def icone_escada():
    s = pygame.transform.scale(sprite_escada(), (12, 15))
    out = nova_superficie(TILE, TILE)
    out.blit(s, (2, 0))
    return out


COR_DIAMANTE = (110, 236, 226)


def icones(blocos_sprites):
    ic = {
        "tabuas": icone_bloco(blocos_sprites["bloco_tabuas"][0]),
        "terra": icone_bloco(blocos_sprites["bloco_terra"][0]),
        "areia": icone_bloco(blocos_sprites["bloco_areia"][0]),
        "vidro": icone_bloco(blocos_sprites["bloco_vidro"][0]),
        "pedra_lisa": icone_bloco(blocos_sprites["bloco_pedra_lisa"][0]),
        "lampada": icone_bloco(blocos_sprites["lampada"][0]),
        "graveto": icone_graveto(),
        "minerio_ouro": icone_minerio((246, 206, 60)),
        "ouro": icone_barra((240, 196, 50), (255, 244, 160)),
        "cristal": _gema((220, 40, 70), (255, 150, 160), "po"),
        "diamante": _gema(COR_DIAMANTE, (230, 255, 252)),
        "escada": icone_escada(),
        "la": icone_la(),
        "carne_podre": icone_carne_podre(),
        "osso": icone_osso(),
        "polvora": icone_polvora(),
        "machado_diamante": icone_machado(COR_DIAMANTE),
        "picareta_diamante": icone_picareta(COR_DIAMANTE),
        "espada_diamante": icone_espada(COR_DIAMANTE),
        "capacete_diamante": icone_capacete(COR_DIAMANTE),
        "armadura_diamante": icone_roupa(COR_DIAMANTE),
    }
    for tier, cor in (("madeira", (176, 124, 72)), ("pedra", (140, 142, 156)), ("ferro", (214, 220, 232)),
                      ("diamante", COR_DIAMANTE)):
        ic[f"pa_{tier}"] = icone_pa(cor)
    return ic


def sprites_blocos():
    d = {
        "bloco_pedra": [bloco_pedra(i) for i in range(3)],
        "bloco_pedregulho": [bloco_pedregulho()],
        "bloco_pedra_lisa": [bloco_pedra_lisa()],
        "bloco_terra": [bloco_terra()],
        "bloco_areia": [bloco_areia()],
        "bloco_tora": [bloco_tora()],
        "bloco_tabuas": [bloco_tabuas()],
        "bloco_vidro": [bloco_vidro()],
        "lampada": [bloco_lampada()],
        "buraco": [sprite_buraco()],
        "escada": [sprite_escada()],
    }
    for n, (nome, (c, cl, br)) in enumerate(MINERIOS_CORES.items()):
        d[nome] = [bloco_minerio(n * 10 + i, (c, cl), br) for i in range(3)]
    return d


_CACHE = {}


def icones_para_criar():
    """Usado por sprites.criar_icones (antes do assert de ícones)."""
    if "sprites" not in _CACHE:
        _CACHE["sprites"] = sprites_blocos()
    return icones(_CACHE["sprites"])


def instalar(sp):
    """Põe tudo num objeto Sprites já criado."""
    if getattr(sp, "_blocos_ok", False):
        return
    sp._blocos_ok = True
    if "sprites" not in _CACHE:
        _CACHE["sprites"] = sprites_blocos()
    sp.objetos.update(_CACHE["sprites"])
    sp.chao[CAVERNA] = [tile_caverna(i) for i in range(4)]
    sp.chao[LAVA] = [tile_lava(i) for i in range(4)]
    sp.forno_apagado = forno_apagado(sp.forno[0])
    sp.rachaduras_chao = [None] + [rachaduras_chao(e) for e in (1, 2, 3)]
    for tipo, fabrica in FABRICA.items():
        dir_ = [fabrica(0), fabrica(1)]
        mascara = pygame.mask.from_surface(dir_[0])
        branco = mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        sp.criaturas[tipo] = {"direita": dir_,
                              "esquerda": [pygame.transform.flip(f, True, False) for f in dir_],
                              "branco": branco}
    for nome, img in sp.icones.items():
        if nome not in sp.itens_chao:
            sp.itens_chao[nome] = pygame.transform.scale(img, (10, 10))
