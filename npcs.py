# -*- coding: utf-8 -*-
"""
npcs.py - Moradores e defensores das estruturas.

- Aldeao: anda perto de casa, volta para casa à noite e FAZ TROCAS
  (aperte E perto dele ou clique com o botão direito).
- Guarda: protege a cidadela, persegue monstros e lobos perto do posto.
- Inimigo: cavaleiros e esqueletos defendem castelos, ruínas e masmorras;
  não se afastam muito do posto. Chefes (Cavaleiro Negro e Rei Esqueleto)
  têm muita vida e, se morrerem, não voltam mais (fica no save).
- MenuTroca: a janela de trocas (dar itens -> receber itens).
"""
import math
import random

import pygame

from config import TILE, LARGURA_TELA, ALTURA_TELA, COR_DESTAQUE, COR_TEXTO
from dados import ITENS, CRIATURAS
from entidades import Criatura
from estruturas import numero

HOSTIS = ("monstro", "predador", "inimigo")
FALAS_ALDEAO = ["Bom dia, viajante!", "Quer trocar alguma coisa?", "Cuidado com os lobos à noite.",
                "Dizem que há um castelo perto daqui...", "As masmorras são perigosas!",
                "A colheita está boa este ano."]
FALAS_GUARDA = ["Bem-vindo à cidadela!", "Mantenha a ordem.", "Os portões fecham ao anoitecer... brincadeira.",
                "Estou de olho nos monstros."]


# ===============================================================
# Trocas
# ===============================================================
VENDE_PARA_ALDEAO = [({"madeira": 10}, ("moeda_ouro", 1)), ({"pedra": 12}, ("moeda_ouro", 1)),
                     ({"couro": 3}, ("moeda_ouro", 2)), ({"peixe": 3}, ("moeda_ouro", 1)),
                     ({"carne_crua": 3}, ("moeda_ouro", 1)), ({"minerio_ferro": 4}, ("moeda_ouro", 2)),
                     ({"fibra": 12}, ("moeda_ouro", 1))]
COMIDA = [({"frutas": 6}, ("pao", 2)), ({"trigo": 4}, ("pao", 2)), ({"moeda_ouro": 1}, ("pao", 3)),
          ({"moeda_ouro": 1}, ("trigo", 6)), ({"moeda_ouro": 2}, ("carne_assada", 3))]
COMPRA = [({"moeda_ouro": 2}, ("tocha", 4)), ({"moeda_ouro": 3}, ("pocao_vida", 1)),
          ({"moeda_ouro": 6}, ("ferro", 3)), ({"moeda_ouro": 8}, ("espada_ferro", 1)),
          ({"moeda_ouro": 4}, ("vara_pesca", 1)), ({"moeda_ouro": 3}, ("cantil_cheio", 1))]
POR_BIOMA = {
    "deserto": [({"moeda_ouro": 2}, ("cantil_cheio", 1)), ({"fibra": 6}, ("moeda_ouro", 1))],
    "neve": [({"moeda_ouro": 5}, ("roupa_couro", 1)), ({"moeda_ouro": 3}, ("capuz_couro", 1))],
    "floresta": [({"moeda_ouro": 3}, ("machado_pedra", 1)), ({"madeira": 20}, ("moeda_ouro", 3))],
    "pantano": [({"fibra": 8}, ("pocao_vida", 1))],
    "planicie": [({"moeda_ouro": 3}, ("picareta_pedra", 1))],
}
COMERCIANTE = [({"moeda_ouro": 15}, ("armadura_ferro", 1)), ({"moeda_ouro": 9}, ("picareta_ferro", 1)),
               ({"moeda_ouro": 10}, ("capacete_ferro", 1)), ({"moeda_ouro": 5}, ("pocao_vida", 2))]


def valida(oferta):
    custo, (item, qtd) = oferta
    return item in ITENS and all(i in ITENS and q > 0 for i, q in custo.items())


def ofertas_para(npc_id, bioma, comerciante=False):
    """3 ou 4 trocas fixas para cada aldeão (sorteadas pelo id dele)."""
    rng = random.Random(numero("trocas", npc_id))
    lista = [rng.choice(VENDE_PARA_ALDEAO), rng.choice(COMIDA)]
    extras = COMPRA + POR_BIOMA.get(bioma, []) + (COMERCIANTE * 2 if comerciante else [])
    extras = [o for o in extras if valida(o)]
    rng.shuffle(extras)
    for o in extras:
        if o not in lista:
            lista.append(o)
        if len(lista) >= (4 if comerciante or rng.random() < 0.5 else 3):
            break
    return [o for o in lista if valida(o)]


# ===============================================================
# NPCs
# ===============================================================
class NPC(Criatura):
    def __init__(self, tipo, x, y, dados):
        super().__init__(tipo, x, y)
        self.npc_id = dados["id"]
        self.estrutura = dados.get("estrutura")
        self.casa = (x, y)
        self.raio = dados.get("raio", 5) * TILE
        self.dados = dados
        self.chefe = bool(dados.get("chefe") or CRIATURAS[tipo].get("chefe"))
        self.fala = 0.0
        self._dt = 1 / 60.0

    def atualizar(self, dt, jogo):
        self._dt = dt
        super().atualizar(dt, jogo)

    def _ir_para_casa(self):
        d = self._rumo(*self.casa)
        if d < 6:
            self.direcao = (0.0, 0.0)
        self.estado = "voltar"
        self.tempo_estado = 0.5

    def _vagar_perto(self):
        if math.hypot(self.x - self.casa[0], self.y - self.casa[1]) > self.raio:
            self._ir_para_casa()
            return
        if self.estado == "voltar":
            self.estado = "vagar"
            self.tempo_estado = 0
        self._vagar()


class Aldeao(NPC):
    def __init__(self, tipo, x, y, dados):
        super().__init__(tipo, x, y, dados)
        self.ofertas = ofertas_para(self.npc_id, dados.get("bioma", "planicie"), dados.get("comerciante"))

    def levar_golpe(self, dano, de_x, de_y):
        self.piscar = 0.1                       # aldeões não se machucam (e não brigam)
        self.estado, self.tempo_estado = "fugir", 1.0
        dx, dy = self.x - de_x, self.y - de_y
        d = math.hypot(dx, dy) or 1.0
        self.direcao = (dx / d, dy / d)

    def _pensar_cacador(self, jogo):
        if self.estado == "fugir" and self.tempo_estado > 0:
            return
        if self.estado == "conversar" and self.tempo_estado > 0:
            self.direcao = (0.0, 0.0)
            return
        if jogo.e_noite() and math.hypot(self.x - self.casa[0], self.y - self.casa[1]) > 10:
            self._ir_para_casa()                # de noite fica em casa
            return
        self._vagar_perto()


class Guarda(NPC):
    def levar_golpe(self, dano, de_x, de_y):
        self.piscar = 0.1

    def _pensar_cacador(self, jogo):
        alvo, melhor = None, 100.0
        for c in jogo.criaturas:
            if c is self or c.comportamento not in HOSTIS or c.vida <= 0:
                continue
            d = math.hypot(c.x - self.x, c.y - self.y)
            if d < melhor and math.hypot(c.x - self.casa[0], c.y - self.casa[1]) < self.raio + 90:
                alvo, melhor = c, d
        if alvo is None:
            self._vagar_perto()
            return
        self.estado = "perseguir"
        d = self._rumo(alvo.x, alvo.y)
        if d < 12 and self.espera_ataque <= 0:
            self.espera_ataque = 0.8
            alvo.levar_golpe(self.info.get("dano", 6), self.x, self.y)


class Inimigo(NPC):
    def __init__(self, tipo, x, y, dados):
        super().__init__(tipo, x, y, dados)
        self.tempo_chamar = 6.0

    def _pensar_cacador(self, jogo):
        j = jogo.jogador
        alcance = self.info.get("alcance", 120)
        dj = math.hypot(j.x - self.x, j.y - self.y)
        longe_de_casa = math.hypot(j.x - self.casa[0], j.y - self.casa[1]) > self.raio + alcance
        if j.vida <= 0 or dj > alcance or longe_de_casa:
            self._vagar_perto()
            return
        self.estado = "perseguir"
        d = self._rumo(j.x, j.y)
        if d < 11 and self.espera_ataque <= 0:
            self.espera_ataque = 1.0 if not self.chefe else 1.3
            jogo.jogador_atacado(self)
        # o Rei Esqueleto chama esqueletos para ajudar
        if self.tipo == "rei_esqueleto":
            self.tempo_chamar -= self._dt
            if self.tempo_chamar <= 0:
                self.tempo_chamar = 7.0
                ajudantes = sum(1 for c in jogo.criaturas if getattr(c, "invocado", False))
                if ajudantes < 3:
                    ang = random.uniform(0, math.tau)
                    novo = Inimigo("esqueleto", self.x + math.cos(ang) * 14, self.y + math.sin(ang) * 10,
                                   {"id": f"{self.npc_id}+{random.random()}", "raio": 8})
                    novo.casa = self.casa
                    novo.invocado = True
                    if not jogo.mundo.colide(novo.retangulo()):
                        jogo.criaturas.append(novo)
                        jogo.avisar("O Rei Esqueleto chamou reforços!", 2)


CLASSES = {"aldeao": Aldeao, "guarda": Guarda}


def criar_npc(dados):
    tipo = dados["tipo"]
    x, y = dados["x"] * TILE + 8, dados["y"] * TILE + 12
    return CLASSES.get(tipo, Inimigo)(tipo, x, y, dados)


def falar(npc):
    rng = random
    return rng.choice(FALAS_GUARDA if npc.tipo == "guarda" else FALAS_ALDEAO)


# ===============================================================
# Janela de trocas
# ===============================================================
class MenuTroca:
    def __init__(self, npc):
        self.npc = npc
        self.linhas = []          # [(rect, índice)]
        self.ret = pygame.Rect(0, 0, 0, 0)

    def pode(self, inv, oferta):
        custo, _ = oferta
        return all(inv.tem(i, q) for i, q in custo.items())

    def trocar(self, jogo, indice):
        inv = jogo.jogador.inventario
        custo, (item, qtd) = self.npc.ofertas[indice]
        if not self.pode(inv, self.npc.ofertas[indice]):
            falta = next(i for i, q in custo.items() if not inv.tem(i, q))
            jogo.avisar(f"Falta: {ITENS[falta]['nome']}", 1.5)
            return False
        for i, q in custo.items():
            inv.remover(i, q)
        sobra = inv.adicionar(item, qtd)
        if sobra:
            jogo.jogar_no_chao([item, sobra])
        if qtd - sobra:
            jogo.popup(item, qtd - sobra)
        jogo.avisar(f"Troca feita: {qtd}x {ITENS[item]['nome']}", 2)
        return True

    def clique(self, pos):
        for r, i in self.linhas:
            if r.collidepoint(pos):
                return i
        return None

    def desenhar(self, tela, ui, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ofertas = self.npc.ofertas
        larg, alt_linha = 520, 64
        alt = 110 + alt_linha * len(ofertas)
        r = pygame.Rect((LARGURA_TELA - larg) // 2, (ALTURA_TELA - alt) // 2 - 30, larg, alt)
        self.ret = r
        ui.painel(tela, r, 240)
        ui.texto(tela, f"Trocas com {self.npc.info['nome']}", (r.centerx, r.y + 14), ui.fonte_media,
                 COR_DESTAQUE, centro=True)
        self.linhas = []
        for n, oferta in enumerate(ofertas):
            custo, (item, qtd) = oferta
            y = r.y + 54 + n * alt_linha
            linha = pygame.Rect(r.x + 16, y, larg - 32, alt_linha - 8)
            ok = self.pode(inv, oferta)
            em_cima = linha.collidepoint(pos_mouse)
            fundo = pygame.Surface(linha.size, pygame.SRCALPHA)
            fundo.fill((80, 72, 110, 230) if em_cima else (44, 40, 62, 230))
            tela.blit(fundo, linha.topleft)
            pygame.draw.rect(tela, COR_DESTAQUE if em_cima and ok else (90, 84, 110), linha, 2)
            ui.texto(tela, f"{n + 1}", (linha.x + 10, linha.y + 16), ui.fonte, (190, 186, 200))
            x = linha.x + 34
            for i, q in custo.items():
                tela.blit(ui.icones[i], (x, linha.y + 12))
                cor = COR_TEXTO if inv.tem(i, q) else (240, 110, 110)
                ui.texto(tela, f"{q}x {ITENS[i]['nome']}", (x + 38, linha.y + 18), ui.fonte_peq, cor)
                x += 190
            ui.texto(tela, "->", (linha.x + 236, linha.y + 16), ui.fonte, COR_DESTAQUE)
            tela.blit(ui.icones[item], (linha.x + 270, linha.y + 12))
            ui.texto(tela, f"{qtd}x {ITENS[item]['nome']}", (linha.x + 308, linha.y + 18), ui.fonte_peq,
                     COR_TEXTO if ok else (170, 166, 180))
            self.linhas.append((linha, n))
        ui.texto(tela, "Clique numa troca (ou tecla 1-4)   -   E / Esc para sair",
                 (r.centerx, r.bottom - 34), ui.fonte_peq, (200, 196, 210), centro=True)
