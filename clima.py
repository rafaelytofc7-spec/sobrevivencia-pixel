# -*- coding: utf-8 -*-
"""
clima.py - Chuva e seca.

O clima alterna entre "normal", "chuva" e "seca". Cada um muda o
NÍVEL DA ÁGUA regional (um número somado ao nível base):
  - chuva: o nível sobe -> blocos rasos alagam, rios transbordam e ligam lagos
  - seca:  o nível desce -> a beira dos lagos vira lama
O nível muda devagar, então dá para ver os lagos crescendo/encolhendo.
"""
import random

from config import NIVEL_CHUVA, NIVEL_SECA, VELOCIDADE_NIVEL
from estacoes import PESOS_CLIMA

ALVO_NIVEL = {"normal": 0.0, "chuva": NIVEL_CHUVA, "seca": NIVEL_SECA}
NOMES_CLIMA = {"normal": "Tempo bom", "chuva": "Chuva", "seca": "Seca"}


class Clima:
    def __init__(self, semente):
        self.rng = random.Random(semente + 4242)
        self.estado = "normal"
        self.tempo_restante = self.rng.uniform(90, 160)
        self.nivel = 0.0          # deslocamento do nível da água
        self.chuva = 0.0          # 0..1 (intensidade visual da chuva)
        self.secura = 0.0         # 0..1 (intensidade visual da seca)
        self.estacao = "primavera"  # o jogo atualiza; muda a chance de chuva/seca

    def mudar(self, estado, duracao=None):
        self.estado = estado
        if duracao is None:
            duracao = self.rng.uniform(80, 150) if estado != "normal" else self.rng.uniform(100, 200)
        self.tempo_restante = duracao

    def atualizar(self, dt):
        self.tempo_restante -= dt
        if self.tempo_restante <= 0:
            if self.estado == "normal":
                chuva, seca = PESOS_CLIMA.get(self.estacao, (2.0, 1.0))
                self.mudar("chuva" if self.rng.random() * (chuva + seca) < chuva else "seca")
            else:
                self.mudar("normal")
        # o nível da água anda devagar até o alvo
        alvo = ALVO_NIVEL[self.estado]
        passo = VELOCIDADE_NIVEL * dt
        if abs(alvo - self.nivel) <= passo:
            self.nivel = alvo
        else:
            self.nivel += passo if alvo > self.nivel else -passo
        # efeitos visuais aparecem/somem suavemente
        self.chuva = _aproximar(self.chuva, 1.0 if self.estado == "chuva" else 0.0, dt * 0.4)
        self.secura = _aproximar(self.secura, 1.0 if self.estado == "seca" else 0.0, dt * 0.25)

    def nome(self):
        if self.estado == "chuva" and self.estacao == "inverno":
            return "Neve"
        return NOMES_CLIMA[self.estado]

    @property
    def nevando(self):
        return self.estacao == "inverno"

    def para_dict(self):
        return {"estado": self.estado, "tempo_restante": self.tempo_restante,
                "nivel": self.nivel, "chuva": self.chuva, "secura": self.secura}

    def carregar_dict(self, d):
        self.estado = d.get("estado", "normal")
        self.tempo_restante = d.get("tempo_restante", 120.0)
        self.nivel = d.get("nivel", 0.0)
        self.chuva = d.get("chuva", 0.0)
        self.secura = d.get("secura", 0.0)


def _aproximar(valor, alvo, passo):
    if abs(alvo - valor) <= passo:
        return alvo
    return valor + (passo if alvo > valor else -passo)
