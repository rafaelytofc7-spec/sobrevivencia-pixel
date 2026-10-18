# -*- coding: utf-8 -*-
"""
mobs.py - Monstros da v0.5 com jeito próprio:
- Zumbi: anda devagar até você e bate. Queima no sol.
- Esqueleto: mantém distância e atira flechas. Queima no sol.
- Explosivo: chega perto, chia (pisca) e EXPLODE, quebrando blocos em volta.
  Se você se afastar a tempo, ele desiste.
criar_criatura() escolhe a classe certa para cada espécie.
"""
import math
import random

from config import TILE
from dados import CRIATURAS
from entidades import Criatura, Flecha

PAVIO = 1.5            # segundos chiando antes de explodir
RAIO_EXPLOSAO = 2.3    # em blocos
DANO_EXPLOSAO = 48


class Arqueiro(Criatura):
    def __init__(self, tipo, x, y):
        super().__init__(tipo, x, y)
        self.espera_ataque = random.uniform(0.8, 2.0)

    def _pensar_cacador(self, jogo):
        j = jogo.jogador
        dj = math.hypot(j.x - self.x, j.y - self.y)
        if dj > self.info.get("alcance", 160) or j.vida <= 0:
            self._vagar()
            return
        self.estado = "perseguir"
        if dj < 56:
            self._rumo(j.x, j.y, fugir=True)          # muito perto: recua
        elif dj > 96:
            self._rumo(j.x, j.y)
        else:
            # de lado, rodeando o jogador
            dx, dy = (j.x - self.x) / dj, (j.y - self.y) / dj
            lado = 1 if int(self.tempo_anim / 2) % 2 else -1
            self.direcao = (-dy * lado * 0.6, dx * lado * 0.6)
        self.olhando = "direita" if j.x > self.x else "esquerda"
        if self.espera_ataque <= 0 and dj < 150 and _linha_livre(jogo.mundo, self.x, self.y - 6, j.x, j.y - 6):
            self.espera_ataque = random.uniform(1.8, 2.6)
            erro = random.uniform(-0.12, 0.12)
            ang = math.atan2(j.y - self.y, j.x - self.x) + erro
            f = Flecha(self.x, self.y - 7, math.cos(ang), math.sin(ang), self.info.get("dano", 6), velocidade=150.0)
            f.hostil = True
            f.dono = self
            jogo.flechas.append(f)


class Explosivo(Criatura):
    def __init__(self, tipo, x, y):
        super().__init__(tipo, x, y)
        self.pavio = 0.0

    def atualizar(self, dt, jogo):
        j = jogo.jogador
        dj = math.hypot(j.x - self.x, j.y - self.y)
        if self.pavio > 0:
            self.pavio += dt
            self.piscar = 0.05 if int(self.pavio * 8) % 2 == 0 else 0.0
            if dj > 46:
                self.pavio = 0.0                       # você fugiu: ele desiste
            elif self.pavio >= PAVIO:
                self.morta = True
                self.vida = 0
                if hasattr(jogo, "explosao"):
                    jogo.explosao(self.x, self.y - 4, RAIO_EXPLOSAO, DANO_EXPLOSAO)
                return
            self.tempo_anim += dt
            self.andando = False
            return
        super().atualizar(dt, jogo)
        if dj < 20 and j.vida > 0:
            self.pavio = 0.01
            if hasattr(jogo, "avisar"):
                jogo.avisar("Tsssss... (fuja!)", 1.2)

    def _pensar_cacador(self, jogo):
        j = jogo.jogador
        dj = math.hypot(j.x - self.x, j.y - self.y)
        if dj > self.info.get("alcance", 140) or j.vida <= 0:
            self._vagar()
            return
        self.estado = "perseguir"
        self._rumo(j.x, j.y)


def _linha_livre(mundo, x0, y0, x1, y1):
    d = math.hypot(x1 - x0, y1 - y0)
    passos = max(1, int(d / 6))
    for k in range(1, passos):
        x = x0 + (x1 - x0) * k / passos
        y = y0 + (y1 - y0) * k / passos
        o = mundo.objeto(int(x // TILE), int((y + 4) // TILE))
        if o is not None and o.solido and o.retangulo_colisao().collidepoint(x, y + 4):
            return False
    return True


def criar_criatura(tipo, x, y):
    info = CRIATURAS.get(tipo, {})
    if info.get("arqueiro"):
        return Arqueiro(tipo, x, y)
    if info.get("explode"):
        return Explosivo(tipo, x, y)
    return Criatura(tipo, x, y)
