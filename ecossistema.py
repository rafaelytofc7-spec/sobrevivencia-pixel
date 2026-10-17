# -*- coding: utf-8 -*-
"""
ecossistema.py - Faz os bichos aparecerem, sumirem e terem filhotes.

- Quando um chunk novo carrega, ele ganha alguns animais do seu bioma.
- A cada poucos segundos, tenta nascer uma criatura num chunk carregado
  (longe da tela), respeitando limites (caps) por categoria.
- Criaturas em chunks descarregados somem. Monstros noturnos somem de dia.
- Animais da mesma espécie que ficam perto têm filhotes devagar.
"""
import math
import random

from config import (TILE, TAMANHO_CHUNK, CHAO_AGUA, LAMA, MAX_PASSIVOS, MAX_PREDADORES,
                    MAX_MONSTROS_BASE, MAX_POR_CHUNK, TEMPO_ENTRE_SPAWNS, RAIO_LUZ_FOGUEIRA)
from dados import BIOMAS, CRIATURAS
from entidades import Criatura
from mundo import chunk_do_bloco
from ruido import numero_chunk

CH = TAMANHO_CHUNK


class Ecossistema:
    def __init__(self, jogo):
        self.jogo = jogo
        self.tempo_spawn = 0.0

    # -----------------------------------------------------------
    def contar(self, comportamento):
        return sum(1 for c in self.jogo.criaturas if c.comportamento == comportamento)

    def limite_monstros(self):
        return min(14, MAX_MONSTROS_BASE + self.jogo.dia - 1)

    def lugar_livre(self, ch, rng):
        """Sorteia um bloco andável dentro do chunk (ou None)."""
        mundo = self.jogo.mundo
        for _ in range(8):
            i, j = rng.randrange(CH), rng.randrange(CH)
            tx, ty = ch.cx * CH + i, ch.cy * CH + j
            if ch.chao[j * CH + i] in CHAO_AGUA or ch.chao[j * CH + i] == LAMA:
                continue
            if (tx, ty) in ch.objetos and ch.objetos[(tx, ty)].solido:
                continue
            x, y = tx * TILE + 8, ty * TILE + 12
            c = Criatura("coelho", x, y)
            if not mundo.colide(c.retangulo()):
                return x, y
        return None

    # -----------------------------------------------------------
    def ao_carregar_chunk(self, ch):
        """Animais iniciais de um chunk recém-carregado (sorteio fixo pela semente)."""
        if self.contar("passivo") >= MAX_PASSIVOS:
            return
        rng = random.Random(numero_chunk(self.jogo.mundo.semente, ch.cx, ch.cy) + 7)
        bioma = ch.biomas[CH * CH // 2]
        animais = BIOMAS[bioma]["animais"]
        if not animais or rng.random() < 0.45:
            return
        especie = rng.choice(animais)
        for _ in range(rng.randint(1, 3)):        # vêm em grupinhos
            lugar = self.lugar_livre(ch, rng)
            if lugar:
                self.jogo.criaturas.append(Criatura(especie, *lugar))

    # -----------------------------------------------------------
    def atualizar(self, dt):
        jogo = self.jogo
        j = jogo.jogador
        noite = jogo.e_noite()
        dia_claro = jogo.nivel_escuridao() < 0.2

        # --- nascimentos ---
        self.tempo_spawn -= dt
        if self.tempo_spawn <= 0:
            self.tempo_spawn = TEMPO_ENTRE_SPAWNS
            self.tentar_spawn(noite)

        # --- filhotes ---
        for c in list(jogo.criaturas):
            if c.comportamento == "passivo" and c.reproduzir <= 0:
                c.reproduzir = random.uniform(90, 160)
                par = any(o is not c and o.tipo == c.tipo and math.hypot(o.x - c.x, o.y - c.y) < 48
                          for o in jogo.criaturas)
                chunk_c = chunk_do_bloco(int(c.x // TILE), int(c.y // TILE))
                no_chunk = sum(1 for o in jogo.criaturas if o.tipo == c.tipo and
                               chunk_do_bloco(int(o.x // TILE), int(o.y // TILE)) == chunk_c)
                if par and no_chunk < MAX_POR_CHUNK and self.contar("passivo") < MAX_PASSIVOS:
                    filhote = Criatura(c.tipo, c.x + random.uniform(-6, 6), c.y + random.uniform(-4, 4))
                    if not jogo.mundo.colide(filhote.retangulo()):
                        jogo.criaturas.append(filhote)

        # --- quem some ---
        fogueiras = jogo.mundo.lista_fogueiras()
        vivas = []
        for c in jogo.criaturas:
            if c.morta:
                continue
            if c.vida <= 0:
                jogo.criatura_morreu(c)
                continue
            tx, ty = int(c.x // TILE), int(c.y // TILE)
            if jogo.mundo.chunk(tx, ty) is None:
                continue                                  # chunk foi descarregado
            longe = math.hypot(c.x - j.x, c.y - j.y)
            if CRIATURAS[c.tipo].get("noturno"):
                if c.tipo == "slime" and dia_claro:
                    c.vida -= dt * 0.8                    # o sol derrete os slimes
                elif dia_claro and longe > 200:
                    continue                              # aranhas vão embora de dia
                # o fogo queima monstros noturnos
                for f in fogueiras:
                    if math.hypot(c.x - f.centro[0], c.y - f.centro[1]) < RAIO_LUZ_FOGUEIRA * 0.6:
                        c.vida -= dt * 1.5
                        c.piscar = 0.05
            vivas.append(c)
        jogo.criaturas = vivas

    def tentar_spawn(self, noite):
        jogo = self.jogo
        j = jogo.jogador
        # escolhe um chunk carregado que não esteja colado no jogador
        pcx, pcy = chunk_do_bloco(int(j.x // TILE), int(j.y // TILE))
        candidatos = [ch for (cx, cy), ch in jogo.mundo.chunks.items()
                      if 1 <= max(abs(cx - pcx), abs(cy - pcy)) <= 2]
        if not candidatos:
            return
        ch = random.choice(candidatos)
        bioma = ch.biomas[CH * CH // 2]
        info = BIOMAS[bioma]
        sorteio = random.random()
        especie = None
        if noite and info["noturnos"] and sorteio < 0.75 and self.contar("monstro") < self.limite_monstros():
            especie = random.choice(info["noturnos"])
        elif info["predadores"] and sorteio < 0.12 and self.contar("predador") < MAX_PREDADORES:
            especie = random.choice(info["predadores"])
        elif not noite and info["animais"] and sorteio < 0.6 and self.contar("passivo") < MAX_PASSIVOS:
            especie = random.choice(info["animais"])
        if especie is None:
            return
        if CRIATURAS[especie]["comportamento"] == "monstro" and self.contar("monstro") >= self.limite_monstros():
            return
        lugar = self.lugar_livre(ch, random)
        if not lugar:
            return
        x, y = lugar
        if math.hypot(x - j.x, y - j.y) < 150:
            return                                        # não nasce na cara do jogador
        if CRIATURAS[especie].get("noturno"):
            for f in jogo.mundo.lista_fogueiras():
                if math.hypot(x - f.centro[0], y - f.centro[1]) < RAIO_LUZ_FOGUEIRA * 1.2:
                    return
        jogo.criaturas.append(Criatura(especie, x, y))
