# -*- coding: utf-8 -*-
"""
mundo.py - Mundo INFINITO dividido em chunks (pedaços de 16x16 blocos).

- Gerador: transforma (x, y) + semente em bioma, altura e chão. É uma função
  pura: a mesma semente sempre gera o mesmo mundo.
- Chunk: guarda os blocos e objetos de um pedaço do mapa.
- Mundo: carrega chunks perto do jogador, descarrega os longe e guarda
  as mudanças (árvores cortadas, construções, itens no chão) de cada chunk.
"""
import math
import random
import pygame

from config import (TILE, TAMANHO_CHUNK, RAIO_CARREGAR, RAIO_DESCARREGAR,
                    AGUA_FUNDA, AGUA_RASA, LAMA, AREIA, CHAO_AGUA, CHAO_DO_BIOMA,
                    NIVEL_AGUA_BASE, PROFUNDIDADE_FUNDA, TEMPO_FRUTAS_VOLTAR,
                    TEMPO_REGENERAR_DANO, COMBUSTIVEL_INICIAL, TAMANHO_BAU,
                    RAIO_LUZ_FOGUEIRA, RAIO_LUZ_TOCHA, LAVA)
from dados import OBJETOS, BIOMAS
import blocos                                   # noqa: F401  [v0.5] blocos, minérios, receitas
from ruido import fractal, ruido, numero_chunk, fractal_grade
from estruturas import PlanoEstruturas          # [ESTRUTURAS]
from dados_estruturas import e_piso             # [ESTRUTURAS]

CH = TAMANHO_CHUNK
TEMPO_CRESCER = 40.0          # segundos por estágio da plantação (na estação normal)


# ===============================================================
# Objetos do mundo (árvores, pedras, construções...)
# ===============================================================
class Objeto:
    def __init__(self, tipo, tx, ty, variante=0):
        self.tipo = tipo
        self.tx = tx
        self.ty = ty
        self.variante = variante
        self.vida = self.vida_max
        self.tempo_sem_golpe = 0.0
        self.tem_frutas = True             # só arbustos
        self.tempo_frutas = 0.0
        self.combustivel = COMBUSTIVEL_INICIAL if tipo == "fogueira" else 0.0
        self.tremor = 0.0
        self.crescimento = 0.0             # plantação: segundos crescendo
        self.conteudo = [None] * TAMANHO_BAU if tipo == "bau" else ([None] * 3 if tipo == "forno" else None)
        self.queima = 0.0                  # forno: segundos de fogo que ainda restam
        self.queima_max = 1.0
        self.progresso = 0.0               # forno: segundos derretendo o item atual

    @property
    def info(self):
        return OBJETOS[self.tipo]

    @property
    def vida_max(self):
        return OBJETOS[self.tipo]["vida"]

    @property
    def centro(self):
        return (self.tx * TILE + TILE / 2, self.ty * TILE + TILE / 2)

    @property
    def base_y(self):
        return self.ty * TILE + TILE - 2

    @property
    def solido(self):
        return OBJETOS[self.tipo]["solido"]

    @property
    def construcao(self):
        return OBJETOS[self.tipo].get("construcao", False)

    @property
    def acesa(self):
        return self.tipo == "fogueira" and self.combustivel > 0

    @property
    def estagio_dano(self):
        if self.vida >= self.vida_max:
            return 0
        return min(3, 1 + int((1.0 - self.vida / self.vida_max) * 3))

    @property
    def estagio(self):
        """Plantação: 0 (semente) ... 3 (madura)."""
        return min(3, int(self.crescimento / TEMPO_CRESCER))

    @property
    def maduro(self):
        return self.tipo == "plantacao" and self.estagio >= 3

    def retangulo_desenho(self):
        extra = OBJETOS[self.tipo].get("altura", 0)
        return pygame.Rect(self.tx * TILE, self.ty * TILE - extra, TILE, TILE + extra)

    @property
    def bloco(self):
        return OBJETOS[self.tipo].get("bloco", False)

    def retangulo_colisao(self):
        x, y = self.tx * TILE, self.ty * TILE
        if self.tipo in ("parede_madeira", "parede_pedra") or OBJETOS[self.tipo].get("bloco"):
            return pygame.Rect(x, y, TILE, TILE)
        if self.tipo in ("arvore", "arvore_pantano", "pinheiro", "cacto"):
            return pygame.Rect(x + 4, y + 6, 8, 9)
        if self.tipo in ("bau", "cama", "forno"):
            return pygame.Rect(x + 1, y + 4, 14, 11)
        return pygame.Rect(x + 2, y + 5, 12, 10)

    def atualizar(self, dt, fator=1.0):
        """fator = crescimento da estação (0 no inverno)."""
        if self.tremor > 0:
            self.tremor = max(0.0, self.tremor - dt)
        if self.vida < self.vida_max:
            self.tempo_sem_golpe += dt
            if self.tempo_sem_golpe >= TEMPO_REGENERAR_DANO:
                self.vida = self.vida_max
        if self.tipo == "plantacao":
            if self.crescimento < TEMPO_CRESCER * 3:
                self.crescimento += dt * fator
        elif self.tipo == "arbusto" and not self.tem_frutas:
            self.tempo_frutas += dt * fator
            if self.tempo_frutas >= TEMPO_FRUTAS_VOLTAR:
                self.tem_frutas = True
                self.tempo_frutas = 0.0
        elif self.tipo == "fogueira" and self.combustivel > 0:
            self.combustivel = max(0.0, self.combustivel - dt)
        elif self.tipo == "forno":
            from criacao import atualizar_forno
            return atualizar_forno(self, dt)
        return False

    def para_dict(self):
        d = {"t": self.tipo, "x": self.tx, "y": self.ty, "v": self.variante}
        if self.tipo == "arbusto":
            d["f"] = self.tem_frutas
            d["tf"] = round(self.tempo_frutas, 1)
        if self.tipo == "fogueira":
            d["c"] = round(self.combustivel, 1)
        if self.tipo == "plantacao":
            d["g"] = round(self.crescimento, 1)
        if self.conteudo is not None:
            d["i"] = [list(e) if e else None for e in self.conteudo]
        if self.tipo == "forno":
            d["fq"] = round(self.queima, 1)
            d["fm"] = round(self.queima_max, 1)
            d["fp"] = round(self.progresso, 1)
        return d

    @staticmethod
    def de_dict(d):
        o = Objeto(d["t"], d["x"], d["y"], d.get("v", 0))
        o.tem_frutas = d.get("f", True)
        o.tempo_frutas = d.get("tf", 0.0)
        if "c" in d:
            o.combustivel = d["c"]
        o.crescimento = d.get("g", 0.0)
        if o.conteudo is not None and isinstance(d.get("i"), list):
            n = len(o.conteudo)
            itens = [list(e) if e else None for e in d["i"]][:n]
            o.conteudo = itens + [None] * (n - len(itens))
        o.queima = d.get("fq", 0.0)
        o.queima_max = d.get("fm", 1.0) or 1.0
        o.progresso = d.get("fp", 0.0)
        return o


# ===============================================================
# Gerador procedural (função pura da semente)
# ===============================================================
class Gerador:
    def __init__(self, semente):
        self.semente = semente
        self.estruturas = PlanoEstruturas(semente, self)   # [ESTRUTURAS] vilas, castelos...

    def bioma(self, x, y):
        s = self.semente
        e = fractal(x / 110.0, y / 110.0, s + 11)     # "elevação"
        if e > 0.67:
            return "montanha"
        t = fractal(x / 160.0, y / 160.0, s + 23)     # temperatura
        m = fractal(x / 130.0, y / 130.0, s + 37)     # umidade
        if t < 0.34:
            return "neve"
        if t > 0.62 and m < 0.52:
            return "deserto"
        if m > 0.63:
            return "pantano"
        if m > 0.50:
            return "floresta"
        return "planicie"

    def dados_bloco(self, x, y):
        """Retorna (bioma, altura, nivel_base) de um bloco."""
        s = self.semente
        bioma = self.bioma(x, y)
        nivel_base = NIVEL_AGUA_BASE + BIOMAS[bioma]["agua"]
        h = fractal(x / 26.0, y / 26.0, s + 51)        # lagos
        # rios: faixas finas onde um ruído passa perto de 0,5
        r = fractal(x / 85.0, y / 85.0, s + 67)
        dr = abs(r - 0.5)
        if bioma != "montanha":
            if dr < 0.010:
                h = min(h, nivel_base - 0.025)         # leito do rio
            elif dr < 0.020:
                h = min(h, nivel_base + 0.012)         # margem: alaga na chuva
        return bioma, h, nivel_base

    def dados_chunk(self, x0, y0):
        """Igual a dados_bloco() para os CH x CH blocos de um chunk (linha a linha),
        mas calculando o ruído em grade: dá o mesmo mundo, bem mais rápido."""
        s = self.semente
        xs, ys = range(x0, x0 + CH), range(y0, y0 + CH)
        E = fractal_grade(xs, ys, 110.0, s + 11)
        T = fractal_grade(xs, ys, 160.0, s + 23)
        M = fractal_grade(xs, ys, 130.0, s + 37)
        H = fractal_grade(xs, ys, 26.0, s + 51)
        R = fractal_grade(xs, ys, 85.0, s + 67)
        saida = []
        for j in range(CH):
            for i in range(CH):
                e, t, m = E[j][i], T[j][i], M[j][i]
                if e > 0.67:
                    bioma = "montanha"
                elif t < 0.34:
                    bioma = "neve"
                elif t > 0.62 and m < 0.52:
                    bioma = "deserto"
                elif m > 0.63:
                    bioma = "pantano"
                elif m > 0.50:
                    bioma = "floresta"
                else:
                    bioma = "planicie"
                nivel_base = NIVEL_AGUA_BASE + BIOMAS[bioma]["agua"]
                h = H[j][i]
                dr = abs(R[j][i] - 0.5)
                if bioma != "montanha":
                    if dr < 0.010:
                        h = min(h, nivel_base - 0.025)
                    elif dr < 0.020:
                        h = min(h, nivel_base + 0.012)
                saida.append((bioma, h, nivel_base))
        return saida

    @staticmethod
    def classificar(bioma, h, nivel_base, deslocamento):
        """Decide o tipo de chão a partir da altura e do nível da água atual."""
        nivel = nivel_base + deslocamento
        if h < nivel - PROFUNDIDADE_FUNDA:
            return AGUA_FUNDA
        if h < nivel:
            return AGUA_RASA
        if h < nivel_base:
            return LAMA                     # fundo do lago que secou
        if h < nivel + 0.015 and bioma in ("planicie", "floresta", "deserto"):
            return AREIA                    # prainha
        return CHAO_DO_BIOMA[bioma]

    def gerar_chunk(self, cx, cy):
        ch = Chunk(cx, cy)
        x0, y0 = cx * CH, cy * CH
        dados = self.dados_chunk(x0, y0)
        for k, (b, h, nb) in enumerate(dados):
            ch.biomas[k] = b
            ch.alturas[k] = h
            ch.niveis[k] = nb
        ch.recalcular_chao(0.0)
        manchas = fractal_grade(range(x0, x0 + CH), range(y0, y0 + CH), 7.0, self.semente + 91, 1)
        # objetos (sorteio fixo por chunk)
        rng = random.Random(numero_chunk(self.semente, cx, cy))
        s = self.semente
        for j in range(CH):
            for i in range(CH):
                k = j * CH + i
                tipo_chao = ch.chao[k]
                sorteio = rng.random()
                variante = rng.randrange(3)
                if tipo_chao in CHAO_AGUA or tipo_chao in (LAMA, AREIA) and ch.biomas[k] != "deserto":
                    continue
                x, y = x0 + i, y0 + j
                # manchas: em alguns lugares tem mais coisas (florestas fechadas)
                mancha = 0.35 + 1.3 * manchas[j][i]
                acumulado = 0.0
                for tipo, chance in BIOMAS[ch.biomas[k]]["recursos"]:
                    acumulado += chance * mancha
                    if sorteio < acumulado:
                        ch.objetos[(x, y)] = Objeto(tipo, x, y, variante)
                        break
        self.estruturas.carimbar(ch, Objeto)               # [ESTRUTURAS] carimba vilas, castelos...
        return ch


# ===============================================================
# Chunk
# ===============================================================
class Chunk:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        n = CH * CH
        self.biomas = [""] * n
        self.alturas = [0.0] * n
        self.niveis = [0.0] * n
        self.chao = [0] * n
        self.objetos = {}            # (tx, ty) -> Objeto
        self.pisos = {}              # (tx, ty) -> Objeto "piso"
        self.modificado = False      # True = precisa ir para o save
        self.superficie = None       # imagem do chão já desenhada (cache)
        self.sujo = True             # True = redesenhar a imagem do chão
        self.chao_mod = {}           # [v0.5] índice -> tipo de chão mudado pelo jogador (vai no save)

    def recalcular_chao(self, deslocamento):
        """Reclassifica água/lama/terra para um novo nível. Retorna True se mudou algo."""
        mudou = False
        classificar = Gerador.classificar
        for k in range(CH * CH):
            novo = classificar(self.biomas[k], self.alturas[k], self.niveis[k], deslocamento)
            if novo != self.chao[k]:
                self.chao[k] = novo
                mudou = True
        for k, t in self.chao_mod.items():          # [v0.5] o que o jogador mudou continua
            self.chao[k] = t
        if mudou:
            self.sujo = True
        return mudou

    def para_dict(self, itens):
        d = {"objetos": [o.para_dict() for o in self.objetos.values()],
             "pisos": [o.para_dict() for o in self.pisos.values()],
             "itens": [it.para_dict() for it in itens]}
        if self.chao_mod:
            d["chao"] = [[k, t] for k, t in self.chao_mod.items()]
        return d

    def mudar_chao(self, k, tipo):
        """[v0.5] Troca o chão de um bloco (fica salvo)."""
        self.chao_mod[k] = tipo
        self.chao[k] = tipo
        self.modificado = True
        self.sujo = True


def chunk_do_bloco(tx, ty):
    return (tx // CH, ty // CH)


def chave(cx, cy):
    return f"{cx},{cy}"


# ===============================================================
# Mundo
# ===============================================================
class Mundo:
    def __init__(self, semente):
        self.semente = semente
        self.gerador = Gerador(semente)
        self.chunks = {}            # (cx, cy) -> Chunk carregado
        self.salvos = {}            # "cx,cy" -> dados de chunks modificados (fora da memória)
        self.itens = []             # itens no chão (dos chunks carregados)
        self.deslocamento_agua = 0.0
        self.fogueiras = []         # fogueiras dos chunks carregados
        self.luzes = []             # fogueiras, tochas e fornos dos chunks carregados
        self._fogueiras_sujas = True
        self._especiais = []        # [v0.5] objetos que mudam sozinhos (arbusto, fogueira, plantação, forno)
        self._especiais_sujos = True
        self.golpeados = set()      # [v0.5] objetos com dano/tremor (voltam ao normal sozinhos)
        self.ao_carregar = None     # função chamada quando um chunk novo é carregado
        self.fator_crescimento = 1.0  # estação: quão rápido frutas/plantações crescem

    # ----------------------- chunks -----------------------
    def gerar(self, cx, cy):
        """Gera (ou recupera do save) um chunk e coloca na memória."""
        ch = self.gerador.gerar_chunk(cx, cy)
        if abs(self.deslocamento_agua) > 1e-9:
            ch.recalcular_chao(self.deslocamento_agua)
        k = chave(cx, cy)
        if k in self.salvos:
            from entidades import ItemChao   # import aqui para evitar import circular
            d = self.salvos.pop(k)
            ch.objetos = {}
            for od in d.get("objetos", []):
                o = Objeto.de_dict(od)
                ch.objetos[(o.tx, o.ty)] = o
            ch.pisos = {}
            for od in d.get("pisos", []):
                o = Objeto.de_dict(od)
                ch.pisos[(o.tx, o.ty)] = o
            self.itens.extend(ItemChao.de_dict(i) for i in d.get("itens", []))
            for k, t in d.get("chao", []):
                ch.chao_mod[int(k)] = t
                ch.chao[int(k)] = t
            ch.modificado = True
        self.chunks[(cx, cy)] = ch
        self._sujar()
        if self.ao_carregar:
            self.ao_carregar(ch)
        return ch

    def descarregar(self, cx, cy):
        ch = self.chunks.pop((cx, cy))
        meus_itens = [it for it in self.itens if chunk_do_bloco(int(it.x // TILE), int(it.y // TILE)) == (cx, cy)]
        if meus_itens:
            ids = set(map(id, meus_itens))
            self.itens = [it for it in self.itens if id(it) not in ids]
        if ch.modificado or meus_itens:
            self.salvos[chave(cx, cy)] = ch.para_dict(meus_itens)
        self._sujar()

    def atualizar_chunks(self, px, py, limite=2, raio=RAIO_CARREGAR):
        """Carrega chunks perto de (px, py) (mais próximos primeiro) e descarrega os longe."""
        pcx, pcy = int(px // TILE) // CH, int(py // TILE) // CH
        faltando = [(cx, cy) for cy in range(pcy - raio, pcy + raio + 1)
                    for cx in range(pcx - raio, pcx + raio + 1) if (cx, cy) not in self.chunks]
        faltando.sort(key=lambda c: (c[0] - pcx) ** 2 + (c[1] - pcy) ** 2)
        for c in faltando[:limite]:
            self.gerar(*c)
        for c in list(self.chunks):
            if max(abs(c[0] - pcx), abs(c[1] - pcy)) > RAIO_DESCARREGAR:
                self.descarregar(*c)
        return len(faltando) > limite

    def chunk(self, tx, ty):
        return self.chunks.get((tx // CH, ty // CH))

    def definir_nivel_agua(self, deslocamento):
        """Muda o nível da água (clima). Só recalcula se mudar o suficiente."""
        q = round(deslocamento / 0.0025) * 0.0025
        if abs(q - self.deslocamento_agua) < 1e-9:
            return
        self.deslocamento_agua = q
        for ch in self.chunks.values():
            if ch.recalcular_chao(q):
                # vizinhos também redesenham (espuma da beira da água)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = self.chunks.get((ch.cx + dx, ch.cy + dy))
                    if v:
                        v.sujo = True

    # ----------------------- blocos -----------------------
    def tipo_chao(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        if ch:
            return ch.chao[(ty % CH) * CH + (tx % CH)]
        b, h, nb = self.gerador.dados_bloco(tx, ty)
        return Gerador.classificar(b, h, nb, self.deslocamento_agua)

    def bioma(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        if ch:
            return ch.biomas[(ty % CH) * CH + (tx % CH)]
        return self.gerador.bioma(tx, ty)

    def objeto(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        return ch.objetos.get((tx, ty)) if ch else None

    def piso(self, tx, ty):
        ch = self.chunks.get((tx // CH, ty // CH))
        return ch.pisos.get((tx, ty)) if ch else None

    def colocar(self, obj):
        ch = self.chunk(obj.tx, obj.ty)
        if ch is None:
            return False
        if e_piso(obj.tipo):                               # [ESTRUTURAS] (era: == "piso")
            ch.pisos[(obj.tx, obj.ty)] = obj
            ch.sujo = True
        else:
            ch.objetos[(obj.tx, obj.ty)] = obj
        ch.modificado = True
        self._sujar()
        return True

    def remover(self, obj):
        ch = self.chunk(obj.tx, obj.ty)
        if ch is None:
            return
        if e_piso(obj.tipo):                               # [ESTRUTURAS] (era: == "piso")
            ch.pisos.pop((obj.tx, obj.ty), None)
            ch.sujo = True
        else:
            ch.objetos.pop((obj.tx, obj.ty), None)
        ch.modificado = True
        self._sujar()

    def marcar_modificado(self, obj):
        ch = self.chunk(obj.tx, obj.ty)
        if ch:
            ch.modificado = True

    def colide(self, ret, agua=True):
        """True se o retângulo bate em objeto sólido (ou em água funda, se agua=True)."""
        x0, y0 = int(ret.left // TILE), int(ret.top // TILE)
        x1, y1 = int((ret.right - 1) // TILE), int((ret.bottom - 1) // TILE)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if agua and self.tipo_chao(tx, ty) in (AGUA_FUNDA, LAVA):
                    return True
                obj = self.objeto(tx, ty)
                if obj and obj.solido and ret.colliderect(obj.retangulo_colisao()):
                    return True
        return False

    def perto_de_agua(self, px, py, alcance=1):
        tx, ty = int(px // TILE), int(py // TILE)
        for dy in range(-alcance, alcance + 1):
            for dx in range(-alcance, alcance + 1):
                if self.tipo_chao(tx + dx, ty + dy) in CHAO_AGUA:
                    return True
        return False

    def agua_mais_proxima(self, px, py, raio=7):
        tx, ty = int(px // TILE), int(py // TILE)
        melhor, melhor_d = None, 1e9
        for dy in range(-raio, raio + 1):
            for dx in range(-raio, raio + 1):
                if self.tipo_chao(tx + dx, ty + dy) in CHAO_AGUA:
                    d = dx * dx + dy * dy
                    if d < melhor_d:
                        melhor, melhor_d = (tx + dx, ty + dy), d
        return melhor

    def objeto_mais_proximo(self, px, py, alcance, tipos=None):
        tx, ty = int(px // TILE), int(py // TILE)
        melhor, melhor_d = None, alcance
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                obj = self.objeto(tx + dx, ty + dy)
                if obj is None or (tipos and obj.tipo not in tipos):
                    continue
                ox, oy = obj.centro
                d = math.hypot(ox - px, oy - py)
                if d < melhor_d:
                    melhor, melhor_d = obj, d
        return melhor

    def objeto_no_ponto(self, wx, wy):
        """Objeto embaixo do mouse (a copa da árvore conta para o bloco de baixo)."""
        tx, ty = int(wx // TILE), int(wy // TILE)
        aqui = self.objeto(tx, ty)
        if aqui is not None and aqui.bloco:              # [v0.5] blocos: o de cima tem prioridade
            return aqui
        abaixo = self.objeto(tx, ty + 1)
        if abaixo and abaixo.retangulo_desenho().collidepoint(wx, wy):
            return abaixo
        obj = self.objeto(tx, ty)
        if obj:
            return obj
        return self.piso(tx, ty)

    def estacao_perto(self, tipo, px, py, raio):
        """Tem uma bancada/fogueira acesa a menos de 'raio' pixels?"""
        r = int(raio // TILE) + 1
        tx, ty = int(px // TILE), int(py // TILE)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                o = self.objeto(tx + dx, ty + dy)
                if o and o.tipo == tipo and (tipo != "fogueira" or o.acesa):
                    ox, oy = o.centro
                    if math.hypot(ox - px, oy - py) <= raio:
                        return o
        return None

    def lista_fogueiras(self):
        if self._fogueiras_sujas:
            self.luzes = [o for ch in self.chunks.values() for o in ch.objetos.values()
                          if o.tipo in ("fogueira", "tocha", "forno", "lampada")]
            self.fogueiras = [o for o in self.luzes if o.tipo == "fogueira"]
            self._fogueiras_sujas = False
        return [f for f in self.fogueiras if f.acesa]

    def lista_luzes(self):
        """[(objeto, raio)] de tudo que ilumina: fogueiras acesas, tochas e fornos."""
        self.lista_fogueiras()
        raios = {"fogueira": RAIO_LUZ_FOGUEIRA, "tocha": RAIO_LUZ_TOCHA, "lampada": blocos.RAIO_LUZ_LAMPADA}
        return [(o, raios.get(o.tipo, 34)) for o in self.luzes
                if (o.tipo != "fogueira" or o.acesa) and (o.tipo != "forno" or o.queima > 0)]

    def _sujar(self):
        self._fogueiras_sujas = True
        self._especiais_sujos = True

    def golpeado(self, obj):
        """[v0.5] Avisa que um objeto levou golpe (para tremer e se recuperar)."""
        self.golpeados.add(obj)

    def atualizar(self, dt):
        # [v0.5] só olha os objetos que mudam sozinhos (antes passava por todos: lento nas cavernas)
        if self._especiais_sujos:
            self._especiais = [(ch, o) for ch in self.chunks.values() for o in ch.objetos.values()
                               if o.tipo in ("arbusto", "fogueira", "plantacao", "forno")]
            self._especiais_sujos = False
        for ch, obj in self._especiais:
            if obj.tipo == "forno":
                if (obj.queima > 0 or obj.progresso > 0 or obj.conteudo[0]) and obj.atualizar(dt):
                    ch.modificado = True
            else:
                obj.atualizar(dt, self.fator_crescimento)
        for obj in list(self.golpeados):
            if obj.tipo not in ("arbusto", "fogueira", "plantacao", "forno"):
                obj.atualizar(dt, self.fator_crescimento)
            if obj.tremor <= 0 and obj.vida >= obj.vida_max:
                self.golpeados.discard(obj)

    # ----------------------- início e save -----------------------
    def ponto_inicial(self):
        """Procura um lugar de terra firme perto do centro, de preferência na planície."""
        melhor = None
        for raio in range(0, 400, 4):
            for ang in range(0, 360, 20):
                x = int(math.cos(math.radians(ang)) * raio)
                y = int(math.sin(math.radians(ang)) * raio)
                b, h, nb = self.gerador.dados_bloco(x, y)
                if Gerador.classificar(b, h, nb, 0.0) in CHAO_AGUA + (LAMA,):
                    continue
                if b in ("planicie", "floresta"):
                    return x, y
                if melhor is None:
                    melhor = (x, y)
            if raio == 0:
                continue
        return melhor or (0, 0)

    def limpar_area(self, tx, ty, raio=2):
        for yy in range(ty - raio, ty + raio + 1):
            for xx in range(tx - raio, tx + raio + 1):
                o = self.objeto(xx, yy)
                if o and not o.construcao:
                    self.remover(o)

    def dados_save(self):
        """Todos os chunks modificados (guardados + carregados) para o arquivo."""
        dados = dict(self.salvos)
        por_chunk = {}
        for it in self.itens:
            c = chunk_do_bloco(int(it.x // TILE), int(it.y // TILE))
            por_chunk.setdefault(c, []).append(it)
        for c, ch in self.chunks.items():
            itens = por_chunk.get(c, [])
            if ch.modificado or itens:
                dados[chave(*c)] = ch.para_dict(itens)
        return dados
