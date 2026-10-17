# -*- coding: utf-8 -*-
"""
arte_estruturas.py - Pixel art (feita por código) das ESTRUTURAS: pisos,
paredes novas (arenito, masmorra, castelo, musgo), baús, portas, poço,
plantações, tochas, trono, escadas, NPCs, chefes e ícones dos itens novos.

Nada aqui altera sprites.py: as imagens são ACRESCENTADAS no objeto
Sprites com instalar(sprites). Os ícones dos itens novos entram por um
"embrulho" em sprites.criar_icones (feito ao importar este arquivo).
"""
import random
import pygame

import sprites as _sp
from sprites import (nova_superficie, contornar, bolha, pixels, retangulo, linha, escurecer,
                     tile_textura, icone_espada, CONTORNO)
from config import TILE
from dados import ITENS
import dados_estruturas as DE

OLHO = (24, 20, 30)


# ===============================================================
# Chão das masmorras
# ===============================================================
def tile_masmorra(semente):
    s, rng = tile_textura((58, 54, 66), (46, 42, 54), (74, 70, 84), semente, 0.12, 0.06)
    # lajes 8x8
    for y in (0, 8):
        retangulo(s, 0, y, 16, 1, (38, 34, 44))
    for y, x in ((0, 4 + semente % 3), (8, 11 - semente % 3)):
        retangulo(s, x, y, 1, 8, (38, 34, 44))
    if semente % 2:
        x, y = rng.randrange(2, 12), rng.randrange(2, 12)
        pixels(s, [(x, y), (x + 1, y + 1), (x + 2, y + 1)], (34, 30, 40))
    return s


def tile_vazio(semente):
    s, _ = tile_textura((10, 9, 14), (6, 5, 9), (16, 14, 20), semente, 0.08, 0.04)
    return s


# ===============================================================
# Pisos das construções (camada de pisos dos chunks)
# ===============================================================
def piso_caminho(semente, base, escuro, claro):
    rng = random.Random(semente)
    s, _ = tile_textura(base, escuro, claro, semente, 0.14, 0.08)
    for _ in range(4):   # pedrinhas
        x, y = rng.randrange(1, 14), rng.randrange(1, 14)
        retangulo(s, x, y, 2, 2, claro)
        s.set_at((x + 1, y + 1), escuro)
    return s


def piso_lajes(base, junta, claro, rachado=False, semente=0):
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE)
    s.fill(base)
    for y in (0, 8):
        retangulo(s, 0, y, 16, 1, junta)
        corte = 4 if y == 0 else 12
        retangulo(s, corte, y, 1, 8, junta)
        s.set_at((corte + 2, y + 2), claro)
        s.set_at(((corte + 9) % 16, y + 5), claro)
    if rachado:
        for _ in range(3):
            x, y = rng.randrange(1, 14), rng.randrange(1, 14)
            pixels(s, [(x, y), (x + 1, y), (x + 1, y + 1)], escurecer(junta, 0.8))
        for _ in range(4):   # musgo
            x, y = rng.randrange(0, 15), rng.randrange(0, 15)
            pixels(s, [(x, y), (x + 1, y)], (82, 120, 64))
    return s


def piso_tapete():
    s = nova_superficie(TILE, TILE)
    s.fill((160, 36, 44))
    retangulo(s, 0, 0, 2, 16, (220, 180, 70))
    retangulo(s, 14, 0, 2, 16, (220, 180, 70))
    retangulo(s, 2, 0, 1, 16, (110, 24, 32))
    retangulo(s, 13, 0, 1, 16, (110, 24, 32))
    for y in (3, 11):
        pixels(s, [(8, y - 1), (7, y), (9, y), (8, y + 1)], (230, 190, 80))
    return s


def piso_terra_arada():
    s = nova_superficie(TILE, TILE)
    s.fill((112, 78, 50))
    for y in range(1, 16, 4):
        retangulo(s, 0, y, 16, 2, (90, 60, 38))
        retangulo(s, 0, y + 2, 16, 1, (136, 98, 64))
    return s


# ===============================================================
# Paredes novas (mesmo formato 16x20 da parede de pedra)
# ===============================================================
def parede_blocos(topo, topo_esc, frente, junta, brilho, alt_bloco=4, musgo=False, semente=0):
    rng = random.Random(semente)
    s = nova_superficie(TILE, 20)
    retangulo(s, 0, 0, 16, 5, topo)
    retangulo(s, 0, 4, 16, 1, topo_esc)
    retangulo(s, 0, 5, 16, 15, frente)
    for n, y in enumerate(range(5, 20, alt_bloco)):
        retangulo(s, 0, y, 16, 1, junta)
        inicio = 0 if n % 2 == 0 else 4
        for x in range(inicio, 16, 8):
            retangulo(s, x, y, 1, alt_bloco, junta)
        for x in range(inicio + 2, 16, 8):
            s.set_at((x, y + 1), brilho)
    retangulo(s, 0, 18, 16, 2, escurecer(frente, 0.78))
    if musgo:
        for _ in range(9):
            x, y = rng.randrange(0, 16), rng.randrange(0, 19)
            pixels(s, [(x, y)], (78, 128, 62))
            if x < 15:
                s.set_at((x + 1, y), (98, 150, 74))
        retangulo(s, 0, 0, 16, 2, (88, 138, 68))
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 20), 1)
    return s


def parede_madeira_escura():
    s = _sp.sprite_parede_madeira()
    s.fill((150, 140, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
    retangulo(s, 1, 1, 14, 3, (236, 242, 252))           # neve no telhado
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 20), 1)
    return s


# ===============================================================
# Objetos
# ===============================================================
def sprite_bau(aberto, ouro=False):
    s = nova_superficie(TILE, TILE)
    madeira, esc, claro = (150, 96, 50), (106, 64, 34), (186, 128, 72)
    metal = (232, 196, 80) if ouro else (176, 178, 190)
    if aberto:
        retangulo(s, 1, 3, 14, 4, esc)                     # tampa levantada
        retangulo(s, 2, 4, 12, 2, (70, 40, 24))
        retangulo(s, 1, 7, 14, 8, madeira)
        retangulo(s, 2, 7, 12, 2, (40, 26, 18))            # vazio por dentro
    else:
        retangulo(s, 1, 5, 14, 10, madeira)
        retangulo(s, 1, 5, 14, 4, claro)
        retangulo(s, 1, 9, 14, 1, esc)
    retangulo(s, 1, 12, 14, 1, esc)
    for x in (3, 12):
        retangulo(s, x, 5 if not aberto else 7, 1, 10 if not aberto else 8, metal)
    if not aberto:
        retangulo(s, 7, 8, 2, 3, metal)
        s.set_at((7, 10), OLHO)
    return contornar(s)


def sprite_porta():
    s = nova_superficie(TILE, 20)
    retangulo(s, 0, 0, 16, 20, (92, 60, 34))              # batente
    retangulo(s, 2, 2, 12, 18, (156, 104, 58))
    for x in (5, 9, 13):
        retangulo(s, x, 2, 1, 18, (124, 80, 44))
    retangulo(s, 2, 6, 12, 1, (110, 72, 40))
    retangulo(s, 2, 14, 12, 1, (110, 72, 40))
    pixels(s, [(11, 11), (11, 12)], (232, 196, 80))       # maçaneta
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 20), 1)
    return s


def sprite_poco():
    s = nova_superficie(TILE, 22)
    retangulo(s, 2, 1, 12, 2, (150, 96, 50))               # telhadinho
    retangulo(s, 3, 3, 1, 9, (110, 72, 40))
    retangulo(s, 12, 3, 1, 9, (110, 72, 40))
    linha(s, (200, 190, 170), (8, 3), (8, 9))              # corda
    retangulo(s, 7, 9, 3, 2, (120, 80, 44))                # balde
    bolha(s, 8, 16, 7, 5, ((96, 98, 112), (132, 134, 148), (176, 178, 190)))
    bolha(s, 8, 15, 4.5, 2.5, ((24, 40, 80), (40, 70, 130), (60, 100, 170)))
    return contornar(s)


def sprite_plantacao(var):
    s = nova_superficie(TILE, TILE)
    rng = random.Random(40 + var)
    if var == 0:   # trigo
        for x in range(2, 15, 3):
            alt = rng.randrange(7, 11)
            linha(s, (150, 160, 60), (x, 15), (x, 15 - alt))
            retangulo(s, x - 1, 15 - alt - 1, 2, 4, (226, 196, 90))
            s.set_at((x, 15 - alt - 2), (246, 220, 120))
    else:          # abóboras
        for (x, y) in ((4, 11), (11, 12)):
            linha(s, (60, 130, 50), (x, y - 4), (x + 2, y - 6))
            bolha(s, x, y, 3.2, 2.6, ((190, 90, 20), (230, 130, 40), (250, 180, 80)))
        pixels(s, [(7, 6), (8, 5), (9, 6)], (70, 150, 60))
    return s


def sprite_cerca():
    s = nova_superficie(TILE, TILE)
    for x in (2, 7, 12):
        retangulo(s, x, 3, 2, 12, (160, 112, 64))
        s.set_at((x, 3), (196, 146, 92))
    retangulo(s, 0, 6, 16, 2, (140, 94, 52))
    retangulo(s, 0, 11, 16, 2, (140, 94, 52))
    return contornar(s)


def sprite_tocha(quadro=0):
    s = nova_superficie(TILE, 18)
    retangulo(s, 7, 7, 2, 10, (120, 78, 44))
    retangulo(s, 6, 6, 4, 2, (90, 90, 100))
    alt = 4 + quadro
    bolha(s, 8, 6 - alt / 2 + 1, 2.4, alt / 2 + 0.8, ((220, 70, 30), (250, 150, 40), (255, 236, 140)))
    s.set_at((8, 4), (255, 250, 210))
    return contornar(s)


def sprite_cama():
    s = nova_superficie(TILE, TILE)
    retangulo(s, 1, 2, 14, 13, (120, 78, 44))
    retangulo(s, 2, 3, 12, 4, (236, 232, 222))             # travesseiro
    retangulo(s, 2, 7, 12, 7, (70, 110, 190))              # cobertor
    retangulo(s, 2, 7, 12, 1, (110, 150, 220))
    return contornar(s)


def sprite_trono():
    s = nova_superficie(TILE, 24)
    ouro, ouro_esc = (232, 196, 80), (180, 140, 50)
    retangulo(s, 3, 1, 10, 14, ouro)                       # encosto
    retangulo(s, 5, 3, 6, 11, (150, 30, 44))
    pixels(s, [(3, 0), (8, 0), (12, 0)], ouro)
    retangulo(s, 1, 14, 14, 6, ouro_esc)                   # assento
    retangulo(s, 3, 14, 10, 3, (170, 40, 54))
    retangulo(s, 1, 20, 3, 3, ouro_esc)
    retangulo(s, 12, 20, 3, 3, ouro_esc)
    return contornar(s)


def sprite_estandarte(cor=(160, 36, 44)):
    s = nova_superficie(TILE, 24)
    retangulo(s, 7, 0, 2, 24, (110, 72, 40))
    retangulo(s, 3, 1, 10, 2, (90, 60, 34))
    pygame.draw.polygon(s, cor, [(4, 3), (12, 3), (12, 15), (8, 12), (4, 15)])
    pixels(s, [(8, 6), (7, 7), (8, 7), (9, 7), (8, 8)], (232, 196, 80))
    return contornar(s)


def sprite_escada(descer):
    s = nova_superficie(TILE, TILE)
    if descer:
        s.fill((20, 18, 26))
        for n in range(4):
            y = 2 + n * 3
            cor = escurecer((150, 146, 156), 1.0 - n * 0.22)
            retangulo(s, 2 + n, y, 12 - 2 * n, 2, cor)
        pygame.draw.rect(s, (110, 108, 120), (0, 0, 16, 16), 1)
    else:
        s.fill((40, 36, 46))
        for n in range(4):
            y = 12 - n * 3
            cor = escurecer((170, 166, 176), 0.6 + n * 0.15)
            retangulo(s, 1, y, 14, 3, cor)
            retangulo(s, 1, y + 2, 14, 1, escurecer(cor, 0.7))
        retangulo(s, 4, 0, 8, 2, (255, 240, 180))          # luz lá de cima
    return s


def sprite_ossos():
    s = nova_superficie(TILE, TILE)
    osso = (226, 222, 206)
    linha(s, osso, (3, 12), (10, 9))
    linha(s, osso, (5, 8), (12, 13))
    bolha(s, 11, 6, 3, 2.6, ((170, 166, 150), osso, (250, 248, 240)))
    pixels(s, [(10, 6), (12, 6)], OLHO)
    return contornar(s)


# ===============================================================
# NPCs (olhando para a direita; 2 quadros)
# ===============================================================
def humanoide(q, pele, roupa, calca, cabelo=None, capacete=None, extra=None, olho=OLHO, cinto=None):
    s = nova_superficie(TILE, TILE)
    roupa_esc = escurecer(roupa, 0.75)
    retangulo(s, 6, 2, 5, 5, pele)                     # cabeça
    if cabelo:
        retangulo(s, 6, 1, 5, 2, cabelo)
        retangulo(s, 6, 1, 2, 5, cabelo)
    if capacete:
        retangulo(s, 5, 1, 7, 3, capacete)
        retangulo(s, 5, 3, 2, 3, capacete)
        s.set_at((11, 3), escurecer(capacete, 0.7))
    s.set_at((9, 4), olho)
    retangulo(s, 6, 7, 5, 4, roupa)
    retangulo(s, 6, 10, 5, 1, roupa_esc)
    if cinto:
        retangulo(s, 6, 9, 5, 1, cinto)
    retangulo(s, 6, 11, 5, 1, calca)
    bota = escurecer(calca, 0.6)
    if q == 0:
        retangulo(s, 7, 12, 3, 2, calca)
        retangulo(s, 7, 14, 3, 1, bota)
        retangulo(s, 8, 8, 1, 3, pele)
    else:
        retangulo(s, 9, 12, 2, 2, calca)
        retangulo(s, 9, 14, 2, 1, bota)
        retangulo(s, 6, 12, 2, 1, calca)
        retangulo(s, 6, 13, 2, 1, bota)
        retangulo(s, 9, 8, 1, 3, pele)
    if extra:
        extra(s, q)
    return contornar(s)


def _lanca(s, q):
    linha(s, (130, 90, 50), (12, 14), (12, 1 + q))
    pixels(s, [(12, 0 + q), (11, 1 + q), (13, 1 + q)], (210, 214, 226))


def _espada(s, q):
    linha(s, (210, 214, 226), (11, 9 - q), (14, 4 - q))
    s.set_at((10, 10 - q), (232, 196, 80))


def _cajado_coroa(s, q):
    pixels(s, [(6, 0), (8, 0), (10, 0), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1)], (232, 196, 80))
    s.set_at((8, 0), (220, 40, 60))
    linha(s, (90, 60, 120), (13, 14), (13, 2 + q))
    bolha(s, 13, 2 + q, 1.6, 1.6, ((120, 40, 160), (170, 80, 220), (230, 180, 255)))


def _pluma(s, q):
    pixels(s, [(7, 0), (8, 0), (9, 0), (6, 1)], (200, 40, 40))
    _espada(s, q)


def criatura_aldeao(q):
    return humanoide(q, (226, 178, 136), (120, 150, 70), (96, 72, 52), cabelo=(70, 46, 28),
                     cinto=(150, 110, 60))


def criatura_guarda(q):
    return humanoide(q, (236, 190, 150), (50, 80, 170), (84, 84, 96), capacete=(176, 180, 194),
                     extra=_lanca, cinto=(232, 196, 80))


def criatura_cavaleiro(q):
    return humanoide(q, (150, 150, 162), (110, 112, 126), (80, 80, 92), capacete=(120, 122, 136),
                     extra=_pluma, olho=(250, 60, 60))


def criatura_esqueleto(q):
    def costelas(s, q):
        for y in (7, 9):
            linha(s, (150, 146, 136), (7, y), (10, y))
        _espada(s, q)
    return humanoide(q, (230, 226, 210), (210, 206, 190), (190, 186, 172), extra=costelas,
                     olho=(30, 10, 10))


def criatura_senhor_castelo(q):
    def detalhes(s, q):
        pixels(s, [(7, 0), (8, 0), (9, 0)], (232, 196, 80))
        _espada(s, q)
    return humanoide(q, (60, 58, 70), (36, 34, 44), (30, 28, 36), capacete=(50, 48, 60),
                     extra=detalhes, olho=(255, 200, 60), cinto=(232, 196, 80))


def criatura_rei_esqueleto(q):
    def detalhes(s, q):
        retangulo(s, 5, 7, 1, 7, (110, 30, 140))          # capa
        _cajado_coroa(s, q)
    return humanoide(q, (236, 232, 216), (110, 40, 140), (90, 30, 110), extra=detalhes,
                     olho=(255, 60, 200), cinto=(232, 196, 80))


FABRICA_NPCS = {
    "aldeao": criatura_aldeao, "guarda": criatura_guarda, "cavaleiro": criatura_cavaleiro,
    "esqueleto": criatura_esqueleto, "senhor_castelo": criatura_senhor_castelo,
    "rei_esqueleto": criatura_rei_esqueleto,
}


# ===============================================================
# Ícones dos itens novos
# ===============================================================
def icone_moeda():
    s = nova_superficie(TILE, TILE)
    for (x, y) in ((9, 10), (6, 8)):
        bolha(s, x, y, 4.5, 4.5, ((180, 140, 50), (232, 196, 80), (255, 240, 160)))
        pixels(s, [(x - 1, y - 2), (x - 1, y - 1), (x - 1, y), (x - 1, y + 1)], (170, 130, 40))
    return contornar(s)


def icone_trigo():
    s = nova_superficie(TILE, TILE)
    for dx in (-3, 0, 3):
        linha(s, (170, 160, 70), (8, 15), (8 + dx, 5))
        retangulo(s, 7 + dx, 2, 2, 5, (226, 196, 90))
        s.set_at((7 + dx, 2), (250, 226, 130))
    return contornar(s)


def icone_pao():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 6.5, 4.5, ((160, 96, 40), (204, 140, 66), (236, 186, 110)))
    for x in (5, 8, 11):
        linha(s, (240, 210, 150), (x, 7), (x + 1, 10))
    return contornar(s)


def icone_pocao():
    s = nova_superficie(TILE, TILE)
    retangulo(s, 6, 1, 4, 2, (150, 100, 60))               # rolha
    retangulo(s, 7, 3, 2, 3, (200, 220, 240))
    bolha(s, 8, 10.5, 5, 4.8, ((150, 20, 40), (220, 40, 60), (255, 120, 140)))
    pixels(s, [(6, 8), (6, 9)], (255, 220, 230))
    return contornar(s)


def icones_novos():
    return {
        "moeda_ouro": icone_moeda(), "trigo": icone_trigo(), "pao": icone_pao(),
        "pocao_vida": icone_pocao(), "tocha": pygame.transform.scale(sprite_tocha(1), (14, 16)),
        "espada_rubi": icone_espada((230, 50, 70)),
    }


# --- embrulho em sprites.criar_icones: os itens novos ganham ícone ---
if not getattr(_sp.criar_icones, "_com_estruturas", False):
    _criar_icones_original = _sp.criar_icones

    def _criar_icones_com_estruturas():
        meus = {k: ITENS.pop(k) for k in list(DE.REGISTRADOS) if k in ITENS}
        try:
            ic = _criar_icones_original()
        finally:
            ITENS.update(meus)
        for nome, img in icones_novos().items():
            ic.setdefault(nome, img)
        return ic

    _criar_icones_com_estruturas._com_estruturas = True
    _sp.criar_icones = _criar_icones_com_estruturas


# ===============================================================
# Instala tudo num objeto Sprites já criado
# ===============================================================
def instalar(sp):
    if getattr(sp, "_estruturas_ok", False):
        return
    sp._estruturas_ok = True
    sp.chao[DE.PISO_MASMORRA] = [tile_masmorra(i) for i in range(4)]
    sp.chao[DE.VAZIO] = [tile_vazio(90 + i) for i in range(4)]
    ob = sp.objetos
    # paredes: as variantes novas entram depois da original (variante 0)
    pedra = ob["parede_pedra"]
    while len(pedra) < 5:
        pedra.append(pedra[0])
    pedra[1] = parede_blocos((236, 214, 160), (206, 182, 128), (214, 186, 124), (168, 140, 88), (240, 220, 170))
    pedra[2] = parede_blocos((92, 88, 104), (70, 66, 82), (66, 62, 78), (40, 36, 50), (96, 92, 110))
    pedra[3] = parede_blocos((150, 156, 176), (112, 118, 140), (92, 98, 120), (60, 64, 84),
                             (130, 136, 158), alt_bloco=5)
    pedra[4] = parede_blocos((182, 184, 196), (150, 152, 166), (124, 128, 136), (90, 94, 102),
                             (150, 156, 160), musgo=True, semente=5)
    madeira = ob["parede_madeira"]
    if len(madeira) < 2:
        madeira.append(parede_madeira_escura())
    ob["bau_tesouro"] = [sprite_bau(False), sprite_bau(False, ouro=True)]
    ob["bau_tesouro_aberto"] = [sprite_bau(True), sprite_bau(True, ouro=True)]
    ob["porta"] = [sprite_porta()]
    ob["poco"] = [sprite_poco()]
    ob["plantacao_trigo"] = [sprite_plantacao(0)]
    ob["plantacao_abobora"] = [sprite_plantacao(1)]
    ob["cerca"] = [sprite_cerca()]
    if "tocha" not in ob:                      # se sprites.py já tem tocha, usa a de lá
        ob["tocha"] = [sprite_tocha(0)]
        sp.tocha_quadros = [sprite_tocha(q) for q in range(3)]
    ob.setdefault("cama", [sprite_cama()])
    ob["trono"] = [sprite_trono()]
    ob["estandarte"] = [sprite_estandarte(), sprite_estandarte((40, 70, 170))]
    ob["escada_descer"] = [sprite_escada(True)]
    ob["escada_subir"] = [sprite_escada(False)]
    ob["ossos"] = [sprite_ossos()]
    ob["caminho"] = [piso_caminho(1, (150, 140, 124), (126, 116, 102), (178, 168, 150)),
                     piso_caminho(2, (214, 186, 130), (190, 160, 108), (234, 210, 160)),
                     piso_caminho(3, (176, 180, 190), (146, 150, 162), (230, 236, 246))]
    ob["piso_pedra"] = [piso_lajes((178, 170, 152), (138, 130, 114), (200, 194, 178)),
                        piso_lajes((96, 94, 108), (66, 64, 78), (120, 118, 132)),
                        piso_lajes((140, 142, 146), (100, 104, 108), (166, 168, 170), rachado=True, semente=3)]
    ob["piso_arenito"] = [piso_lajes((222, 196, 138), (182, 154, 100), (240, 220, 170))]
    ob["tapete"] = [piso_tapete()]
    ob["terra_arada"] = [piso_terra_arada()]
    # NPCs e chefes
    for tipo, fabrica in FABRICA_NPCS.items():
        dir_ = [fabrica(0), fabrica(1)]
        mascara = pygame.mask.from_surface(dir_[0])
        branco = mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        sp.criaturas[tipo] = {"direita": dir_,
                              "esquerda": [pygame.transform.flip(f, True, False) for f in dir_],
                              "branco": branco}
