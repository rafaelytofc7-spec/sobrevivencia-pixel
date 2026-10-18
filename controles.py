# -*- coding: utf-8 -*-
"""
controles.py - Teclas configuráveis e controle (gamepad).

Cada AÇÃO do jogo tem até duas teclas. As escolhas do jogador ficam em
controles.json (na pasta do jogo) e podem ser trocadas na tela "Controles".
O gamepad é opcional: se um estiver conectado, o analógico esquerdo anda,
e os botões fazem as ações (veja BOTOES_PADRAO).
"""
import json
import os

import pygame

from config import ARQUIVO_CONTROLES

# (ação, nome na tela, teclas padrão)
ACOES = [
    ("cima", "Andar para cima", [pygame.K_w, pygame.K_UP]),
    ("baixo", "Andar para baixo", [pygame.K_s, pygame.K_DOWN]),
    ("esquerda", "Andar para a esquerda", [pygame.K_a, pygame.K_LEFT]),
    ("direita", "Andar para a direita", [pygame.K_d, pygame.K_RIGHT]),
    ("correr", "Correr (gasta energia)", [pygame.K_LSHIFT, pygame.K_RSHIFT]),
    ("rolar", "Rolar / esquivar", [pygame.K_SPACE]),
    ("atacar", "Atacar (na direção do mouse)", [pygame.K_j]),
    ("interagir", "Interagir / beber / assar", [pygame.K_e]),
    ("comer", "Comer", [pygame.K_f]),
    ("inventario", "Inventário", [pygame.K_i, pygame.K_TAB]),
    ("criar", "Criação", [pygame.K_c]),
    ("minimapa", "Minimapa: tamanho", [pygame.K_m]),
    ("mapa", "Mapa completo", [pygame.K_n]),
    ("ajuda", "Ajuda", [pygame.K_h]),
    ("espiar", "Ver a camada de cima (cavernas)", [pygame.K_v]),
]
NOMES_ACOES = {a: n for a, n, _ in ACOES}
PADRAO = {a: list(t) for a, _, t in ACOES}

# botões do gamepad (layout Xbox: 0=A 1=B 2=X 3=Y 4=LB 5=RB 6=Back 7=Start)
BOTOES_PADRAO = {0: "interagir", 1: "rolar", 2: "atacar", 3: "inventario",
                 4: "barra_anterior", 5: "barra_proxima", 6: "mapa", 7: "pausa", 8: "comer", 9: "criar"}
ZONA_MORTA = 0.25


def nome_tecla(k):
    nome = pygame.key.name(k)
    traduz = {"space": "Espaço", "left shift": "Shift esq.", "right shift": "Shift dir.",
              "tab": "Tab", "up": "Seta cima", "down": "Seta baixo", "left": "Seta esq.",
              "right": "Seta dir.", "return": "Enter", "left ctrl": "Ctrl esq.",
              "right ctrl": "Ctrl dir.", "left alt": "Alt esq.", "escape": "Esc"}
    return traduz.get(nome, nome.upper() if len(nome) == 1 else nome.capitalize())


class Controles:
    def __init__(self, arquivo=ARQUIVO_CONTROLES):
        self.arquivo = arquivo
        self.teclas = {a: list(t) for a, t in PADRAO.items()}
        self.carregar()
        self.joystick = None
        self.procurar_gamepad()

    # ---------------- arquivo ----------------
    def carregar(self):
        try:
            with open(self.arquivo, "r", encoding="utf-8") as f:
                d = json.load(f)
            for a in self.teclas:
                if isinstance(d.get(a), list):
                    self.teclas[a] = [int(k) for k in d[a]][:2]
        except (OSError, ValueError, TypeError):
            pass

    def salvar(self):
        try:
            with open(self.arquivo, "w", encoding="utf-8") as f:
                json.dump(self.teclas, f)
        except OSError:
            pass

    def restaurar_padrao(self):
        self.teclas = {a: list(t) for a, t in PADRAO.items()}
        self.salvar()

    def definir(self, acao, tecla):
        """Troca a 1ª tecla da ação (tira a tecla de outras ações para não repetir)."""
        for a, ks in self.teclas.items():
            if a != acao and tecla in ks:
                ks.remove(tecla)
        ks = self.teclas[acao]
        if tecla in ks:
            ks.remove(tecla)
        ks.insert(0, tecla)
        del ks[2:]
        self.salvar()

    # ---------------- consultas ----------------
    def acao_da_tecla(self, tecla):
        for a, ks in self.teclas.items():
            if tecla in ks:
                return a
        return None

    def apertado(self, teclas, acao):
        try:
            return any(teclas[k] for k in self.teclas[acao])
        except IndexError:
            return False

    def texto(self, acao):
        ks = self.teclas.get(acao, [])
        return " / ".join(nome_tecla(k) for k in ks) if ks else "(nenhuma)"

    # ---------------- gamepad ----------------
    def procurar_gamepad(self):
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
        except pygame.error:
            self.joystick = None

    def _eixo(self, n):
        j = self.joystick
        if j is None or j.get_numaxes() <= n:
            return 0.0
        v = j.get_axis(n)
        return v if abs(v) > ZONA_MORTA else 0.0

    def movimento(self, teclas):
        """Vetor de movimento (-1..1) do teclado + analógico."""
        dx = (1 if self.apertado(teclas, "direita") else 0) - (1 if self.apertado(teclas, "esquerda") else 0)
        dy = (1 if self.apertado(teclas, "baixo") else 0) - (1 if self.apertado(teclas, "cima") else 0)
        if self.joystick is not None:
            dx += self._eixo(0)
            dy += self._eixo(1)
            if self.joystick.get_numhats() > 0:
                hx, hy = self.joystick.get_hat(0)
                dx += hx
                dy -= hy
        return max(-1.0, min(1.0, dx)), max(-1.0, min(1.0, dy))

    def mira_gamepad(self):
        """Direção do analógico direito (ou None)."""
        x, y = self._eixo(3), self._eixo(4)
        if abs(x) + abs(y) < 0.4:
            return None
        return x, y

    def correndo(self, teclas):
        if self.apertado(teclas, "correr"):
            return True
        j = self.joystick
        if j is not None:
            # gatilho esquerdo (LT, eixo 2: solto = -1, apertado = +1)
            if j.get_numaxes() > 2 and j.get_axis(2) > 0.3:
                return True
        return False

    def acao_do_botao(self, botao):
        return BOTOES_PADRAO.get(botao)
