# -*- coding: utf-8 -*-
"""
dungeon.py - MASMORRAS: um nível subterrâneo separado, gerado pela semente
de cada entrada (salas + corredores), escuro (só a sua luz e as tochas),
com monstros, um chefe (Rei Esqueleto) e baús de tesouro.

- GeradorMasmorra: monta a planta (64x64 blocos) e entrega chunks como o
  gerador da superfície.
- MundoMasmorra: um Mundo com o mesmo jeito de usar (o jogo troca
  jogo.mundo por ele enquanto você está lá embaixo).
- EcossistemaMasmorra: lá embaixo não nasce bicho novo; só os da planta.
"""
import random

from config import TAMANHO_CHUNK
from mundo import Mundo, Chunk, Objeto
from ecossistema import Ecossistema
from dados_estruturas import PISO_MASMORRA, VAZIO
from estruturas import numero

CH = TAMANHO_CHUNK
TAM = 64                 # a masmorra tem TAM x TAM blocos (4x4 chunks)
PAREDE = ("parede_pedra", 2)
MONSTROS = ["esqueleto", "esqueleto", "aranha", "slime", "esqueleto"]


class PlantaMasmorra:
    def __init__(self, semente, ident, nivel=1):
        self.id = ident
        rng = random.Random(semente)
        self.chao = {}            # (x, y) -> True (andável)
        self.objetos = {}         # (x, y) -> (tipo, variante)
        self.baus = {}            # (x, y) -> nível
        self.monstros = []        # (tipo, x, y, chefe?)
        salas = []
        for _ in range(300):
            if len(salas) >= 9:
                break
            w, h = rng.randint(6, 11), rng.randint(5, 9)
            x, y = rng.randint(2, TAM - w - 3), rng.randint(2, TAM - h - 3)
            if all(x + w + 2 < a or a + c + 2 < x or y + h + 2 < b or b + d + 2 < y for a, b, c, d in salas):
                salas.append((x, y, w, h))
        self.salas = salas
        for (x, y, w, h) in salas:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.chao[(xx, yy)] = True
        centros = [(x + w // 2, y + h // 2) for (x, y, w, h) in salas]
        # corredores: cada sala liga na mais perto das anteriores (+ uns atalhos)
        ligacoes = []
        for i in range(1, len(salas)):
            j = min(range(i), key=lambda k: (centros[k][0] - centros[i][0]) ** 2 + (centros[k][1] - centros[i][1]) ** 2)
            ligacoes.append((i, j))
        for _ in range(2):
            a, b = rng.randrange(len(salas)), rng.randrange(len(salas))
            if a != b:
                ligacoes.append((a, b))
        for (a, b) in ligacoes:
            self._corredor(centros[a], centros[b], rng.random() < 0.5, rng.random() < 0.35)
        # paredes em volta de tudo que é andável
        for (x, y) in list(self.chao):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    p = (x + dx, y + dy)
                    if p not in self.chao:
                        self.objetos[p] = PAREDE
        # entrada = sala 0; chefe = sala mais longe da entrada
        self.inicio = (centros[0][0], centros[0][1])
        self.objetos[self.inicio] = ("escada_subir", 0)
        self.chegada = (self.inicio[0], self.inicio[1] + 1)
        longe = max(range(1, len(salas)), key=lambda k: (centros[k][0] - centros[0][0]) ** 2 +
                    (centros[k][1] - centros[0][1]) ** 2)
        self.sala_chefe = salas[longe]
        for n, (x, y, w, h) in enumerate(salas):
            livres = [(xx, yy) for yy in range(y + 1, y + h - 1) for xx in range(x + 1, x + w - 1)
                      if (xx, yy) not in self.objetos and abs(xx - self.inicio[0]) + abs(yy - self.inicio[1]) > 2]
            rng.shuffle(livres)
            # tochas nas bordas das salas
            beiras = [(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)
                      if (xx in (x, x + w - 1) or yy in (y, y + h - 1)) and (xx, yy) not in self.objetos]
            rng.shuffle(beiras)
            for p in beiras[:2 if n != longe else 4]:
                self.objetos[p] = ("tocha", 0)
            if n == 0:
                continue
            if n == longe:
                cx, cy = centros[n]
                self.monstros.append(("rei_esqueleto", cx, cy, True))
                for p in livres[:2]:
                    self.monstros.append(("esqueleto", p[0], p[1], False))
                for p in ((x + 1, y + 1), (x + w - 2, y + 1), (x + w // 2, y + 1)):
                    if p not in self.objetos:
                        self.objetos[p] = ("bau", 1)
                        self.baus[p] = 3
                continue
            for p in livres[:rng.randint(1, 3)]:
                self.monstros.append((rng.choice(MONSTROS), p[0], p[1], False))
            if rng.random() < 0.45 and len(livres) > 4:
                p = livres[4]
                self.objetos[p] = ("bau", 0)
                self.baus[p] = 2
            if rng.random() < 0.6 and len(livres) > 5:
                self.objetos[livres[5]] = ("ossos", 0)

    def _corredor(self, a, b, horizontal_primeiro, largo):
        (x0, y0), (x1, y1) = a, b
        pontos = []
        if horizontal_primeiro:
            pontos += [(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)]
            pontos += [(x1, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
        else:
            pontos += [(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
            pontos += [(x, y1) for x in range(min(x0, x1), max(x0, x1) + 1)]
        for (x, y) in pontos:
            self.chao[(x, y)] = True
            if largo:
                self.chao[(x + 1, y)] = True
                self.chao[(x, y + 1)] = True

    def andavel(self, x, y):
        return (x, y) in self.chao


class ChunkMasmorra(Chunk):
    def recalcular_chao(self, deslocamento):
        return False          # lá embaixo não tem água subindo e descendo


class GeradorMasmorra:
    def __init__(self, planta, abertos):
        self.planta = planta
        self.abertos = abertos
        self.semente = 0

    def chao_em(self, x, y):
        return PISO_MASMORRA if self.planta.andavel(x, y) else VAZIO

    def bioma(self, x, y):
        return "montanha"

    def gerar_chunk(self, cx, cy):
        ch = ChunkMasmorra(cx, cy)
        x0, y0 = cx * CH, cy * CH
        pl = self.planta
        for j in range(CH):
            for i in range(CH):
                k = j * CH + i
                ch.biomas[k] = "montanha"
                ch.alturas[k] = 1.0
                ch.niveis[k] = 0.0
                ch.chao[k] = self.chao_em(x0 + i, y0 + j)
        for j in range(CH):
            for i in range(CH):
                p = (x0 + i, y0 + j)
                if p in pl.objetos:
                    t, v = pl.objetos[p]
                    if t == "bau" and f"{pl.id}|{p[0]},{p[1]}" in self.abertos:
                        t = "bau_aberto"
                    ch.objetos[p] = Objeto(t, p[0], p[1], v)
        return ch


class MundoMasmorra(Mundo):
    """Mundo subterrâneo. dados_save() devolve o da SUPERFÍCIE (o save é sempre da superfície)."""
    def __init__(self, superficie, ident, abertos):
        super().__init__(superficie.semente)
        self.superficie = superficie
        self.id = ident
        self.planta = PlantaMasmorra(numero(superficie.semente, "masmorra", ident), ident)
        self.gerador = GeradorMasmorra(self.planta, abertos)
        self.subterraneo = True

    def tipo_chao(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        if ch:
            return ch.chao[(ty % CH) * CH + (tx % CH)]
        return self.gerador.chao_em(tx, ty)

    def bioma(self, tx, ty):
        return "montanha"

    def definir_nivel_agua(self, deslocamento):
        pass

    def carregar_tudo(self):
        for cy in range(-1, TAM // CH + 1):
            for cx in range(-1, TAM // CH + 1):
                if (cx, cy) not in self.chunks:
                    self.gerar(cx, cy)

    def dados_save(self):
        return self.superficie.dados_save()


class EcossistemaMasmorra(Ecossistema):
    def ao_carregar_chunk(self, ch):
        pass

    def tentar_spawn(self, noite):
        pass
