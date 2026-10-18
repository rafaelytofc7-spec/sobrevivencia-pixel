# -*- coding: utf-8 -*-
"""
personagem.py - Pixel art do jogador, desenhada por código e montada em camadas:
corpo (pele, cabelo, roupa) + armadura equipada (cabeça e corpo) + item na mão.

Animações (4 direções):
  parado (2 quadros, respirando), andar (4), atacar (3, girando o item),
  nadar (2, só cabeça e ombros para fora d'água), rolar (4).
Cada sprite tem 32x32 pixels; os pés ficam na linha 27 (ver PES_Y).
"""
import math
import pygame

from dados import ITENS

TAM = 32
OX, OY = 8, 8            # onde fica o "corpo" (16x20) dentro do quadro
PES_Y = 27               # linha dos pés dentro do quadro
CONTORNO = (28, 24, 36, 255)

PELE = (240, 192, 150)
PELE_ESC = (212, 160, 124)
CABELO = (92, 56, 32)
CABELO_CLARO = (128, 82, 46)
OLHO = (24, 20, 30)
CALCA = (66, 70, 96)
CALCA_ESC = (50, 52, 74)
BOTA = (70, 46, 30)
BOTA_CLARO = (98, 66, 42)
CINTO = (96, 62, 36)
FIVELA = (236, 206, 92)

ROUPAS = {
    None: ((44, 82, 160), (64, 116, 206), (104, 152, 230)),               # camisa azul
    "roupa_couro": ((112, 72, 40), (150, 100, 58), (186, 136, 84)),
    "armadura_ferro": ((122, 128, 146), (170, 176, 192), (222, 226, 238)),
    "armadura_diamante": ((40, 150, 160), (90, 210, 214), (170, 246, 240)),     # v0.5
}
METAIS = ("armadura_ferro", "armadura_diamante")


def _metal(cabeca):
    return "armadura_diamante" if cabeca == "capacete_diamante" else "armadura_ferro"

ANIMACOES = {"parado": 2, "andar": 4, "atacar": 3, "nadar": 2, "rolar": 4}


def _contornar(sup):
    larg, alt = sup.get_size()
    cheios = {(x, y) for y in range(alt) for x in range(larg) if sup.get_at((x, y)).a > 0}
    for (x, y) in list(cheios):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < larg and 0 <= ny < alt and (nx, ny) not in cheios:
                sup.set_at((nx, ny), CONTORNO)
    return sup


class Pintor:
    """Ajuda a pintar em coordenadas do 'corpo' (16x20) com deslocamento."""
    def __init__(self, sup, dx=0, dy=0):
        self.s = sup
        self.dx = OX + dx
        self.dy = OY + dy

    def p(self, x, y, cor):
        X, Y = x + self.dx, y + self.dy
        if 0 <= X < TAM and 0 <= Y < TAM:
            self.s.set_at((X, Y), cor)

    def r(self, x, y, l, a, cor):
        for yy in range(y, y + a):
            for xx in range(x, x + l):
                self.p(xx, yy, cor)


# ---------------------------------------------------------------
# Partes do corpo
# ---------------------------------------------------------------
def _cabeca_frente(pt, cabeca, costas):
    # rosto
    pt.r(4, 2, 8, 7, PELE)
    pt.r(11, 3, 1, 6, PELE_ESC)
    pt.r(5, 8, 6, 1, PELE_ESC)
    if costas:
        pt.r(4, 1, 8, 7, CABELO)
        pt.r(5, 7, 6, 1, CABELO_CLARO)
        pt.r(5, 1, 3, 1, CABELO_CLARO)
    else:
        pt.r(4, 1, 8, 2, CABELO)
        pt.r(4, 3, 1, 3, CABELO)
        pt.r(11, 3, 1, 2, CABELO)
        pt.r(6, 1, 3, 1, CABELO_CLARO)
        pt.p(7, 3, CABELO)
        pt.p(6, 5, OLHO)
        pt.p(9, 5, OLHO)
        pt.p(6, 4, (250, 250, 250))
        pt.p(9, 4, (250, 250, 250))
        pt.r(7, 7, 2, 1, (196, 120, 110))     # boca
    if cabeca == "capuz_couro":
        esc, med, cla = ROUPAS["roupa_couro"]
        pt.r(3, 0, 10, 3, med)
        pt.r(3, 3, 2, 6, med)
        pt.r(11, 3, 2, 6, esc)
        pt.r(4, 0, 4, 1, cla)
        if costas:
            pt.r(3, 0, 10, 9, med)
            pt.r(6, 2, 4, 5, esc)
    elif cabeca in ("capacete_ferro", "capacete_diamante"):
        esc, med, cla = ROUPAS[_metal(cabeca)]
        pt.r(3, 0, 10, 4, med)
        pt.r(3, 4, 10, 1, esc)
        pt.r(4, 0, 3, 1, cla)
        pt.r(3, 1, 1, 3, cla)
        if costas:
            pt.r(3, 4, 10, 3, med)
            pt.r(4, 7, 8, 1, esc)
        else:
            pt.r(7, 5, 2, 2, esc)               # protetor do nariz


def _cabeca_lado(pt, cabeca):
    pt.r(5, 2, 7, 7, PELE)
    pt.r(5, 8, 6, 1, PELE_ESC)
    pt.r(4, 1, 7, 2, CABELO)
    pt.r(4, 3, 3, 5, CABELO)
    pt.r(5, 1, 3, 1, CABELO_CLARO)
    pt.p(7, 5, PELE_ESC)                       # orelha
    pt.p(10, 5, OLHO)
    pt.p(10, 4, (250, 250, 250))
    pt.p(12, 6, PELE)                          # nariz
    pt.p(11, 7, (196, 120, 110))
    if cabeca == "capuz_couro":
        esc, med, cla = ROUPAS["roupa_couro"]
        pt.r(3, 0, 9, 3, med)
        pt.r(3, 3, 5, 6, med)
        pt.r(3, 3, 1, 6, esc)
        pt.r(5, 0, 4, 1, cla)
    elif cabeca in ("capacete_ferro", "capacete_diamante"):
        esc, med, cla = ROUPAS[_metal(cabeca)]
        pt.r(3, 0, 10, 4, med)
        pt.r(3, 4, 10, 1, esc)
        pt.r(3, 4, 4, 3, med)
        pt.r(5, 0, 4, 1, cla)


def _torso_frente(pt, corpo, costas, braco_e=0, braco_d=0, ombro=True):
    esc, med, cla = ROUPAS.get(corpo, ROUPAS[None])
    pt.r(7, 9, 2, 1, PELE_ESC)                 # pescoço
    pt.r(4, 9, 8, 5, med)
    pt.r(4, 9, 1, 5, cla)
    pt.r(11, 9, 1, 5, esc)
    if not costas:
        pt.r(6, 9, 4, 1, cla)                  # gola
        if corpo == "roupa_couro":
            pt.p(7, 11, esc), pt.p(8, 12, esc)  # costura
        elif corpo in METAIS:
            pt.r(5, 11, 6, 1, cla)              # placa do peito
            pt.r(5, 12, 6, 1, esc)
    pt.r(4, 14, 8, 1, CINTO)
    if not costas:
        pt.r(7, 14, 2, 1, FIVELA)
    # braços (mangas + mãos)
    for x, desl in ((3, braco_e), (12, braco_d)):
        pt.r(x, 10, 1, 3 + desl, med if x == 3 else esc)
        pt.r(x, 13 + desl, 1, 2, PELE)
    if corpo in METAIS and ombro:
        pt.r(2, 9, 3, 2, cla)
        pt.r(11, 9, 3, 2, med)


def _pernas_frente(pt, levanta_e=0, levanta_d=0):
    for x, lev in ((5, levanta_e), (8, levanta_d)):
        pt.r(x, 15, 3, 3 - lev, CALCA)
        pt.r(x + 2, 15, 1, 3 - lev, CALCA_ESC)
        pt.r(x, 18 - lev, 3, 2, BOTA)
        pt.r(x, 18 - lev, 2, 1, BOTA_CLARO)


def _torso_lado(pt, corpo, braco=0):
    esc, med, cla = ROUPAS.get(corpo, ROUPAS[None])
    pt.r(7, 9, 3, 1, PELE_ESC)
    pt.r(5, 9, 6, 5, med)
    pt.r(5, 9, 1, 5, esc)
    pt.r(10, 9, 1, 5, cla)
    if corpo in METAIS:
        pt.r(6, 11, 5, 1, cla)
        pt.r(5, 9, 4, 2, cla)
    pt.r(5, 14, 6, 1, CINTO)
    # braço da frente balançando (braco = -1, 0, 1)
    bx = 7 + braco
    pt.r(bx, 10, 2, 3, esc if corpo else med)
    pt.r(bx, 13, 2, 2, PELE)


def _pernas_lado(pt, fase=0):
    # perna de trás (mais escura) e da frente
    tras, frente = 7 - fase, 7 + fase
    pt.r(tras, 15, 2, 3, CALCA_ESC)
    pt.r(tras, 18, 3 if fase <= 0 else 2, 2, (54, 36, 24))
    pt.r(frente, 15, 2, 3, CALCA)
    pt.r(frente, 18, 3, 2, BOTA)
    pt.r(frente + 1, 18, 2, 1, BOTA_CLARO)


# ---------------------------------------------------------------
# Item na mão
# ---------------------------------------------------------------
def _girar_no_cabo(img, angulo, cabo=(3, 13)):
    """Gira o ícone em volta do ponto do cabo. Retorna (imagem, deslocamento do cabo)."""
    w, h = img.get_size()
    cx, cy = w / 2, h / 2
    vx, vy = cabo[0] - cx, cabo[1] - cy
    girada = pygame.transform.rotate(img, angulo)
    a = math.radians(angulo)
    rx = vx * math.cos(a) + vy * math.sin(a)
    ry = -vx * math.sin(a) + vy * math.cos(a)
    gw, gh = girada.get_size()
    return girada, (gw / 2 + rx, gh / 2 + ry)


# ângulos do item (graus, anti-horário; o ícone natural aponta para cima-direita)
ANG_SEGURAR = {"direita": 10, "baixo": -60, "cima": 30}
ANG_ATAQUE = {"direita": (80, 5, -85), "baixo": (40, -50, -140), "cima": (100, 40, -20)}
MAO = {  # posição da mão (coordenadas do corpo) por direção
    "direita": (9, 14), "baixo": (12, 15), "cima": (3, 14),
}


def _item_na_mao(sup, icone, direcao, angulo, mao, dy=0):
    img = pygame.transform.scale(icone, (12, 12))
    girada, (hx, hy) = _girar_no_cabo(img, angulo, cabo=(2.5, 9.8))
    x = OX + mao[0] - hx
    y = OY + mao[1] + dy - hy
    sup.blit(girada, (int(round(x)), int(round(y))))


# ---------------------------------------------------------------
# Montagem de um quadro
# ---------------------------------------------------------------
def montar(direcao, anim, quadro, cabeca=None, corpo=None, icone_mao=None):
    """Sprite 32x32 do jogador. direcao em baixo/cima/direita/esquerda."""
    if direcao == "esquerda":
        s = montar("direita", anim, quadro, cabeca, corpo, icone_mao)
        return pygame.transform.flip(s, True, False)
    sup = pygame.Surface((TAM, TAM), pygame.SRCALPHA)

    if anim == "rolar":
        return _rolar(quadro, cabeca, corpo)

    bob = 0
    perna = (0, 0)
    braco = (0, 0)
    fase = 0
    if anim == "parado":
        bob = quadro % 2
    elif anim == "andar":
        perna = [(1, 0), (0, 0), (0, 1), (0, 0)][quadro % 4]
        braco = [(0, 1), (0, 0), (1, 0), (0, 0)][quadro % 4]
        fase = [1, 0, -1, 0][quadro % 4]
        bob = 1 if quadro % 2 == 1 else 0
    elif anim == "atacar":
        braco = (0, -1 if quadro == 0 else 1)
        fase = [0, 1, 1][quadro]

    corpo_pt = Pintor(sup, 0, bob)
    pernas_pt = Pintor(sup, 0, 0)
    costas = direcao == "cima"

    # item atrás do corpo (olhando para cima)
    angulo_item = None
    if icone_mao is not None:
        if anim == "atacar":
            angulo_item = ANG_ATAQUE[direcao][quadro]
        else:
            angulo_item = ANG_SEGURAR[direcao]
    if icone_mao is not None and costas and anim != "nadar":
        _item_na_mao(sup, icone_mao, direcao, angulo_item, MAO[direcao], bob)

    if anim == "nadar":
        return _nadar(direcao, quadro, cabeca, corpo)

    if direcao in ("baixo", "cima"):
        _pernas_frente(pernas_pt, *perna)
        _torso_frente(corpo_pt, corpo, costas, *braco)
        _cabeca_frente(corpo_pt, cabeca, costas)
    else:
        _pernas_lado(pernas_pt, fase)
        braco_lado = {"andar": [-1, 0, 1, 0][quadro % 4], "atacar": [-1, 1, 2][quadro % 3]}.get(anim, 0)
        _torso_lado(corpo_pt, corpo, braco_lado)
        _cabeca_lado(corpo_pt, cabeca)
    _contornar(sup)

    if icone_mao is not None and not costas:
        mao = MAO[direcao]
        if direcao == "direita" and anim == "atacar":
            mao = (mao[0] + [-1, 2, 3][quadro], mao[1] - [2, 0, -1][quadro])
        elif direcao == "direita" and anim == "andar":
            mao = (mao[0] + [-1, 0, 1, 0][quadro % 4], mao[1])
        _item_na_mao(sup, icone_mao, direcao, angulo_item, mao, bob)
    return sup


def _nadar(direcao, quadro, cabeca, corpo):
    """Só cabeça e ombros (o resto está debaixo d'água) + braçadas."""
    sup = pygame.Surface((TAM, TAM), pygame.SRCALPHA)
    pt = Pintor(sup, 0, 6)            # afunda 6 pixels
    esc, med, cla = ROUPAS.get(corpo, ROUPAS[None])
    if direcao in ("baixo", "cima"):
        pt.r(4, 9, 8, 2, med)
        _cabeca_frente(pt, cabeca, direcao == "cima")
        # braçada: uma mão para fora d'água
        if quadro == 0:
            pt.r(2, 8, 2, 2, PELE)
        else:
            pt.r(12, 8, 2, 2, PELE)
    else:
        pt.r(5, 9, 6, 2, med)
        _cabeca_lado(pt, cabeca)
        if quadro == 0:
            pt.r(11, 8, 2, 2, PELE)
        else:
            pt.r(3, 9, 2, 2, PELE)
    # corta tudo abaixo da linha d'água
    linha = OY + 6 + 11
    for y in range(linha, TAM):
        for x in range(TAM):
            sup.set_at((x, y), (0, 0, 0, 0))
    return _contornar(sup)


def _rolar(quadro, cabeca, corpo):
    """Bolinha rodando (4 quadros = 4 giros de 90°)."""
    base = pygame.Surface((TAM, TAM), pygame.SRCALPHA)
    esc, med, cla = ROUPAS.get(corpo, ROUPAS[None])
    pt = Pintor(base, 0, 0)
    # corpo encolhido: círculo de roupa, cabeça em cima, pés do lado
    for y in range(9, 20):
        for x in range(2, 14):
            if (x - 7.5) ** 2 + (y - 14) ** 2 <= 30:
                pt.p(x, y, med)
    for y in range(9, 20):
        for x in range(2, 14):
            if (x - 7.5) ** 2 + (y - 14) ** 2 <= 30 and x - 7.5 + y - 14 > 4:
                pt.p(x, y, esc)
    pt.r(5, 7, 6, 5, PELE)
    pt.r(5, 6, 6, 2, CABELO if cabeca is None else ROUPAS["roupa_couro" if cabeca == "capuz_couro"
                                                          else _metal(cabeca)][1])
    pt.r(12, 15, 2, 3, BOTA)
    pt.r(4, 16, 3, 2, PELE)
    _contornar(base)
    return pygame.transform.rotate(base, -90 * quadro) if quadro % 4 else base


def icone_na_mao(inventario, icones):
    """Que item aparece na mão: o escolhido na barra (se for ferramenta/arma/tocha)
    ou, se não, a arma/ferramenta equipada."""
    item = inventario.item_selecionado()
    if item and (ITENS[item]["tipo"] in ("ferramenta", "arma") or item == "tocha"):
        return item
    for slot in ("arma", "ferramenta"):
        e = inventario.equipamento.get(slot)
        if e:
            return e[0]
    return None
