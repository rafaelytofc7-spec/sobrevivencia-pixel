# -*- coding: utf-8 -*-
"""
entidades.py - Coisas que se mexem ou que o jogador carrega:
inventário (com equipamentos), jogador, itens no chão e criaturas.
"""
import math
import random
import pygame

from config import (VELOCIDADE_JOGADOR, VIDA_MAX, FOME_MAX, SEDE_MAX, TILE,
                    TAMANHO_INVENTARIO, TAMANHO_BARRA, AGUA_RASA, AGUA_FUNDA, CHAO_AGUA,
                    RAIO_IMA_ITENS, TEMPO_SUMIR_ITEM, ACELERACAO, ATRITO, MULT_CORRIDA,
                    MULT_AGUA_RASA, MULT_NADANDO, ENERGIA_MAX, GASTO_CORRIDA, GASTO_ROLAR,
                    REGEN_ENERGIA, ESPERA_REGEN_ENERGIA, GASTO_NADO, DURACAO_ROLAR,
                    VELOCIDADE_ROLAR, AR_MAX, GASTO_AR, REGEN_AR, DANO_AFOGAR, CANTO_DESLIZE)
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
    def adicionar(self, item, qtd=1, usos=None):
        """Adiciona itens (barra primeiro). Retorna quanto NÃO coube.
        usos: durabilidade que sobra (ferramentas); None = nova."""
        pilha = ITENS[item]["pilha"]
        maximo = ITENS[item].get("durabilidade")
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
                self.espacos[i] = [item, cabe] if not maximo else [item, cabe, usos if usos is not None else maximo]
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
def mover_com_colisao(ent, dx, dy, mundo, deslizar=False, agua=True):
    """Move X e Y separados (desliza nas paredes). Se já estiver preso, deixa sair.
    deslizar=True: ao bater numa quina, empurra de lado para contornar (correção de quina).
    agua=False: água funda não bloqueia (o jogador nada)."""
    def bate():
        return mundo.colide(ent.retangulo(), agua)

    preso = bate()
    bloqueou_x = bloqueou_y = False
    if dx:
        ent.x += dx
        if not preso and bate():
            ent.x -= dx
            bloqueou_x = True
    if dy:
        ent.y += dy
        if not preso and bate():
            ent.y -= dy
            bloqueou_y = True
    if deslizar and not preso:
        if bloqueou_x and abs(dy) < 1e-6:
            _contornar_quina(ent, dx, "x", bate)
        elif bloqueou_y and abs(dx) < 1e-6:
            _contornar_quina(ent, dy, "y", bate)
    return bloqueou_x, bloqueou_y


def _contornar_quina(ent, passo, eixo, bate):
    """Procura o menor desvio lateral (até CANTO_DESLIZE px) que deixa passar e anda um pouco para lá."""
    lado = "y" if eixo == "x" else "x"
    for k in range(1, CANTO_DESLIZE + 1):
        for sinal in (-1, 1):
            setattr(ent, lado, getattr(ent, lado) + sinal * k)
            setattr(ent, eixo, getattr(ent, eixo) + passo)
            livre = not bate()
            setattr(ent, eixo, getattr(ent, eixo) - passo)
            setattr(ent, lado, getattr(ent, lado) - sinal * k)
            if livre:
                desvio = sinal * min(abs(passo), k)
                setattr(ent, lado, getattr(ent, lado) + desvio)
                if bate():
                    setattr(ent, lado, getattr(ent, lado) - desvio)
                return True
    return False


# ===============================================================
# Jogador
# ===============================================================
DURACAO_GOLPE = 0.24


class Jogador:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.direcao = "baixo"
        self.andando = False
        self.correndo = False
        self.tempo_anim = 0.0
        self.vida = VIDA_MAX
        self.fome = FOME_MAX
        self.sede = SEDE_MAX
        self.energia = ENERGIA_MAX
        self.ar = AR_MAX
        self.espera_energia = 0.0
        self.inventario = Inventario()
        self.espera_coleta = 0.0
        self.espera_ataque = 0.0
        self.espera_construir = 0.0
        self.invencivel = 0.0
        self.tempo_golpe = 0.0
        self.rolando = 0.0
        self.espera_rolar = 0.0
        self.dir_rolar = (0.0, 1.0)
        self.na_agua = False          # água rasa ou funda
        self.nadando = False          # água funda
        self.saturacao = 5.0          # [v0.5] fome "escondida": gasta antes da barra de fome
        self.exaustao = 0.0           # [v0.5] cansaço acumulado (correr, minerar, lutar...)
        self.xp = 0                   # [v0.5] pontos de experiência
        self.tempo_regen = 0.0
        self.ultimo_input = (0.0, 1.0)

    def retangulo(self):
        return pygame.Rect(int(self.x - 4), int(self.y - 5), 8, 5)

    @property
    def centro(self):
        return (self.x, self.y - 6)

    VETORES = {"baixo": (0, 1), "cima": (0, -1), "esquerda": (-1, 0), "direita": (1, 0)}

    def ponto_frente(self, distancia=10):
        cx, cy = self.centro
        dx, dy = self.VETORES[self.direcao]
        return (cx + dx * distancia, cy + dy * distancia)

    def olhar_para(self, px, py):
        dx, dy = px - self.centro[0], py - self.centro[1]
        if abs(dx) > abs(dy):
            self.direcao = "direita" if dx > 0 else "esquerda"
        elif dy or dx:
            self.direcao = "baixo" if dy > 0 else "cima"

    def _direcao_do_vetor(self, dx, dy):
        if abs(dx) > abs(dy) + 0.01:
            self.direcao = "direita" if dx > 0 else "esquerda"
        elif dy:
            self.direcao = "baixo" if dy > 0 else "cima"

    def pode_usar_ferramentas(self):
        return not self.nadando and self.rolando <= 0

    def rolar(self):
        """Rolamento/esquiva: rápido, invencível por um instante, gasta energia."""
        if self.rolando > 0 or self.espera_rolar > 0 or self.nadando or self.energia < GASTO_ROLAR * 0.5:
            return False
        dx, dy = self.ultimo_input if self.andando else self.VETORES[self.direcao]
        d = math.hypot(dx, dy) or 1.0
        self.dir_rolar = (dx / d, dy / d)
        self.rolando = DURACAO_ROLAR
        self.espera_rolar = DURACAO_ROLAR + 0.25
        self.energia = max(0.0, self.energia - GASTO_ROLAR)
        self.espera_energia = ESPERA_REGEN_ENERGIA
        return True

    def atualizar(self, dt, entrada, mundo):
        """entrada: dict com mx, my (-1..1), correr (bool), mira (ponto do mundo ou None)."""
        mx, my = entrada.get("mx", 0.0), entrada.get("my", 0.0)
        tam = math.hypot(mx, my)
        if tam > 1:
            mx, my = mx / tam, my / tam
            tam = 1.0
        chao = mundo.tipo_chao(int(self.x // TILE), int((self.y - 2) // TILE))
        self.nadando = chao == AGUA_FUNDA
        self.na_agua = chao in CHAO_AGUA
        self.andando = tam > 0.05
        if self.andando:
            self.ultimo_input = (mx, my)

        # velocidade desejada
        mult = MULT_NADANDO if self.nadando else (MULT_AGUA_RASA if self.na_agua else 1.0)
        self.correndo = bool(entrada.get("correr")) and self.andando and not self.nadando and self.energia > 1
        if self.correndo:
            mult *= MULT_CORRIDA
        if self.rolando > 0:
            vel = VELOCIDADE_ROLAR * (MULT_AGUA_RASA if self.na_agua else 1.0)
            self.vx, self.vy = self.dir_rolar[0] * vel, self.dir_rolar[1] * vel
        else:
            alvo_x, alvo_y = mx * VELOCIDADE_JOGADOR * mult, my * VELOCIDADE_JOGADOR * mult
            taxa = (ACELERACAO if self.andando else ATRITO) * dt
            if self.nadando:
                taxa *= 0.5                      # na água tudo é mais "mole"
            dvx, dvy = alvo_x - self.vx, alvo_y - self.vy
            d = math.hypot(dvx, dvy)
            if d <= taxa:
                self.vx, self.vy = alvo_x, alvo_y
            else:
                self.vx += dvx / d * taxa
                self.vy += dvy / d * taxa

        if abs(self.vx) + abs(self.vy) > 0.01:
            bx, by = mover_com_colisao(self, self.vx * dt, self.vy * dt, mundo, deslizar=True, agua=False)
            if bx:
                self.vx *= 0.3
            if by:
                self.vy *= 0.3
        rapidez = math.hypot(self.vx, self.vy)

        # para onde olha: andando = direção do movimento; parado = para a mira (mouse)
        if self.rolando <= 0:
            if self.andando:
                self._direcao_do_vetor(mx, my)
            elif entrada.get("mira") is not None and self.tempo_golpe <= 0:
                self.olhar_para(*entrada["mira"])

        # energia e ar
        gastou = False
        if self.correndo and rapidez > 5:
            self.energia = max(0.0, self.energia - GASTO_CORRIDA * dt)
            gastou = True
        if self.nadando:
            self.energia = max(0.0, self.energia - GASTO_NADO * dt)
            gastou = True
            self.ar = max(0.0, self.ar - GASTO_AR * dt * (1.6 if self.energia <= 0 else 1.0))
            if self.ar <= 0:
                self.vida = max(0.0, self.vida - DANO_AFOGAR * dt)
        else:
            self.ar = min(AR_MAX, self.ar + REGEN_AR * dt)
        if gastou:
            self.espera_energia = ESPERA_REGEN_ENERGIA
        elif self.espera_energia > 0:
            self.espera_energia -= dt
        else:
            self.energia = min(ENERGIA_MAX, self.energia + REGEN_ENERGIA * dt)

        self.tempo_anim += dt * (1.5 if self.correndo else 1.0)
        for nome in ("espera_coleta", "espera_ataque", "invencivel", "tempo_golpe", "espera_construir",
                     "rolando", "espera_rolar"):
            setattr(self, nome, max(0.0, getattr(self, nome) - dt))
        self.rapidez = rapidez

    # ----- animação -----
    def animacao(self):
        """(nome da animação, quadro)."""
        if self.rolando > 0:
            q = int((DURACAO_ROLAR - self.rolando) / DURACAO_ROLAR * 4)
            return "rolar", min(3, q)
        if self.nadando:
            return "nadar", int(self.tempo_anim * 3) % 2
        if self.tempo_golpe > 0:
            q = int((DURACAO_GOLPE - self.tempo_golpe) / DURACAO_GOLPE * 3)
            return "atacar", max(0, min(2, q))
        if getattr(self, "rapidez", 0) > 8:
            return "andar", int(self.tempo_anim * 9) % 4
        return "parado", int(self.tempo_anim * 1.5) % 2

    def quadro_atual(self):
        return self.animacao()[1]

    def levar_dano(self, dano):
        """Dano reduzido pela armadura. Retorna o dano real (0 se estava invencível/rolando)."""
        if self.invencivel > 0 or self.rolando > 0:
            return 0
        reducao = min(0.7, self.inventario.defesa() * 0.07)
        real = max(1, round(dano * (1 - reducao)))
        self.vida = max(0.0, self.vida - real)
        self.invencivel = 0.8
        return real

    def para_dict(self):
        return {"x": self.x, "y": self.y, "direcao": self.direcao, "vida": self.vida,
                "fome": self.fome, "sede": self.sede, "energia": self.energia, "ar": self.ar,
                "saturacao": round(self.saturacao, 2), "exaustao": round(self.exaustao, 2), "xp": self.xp,
                "inventario": self.inventario.para_dict()}

    def carregar_dict(self, d):
        self.x, self.y = d["x"], d["y"]
        self.direcao = d.get("direcao", "baixo")
        self.vida = d.get("vida", VIDA_MAX)
        self.fome = d.get("fome", FOME_MAX)
        self.sede = d.get("sede", SEDE_MAX)
        self.energia = d.get("energia", ENERGIA_MAX)
        self.ar = d.get("ar", AR_MAX)
        self.saturacao = d.get("saturacao", 5.0)
        self.exaustao = d.get("exaustao", 0.0)
        self.xp = int(d.get("xp", 0))
        self.inventario.carregar_dict(d.get("inventario", {}))


# ===============================================================
# Flecha (projétil do arco)
# ===============================================================
class Flecha:
    def __init__(self, x, y, dx, dy, dano, velocidade=210.0):
        d = math.hypot(dx, dy) or 1.0
        self.x, self.y = x, y
        self.vx, self.vy = dx / d * velocidade, dy / d * velocidade
        self.dano = dano
        self.vida = 0.9
        self.parada = False
        self.hostil = False           # [v0.5] flecha de esqueleto (acerta você)
        self.dono = None

    @property
    def angulo(self):
        return math.degrees(math.atan2(-self.vy, self.vx))

    def atualizar(self, dt, mundo):
        """Anda; retorna True se bateu em algo sólido (ou acabou o alcance)."""
        self.vida -= dt
        passos = 3
        for _ in range(passos):
            self.x += self.vx * dt / passos
            self.y += self.vy * dt / passos
            tx, ty = int(self.x // TILE), int((self.y + 4) // TILE)
            obj = mundo.objeto(tx, ty)
            if obj and obj.solido and obj.retangulo_colisao().inflate(0, 8).collidepoint(self.x, self.y + 4):
                return True
        return self.vida <= 0


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
        self.usos = None              # [v0.5] durabilidade de ferramenta jogada no chão
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
        d = {"i": self.item, "q": self.quantidade, "x": round(self.x, 1),
             "y": round(self.y, 1), "a": round(self.idade, 1)}
        if self.usos is not None:
            d["u"] = self.usos
        return d

    @staticmethod
    def de_dict(d):
        it = ItemChao(d["i"], d["x"], d["y"], d.get("q", 1), pular=False)
        it.idade = d.get("a", 1.0)
        it.usos = d.get("u")
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
            mover_com_colisao(self, dx * vel * dt, dy * vel * dt, mundo, deslizar=True)
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
        if self.tipo == "lobo":
            alcance *= getattr(jogo, "mult_caca_lobo", 1.0)       # inverno: lobos com mais fome
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
