# -*- coding: utf-8 -*-
"""
sprites.py - Toda a pixel art do jogo é DESENHADA POR CÓDIGO aqui.
Nenhuma imagem é baixada: cada sprite é pintado pixel a pixel (16x16)
e depois a tela é ampliada sem suavização, deixando os pixels nítidos.
"""
import math
import random
import pygame

from config import (TILE, AGUA_FUNDA, AGUA_RASA, LAMA, AREIA, GRAMA,
                    GRAMA_FLORESTA, GRAMA_PANTANO, NEVE, ROCHA)
from dados import ITENS
import personagem
from texturas import Texturas

CONTORNO = (28, 24, 36, 255)


# ===============================================================
# Funções auxiliares de pintura
# ===============================================================
def nova_superficie(largura, altura):
    return pygame.Surface((largura, altura), pygame.SRCALPHA)


def contornar(sup, cor=CONTORNO):
    """Contorno de 1 pixel ao redor de tudo que não é transparente."""
    larg, alt = sup.get_size()
    cheios = {(x, y) for y in range(alt) for x in range(larg) if sup.get_at((x, y)).a > 0}
    for (x, y) in list(cheios):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < larg and 0 <= ny < alt and (nx, ny) not in cheios:
                sup.set_at((nx, ny), cor)
    return sup


def bolha(sup, cx, cy, rx, ry, cores, rng=None, ruido=0.15):
    """Elipse com sombreamento simples (luz vindo de cima/esquerda). cores = (escura, média, clara)."""
    escura, media, clara = cores
    larg, alt = sup.get_size()
    for y in range(alt):
        for x in range(larg):
            nx = (x + 0.5 - cx) / rx
            ny = (y + 0.5 - cy) / ry
            if nx * nx + ny * ny <= 1.0:
                luz = (nx + ny) * 0.5
                if rng is not None:
                    luz += rng.uniform(-ruido, ruido)
                cor = clara if luz < -0.35 else (escura if luz > 0.25 else media)
                sup.set_at((x, y), cor)


def pixels(sup, lista, cor):
    for (x, y) in lista:
        sup.set_at((x, y), cor)


def retangulo(sup, x, y, l, a, cor):
    pygame.draw.rect(sup, cor, (x, y, l, a))


def linha(sup, cor, a, b, largura=1):
    pygame.draw.line(sup, cor, a, b, largura)


def escurecer(cor, f):
    return tuple(max(0, min(255, int(c * f))) for c in cor[:3])


# ===============================================================
# Chão
# ===============================================================
def tile_textura(base, escuro, claro, semente, p_escuro=0.10, p_claro=0.05):
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE)
    s.fill(base)
    for y in range(TILE):
        for x in range(TILE):
            r = rng.random()
            if r < p_escuro:
                s.set_at((x, y), escuro)
            elif r < p_escuro + p_claro:
                s.set_at((x, y), claro)
    return s, rng


def tile_grama(semente, base=(92, 168, 72), escuro=(76, 146, 62), claro=(118, 192, 88),
               tufo=(64, 128, 56), flores=True):
    s, rng = tile_textura(base, escuro, claro, semente)
    for _ in range(3):
        x, y = rng.randrange(1, 15), rng.randrange(2, 15)
        pixels(s, [(x, y), (x, y - 1), (x + 1, y)], tufo)
    if flores and rng.random() < 0.25:
        s.set_at((rng.randrange(2, 14), rng.randrange(2, 14)),
                 rng.choice([(250, 240, 120), (240, 120, 160), (250, 250, 250)]))
    return s


def tile_floresta(semente):
    s = tile_grama(semente, (64, 132, 58), (52, 112, 50), (84, 152, 70), (44, 98, 44), flores=False)
    rng = random.Random(semente + 5)
    for _ in range(3):  # folhas secas no chão
        s.set_at((rng.randrange(16), rng.randrange(16)), rng.choice([(140, 100, 50), (120, 86, 44)]))
    return s


def tile_pantano(semente):
    s, rng = tile_textura((92, 112, 62), (74, 92, 54), (112, 132, 74), semente, 0.14, 0.05)
    if rng.random() < 0.5:  # pocinha
        x, y = rng.randrange(2, 11), rng.randrange(2, 12)
        retangulo(s, x, y, 4, 2, (70, 96, 100))
        s.set_at((x + 1, y), (110, 140, 140))
    return s


def tile_neve(semente):
    s, rng = tile_textura((232, 238, 248), (206, 218, 236), (255, 255, 255), semente, 0.10, 0.08)
    return s


def tile_rocha(semente):
    s, rng = tile_textura((128, 124, 120), (104, 100, 98), (154, 150, 144), semente, 0.14, 0.08)
    x, y = rng.randrange(2, 12), rng.randrange(2, 12)
    pixels(s, [(x, y), (x + 1, y + 1), (x + 2, y + 1), (x + 3, y + 2)], (88, 84, 82))
    return s


def tile_areia(semente):
    s, _ = tile_textura((226, 204, 140), (204, 180, 118), (240, 224, 168), semente, 0.08, 0.05)
    return s


def tile_lama(semente):
    s, rng = tile_textura((122, 92, 62), (100, 74, 50), (146, 114, 80), semente, 0.12, 0.06)
    # rachaduras de lama seca
    x, y = rng.randrange(1, 10), rng.randrange(1, 12)
    for i in range(5):
        s.set_at((x + i, y + (i % 2)), (84, 62, 42))
    return s


def tile_agua(semente, funda):
    if funda:
        s, rng = tile_textura((44, 92, 180), (36, 80, 164), (60, 108, 196), semente, 0.08, 0.04)
        brilho = (110, 160, 230)
    else:
        s, rng = tile_textura((82, 148, 212), (70, 134, 200), (100, 166, 224), semente, 0.08, 0.04)
        brilho = (150, 200, 240)
    for _ in range(2):
        x, y = rng.randrange(0, 13), rng.randrange(1, 15)
        for i in range(3):
            s.set_at((x + i, y), brilho)
    return s


# ===============================================================
# Objetos do mundo
# ===============================================================
def sprite_arvore(semente, copa=((40, 110, 52), (56, 140, 62), (86, 176, 80)), pontos=(36, 96, 46)):
    rng = random.Random(semente)
    s = nova_superficie(TILE, 24)
    retangulo(s, 6, 14, 4, 9, (120, 78, 44))
    retangulo(s, 8, 14, 2, 9, (92, 58, 34))
    bolha(s, 8, 8, 7.5, 7.2, copa, rng)
    for _ in range(6):
        x, y = rng.randrange(3, 13), rng.randrange(3, 13)
        if s.get_at((x, y)).a:
            s.set_at((x, y), pontos)
    return contornar(s)


def sprite_arvore_pantano(semente):
    s = sprite_arvore(semente, ((60, 80, 44), (80, 104, 54), (108, 132, 70)), (50, 66, 38))
    rng = random.Random(semente + 9)
    for _ in range(4):  # cipós pendurados
        x = rng.randrange(3, 13)
        for y in range(12, 12 + rng.randrange(3, 7)):
            if y < 24:
                s.set_at((x, y), (70, 96, 50))
    return s


def sprite_pinheiro(semente):
    rng = random.Random(semente)
    s = nova_superficie(TILE, 26)
    retangulo(s, 7, 20, 3, 5, (110, 72, 42))
    escuro, medio, claro = (30, 84, 60), (42, 108, 72), (64, 136, 90)
    for andar, (topo, largura) in enumerate(((1, 3), (6, 5), (11, 7))):
        for y in range(9):
            meia = min(largura, 1 + y * largura // 6)
            for x in range(8 - meia, 8 + meia):
                if 0 <= x < 16 and topo + y < 22:
                    cor = claro if x < 8 - meia + 2 else (escuro if x > 8 + meia - 3 else medio)
                    s.set_at((x, topo + y), cor)
        # neve nas pontas
        s.set_at((8 - 1, topo + 1), (240, 246, 255))
        if rng.random() < 0.8:
            s.set_at((8 - largura + 1, topo + 7), (240, 246, 255))
    return contornar(s)


def sprite_cacto(semente):
    s = nova_superficie(TILE, 20)
    verde, escuro, claro = (70, 150, 70), (50, 116, 56), (110, 190, 100)
    retangulo(s, 6, 2, 4, 17, verde)
    retangulo(s, 9, 2, 1, 17, escuro)
    retangulo(s, 6, 2, 1, 17, claro)
    lado = 1 if semente % 2 else 0
    retangulo(s, 2, 8 - lado, 3, 2, verde)        # braço esquerdo
    retangulo(s, 2, 4 - lado, 2, 5, verde)
    retangulo(s, 11, 10, 3, 2, verde)             # braço direito
    retangulo(s, 12, 6, 2, 5, verde)
    pixels(s, [(7, 5), (8, 9), (7, 13), (8, 16), (3, 6), (12, 8)], (230, 230, 190))  # espinhos
    s.set_at((7, 1), (240, 120, 160))             # florzinha
    return contornar(s)


def sprite_pedra(semente, manchas=None):
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 10, 7, 5.2, ((96, 98, 112), (132, 134, 148), (176, 178, 190)), rng)
    pixels(s, [(9, 8), (10, 9), (10, 10), (11, 11)], (84, 86, 100))
    if manchas:
        for (x, y) in ((4, 9), (7, 7), (11, 12), (6, 12), (12, 8)):
            s.set_at((x, y), manchas[0])
            s.set_at((x + 1, y), manchas[1])
            s.set_at((x, y + 1), manchas[1])
    return contornar(s)


def sprite_arbusto(com_frutas):
    rng = random.Random(7)
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9.5, 7, 6, ((44, 118, 56), (62, 150, 66), (96, 184, 88)), rng)
    if com_frutas:
        for (x, y) in ((4, 7), (9, 6), (11, 10), (6, 11), (8, 9)):
            s.set_at((x, y), (255, 120, 130))
            s.set_at((x + 1, y), (180, 28, 48))
            s.set_at((x, y + 1), (180, 28, 48))
            s.set_at((x + 1, y + 1), (150, 20, 40))
    return contornar(s)


def sprite_capim(semente):
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE)
    for _ in range(5):
        x = rng.randrange(3, 13)
        alt = rng.randrange(4, 8)
        incl = rng.choice((-1, 0, 1))
        for i in range(alt):
            cor = (70, 140, 60) if i < alt - 2 else (150, 200, 100)
            s.set_at((x + (incl if i > alt // 2 else 0), 15 - i), cor)
    return s


def sprite_junco(semente):
    rng = random.Random(semente)
    s = nova_superficie(TILE, 20)
    for i in range(3):
        x = 4 + i * 4 + rng.randrange(-1, 2)
        alt = rng.randrange(10, 16)
        linha(s, (80, 130, 60), (x, 19), (x, 19 - alt))
        retangulo(s, x - 1, 19 - alt + 1, 2, 4, (120, 76, 44))   # "salsicha" do junco
        s.set_at((x - 1, 19 - alt + 1), (150, 100, 60))
    return s


def sprite_bancada():
    s = nova_superficie(TILE, TILE)
    retangulo(s, 1, 5, 14, 4, (178, 128, 76))      # tampo
    retangulo(s, 1, 8, 14, 1, (130, 90, 52))
    retangulo(s, 2, 9, 2, 6, (130, 90, 52))        # pernas
    retangulo(s, 12, 9, 2, 6, (130, 90, 52))
    retangulo(s, 4, 11, 8, 1, (110, 76, 44))
    retangulo(s, 3, 2, 5, 3, (150, 152, 166))      # martelo
    retangulo(s, 5, 3, 1, 3, (110, 72, 42))
    retangulo(s, 9, 3, 5, 2, (200, 204, 214))      # serrote
    pixels(s, [(9, 5), (11, 5), (13, 5)], (200, 204, 214))
    return contornar(s)


def sprite_fogueira(quadro):
    s = nova_superficie(TILE, TILE)
    for (x, y) in ((2, 12), (5, 14), (10, 14), (13, 12)):
        retangulo(s, x - 1, y - 1, 3, 2, (130, 132, 146))
        s.set_at((x - 1, y - 1), (170, 172, 184))
    for i in range(8):
        s.set_at((4 + i, 10 + i // 3), (120, 78, 44))
        s.set_at((11 - i, 10 + i // 3), (96, 60, 34))
    alt_ext, alt_int = [(7, 5), (8, 6), (6, 5)][quadro % 3]
    for y in range(alt_ext):
        meia = max(1, int((alt_ext - y) * 0.6))
        for x in range(8 - meia, 8 + meia):
            s.set_at((x, 11 - y), (232, 80, 36))
    for y in range(alt_int):
        meia = max(1, int((alt_int - y) * 0.4))
        for x in range(8 - meia, 8 + meia):
            s.set_at((x, 11 - y), (252, 168, 48))
    pixels(s, [(7, 10), (8, 10)], (255, 240, 150))
    return s


def sprite_fogueira_apagada():
    s = nova_superficie(TILE, TILE)
    for (x, y) in ((2, 12), (5, 14), (10, 14), (13, 12)):
        retangulo(s, x - 1, y - 1, 3, 2, (110, 112, 124))
    for i in range(8):
        s.set_at((4 + i, 10 + i // 3), (60, 50, 46))
        s.set_at((11 - i, 10 + i // 3), (48, 40, 38))
    return s


def sprite_parede_madeira():
    s = nova_superficie(TILE, 20)
    retangulo(s, 0, 0, 16, 5, (200, 156, 100))
    retangulo(s, 0, 4, 16, 1, (168, 124, 76))
    retangulo(s, 0, 5, 16, 15, (150, 100, 58))
    for x in (0, 5, 10, 15):
        retangulo(s, x, 5, 1, 15, (110, 70, 40))
    for x in (2, 7, 12):
        s.set_at((x + 1, 7), (60, 54, 60))
        s.set_at((x + 1, 16), (60, 54, 60))
    retangulo(s, 0, 18, 16, 2, (112, 74, 42))
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 20), 1)
    return s


def sprite_parede_pedra():
    s = nova_superficie(TILE, 20)
    retangulo(s, 0, 0, 16, 5, (182, 184, 196))
    retangulo(s, 0, 4, 16, 1, (150, 152, 166))
    retangulo(s, 0, 5, 16, 15, (132, 134, 148))
    for n, y in enumerate(range(5, 20, 4)):
        retangulo(s, 0, y, 16, 1, (96, 98, 112))
        inicio = 0 if n % 2 == 0 else 4
        for x in range(inicio, 16, 8):
            retangulo(s, x, y, 1, 4, (96, 98, 112))
        for x in range(inicio + 2, 16, 8):
            s.set_at((x, y + 1), (160, 162, 176))
    retangulo(s, 0, 18, 16, 2, (100, 102, 116))
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 20), 1)
    return s


def sprite_piso():
    s = nova_superficie(TILE, TILE)
    cores = [(178, 130, 82), (164, 118, 72)]
    for i, y in enumerate(range(0, 16, 4)):
        retangulo(s, 0, y, 16, 4, cores[i % 2])
        retangulo(s, 0, y + 3, 16, 1, (124, 86, 52))
        corte = (5 + i * 7) % 16
        retangulo(s, corte, y, 1, 3, (124, 86, 52))
        s.set_at(((corte + 3) % 16, y + 1), (196, 150, 100))
    return s


# ---------------------------------------------------------------
# v0.4: trigo, plantação, tocha, forno, baú e cama
# ---------------------------------------------------------------
TRIGO = ((176, 140, 52), (220, 186, 80), (246, 222, 130))


def sprite_trigo(semente, estagio=3, balanco=0):
    """Trigo (estágio 0 = broto ... 3 = maduro dourado). balanco = -1/0/1 (vento)."""
    rng = random.Random(semente)
    s = nova_superficie(TILE, TILE + 3)
    verde = ((54, 120, 50), (80, 156, 64), (120, 190, 90))
    altura = [3, 6, 10, 12][estagio]
    for n, x in enumerate((3, 6, 9, 12)):
        x += rng.randrange(-1, 2)
        topo = TILE + 2 - altura - rng.randrange(0, 2)
        for y in range(topo, TILE + 2):
            dx = balanco if y < topo + altura // 2 else 0
            cor = verde[1] if estagio < 3 else TRIGO[0]
            s.set_at((x + dx, y), cor)
        if estagio >= 2:
            cor_espiga = verde[2] if estagio == 2 else TRIGO[1]
            for y in range(topo, topo + 4):
                s.set_at((x + balanco, y), cor_espiga)
                if y % 2 == 0:
                    s.set_at((x + balanco + 1, y), TRIGO[2] if estagio == 3 else verde[2])
    return contornar(s)


def sprite_plantacao(estagio, balanco=0):
    s = nova_superficie(TILE, TILE + 3)
    # terra arada
    retangulo(s, 1, 9, 14, 9, (110, 76, 48))
    for y in (10, 13, 16):
        linha(s, (86, 58, 36), (2, y), (13, y))
    planta = sprite_trigo(7, estagio, balanco)
    s.blit(planta, (0, -1))
    return s


def sprite_tocha(quadro):
    s = nova_superficie(TILE, TILE + 2)
    retangulo(s, 7, 8, 2, 9, (120, 80, 44))
    retangulo(s, 7, 8, 1, 9, (150, 104, 60))
    retangulo(s, 6, 7, 4, 2, (70, 60, 56))
    chamas = [((7, 3), (8, 2), (6, 5), (9, 4)), ((8, 3), (7, 2), (9, 5), (6, 4)), ((7, 2), (8, 3), (6, 4), (9, 5))]
    for (x, y) in chamas[quadro % 3]:
        retangulo(s, x, y, 1, 7 - y, (240, 120, 40))
    retangulo(s, 7, 4, 2, 3, (255, 210, 90))
    s.set_at((7 + quadro % 2, 5), (255, 250, 210))
    return contornar(s)


def sprite_forno(quadro=0):
    s = nova_superficie(TILE, TILE + 6)
    pedra = ((100, 98, 110), (138, 136, 148), (172, 170, 182))
    bolha(s, 8, 12, 7.5, 9, pedra)
    for (x, y) in ((4, 6), (10, 8), (6, 14), (12, 15), (3, 11)):
        linha(s, pedra[0], (x, y), (x + 2, y))
    # boca do forno com fogo
    retangulo(s, 5, 13, 6, 5, (40, 24, 20))
    fogo = (240, 120, 40) if quadro == 0 else (250, 160, 60)
    retangulo(s, 6, 15, 4, 3, fogo)
    retangulo(s, 7, 16, 2, 2, (255, 220, 120))
    retangulo(s, 6, 0, 4, 3, (90, 88, 100))       # chaminé
    return contornar(s)


def sprite_bau():
    s = nova_superficie(TILE, TILE)
    madeira = ((120, 74, 40), (160, 106, 58), (196, 142, 84))
    retangulo(s, 1, 4, 14, 11, madeira[1])
    retangulo(s, 1, 4, 14, 4, madeira[2])
    retangulo(s, 1, 8, 14, 1, madeira[0])
    for x in (1, 14):
        retangulo(s, x, 4, 1, 11, (90, 90, 100))
    retangulo(s, 1, 11, 14, 1, madeira[0])
    retangulo(s, 7, 7, 2, 3, (232, 200, 90))       # fechadura
    s.set_at((7, 9), (90, 70, 30))
    return contornar(s)


def sprite_cama():
    s = nova_superficie(TILE, TILE)
    retangulo(s, 1, 2, 14, 13, (130, 84, 46))
    retangulo(s, 2, 3, 12, 11, (230, 226, 216))
    retangulo(s, 3, 3, 10, 3, (250, 250, 246))       # travesseiro
    retangulo(s, 2, 7, 12, 7, (190, 60, 60))         # cobertor
    retangulo(s, 2, 7, 12, 1, (226, 100, 96))
    for x in range(3, 14, 3):
        s.set_at((x, 10), (160, 44, 48))
    return contornar(s)


# ===============================================================
# Jogador (4 direções x 3 quadros)
# ===============================================================
PELE = (240, 192, 150)
CABELO = (90, 54, 30)
CAMISA = (60, 110, 200)
CAMISA_ESC = (44, 82, 160)
CALCA = (70, 60, 52)
BOTA = (52, 36, 26)
OLHO = (24, 20, 30)


def _jogador_frente(costas, quadro):
    s = nova_superficie(TILE, TILE)
    retangulo(s, 5, 2, 6, 5, PELE)
    retangulo(s, 5, 1, 6, 2, CABELO)
    if costas:
        retangulo(s, 5, 1, 6, 5, CABELO)
    else:
        pixels(s, [(5, 3), (10, 3)], CABELO)
        pixels(s, [(6, 4), (9, 4)], OLHO)
    retangulo(s, 4, 7, 8, 4, CAMISA)
    retangulo(s, 4, 10, 8, 1, CAMISA_ESC)
    retangulo(s, 3, 8 + (1 if quadro == 1 else 0), 1, 2, PELE)
    retangulo(s, 12, 8 + (1 if quadro == 2 else 0), 1, 2, PELE)
    retangulo(s, 5, 11, 6, 1, CALCA)
    pe = 13 if quadro == 1 else 14
    pd = 13 if quadro == 2 else 14
    retangulo(s, 5, 12, 2, pe - 12, CALCA)
    retangulo(s, 9, 12, 2, pd - 12, CALCA)
    retangulo(s, 5, pe, 2, 1, BOTA)
    retangulo(s, 9, pd, 2, 1, BOTA)
    return contornar(s)


def _jogador_lado(quadro):
    s = nova_superficie(TILE, TILE)
    retangulo(s, 6, 2, 5, 5, PELE)
    retangulo(s, 6, 1, 5, 2, CABELO)
    retangulo(s, 6, 1, 2, 5, CABELO)
    s.set_at((9, 4), OLHO)
    retangulo(s, 6, 7, 5, 4, CAMISA)
    retangulo(s, 6, 10, 5, 1, CAMISA_ESC)
    retangulo(s, 6, 11, 5, 1, CALCA)
    if quadro == 0:
        retangulo(s, 7, 12, 3, 2, CALCA)
        retangulo(s, 7, 14, 3, 1, BOTA)
        retangulo(s, 8, 8, 1, 3, PELE)
    else:
        frente, tras = (9, 6) if quadro == 1 else (6, 9)
        retangulo(s, frente, 12, 2, 2, CALCA)
        retangulo(s, frente, 14, 2, 1, BOTA)
        retangulo(s, tras, 12, 2, 1, CALCA)
        retangulo(s, tras, 13, 2, 1, BOTA)
        retangulo(s, 9 if quadro == 2 else 7, 8, 1, 3, PELE)
    return contornar(s)


def sprites_jogador():
    direita = [_jogador_lado(q) for q in range(3)]
    return {
        "baixo": [_jogador_frente(False, q) for q in range(3)],
        "cima": [_jogador_frente(True, q) for q in range(3)],
        "direita": direita,
        "esquerda": [pygame.transform.flip(f, True, False) for f in direita],
    }


# ===============================================================
# Criaturas (olhando para a DIREITA; 2 quadros de animação)
# ===============================================================
def _pernas(s, xs, y, alt, cor, quadro):
    for n, x in enumerate(xs):
        desloca = (1 if (n + quadro) % 2 else 0)
        linha(s, cor, (x, y), (x + desloca - (1 - desloca) * 0, y + alt - desloca))


def criatura_coelho(q):
    s = nova_superficie(TILE, TILE)
    pelo, claro = (200, 190, 176), (236, 230, 220)
    _pernas(s, (6, 9), 12, 2, (150, 140, 128), q)
    bolha(s, 7.5, 11 - q * 0.5, 4.5, 3, (escurecer(pelo, 0.85), pelo, claro))
    bolha(s, 11.5, 8 - q * 0.5, 2.6, 2.4, (escurecer(pelo, 0.85), pelo, claro))
    retangulo(s, 10, 2 + q, 1, 4, pelo)                 # orelhas
    retangulo(s, 12, 3 + q, 1, 3, pelo)
    s.set_at((10, 4 + q), (240, 160, 170))
    s.set_at((3, 10), (255, 255, 255))                  # rabinho
    s.set_at((12, 8 - q // 1), OLHO)
    return contornar(s)


def criatura_galinha(q):
    s = nova_superficie(TILE, TILE)
    branco = (246, 244, 236)
    linha(s, (230, 150, 40), (7, 12), (7 - q, 14))
    linha(s, (230, 150, 40), (9, 12), (9 + q, 14))
    bolha(s, 7.5, 9.5, 4.5, 3.5, ((210, 206, 196), branco, (255, 255, 255)))
    bolha(s, 11, 6, 2.2, 2.2, ((210, 206, 196), branco, (255, 255, 255)))
    pixels(s, [(10, 3), (11, 3), (11, 2)], (220, 40, 40))          # crista
    pixels(s, [(13, 6), (14, 6)], (240, 190, 40))                  # bico
    s.set_at((12, 7), (220, 40, 40))
    s.set_at((11, 5), OLHO)
    pixels(s, [(3, 6), (3, 7), (4, 6)], (220, 216, 206))           # rabo
    return contornar(s)


def criatura_cervo(q):
    s = nova_superficie(TILE, TILE)
    pelo = (166, 112, 64)
    _pernas(s, (4, 6, 9, 11), 11, 4, (100, 66, 40), q)
    bolha(s, 7.5, 9, 5.5, 3, (escurecer(pelo, 0.8), pelo, (196, 140, 86)))
    retangulo(s, 11, 4, 2, 4, pelo)                                # pescoço
    bolha(s, 13, 4, 2.2, 1.8, (escurecer(pelo, 0.8), pelo, (196, 140, 86)))
    for (x, y) in ((11, 1), (12, 2), (13, 1), (14, 0), (11, 0)):   # chifres
        s.set_at((x, y), (224, 200, 160))
    s.set_at((14, 4), OLHO)
    pixels(s, [(6, 8), (8, 7), (9, 9)], (230, 210, 180))           # pintinhas
    s.set_at((2, 8), (250, 250, 250))
    return contornar(s)


def criatura_lobo(q):
    s = nova_superficie(TILE, TILE)
    pelo = (128, 130, 142)
    _pernas(s, (4, 6, 9, 11), 11, 4, (80, 80, 92), q)
    bolha(s, 7.5, 9.5, 5.5, 3, (escurecer(pelo, 0.75), pelo, (170, 172, 182)))
    bolha(s, 12, 7.5, 2.8, 2.5, (escurecer(pelo, 0.75), pelo, (170, 172, 182)))
    retangulo(s, 14, 8, 2, 2, (150, 152, 162))                     # focinho
    s.set_at((15, 8), OLHO)
    pixels(s, [(11, 4), (11, 5), (13, 4), (13, 5)], pelo)          # orelhas
    s.set_at((12, 7), (250, 220, 70))                              # olho amarelo
    linha(s, pelo, (2, 7 + q), (1, 5 + q))                         # rabo
    return contornar(s)


def criatura_aranha(q):
    s = nova_superficie(TILE, TILE)
    corpo = (60, 44, 60)
    for i in range(4):  # 8 pernas
        x = 5 + i * 2
        sobe = (i + q) % 2
        linha(s, (40, 30, 40), (x, 10), (x - 2, 6 + sobe))
        linha(s, (40, 30, 40), (x - 2, 6 + sobe), (x - 3, 13))
    bolha(s, 6.5, 10, 3.5, 3, ((40, 28, 40), corpo, (96, 70, 96)))
    bolha(s, 11, 10.5, 2.2, 2, ((40, 28, 40), corpo, (96, 70, 96)))
    pixels(s, [(11, 9), (12, 10)], (240, 50, 50))                  # olhos vermelhos
    s.set_at((6, 8), (150, 60, 60))
    return contornar(s)


def criatura_escorpiao(q):
    s = nova_superficie(TILE, TILE)
    cor, escuro = (206, 150, 76), (160, 110, 52)
    for i in range(3):
        linha(s, escuro, (5 + i * 2, 12), (4 + i * 2 + q, 14))
    bolha(s, 8, 11, 4.5, 2.2, (escuro, cor, (236, 186, 110)))
    rabo = [(4, 10), (3, 9), (2, 7), (2, 5), (3, 4), (5, 3), (7, 3 + q)]
    pixels(s, rabo, cor)
    pixels(s, [(8, 4 + q), (8, 5 + q)], (120, 40, 40))             # ferrão
    pixels(s, [(12, 9), (13, 8), (14, 8), (14, 10), (13, 11), (12, 11)], escuro)  # garras
    s.set_at((11, 10), OLHO)
    return contornar(s)


def criatura_slime(q, piscando=False):
    s = nova_superficie(TILE, TILE)
    cx, cy, rx, ry = (8, 10.5, 6.5, 5) if q == 0 else (8, 11.5, 7.5, 4)
    cores = ((60, 150, 60), (96, 200, 84), (160, 236, 140))
    bolha(s, cx, cy, rx, ry, cores)
    oy = int(cy) - 1
    for ox in (6, 10):
        pixels(s, [(ox, oy), (ox, oy + 1)], (20, 30, 20))
    s.set_at((int(cx - rx * 0.5), int(cy - ry * 0.55)), (240, 255, 240))
    return contornar(s, (20, 60, 24, 255))


FABRICA_CRIATURAS = {
    "coelho": criatura_coelho, "galinha": criatura_galinha, "cervo": criatura_cervo,
    "lobo": criatura_lobo, "aranha": criatura_aranha, "escorpiao": criatura_escorpiao,
    "slime": criatura_slime,
}


# ===============================================================
# Ícones dos itens
# ===============================================================
COR_TIER = {"madeira": (176, 124, 72), "pedra": (140, 142, 156), "ferro": (214, 220, 232)}
CABO = (140, 92, 52)
CABO_ESC = (110, 70, 40)


def _cabo(s, comprimento=10):
    for i in range(comprimento):
        s.set_at((3 + i, 13 - i), CABO)
        s.set_at((4 + i, 13 - i), CABO_ESC)


def icone_machado(cor):
    s = nova_superficie(TILE, TILE)
    _cabo(s)
    retangulo(s, 9, 2, 4, 5, cor)
    retangulo(s, 12, 3, 2, 3, escurecer(cor, 1.2))
    retangulo(s, 9, 2, 1, 5, escurecer(cor, 0.75))
    return contornar(s)


def icone_picareta(cor):
    s = nova_superficie(TILE, TILE)
    _cabo(s)
    curva = [(4, 4), (5, 3), (6, 2), (7, 2), (8, 2), (9, 2), (10, 3), (11, 3),
             (12, 4), (13, 5), (13, 6), (14, 7), (14, 8), (3, 5)]
    pixels(s, curva, cor)
    pixels(s, [(6, 3), (7, 3), (8, 3), (9, 3)], escurecer(cor, 0.75))
    return contornar(s)


def icone_espada(cor):
    s = nova_superficie(TILE, TILE)
    for i in range(9):  # lâmina
        s.set_at((5 + i, 10 - i), cor)
        s.set_at((6 + i, 10 - i), escurecer(cor, 0.8))
    s.set_at((13, 2), escurecer(cor, 1.2))
    linha(s, (120, 90, 50), (3, 9), (7, 13))      # guarda
    linha(s, CABO, (3, 12), (5, 10))
    s.set_at((2, 13), (200, 170, 70))
    return contornar(s)


def icone_vara():
    s = nova_superficie(TILE, TILE)
    linha(s, CABO, (2, 14), (12, 2))
    linha(s, (220, 220, 230), (12, 2), (14, 9))
    pixels(s, [(14, 10), (13, 11)], (180, 180, 190))
    s.set_at((14, 7), (220, 40, 40))
    return contornar(s)


def icone_madeira():
    s = nova_superficie(TILE, TILE)
    for i in range(2):
        y = 5 + i * 4
        retangulo(s, 2, y, 11, 4, (140, 92, 52))
        retangulo(s, 2, y + 3, 11, 1, (104, 66, 38))
        retangulo(s, 12, y, 2, 4, (214, 172, 116))
        s.set_at((13, y + 1), (170, 120, 70))
    return contornar(s)


def icone_pedra(manchas=None):
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 5.5, 4.5, ((96, 98, 112), (132, 134, 148), (176, 178, 190)))
    if manchas:
        for (x, y) in ((6, 8), (9, 10), (10, 7)):
            s.set_at((x, y), manchas[0])
            s.set_at((x + 1, y), manchas[1])
    return contornar(s)


def icone_frutas():
    s = nova_superficie(TILE, TILE)
    for (cx, cy) in ((6, 9), (10, 9), (8, 6)):
        bolha(s, cx, cy, 2.6, 2.6, ((150, 20, 40), (210, 40, 60), (255, 120, 130)))
    pixels(s, [(8, 2), (9, 2), (9, 3)], (60, 140, 60))
    return contornar(s)


def icone_fibra():
    s = nova_superficie(TILE, TILE)
    for i, x in enumerate((5, 7, 9, 11)):
        linha(s, (110, 170, 70) if i % 2 else (90, 150, 60), (x, 2), (x - 2 + i, 14))
    retangulo(s, 4, 8, 8, 2, (180, 140, 80))      # amarrado
    return contornar(s)


def icone_couro():
    s = nova_superficie(TILE, TILE)
    pontos = [(3, 4), (7, 2), (12, 3), (13, 8), (12, 13), (7, 12), (3, 13), (2, 8)]
    pygame.draw.polygon(s, (190, 136, 84), pontos)
    pixels(s, [(6, 6), (9, 8), (7, 10)], (160, 108, 64))
    pixels(s, [(5, 4), (10, 5)], (214, 166, 110))
    return contornar(s)


def icone_barra_ferro():
    s = nova_superficie(TILE, TILE)
    pygame.draw.polygon(s, (196, 202, 214), [(2, 11), (5, 6), (14, 6), (12, 11)])
    retangulo(s, 2, 11, 11, 2, (150, 156, 170))
    linha(s, (240, 244, 250), (6, 7), (12, 7))
    return contornar(s)


def icone_carne(assada):
    s = nova_superficie(TILE, TILE)
    if assada:
        cores = ((120, 64, 30), (160, 90, 44), (200, 130, 70))
    else:
        cores = ((170, 50, 60), (220, 90, 100), (250, 150, 160))
    bolha(s, 7, 7, 5, 4.5, cores)
    linha(s, (240, 236, 220), (10, 10), (13, 13), 2)    # osso
    pixels(s, [(14, 12), (12, 14), (14, 14)], (240, 236, 220))
    return contornar(s)


def icone_peixe(assado):
    s = nova_superficie(TILE, TILE)
    cores = ((150, 90, 40), (200, 130, 60), (230, 170, 90)) if assado else \
        ((70, 100, 140), (110, 150, 190), (170, 200, 230))
    bolha(s, 7, 8, 5, 3, cores)
    pygame.draw.polygon(s, cores[1], [(11, 8), (14, 5), (14, 11)])
    s.set_at((4, 7), OLHO)
    return contornar(s)


def icone_cantil(cheio):
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9.5, 5, 5, ((110, 76, 44), (150, 104, 62), (186, 136, 86)))
    retangulo(s, 7, 2, 3, 3, (100, 100, 110))
    linha(s, (90, 60, 36), (3, 6), (12, 13))           # alça
    if cheio:
        pixels(s, [(7, 1), (8, 1), (9, 1)], (90, 170, 240))
        bolha(s, 8, 10, 2, 2, ((50, 110, 200), (80, 150, 230), (150, 200, 250)))
    return contornar(s)


def icone_capuz(cor):
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 8, 6, 6, (escurecer(cor, 0.75), cor, escurecer(cor, 1.2)))
    for y in range(7, 13):
        for x in range(5, 11):
            s.set_at((x, y), (0, 0, 0, 0))
    retangulo(s, 2, 12, 12, 2, escurecer(cor, 0.85))
    return contornar(s)


def icone_capacete(cor):
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 6, 5.5, (escurecer(cor, 0.7), cor, escurecer(cor, 1.15)))
    for y in range(9, 15):
        for x in range(0, 16):
            if y > 11:
                s.set_at((x, y), (0, 0, 0, 0))
    retangulo(s, 2, 10, 12, 2, escurecer(cor, 0.8))
    retangulo(s, 7, 9, 2, 4, escurecer(cor, 0.7))       # protetor do nariz
    return contornar(s)


def icone_roupa(cor):
    s = nova_superficie(TILE, TILE)
    pygame.draw.polygon(s, cor, [(4, 2), (6, 3), (10, 3), (12, 2), (15, 6), (12, 8),
                                 (12, 14), (4, 14), (4, 8), (1, 6)])
    linha(s, escurecer(cor, 0.75), (8, 4), (8, 14))
    linha(s, escurecer(cor, 1.2), (5, 9), (6, 13))
    return contornar(s)


def icone_de_parede(parede):
    s = nova_superficie(TILE, TILE)
    s.blit(pygame.transform.scale(parede, (12, 15)), (2, 0))
    return s


def icone_piso():
    s = nova_superficie(TILE, TILE)
    s.blit(pygame.transform.scale(sprite_piso(), (14, 14)), (1, 1))
    pygame.draw.rect(s, CONTORNO, (0, 0, 16, 16), 1)
    return s


def icone_lanca():
    s = nova_superficie(TILE, TILE)
    for i in range(11):
        s.set_at((2 + i, 13 - i), CABO)
    pygame.draw.polygon(s, (150, 152, 166), [(11, 1), (14, 1), (14, 4), (12, 5), (10, 3)])
    s.set_at((13, 2), (210, 212, 224))
    pixels(s, [(9, 5), (10, 6)], (200, 180, 120))
    return contornar(s)


def icone_arco():
    s = nova_superficie(TILE, TILE)
    pontos = [(3, 13), (3, 10), (4, 7), (6, 5), (9, 4), (12, 3), (13, 3)]
    for a, b in zip(pontos, pontos[1:]):
        linha(s, CABO, a, b)
    linha(s, CABO_ESC, (4, 12), (5, 8))
    linha(s, (230, 226, 210), (3, 13), (13, 3))
    retangulo(s, 6, 8, 2, 2, (180, 130, 80))
    return contornar(s)


def icone_flecha():
    s = nova_superficie(TILE, TILE)
    linha(s, (176, 130, 80), (3, 12), (12, 3))
    pixels(s, [(12, 2), (13, 2), (13, 3), (11, 3), (12, 4)], (190, 192, 204))
    pixels(s, [(2, 11), (3, 13), (2, 12), (4, 13)], (230, 230, 236))
    return contornar(s)


def icone_carvao():
    s = nova_superficie(TILE, TILE)
    bolha(s, 6, 9, 3.8, 3.2, ((24, 22, 26), (46, 44, 50), (84, 82, 90)))
    bolha(s, 10.5, 10, 3.2, 2.8, ((24, 22, 26), (46, 44, 50), (84, 82, 90)))
    pixels(s, [(5, 7), (10, 8)], (120, 118, 128))
    return contornar(s)


def icone_trigo():
    s = nova_superficie(TILE, TILE)
    for n, x in enumerate((6, 8, 10)):
        linha(s, TRIGO[0], (x, 14), (x - 1 + n, 6))
        for y in range(2, 7):
            s.set_at((x - 1 + n, y), TRIGO[1])
            if y % 2 == 0:
                s.set_at((x + n, y), TRIGO[2])
    retangulo(s, 5, 10, 7, 1, (150, 100, 50))
    return contornar(s)


def icone_sementes():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 10, 5.5, 4, ((150, 110, 70), (190, 150, 100), (220, 190, 140)))   # saquinho
    retangulo(s, 6, 4, 4, 3, (170, 130, 84))
    for (x, y) in ((6, 9), (9, 10), (8, 12), (10, 8)):
        s.set_at((x, y), (240, 214, 120))
    return contornar(s)


def icone_pao():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 9, 6.5, 4.2, ((150, 90, 40), (200, 138, 70), (236, 186, 110)))
    for x in (5, 8, 11):
        linha(s, (236, 206, 150), (x, 7), (x + 1, 9))
    return contornar(s)


def icone_sopa():
    s = nova_superficie(TILE, TILE)
    bolha(s, 8, 10, 6.5, 4.5, ((110, 70, 40), (150, 100, 58), (186, 136, 84)))   # tigela
    retangulo(s, 2, 6, 13, 3, (0, 0, 0, 0))
    bolha(s, 8, 8.5, 6, 2, ((170, 90, 50), (210, 130, 70), (240, 180, 110)))
    pixels(s, [(6, 8), (10, 9)], (110, 170, 70))
    pixels(s, [(6, 3), (7, 2), (9, 4), (10, 3)], (230, 230, 240))                 # vapor
    return contornar(s)


def icone_tocha():
    s = nova_superficie(TILE, TILE)
    t = sprite_tocha(0)
    s.blit(t, (0, -2))
    return s


def icone_reduzido(sprite):
    s = nova_superficie(TILE, TILE)
    w, h = sprite.get_size()
    f = min(15 / w, 15 / h)
    img = pygame.transform.scale(sprite, (max(1, int(w * f)), max(1, int(h * f))))
    s.blit(img, ((TILE - img.get_width()) // 2, (TILE - img.get_height()) // 2))
    return s


# ---------------------------------------------------------------
# Ícones pequenos (8x8) do HUD
# ---------------------------------------------------------------
def _icone8(desenho, cores):
    s = nova_superficie(8, 8)
    for y, linha_ in enumerate(desenho):
        for x, c in enumerate(linha_):
            if c != ".":
                s.set_at((x, y), cores[c])
    return s


def icones_hud():
    k = CONTORNO
    return {
        "vida": _icone8(["........", ".RR.RR..", "RWRRRRR.", "RRRRRRR.", ".RRRRR..", "..RRR...", "...R....", "........"],
                        {"R": (220, 50, 60), "W": (255, 190, 190)}),
        "fome": _icone8(["...BB...", "..BMMB..", ".BMMMMB.", ".BMMMMB.", "..BMMB..", "...WW...", "..W..W..", "........"],
                        {"B": (140, 70, 36), "M": (200, 120, 60), "W": (240, 236, 220)}),
        "sede": _icone8(["...B....", "...B....", "..BBB...", ".BBWBB..", ".BBBBB..", ".BBBBB..", "..BBB...", "........"],
                        {"B": (70, 150, 236), "W": (200, 230, 255)}),
        "energia": _icone8(["....YY..", "...YY...", "..YY....", ".YYYYY..", "...YY...", "..YY....", ".YY.....", "........"],
                           {"Y": (240, 220, 80)}),
        "ar": _icone8(["........", "..BBB...", ".B.WWB..", ".B.W.B..", ".B...B..", "..BBB...", "......B.", ".....B.B"],
                      {"B": (150, 220, 250), "W": (255, 255, 255)}),
        "dano": _icone8([".......W", "......WG", ".....WG.", "....WG..", ".B.WG...", "..BG....", ".BBB....", "B..B...."],
                        {"W": (230, 232, 240), "G": (160, 164, 180), "B": (150, 100, 50)}),
        "defesa": _icone8([".GGGGGG.", "GWWGGGGG", "GWGGGGDG", "GGGGGGDG", ".GGGGDG.", ".GGGGDG.", "..GGDG..", "...GG..."],
                          {"G": (160, 170, 190), "W": (230, 236, 246), "D": (110, 116, 136)}),
        "temp": _icone8(["...W....", "..WRW...", "..WRW...", "..WRW...", "..WRW...", ".WRRRW..", ".WRRRW..", "..WWW..."],
                        {"W": (236, 236, 240), "R": (230, 70, 60)}),
        "sol": _icone8(["...Y....", ".Y...Y..", "...YY...", "Y.YOOY.Y", "..YOOY..", "...YY...", ".Y...Y..", "...Y...."],
                       {"Y": (250, 220, 80), "O": (250, 170, 50)}),
        "lua": _icone8(["..WWW...", ".WW.....", "WW......", "WW......", "WW......", ".WW...W.", "..WWWW..", "........"],
                       {"W": (220, 226, 250)}),
        "chuva": _icone8(["..GGG...", ".GGGGG..", "GGGGGGG.", "........", ".B..B...", "B..B..B.", "..B..B..", "........"],
                         {"G": (170, 176, 196), "B": (100, 160, 240)}),
        "neve": _icone8(["...W....", ".W.W.W..", "..WWW...", "WWWBWWW.", "..WWW...", ".W.W.W..", "...W....", "........"],
                        {"W": (240, 246, 255), "B": (160, 200, 250)}),
        "seca": _icone8(["...O....", ".O.O.O..", "..OOO...", "OOORROOO", "..OOO...", ".O.O.O..", "...O....", "........"],
                        {"O": (250, 140, 50), "R": (230, 70, 40)}),
        "primavera": _icone8(["..P.P...", ".PPYPP..", "..PPP...", "...G....", ".GGG....", "...G.G..", "...GG...", "........"],
                             {"P": (250, 150, 190), "Y": (250, 230, 100), "G": (90, 170, 70)}),
        "verao": _icone8(["...Y....", ".Y...Y..", "...YY...", "Y.YYYY.Y", "..YYYY..", "...YY...", ".Y...Y..", "...Y...."],
                         {"Y": (250, 200, 60)}),
        "outono": _icone8(["....OO..", "...OOOO.", "..OROOO.", ".OORRO..", ".OOOO...", "..OO....", ".B......", "B......."],
                          {"O": (230, 130, 40), "R": (190, 70, 30), "B": (120, 80, 40)}),
        "inverno": _icone8(["...W....", ".W.W.W..", "..WWW...", "WWWBWWW.", "..WWW...", ".W.W.W..", "...W....", "........"],
                           {"W": (230, 240, 255), "B": (140, 190, 250)}),
        "nublado": _icone8(["........", "..GGG...", ".GWWGG..", "GWWGGGG.", "GGGGGGG.", ".GGGGG..", "........", "........"],
                           {"G": (180, 186, 204), "W": (230, 234, 244)}),
        "cama": _icone8(["........", "W.......", "WPP.....", "WRRRRRR.", "WRRRRRR.", "WWWWWWW.", "W.....W.", "........"],
                        {"W": (140, 96, 56), "P": (250, 250, 246), "R": (200, 60, 60)}),
        "_k": _icone8(["k"], {"k": k}),
    }


MANCHAS_FERRO = ((214, 140, 90), (180, 100, 70))


def criar_icones():
    ic = {
        "madeira": icone_madeira(), "pedra": icone_pedra(), "frutas": icone_frutas(),
        "fibra": icone_fibra(), "couro": icone_couro(),
        "minerio_ferro": icone_pedra(MANCHAS_FERRO), "ferro": icone_barra_ferro(),
        "carne_crua": icone_carne(False), "carne_assada": icone_carne(True),
        "peixe": icone_peixe(False), "peixe_assado": icone_peixe(True),
        "cantil": icone_cantil(False), "cantil_cheio": icone_cantil(True),
        "vara_pesca": icone_vara(),
        "capuz_couro": icone_capuz((170, 116, 66)), "roupa_couro": icone_roupa((170, 116, 66)),
        "capacete_ferro": icone_capacete((196, 202, 214)), "armadura_ferro": icone_roupa((196, 202, 214)),
        "bancada": sprite_bancada(), "fogueira": sprite_fogueira(0),
        "parede_madeira": icone_de_parede(sprite_parede_madeira()),
        "parede_pedra": icone_de_parede(sprite_parede_pedra()),
        "piso": icone_piso(),
        "lanca": icone_lanca(), "arco": icone_arco(), "flecha": icone_flecha(),
        "carvao": icone_carvao(), "trigo": icone_trigo(), "sementes_trigo": icone_sementes(),
        "pao": icone_pao(), "sopa": icone_sopa(), "tocha": icone_tocha(),
        "forno": icone_reduzido(sprite_forno()), "bau": sprite_bau(), "cama": sprite_cama(),
    }
    for tier, cor in COR_TIER.items():
        ic[f"machado_{tier}"] = icone_machado(cor)
        ic[f"picareta_{tier}"] = icone_picareta(cor)
        ic[f"espada_{tier}"] = icone_espada(cor)
    faltando = [i for i in ITENS if i not in ic]
    assert not faltando, f"Itens sem ícone: {faltando}"
    return ic


# ===============================================================
# Itens no chão, rachaduras, cursor e luz
# ===============================================================
def item_chao_madeira():
    s = nova_superficie(10, 7)
    retangulo(s, 1, 1, 7, 4, (140, 92, 52))
    retangulo(s, 1, 4, 7, 1, (104, 66, 38))
    retangulo(s, 7, 1, 2, 4, (214, 172, 116))
    return contornar(s)


def item_chao_pedra():
    s = nova_superficie(9, 8)
    bolha(s, 4.5, 4.5, 3.6, 3, ((96, 98, 112), (132, 134, 148), (186, 188, 200)))
    return contornar(s)


def rachar(sprite, estagio, semente=3):
    """Cópia do sprite com rachaduras (estagio 1..3)."""
    s = sprite.copy()
    larg, alt = s.get_size()
    rng = random.Random(semente)
    escuro, claro = (30, 22, 26, 255), (235, 225, 200, 255)
    dentro = [(x, y) for y in range(alt) for x in range(larg)
              if s.get_at((x, y)).a > 0 and s.get_at((x, y))[:3] != CONTORNO[:3]]
    if not dentro:
        return s
    mx = sum(p[0] for p in dentro) / len(dentro)
    my = sum(p[1] for p in dentro) / len(dentro)
    dentro.sort(key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)
    centro = dentro[:max(1, len(dentro) // 3)]
    conjunto = set(dentro)
    for _ in range(1 + estagio * 2):
        x, y = rng.choice(centro)
        dx, dy = rng.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
        for _ in range(3 + estagio * 2):
            if (x, y) in conjunto:
                s.set_at((x, y), escuro)
                if (x + 1, y) in conjunto and rng.random() < 0.4:
                    s.set_at((x + 1, y), claro)
            if rng.random() < 0.5:
                x += dx
            else:
                y += dy
    return s


def sprite_cursor():
    desenho = [
        "X.........", "XX........", "XWX.......", "XWWX......", "XWWWX.....",
        "XWWWWX....", "XWWWWWX...", "XWWWWWWX..", "XWWWWXXXX.", "XWXWWX....",
        "XX.XWWX...", "X...XWX...", ".....XX...",
    ]
    s = nova_superficie(10, 13)
    for y, l in enumerate(desenho):
        for x, c in enumerate(l):
            if c == "X":
                s.set_at((x, y), CONTORNO)
            elif c == "W":
                s.set_at((x, y), (250, 246, 230))
    return s


_cache_luz = {}


def gradiente_luz(raio, cor=(255, 200, 140)):
    """Círculo de luz em degraus (cara de pixel art)."""
    chave = (raio, cor)
    if chave in _cache_luz:
        return _cache_luz[chave]
    s = pygame.Surface((raio * 2, raio * 2))
    s.fill((0, 0, 0))
    for y in range(raio * 2):
        for x in range(raio * 2):
            d = math.hypot(x + 0.5 - raio, y + 0.5 - raio) / raio
            if d < 1.0:
                k = math.ceil((1.0 - d) * 5) / 5
                s.set_at((x, y), tuple(int(c * k) for c in cor))
    _cache_luz[chave] = s
    return s


# ===============================================================
# Estações e vento
# ===============================================================
OUTONO = [(140, 56, 30), (196, 92, 38), (232, 148, 54), (250, 204, 90)]
NEVE_TOPO = (244, 248, 255, 255)
NEVE_SOMBRA = (204, 216, 236, 255)
FOLHOSAS = ("arvore", "arbusto", "capim", "junco", "arvore_pantano")


def _folha(c):
    return c.a > 0 and c.g > c.r + 12 and c.g > c.b + 4


def tingir_estacao(sprite, tipo, estacao, semente=0):
    """Versão do sprite para a estação (folhas laranjas, neve em cima, flores...)."""
    if estacao == "verao" or tipo in ("cacto", "pedra", "minerio_ferro"):
        return sprite
    s = sprite.copy()
    larg, alt = s.get_size()
    rng = random.Random(semente * 17 + len(tipo))
    for y in range(alt):
        for x in range(larg):
            c = s.get_at((x, y))
            if not _folha(c):
                continue
            lum = (c.r + c.g + c.b) / 3
            if estacao == "outono" and tipo in FOLHOSAS:
                i = 0 if lum < 70 else 1 if lum < 100 else 2 if lum < 130 else 3
                if tipo in ("capim", "junco"):
                    i = min(3, i + 1)
                s.set_at((x, y), OUTONO[i])
            elif estacao == "inverno":
                acima = s.get_at((x, y - 1)) if y > 0 else pygame.Color(0, 0, 0, 0)
                topo = acima.a == 0 or tuple(acima)[:3] == CONTORNO[:3]
                if topo or (y > 0 and not _folha(acima) and rng.random() < 0.5):
                    s.set_at((x, y), NEVE_TOPO)
                elif tipo in ("capim", "junco"):
                    s.set_at((x, y), (150, 136, 100))
                else:
                    g = int(lum * 0.85)
                    s.set_at((x, y), (g - 10, g + 6, g + 4) if g > 10 else c)
            elif estacao == "primavera" and tipo in ("arvore", "arbusto") and rng.random() < 0.07:
                s.set_at((x, y), rng.choice([(250, 180, 210), (255, 240, 246), (250, 150, 190)]))
    # inverno: um pouco de neve em cima das pedras
    return s


def tingir_pedra_inverno(sprite):
    s = sprite.copy()
    larg, alt = s.get_size()
    for x in range(larg):
        for y in range(alt):
            c = s.get_at((x, y))
            if c.a > 0 and tuple(c)[:3] != CONTORNO[:3]:
                s.set_at((x, y), NEVE_TOPO)
                if y + 1 < alt and s.get_at((x, y + 1)).a > 0:
                    s.set_at((x, y + 1), NEVE_SOMBRA)
                break
    return s


def balancar(sprite, d, proporcao=0.5):
    """Inclina a parte de cima do sprite d pixels (vento)."""
    if d == 0:
        return sprite
    larg, alt = sprite.get_size()
    s = nova_superficie(larg, alt)
    limite = int(alt * proporcao)
    s.blit(sprite, (0, limite), (0, limite, larg, alt - limite))
    s.blit(sprite, (d, 0), (0, 0, larg, limite))
    return s


TAMANHO_SOMBRA = {"arvore": 14, "arvore_pantano": 14, "pinheiro": 12, "cacto": 9, "pedra": 13,
                  "minerio_ferro": 13, "arbusto": 12, "capim": 8, "junco": 8, "trigo": 10, "plantacao": 0,
                  "bancada": 14, "fogueira": 12, "parede_madeira": 0, "parede_pedra": 0, "piso": 0,
                  "tocha": 6, "forno": 14, "bau": 14, "cama": 14}


def criar_sombra(largura):
    s = nova_superficie(largura, max(3, largura // 3))
    pygame.draw.ellipse(s, (0, 0, 0, 72), s.get_rect())
    return s



# ===============================================================
# Guarda de todos os sprites
# ===============================================================
class Sprites:
    def __init__(self):
        n = 4
        self.chao = {
            GRAMA: [tile_grama(i) for i in range(n)],
            GRAMA_FLORESTA: [tile_floresta(10 + i) for i in range(n)],
            GRAMA_PANTANO: [tile_pantano(20 + i) for i in range(n)],
            NEVE: [tile_neve(30 + i) for i in range(n)],
            ROCHA: [tile_rocha(40 + i) for i in range(n)],
            AREIA: [tile_areia(50 + i) for i in range(n)],
            LAMA: [tile_lama(60 + i) for i in range(n)],
            AGUA_RASA: [tile_agua(70 + i, False) for i in range(n)],
            AGUA_FUNDA: [tile_agua(80 + i, True) for i in range(n)],
        }
        self.objetos = {
            "arvore": [sprite_arvore(i) for i in range(3)],
            "arvore_pantano": [sprite_arvore_pantano(i) for i in range(3)],
            "pinheiro": [sprite_pinheiro(i) for i in range(3)],
            "cacto": [sprite_cacto(i) for i in range(3)],
            "pedra": [sprite_pedra(i) for i in range(3)],
            "minerio_ferro": [sprite_pedra(i, MANCHAS_FERRO) for i in range(3)],
            "capim": [sprite_capim(i) for i in range(3)],
            "junco": [sprite_junco(i) for i in range(3)],
            "bancada": [sprite_bancada()],
            "parede_madeira": [sprite_parede_madeira()],
            "parede_pedra": [sprite_parede_pedra()],
            "piso": [sprite_piso()],
            "trigo": [sprite_trigo(i) for i in range(3)],
            "bau": [sprite_bau()],
            "cama": [sprite_cama()],
            "forno": [sprite_forno(0)],
            "tocha": [sprite_tocha(0)],
            "plantacao": [sprite_plantacao(0)],
        }
        self.plantacao = [sprite_plantacao(e) for e in range(4)]
        self.tocha = [sprite_tocha(q) for q in range(3)]
        self.forno = [sprite_forno(q) for q in range(2)]
        self.texturas = Texturas()
        self.hud = {k: pygame.transform.scale(v, (24, 24)) for k, v in icones_hud().items()}
        self.hud_peq = {k: pygame.transform.scale(v, (16, 16)) for k, v in icones_hud().items()}
        self.sombras = {k: criar_sombra(v) for k, v in TAMANHO_SOMBRA.items() if v}
        self._estacao = {}
        self._balanco = {}
        self._jogador = {}
        self.arbusto_com = sprite_arbusto(True)
        self.arbusto_sem = sprite_arbusto(False)
        self.fogueira = [sprite_fogueira(q) for q in range(3)]
        self.fogueira_apagada = sprite_fogueira_apagada()
        self.piso = self.objetos["piso"][0]

        # criaturas: tipo -> {"direita": [q0, q1], "esquerda": [...], "branco": img}
        self.criaturas = {}
        for tipo, fabrica in FABRICA_CRIATURAS.items():
            dir_ = [fabrica(0), fabrica(1)]
            mascara = pygame.mask.from_surface(dir_[0])
            branco = mascara.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            self.criaturas[tipo] = {
                "direita": dir_,
                "esquerda": [pygame.transform.flip(f, True, False) for f in dir_],
                "branco": branco,
            }

        self.icones = criar_icones()
        self.itens_chao = {nome: pygame.transform.scale(img, (10, 10)) for nome, img in self.icones.items()}
        self.itens_chao["madeira"] = item_chao_madeira()
        self.itens_chao["pedra"] = item_chao_pedra()

        self.cursor = pygame.transform.scale(sprite_cursor(), (30, 39))
        self.sombra = nova_superficie(12, 4)
        pygame.draw.ellipse(self.sombra, (0, 0, 0, 70), (0, 0, 12, 4))
        self.sombra_item = nova_superficie(8, 3)
        pygame.draw.ellipse(self.sombra_item, (0, 0, 0, 70), (0, 0, 8, 3))
        self._rachados = {}
        self._fantasmas = {}

    def sprite_objeto(self, obj, estacao="verao", balanco=0):
        if obj.tipo == "arbusto":
            base = self.arbusto_com if obj.tem_frutas else self.arbusto_sem
            chave = ("arbusto", obj.tem_frutas)
        elif obj.tipo == "fogueira":
            return self.fogueira[0] if obj.acesa else self.fogueira_apagada
        elif obj.tipo == "plantacao":
            base = self.plantacao[min(3, obj.estagio)]
            chave = ("plantacao", obj.estagio)
        else:
            lista = self.objetos[obj.tipo]
            base = lista[obj.variante % len(lista)]
            chave = (obj.tipo, obj.variante % len(lista))
        img = self.da_estacao(chave, base, obj.tipo, estacao)
        if balanco:
            k = (chave, estacao, balanco)
            if k not in self._balanco:
                prop = 0.45 if obj.tipo in ("arvore", "arvore_pantano", "pinheiro") else 0.6
                self._balanco[k] = balancar(img, balanco, prop)
            img = self._balanco[k]
        return img

    def da_estacao(self, chave, base, tipo, estacao):
        if estacao == "verao" or tipo not in ("arvore", "arvore_pantano", "pinheiro", "arbusto", "capim",
                                              "junco", "pedra", "minerio_ferro"):
            return base
        k = (chave, estacao)
        if k not in self._estacao:
            if tipo in ("pedra", "minerio_ferro"):
                self._estacao[k] = tingir_pedra_inverno(base) if estacao == "inverno" else base
            else:
                self._estacao[k] = tingir_estacao(base, tipo, estacao, hash(chave) & 0xff)
        return self._estacao[k]

    def jogador(self, direcao, anim, quadro, cabeca=None, corpo=None, mao=None):
        k = (direcao, anim, quadro, cabeca, corpo, mao)
        if k not in self._jogador:
            icone = self.icones.get(mao) if mao else None
            self._jogador[k] = personagem.montar(direcao, anim, quadro, cabeca, corpo, icone)
        return self._jogador[k]

    def rachado(self, chave, sprite, estagio):
        if estagio <= 0:
            return sprite
        k = (chave, estagio)
        if k not in self._rachados:
            self._rachados[k] = rachar(sprite, estagio)
        return self._rachados[k]

    def sprite_construcao(self, item):
        if item == "fogueira":
            return self.fogueira[0]
        if item == "sementes_trigo":
            return self.plantacao[0]
        return self.objetos[item][0]

    def fantasma(self, item, valido):
        k = (item, valido)
        if k not in self._fantasmas:
            s = self.sprite_construcao(item).copy()
            tinta = (170, 255, 170, 255) if valido else (255, 120, 120, 255)
            s.fill(tinta, special_flags=pygame.BLEND_RGBA_MULT)
            s.set_alpha(200)
            self._fantasmas[k] = s
        return self._fantasmas[k]
