# -*- coding: utf-8 -*-
"""
entidades.py - Coisas que se mexem ou que o jogador carrega:
inventário (com equipamentos), jogador, itens no chão e criaturas.
"""
import math
import random
import pygame

from config import (VELOCIDADE_JOGADOR, VIDA_MAX, FOME_MAX, SEDE_MAX, TILE,
                    TAMANHO_INVENTARIO, TAMANHO_BARRA, AGUA_RASA, CHAO_AGUA,
                    RAIO_IMA_ITENS, TEMPO_SUMIR_ITEM)
from dados import ITENS, CRIATURAS, ORDEM_SLOTS


# ===============================================================
# Inventário: 36 espaços (0-8 = barra rápida) + 4 equipamentos
# ===============================================================
class Inventario:
    def __init__(self):
        self.espacos = [None] * TAMANHO_INVENTARIO      # None ou [item, quantidade]
        self.equipamento = {slot: None for slot in ORDEM_SLOTS}
        self.selecionado = 0                             # espaço da barra (0-8)

    # ----- consultas -----
    def quantidade(self, item):
        return sum(e[1] for e in self.espacos if e and e[0] == item)

    def tem(self, item, qtd=1):
        return self.quantidade(item) >= qtd

    def item_selecionado(self):
        e = self.espacos[self.selecionado]
        return e[0] if e else None

    # ----- mudar -----
    def adicionar(self, item, qtd=1):
        """Adiciona itens (barra primeiro). Retorna quanto NÃO coube."""
        pilha = ITENS[item]["pilha"]
        for e in self.espacos:
            if e and e[0] == item and e[1] < pilha:
                cabe = min(qtd, pilha - e[1])
                e[1] += cabe
                qtd -= cabe
                if qtd == 0:
                    return 0
        for i, e in enumerate(self.espacos):
            if e is None:
                cabe = min(qtd, pilha)
                self.espacos[i] = [item, cabe]
                qtd -= cabe
                if qtd == 0:
                    return 0
        return qtd

    def remover(self, item, qtd=1):
        if not self.tem(item, qtd):
            return False
        # tira primeiro do selecionado, depois do resto
        ordem = [self.selecionado] + [i for i in range(len(self.espacos)) if i != self.selecionado]
        for i in ordem:
            e = self.espacos[i]
            if e and e[0] == item:
                tira = min(qtd, e[1])
                e[1] -= tira
                qtd -= tira
                if e[1] == 0:
                    self.espacos[i] = None
                if qtd == 0:
                    break
        return True

    # ----- acesso genérico (usado pelo arrastar-e-soltar) -----
    def pegar(self, ref):
        tipo, chave = ref
        return self.espacos[chave] if tipo == "inv" else self.equipamento[chave]

    def por(self, ref, valor):
        tipo, chave = ref
        if tipo == "inv":
            self.espacos[chave] = valor
        else:
            self.equipamento[chave] = valor

    @staticmethod
    def cabe_no(ref, pilha):
        """Esse item pode ir para esse espaço? (equipamento só aceita o tipo certo)"""
        if pilha is None or ref[0] == "inv":
            return True
        return ITENS[pilha[0]].get("slot") == ref[1]

    def equipar(self, indice):
        """Equipa o item do espaço 'indice' (troca com o que estava equipado)."""
        e = self.espacos[indice]
        if not e or "slot" not in ITENS[e[0]]:
            return False
        slot = ITENS[e[0]]["slot"]
        self.espacos[indice], self.equipamento[slot] = self.equipamento[slot], e
        return True

    def desequipar(self, slot):
        e = self.equipamento[slot]
        if e is None:
            return True
        for i in range(TAMANHO_BARRA, len(self.espacos)):
            if self.espacos[i] is None:
                self.espacos[i] = e
                self.equipamento[slot] = None
                return True
        for i in range(TAMANHO_BARRA):
            if self.espacos[i] is None:
                self.espacos[i] = e
                self.equipamento[slot] = None
                return True
        return False

    # ----- atributos -----
    def _itens_ativos(self):
        """Equipados + o item escolhido na barra (vale como 'na mão')."""
        ativos = [e[0] for e in self.equipamento.values() if e]
        mao = self.item_selecionado()
        if mao:
            ativos.append(mao)
        return ativos

    def dano(self):
        return 1 + max([ITENS[i].get("dano", 0) for i in self._itens_ativos()] + [0])

    def defesa(self):
        return sum(ITENS[e[0]].get("defesa", 0) for e in self.equipamento.values() if e)

    def poder_ferramenta(self, tipo):
        """Poder da melhor ferramenta desse tipo (equipada ou na mão). 1 = mão vazia."""
        melhor = 1
        for i in self._itens_ativos():
            f = ITENS[i].get("ferramenta")
            if f and f[0] == tipo:
                melhor = max(melhor, f[1])
        return melhor

    def para_dict(self):
        return {"espacos": [list(e) if e else None for e in self.espacos],
                "equipamento": {k: (list(v) if v else None) for k, v in self.equipamento.items()},
                "selecionado": self.selecionado}

    def carregar_dict(self, d):
        esp = d.get("espacos", [])
        self.espacos = [(list(e) if e and e[0] in ITENS else None) for e in esp][:TAMANHO_INVENTARIO]
        self.espacos += [None] * (TAMANHO_INVENTARIO - len(self.espacos))
        for k in ORDEM_SLOTS:
            v = d.get("equipamento", {}).get(k)
            self.equipamento[k] = list(v) if v and v[0] in ITENS else None
        self.selecionado = d.get("selecionado", 0) % TAMANHO_BARRA


# ===============================================================
# Movimento com colisão
# ===============================================================
def mover_com_colisao(ent, dx, dy, mundo):
    """Move X e Y separados (desliza nas paredes). Se já estiver preso, deixa sair."""
    preso = mundo.colide(ent.retangulo())
    if dx:
        ent.x += dx
        if not preso and mundo.colide(ent.retangulo()):
            ent.x -= dx
    if dy:
        ent.y += dy
        if not preso and mundo.colide(ent.retangulo()):
            ent.y -= dy


# ===============================================================
# Jogador
# ===============================================================
class Jogador:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direcao = "baixo"
        self.andando = False
        self.tempo_anim = 0.0
        self.vida = VIDA_MAX
        self.fome = FOME_MAX
        self.sede = SEDE_MAX
        self.inventario = Inventario()
        self.espera_coleta = 0.0
        self.espera_ataque = 0.0
        self.espera_construir = 0.0
        self.invencivel = 0.0
        self.tempo_golpe = 0.0
        self.na_agua = False

    def retangulo(self):
        return pygame.Rect(int(self.x - 4), int(self.y - 5), 8, 5)

    @property
    def centro(self):
        return (self.x, self.y - 6)

    def ponto_frente(self, distancia=10):
        cx, cy = self.centro
        dx, dy = {"baixo": (0, 1), "cima": (0, -1), "esquerda": (-1, 0), "direita": (1, 0)}[self.direcao]
        return (cx + dx * distancia, cy + dy * distancia)

    def olhar_para(self, px, py):
        dx, dy = px - self.centro[0], py - self.centro[1]
        if abs(dx) > abs(dy):
            self.direcao = "direita" if dx > 0 else "esquerda"
        elif dy or dx:
            self.direcao = "baixo" if dy > 0 else "cima"

    def atualizar(self, dt, teclas, mundo):
        dx = dy = 0.0
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += 1
        self.andando = bool(dx or dy)
        self.na_agua = mundo.tipo_chao(int(self.x // TILE), int((self.y - 2) // TILE)) == AGUA_RASA
        if self.andando:
            if dx > 0:
                self.direcao = "direita"
            elif dx < 0:
                self.direcao = "esquerda"
            elif dy > 0:
                self.direcao = "baixo"
            else:
                self.direcao = "cima"
            vel = VELOCIDADE_JOGADOR * (0.6 if self.na_agua else 1.0) * dt / math.hypot(dx, dy)
            mover_com_colisao(self, dx * vel, dy * vel, mundo)
            self.tempo_anim += dt
        else:
            self.tempo_anim = 0.0
        for nome in ("espera_coleta", "espera_ataque", "invencivel", "tempo_golpe", "espera_construir"):
            setattr(self, nome, max(0.0, getattr(self, nome) - dt))

    def quadro_atual(self):
        return 0 if not self.andando else 1 + int(self.tempo_anim * 8) % 2

    def levar_dano(self, dano):
        """Dano reduzido pela armadura. Retorna o dano real (0 se estava invencível)."""
        if self.invencivel > 0:
            return 0
        reducao = min(0.7, self.inventario.defesa() * 0.07)
        real = max(1, round(dano * (1 - reducao)))
        self.vida = max(0.0, self.vida - real)
        self.invencivel = 0.8
        return real

    def para_dict(self):
        return {"x": self.x, "y": self.y, "direcao": self.direcao, "vida": self.vida,
                "fome": self.fome, "sede": self.sede, "inventario": self.inventario.para_dict()}

    def carregar_dict(self, d):
        self.x, self.y = d["x"], d["y"]
        self.direcao = d.get("direcao", "baixo")
        self.vida = d.get("vida", VIDA_MAX)
        self.fome = d.get("fome", FOME_MAX)
        self.sede = d.get("sede", SEDE_MAX)
        self.inventario.carregar_dict(d.get("inventario", {}))


# ===============================================================
# Item caído no chão
# ===============================================================
class ItemChao:
    def __init__(self, item, x, y, quantidade=1, pular=True, vx=None, vy=None):
        self.item = item
        self.quantidade = quantidade
        self.x = x
        self.y = y
        self.z = 0.0
        self.idade = 0.0
        if pular:
            ang = random.uniform(0, math.tau)
            vel = random.uniform(18, 40)
            self.vx = math.cos(ang) * vel if vx is None else vx
            self.vy = math.sin(ang) * vel * 0.7 if vy is None else vy
            self.vz = random.uniform(70, 100)
        else:
            self.vx = self.vy = self.vz = 0.0

    @property
    def pode_pegar(self):
        return self.idade > 0.45

    def atualizar(self, dt, jogador, mundo):
        """Retorna True se o item deve sumir."""
        self.idade += dt
        if self.z > 0 or self.vz > 0:
            self.vz -= 320 * dt
            self.z += self.vz * dt
            if self.z <= 0:
                self.z = 0.0
                self.vz = -self.vz * 0.45 if abs(self.vz) > 25 else 0.0
        if abs(self.vx) + abs(self.vy) > 0.5:
            nx, ny = self.x + self.vx * dt, self.y + self.vy * dt
            agua_aqui = mundo.tipo_chao(int(self.x // TILE), int(self.y // TILE)) in CHAO_AGUA
            if not agua_aqui and mundo.tipo_chao(int(nx // TILE), int(ny // TILE)) in CHAO_AGUA:
                self.vx = self.vy = 0.0
            else:
                self.x, self.y = nx, ny
            atrito = 0.90 if self.z <= 0 else 0.99
            self.vx *= atrito
            self.vy *= atrito
        if self.pode_pegar:
            dx, dy = jogador.x - self.x, (jogador.y - 4) - self.y
            d = math.hypot(dx, dy)
            if 0 < d < RAIO_IMA_ITENS:
                passo = min(d, (40 + (RAIO_IMA_ITENS - d) * 8) * dt)
                self.x += dx / d * passo
                self.y += dy / d * passo
        return self.idade > TEMPO_SUMIR_ITEM

    def distancia_jogador(self, jogador):
        return math.hypot(jogador.x - self.x, (jogador.y - 4) - self.y)

    def para_dict(self):
        return {"i": self.item, "q": self.quantidade, "x": round(self.x, 1),
                "y": round(self.y, 1), "a": round(self.idade, 1)}

    @staticmethod
    def de_dict(d):
        it = ItemChao(d["i"], d["x"], d["y"], d.get("q", 1), pular=False)
        it.idade = d.get("a", 1.0)
        return it


# ===============================================================
# Criaturas (animais, predadores e monstros)
# ===============================================================
class Criatura:
    def __init__(self, tipo, x, y):
        self.tipo = tipo
        self.info = CRIATURAS[tipo]
        self.x = x
        self.y = y
        self.vida = self.info["vida"]
        self.olhando = random.choice(("direita", "esquerda"))
        self.tempo_anim = random.random()
        self.andando = False
        self.estado = "vagar"         # vagar, fugir, perseguir, beber
        self.tempo_estado = 0.0
        self.direcao = (0.0, 0.0)
        self.alvo = None
        self.empurrao = [0.0, 0.0]
        self.piscar = 0.0
        self.espera_ataque = 0.0
        self.sede = random.uniform(30, 90)              # segundos até sentir sede
        self.reproduzir = random.uniform(60, 140)       # segundos até poder ter filhote
        self.morta = False

    @property
    def comportamento(self):
        return self.info["comportamento"]

    def retangulo(self):
        return pygame.Rect(int(self.x - 5), int(self.y - 5), 10, 5)

    @property
    def centro(self):
        return (self.x, self.y - 5)

    def quadro(self):
        return int(self.tempo_anim * 6) % 2 if self.andando else 0

    def levar_golpe(self, dano, de_x, de_y):
        self.vida -= dano
        self.piscar = 0.15
        dx, dy = self.x - de_x, self.y - de_y
        d = math.hypot(dx, dy) or 1.0
        self.empurrao = [dx / d * 150, dy / d * 150]
        if self.comportamento == "passivo":
            self.estado = "fugir"
            self.tempo_estado = 2.5
            self.direcao = (dx / d, dy / d)

    # -----------------------------------------------------------
    def atualizar(self, dt, jogo):
        mundo = jogo.mundo
        self.tempo_anim += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.espera_ataque = max(0.0, self.espera_ataque - dt)
        self.tempo_estado -= dt
        self.sede -= dt
        self.reproduzir -= dt

        # empurrão depois de levar golpe
        if abs(self.empurrao[0]) + abs(self.empurrao[1]) > 2:
            mover_com_colisao(self, self.empurrao[0] * dt, self.empurrao[1] * dt, mundo)
            self.empurrao[0] *= 0.85
            self.empurrao[1] *= 0.85
            return

        vel = self.info["velocidade"]
        if self.comportamento == "passivo":
            self._pensar_passivo(jogo)
        else:
            self._pensar_cacador(jogo)

        if self.estado == "fugir":
            vel *= 1.7
        elif self.estado == "vagar":
            vel *= 0.4
        elif self.estado == "beber" and self.alvo is None:
            vel = 0
        # slimes andam pulando
        if self.tipo == "slime" and (self.tempo_anim * 2.5) % 1.0 > 0.6:
            vel = 0
        dx, dy = self.direcao
        self.andando = vel > 0 and (dx or dy)
        if self.andando:
            ax, ay = self.x, self.y
            mover_com_colisao(self, dx * vel * dt, dy * vel * dt, mundo)
            if abs(self.x - ax) + abs(self.y - ay) < 0.01 and self.estado == "vagar":
                self.tempo_estado = 0     # bateu em algo: escolhe outro caminho
            if dx > 0.1:
                self.olhando = "direita"
            elif dx < -0.1:
                self.olhando = "esquerda"

    def _rumo(self, x, y, fugir=False):
        dx, dy = x - self.x, y - self.y
        d = math.hypot(dx, dy) or 1.0
        if fugir:
            dx, dy = -dx, -dy
        self.direcao = (dx / d, dy / d)
        return d

    def _vagar(self):
        if self.tempo_estado <= 0:
            self.estado = "vagar"
            if random.random() < 0.4:
                self.direcao = (0.0, 0.0)          # fica parado um pouco
            else:
                ang = random.uniform(0, math.tau)
                self.direcao = (math.cos(ang), math.sin(ang))
            self.tempo_estado = random.uniform(1.0, 3.5)

    def _pensar_passivo(self, jogo):
        j = jogo.jogador
        # perigo: jogador correndo perto ou um lobo
        perigo = None
        dj = math.hypot(j.x - self.x, j.y - self.y)
        if dj < (44 if j.andando else 20):
            perigo = (j.x, j.y)
        for c in jogo.criaturas:
            if c.tipo == "lobo" and math.hypot(c.x - self.x, c.y - self.y) < 70:
                perigo = (c.x, c.y)
                break
        if perigo:
            self.estado = "fugir"
            self.tempo_estado = 1.5
            self._rumo(*perigo, fugir=True)
            return
        if self.estado == "fugir" and self.tempo_estado > 0:
            return
        # sede: procura água e fica bebendo
        if self.estado == "beber":
            if self.alvo:
                ax, ay = self.alvo
                if self._rumo(ax, ay) < 10:
                    self.alvo = None
                    self.tempo_estado = 2.5
                    self.direcao = (0.0, 0.0)
                elif self.tempo_estado <= 0:
                    self.alvo = None
            elif self.tempo_estado <= 0:
                self.sede = random.uniform(40, 90)
                self.estado = "vagar"
            return
        if self.sede <= 0:
            agua = jogo.mundo.agua_mais_proxima(self.x, self.y, 6)
            if agua:
                self.estado = "beber"
                self.alvo = (agua[0] * TILE + 8, agua[1] * TILE + 8)
                self.tempo_estado = 8.0
                return
            self.sede = 30
        self._vagar()

    def _pensar_cacador(self, jogo):
        j = jogo.jogador
        alcance = self.info.get("alcance", 120)
        alvo = None
        dj = math.hypot(j.x - self.x, j.y - self.y)
        if dj < alcance and j.vida > 0:
            alvo = j
        if self.tipo == "lobo":
            # lobo prefere caçar animais (se estiverem mais perto que o jogador)
            melhor = dj if alvo else alcance
            for c in jogo.criaturas:
                if c.comportamento == "passivo":
                    d = math.hypot(c.x - self.x, c.y - self.y)
                    if d < melhor:
                        alvo, melhor = c, d
        if alvo is None:
            self._vagar()
            return
        self.estado = "perseguir"
        d = self._rumo(alvo.x, alvo.y)
        if d < 11 and self.espera_ataque <= 0:
            self.espera_ataque = 1.0
            if alvo is j:
                jogo.jogador_atacado(self)
            else:
                alvo.levar_golpe(self.info.get("dano", 5), self.x, self.y)
                if alvo.vida <= 0:
                    alvo.morta = True     # o lobo comeu (não solta nada)
