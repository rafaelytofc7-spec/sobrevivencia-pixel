# -*- coding: utf-8 -*-
"""
cavernas.py - As camadas debaixo da terra (z = -1 até -4).

- GeradorCaverna: cada bloco é PEDRA (um bloco sólido) ou ABERTO (caverna).
  Usa ruído 3D (x, y, camada) com a semente do mundo, então camadas vizinhas
  têm túneis parecidos e a mesma semente sempre gera as mesmas cavernas.
  Salões grandes + túneis finos, lagos subterrâneos, lava na camada -4 e
  minérios por profundidade (carvão, ferro, ouro, cristal, diamante).
- MundoCaverna: um Mundo com esse gerador (chunks, cache e save por camada).
- EcossistemaCaverna: monstros nascem no escuro (longe das tochas).
"""
import math
import random

from config import (TILE, TAMANHO_CHUNK, AGUA_FUNDA, AGUA_RASA, CAVERNA, LAVA, CHAO_AGUA)
from mundo import Mundo, Chunk, Objeto
from ecossistema import Ecossistema
from ruido import ruido3, fractal3, numero_chunk
from dados import CRIATURAS
from blocos import MONSTROS_CAVERNA

CH = TAMANHO_CHUNK
CAMADA_MAIS_FUNDA = -4

# (objeto, camada mais alta, camada mais funda, limiar no ruído) - o mais raro primeiro
MINERIOS_POR_CAMADA = [
    ("min_diamante", -4, -4, 0.915),
    ("min_cristal", -3, -4, 0.885),
    ("min_ouro", -2, -4, 0.89),
    ("min_ferro", -1, -4, 0.86),
    ("min_carvao", -1, -4, 0.83),
]


class ChunkCaverna(Chunk):
    def recalcular_chao(self, deslocamento):
        return False


class GeradorCaverna:
    def __init__(self, semente, z):
        self.semente = semente
        self.z = z
        self.estruturas = None
        self.sz = z * 0.55                      # distância entre camadas dentro do ruído
        self.minerios = [(i, nome, lim) for i, (nome, alto, fundo, lim) in enumerate(MINERIOS_POR_CAMADA)
                         if fundo <= z <= alto]

    def aberto(self, x, y):
        s = self.semente
        if fractal3(x / 22.0, y / 22.0, self.sz, s + 101) > 0.615:
            return True                         # salão
        return abs(fractal3(x / 14.0, y / 14.0, self.sz, s + 202) - 0.5) < 0.022   # túnel

    def chao_aberto(self, x, y):
        w = ruido3(x / 12.0, y / 12.0, self.z * 0.7, self.semente + 303)
        if self.z <= CAMADA_MAIS_FUNDA:
            if w > 0.75:
                return LAVA
        elif self.z == -3 and w > 0.86:
            return LAVA
        elif w > 0.86:
            return AGUA_FUNDA
        elif w > 0.80:
            return AGUA_RASA
        return CAVERNA

    def chao_em(self, x, y):
        return self.chao_aberto(x, y) if self.aberto(x, y) else CAVERNA

    def bioma(self, x, y):
        return "caverna"

    def bloco_em(self, x, y):
        """Tipo do bloco sólido em (x, y): pedra ou um minério."""
        s, z = self.semente, self.z
        for i, nome, lim in self.minerios:
            fundo = (CAMADA_MAIS_FUNDA - z) * -0.004     # minérios um pouco mais comuns lá embaixo
            if ruido3(x / 3.2, y / 3.2, z * 1.3 + i * 7.1, s + 400 + i) > lim - fundo:
                return nome
        return "bloco_pedra"

    def gerar_chunk(self, cx, cy):
        ch = ChunkCaverna(cx, cy)
        x0, y0 = cx * CH, cy * CH
        rng = random.Random(numero_chunk(self.semente + 977 * (-self.z), cx, cy))
        for j in range(CH):
            for i in range(CH):
                x, y = x0 + i, y0 + j
                k = j * CH + i
                ch.biomas[k] = "caverna"
                if self.aberto(x, y):
                    ch.chao[k] = self.chao_aberto(x, y)
                    if ch.chao[k] == CAVERNA and rng.random() < 0.012:
                        ch.objetos[(x, y)] = Objeto("ossos", x, y)     # enfeite (some com um golpe)
                else:
                    ch.chao[k] = CAVERNA
                    ch.objetos[(x, y)] = Objeto(self.bloco_em(x, y), x, y, rng.randrange(3))
        ch.sujo = True
        return ch


class MundoCaverna(Mundo):
    """Uma camada debaixo da terra. dados_save() devolve o da SUPERFÍCIE (como a masmorra);
    as mudanças desta camada vão em dados_proprios()."""
    def __init__(self, superficie, z):
        super().__init__(superficie.semente)
        self.superficie = superficie
        self.z = z
        self.gerador = GeradorCaverna(superficie.semente, z)
        self.subterraneo = True

    def tipo_chao(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        if ch:
            return ch.chao[(ty % CH) * CH + (tx % CH)]
        return self.gerador.chao_em(tx, ty)

    def bioma(self, tx, ty):
        return "caverna"

    def definir_nivel_agua(self, deslocamento):
        pass

    def dados_save(self):
        return self.superficie.dados_save()

    def dados_proprios(self):
        return Mundo.dados_save(self)


class EcossistemaCaverna(Ecossistema):
    """Sem bichos de dia: só monstros, que nascem no escuro."""
    def __init__(self, jogo, z):
        super().__init__(jogo)
        self.z = z

    def limite_monstros(self):
        return min(14, 6 + (-self.z) + self.jogo.dia // 3)

    def iluminado(self, x, y):
        for o, raio in self.jogo.mundo.lista_luzes():
            if math.hypot(x - o.centro[0], y - o.centro[1]) < raio * 1.15:
                return True
        return False

    def _lugar_escuro(self, ch, rng):
        mundo = self.jogo.mundo
        j = self.jogo.jogador
        for _ in range(10):
            i, k = rng.randrange(CH), rng.randrange(CH)
            tx, ty = ch.cx * CH + i, ch.cy * CH + k
            chao = ch.chao[k * CH + i]
            if chao in CHAO_AGUA or chao == LAVA:
                continue
            o = ch.objetos.get((tx, ty))
            if o is not None and o.solido:
                continue
            x, y = tx * TILE + 8, ty * TILE + 12
            if math.hypot(x - j.x, y - j.y) < 120 or self.iluminado(x, y):
                continue
            from mobs import criar_criatura
            c = criar_criatura("zumbi", x, y)
            if not mundo.colide(c.retangulo()):
                return x, y
        return None

    def _escolher(self, rng):
        return rng.choice(MONSTROS_CAVERNA.get(self.z, MONSTROS_CAVERNA[-1]))

    def ao_carregar_chunk(self, ch):
        if self.contar("monstro") >= self.limite_monstros():
            return
        rng = random.Random(numero_chunk(self.jogo.mundo.semente + 31 * (-self.z), ch.cx, ch.cy) + 5)
        if rng.random() < 0.6:
            return
        lugar = self._lugar_escuro(ch, rng)
        if lugar:
            from mobs import criar_criatura
            self.jogo.criaturas.append(criar_criatura(self._escolher(rng), *lugar))

    def tentar_spawn(self, noite):
        jogo = self.jogo
        if self.contar("monstro") >= self.limite_monstros():
            return
        j = jogo.jogador
        pcx, pcy = int(j.x // TILE) // CH, int(j.y // TILE) // CH
        candidatos = [ch for (cx, cy), ch in jogo.mundo.chunks.items()
                      if max(abs(cx - pcx), abs(cy - pcy)) <= 2]
        if not candidatos or random.random() < 0.35:
            return
        ch = random.choice(candidatos)
        lugar = self._lugar_escuro(ch, random)
        if lugar:
            from mobs import criar_criatura
            jogo.criaturas.append(criar_criatura(self._escolher(random), *lugar))

    def atualizar(self, dt):
        super().atualizar(dt)
        j = self.jogo.jogador
        # quem ficou muito longe some (as cavernas são grandes)
        self.jogo.criaturas = [c for c in self.jogo.criaturas
                               if math.hypot(c.x - j.x, c.y - j.y) < 420 or not CRIATURAS[c.tipo].get("noturno")]
