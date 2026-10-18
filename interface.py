# -*- coding: utf-8 -*-
"""
interface.py - Telas e HUD em estilo pixel art.

HUD: barras com ícones (vida, fome, sede, energia, ar), relógio com dia,
estação, clima e temperatura, minimapa, barra rápida com molduras e
equipamentos. Janelas: inventário (com o boneco mostrando a armadura),
baú, criação, menu inicial, pausa, controles, mapa completo, ajuda e morte.
Tudo é desenhado na tela grande (960x600) para o texto ficar legível;
as molduras usam "pixels" de 3x3 para combinar com o jogo.
"""
import math
import pygame

from config import (LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_SOMBRA, COR_DESTAQUE, COR_VIDA,
                    COR_FOME, COR_SEDE, COR_ENERGIA, COR_AR, VIDA_MAX, FOME_MAX, SEDE_MAX,
                    ENERGIA_MAX, AR_MAX, ESCALA, TAMANHO_BARRA, TAMANHO_INVENTARIO, TAMANHO_BAU,
                    DIAS_POR_ESTACAO)
from dados import ITENS, RECEITAS, CATEGORIAS, NOMES_SLOTS, ORDEM_SLOTS, NOMES_ESTACOES, BIOMAS
from controles import ACOES
from estacoes import NOMES as NOMES_ESTACOES_ANO
import personagem

TAM = 48          # tamanho de um espaço de item
ESP = 6           # espaço entre eles
P = ESCALA        # "pixel" da interface

# paleta da interface
FUNDO = (34, 30, 48)
FUNDO_2 = (46, 40, 64)
BORDA_ESC = (16, 14, 24)
BORDA_CLARA = (104, 94, 138)
BORDA_MEIO = (70, 62, 96)
DOURADO = (250, 210, 90)
DOURADO_ESC = (176, 132, 48)
CINZA_TEXTO = (196, 190, 210)
VERDE = (140, 230, 120)
VERMELHO = (240, 110, 100)
COR_TIER = {"madeira": (214, 170, 120), "pedra": (190, 196, 210), "ferro": (150, 210, 255),
            "diamante": (120, 245, 235)}
COR_XP = (130, 230, 70)
TIPOS = {"material": "Material", "comida": "Comida", "bebida": "Bebida", "ferramenta": "Ferramenta",
         "arma": "Arma", "armadura": "Armadura", "construcao": "Construção", "utilidade": "Utilidade",
         "municao": "Munição"}


def _tier(item):
    for t in COR_TIER:
        if item.endswith("_" + t):
            return t
    return None


class Interface:
    def __init__(self, sprites):
        pygame.font.init()
        self.fonte = pygame.font.Font(None, 24)
        self.fonte_peq = pygame.font.Font(None, 20)
        self.fonte_media = pygame.font.Font(None, 32)
        self.fonte_grande = pygame.font.Font(None, 72)
        self.fonte_titulo = pygame.font.Font(None, 84)
        self.icones = {n: pygame.transform.scale(img, (32, 32)) for n, img in sprites.icones.items()}
        self.icones_peq = {n: pygame.transform.scale(img, (24, 24)) for n, img in sprites.icones.items()}
        self.icones_mini = {n: pygame.transform.scale(img, (13, 13)) for n, img in sprites.icones.items()}
        self.icones_vazios = {}
        for slot, item in (("cabeca", "capuz_couro"), ("corpo", "roupa_couro"), ("arma", "espada_madeira"),
                           ("ferramenta", "picareta_madeira")):
            ic = self.icones[item].copy()
            ic.fill((60, 56, 80, 255), special_flags=pygame.BLEND_RGBA_MIN)
            ic.set_alpha(150)
            self.icones_vazios[slot] = ic
        self.hud = sprites.hud
        self.hud_peq = sprites.hud_peq
        self.cursor = sprites.cursor
        self.sprites = sprites
        self._molduras = {}
        # áreas clicáveis (preenchidas ao desenhar cada tela)
        self.ret_barra = self._espacos_barra()
        self.slots_inventario = []       # [(rect, ref)]
        self.ret_painel = pygame.Rect(0, 0, 0, 0)
        self.ret_abas = []               # [(rect, categoria)]
        self.ret_receitas = []           # [(rect, indice em RECEITAS)]
        self.ret_controles = []          # [(rect, ação)]
        self.ret_minimapa = pygame.Rect(0, 0, 0, 0)
        self.botoes = {}                 # nome -> rect

    # ===========================================================
    # Peças básicas
    # ===========================================================
    def _espacos_barra(self):
        total = TAMANHO_BARRA * (TAM + ESP) - ESP
        x0 = (LARGURA_TELA - total) // 2
        y0 = ALTURA_TELA - TAM - 12
        return [pygame.Rect(x0 + i * (TAM + ESP), y0, TAM, TAM) for i in range(TAMANHO_BARRA)]

    def texto(self, tela, msg, pos, fonte=None, cor=COR_TEXTO, centro=False, direita=False, contorno=False):
        fonte = fonte or self.fonte
        img = fonte.render(msg, False, cor)
        x, y = pos
        if centro:
            x -= img.get_width() // 2
        elif direita:
            x -= img.get_width()
        sombra = fonte.render(msg, False, COR_SOMBRA)
        if contorno:
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)):
                tela.blit(sombra, (x + dx, y + dy))
        else:
            tela.blit(sombra, (x + 2, y + 2))
        tela.blit(img, (x, y))
        return img.get_width()

    def moldura(self, w, h, estilo="painel", alfa=235):
        """Painel com borda em pixels 3x3: contorno escuro, chanfro claro em cima e escuro embaixo."""
        k = (w, h, estilo, alfa)
        if k in self._molduras:
            return self._molduras[k]
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if estilo == "espaco":
            fundo, claro, escuro = (24, 22, 34, 225), (20, 18, 28), (84, 76, 110)
        elif estilo == "espaco_sel":
            fundo, claro, escuro = (64, 54, 40, 235), DOURADO, DOURADO_ESC
        elif estilo == "botao":
            fundo, claro, escuro = (62, 56, 88, alfa), (120, 110, 160), (36, 32, 52)
        elif estilo == "botao_sel":
            fundo, claro, escuro = (92, 80, 126, alfa), (250, 226, 130), (150, 110, 50)
        elif estilo == "barra":
            fundo, claro, escuro = (20, 18, 28, 240), (20, 18, 28), (70, 64, 90)
        else:
            fundo, claro, escuro = (*FUNDO, alfa), BORDA_CLARA, BORDA_ESC
        s.fill(fundo, (P, P, w - 2 * P, h - 2 * P))
        # contorno escuro (cantos "arredondados" de 1 pixel)
        pygame.draw.rect(s, BORDA_ESC, (P, 0, w - 2 * P, P))
        pygame.draw.rect(s, BORDA_ESC, (P, h - P, w - 2 * P, P))
        pygame.draw.rect(s, BORDA_ESC, (0, P, P, h - 2 * P))
        pygame.draw.rect(s, BORDA_ESC, (w - P, P, P, h - 2 * P))
        # chanfro
        pygame.draw.rect(s, claro, (P, P, w - 2 * P, P))
        pygame.draw.rect(s, claro, (P, P, P, h - 2 * P))
        pygame.draw.rect(s, escuro, (P, h - 2 * P, w - 2 * P, P))
        pygame.draw.rect(s, escuro, (w - 2 * P, P, P, h - 2 * P))
        if estilo == "painel":
            # cantinhos dourados
            for cx, cy in ((P * 2, P * 2), (w - P * 3, P * 2), (P * 2, h - P * 3), (w - P * 3, h - P * 3)):
                s.fill(DOURADO_ESC, (cx, cy, P, P))
        self._molduras[k] = s
        return s

    def painel(self, tela, ret, alfa=235):
        tela.blit(self.moldura(ret.w, ret.h, "painel", alfa), ret.topleft)

    def titulo_painel(self, tela, ret, texto):
        larg = self.fonte_media.size(texto)[0] + 40
        faixa = pygame.Rect(0, 0, larg, 36)
        faixa.midtop = (ret.centerx, ret.y - 14)
        tela.blit(self.moldura(faixa.w, faixa.h, "botao_sel", 250), faixa.topleft)
        self.texto(tela, texto, (faixa.centerx, faixa.y + 8), self.fonte_media, (255, 240, 170), centro=True)

    def botao(self, tela, nome, ret, rotulo, pos_mouse, ativo=True, icone=None):
        self.botoes[nome] = ret
        em_cima = ativo and pos_mouse is not None and ret.collidepoint(pos_mouse)
        tela.blit(self.moldura(ret.w, ret.h, "botao_sel" if em_cima else "botao", 245), ret.topleft)
        cor = (255, 240, 150) if em_cima else ((236, 230, 246) if ativo else (120, 116, 132))
        x = ret.centerx
        if icone:
            larg = self.fonte.size(rotulo)[0] + 28
            tela.blit(icone, (x - larg // 2, ret.centery - icone.get_height() // 2))
            x += 14
        self.texto(tela, rotulo, (x, ret.centery - 8), self.fonte, cor, centro=True)

    def espaco(self, tela, ret, pilha, destaque=False, rotulo=None, vazio=None):
        tela.blit(self.moldura(ret.w, ret.h, "espaco_sel" if destaque else "espaco"), ret.topleft)
        if rotulo:
            self.texto(tela, rotulo, (ret.x + 6, ret.y + 4), self.fonte_peq, (150, 144, 170))
        if pilha:
            ic = self.icones[pilha[0]]
            tela.blit(ic, (ret.centerx - 16, ret.centery - 15 + (-2 if destaque else 0)))
            if pilha[1] > 1:
                self.texto(tela, str(pilha[1]), (ret.right - 5, ret.bottom - 19), self.fonte_peq, direita=True)
            self.barra_durabilidade(tela, ret, pilha)
        elif vazio is not None:
            tela.blit(vazio, (ret.centerx - 16, ret.centery - 16))

    def barra_durabilidade(self, tela, ret, pilha):
        """[v0.5] Barrinha de durabilidade (só aparece quando a ferramenta já foi usada)."""
        if len(pilha) < 3:
            return
        maximo = ITENS[pilha[0]].get("durabilidade") or 1
        frac = max(0.0, min(1.0, pilha[2] / maximo))
        if frac >= 1.0:
            return
        w = ret.w - 14
        x, y = ret.x + 7, ret.bottom - 9
        pygame.draw.rect(tela, (16, 14, 20), (x - 1, y - 1, w + 2, 5))
        cor = (int(255 * min(1, 2 - 2 * frac)), int(255 * min(1, 2 * frac)), 60)
        pygame.draw.rect(tela, cor, (x, y, max(1, int(w * frac)), 3))

    def no_ponto(self, lista, pos):
        for ret, valor in lista:
            if ret.collidepoint(pos):
                return valor
        return None

    def mouse_sobre_interface(self, pos, estado):
        if estado != "jogando":
            return True
        return any(r.collidepoint(pos) for r in self.ret_barra) or self.ret_minimapa.collidepoint(pos)

    def espaco_barra_no_ponto(self, pos):
        for i, r in enumerate(self.ret_barra):
            if r.collidepoint(pos):
                return i
        return None

    # ===========================================================
    # HUD
    # ===========================================================
    def barra(self, tela, x, y, valor, maximo, cor, icone, tempo=0.0, largura=190):
        altura = 18
        tela.blit(self.hud[icone], (x, y - 3))
        bx = x + 30
        tela.blit(self.moldura(largura + 2 * P, altura + 2 * P, "barra"), (bx - P, y - P))
        frac = max(0.0, min(1.0, valor / maximo))
        cheio = int(largura * frac)
        if frac < 0.25 and int(tempo * 4) % 2 == 0:
            cor = tuple(min(255, c + 70) for c in cor)          # pisca quando está acabando
        if cheio > 0:
            pygame.draw.rect(tela, tuple(int(c * 0.7) for c in cor), (bx, y, cheio, altura))
            pygame.draw.rect(tela, cor, (bx, y, cheio, altura - 6))
            pygame.draw.rect(tela, tuple(min(255, c + 70) for c in cor), (bx, y + 3, cheio, 3))
        for i in range(1, 10):                                  # risquinhos a cada 10%
            xx = bx + largura * i // 10
            pygame.draw.rect(tela, (20, 18, 28), (xx, y + altura - 5, 2, 5))
        self.texto(tela, str(int(math.ceil(valor))), (bx + largura + 10, y), self.fonte_peq)

    def desenhar_hud(self, tela, jogo):
        j = jogo.jogador
        inv = j.inventario
        t = jogo.tempo_total
        mostrar_ar = j.nadando or j.ar < AR_MAX - 0.5
        linhas = 5 if mostrar_ar else 4
        painel = pygame.Rect(8, 8, 290, 22 + linhas * 26 + 30)
        self.painel(tela, painel, 205)
        y = painel.y + 14
        self.barra(tela, 20, y, j.vida, VIDA_MAX, COR_VIDA, "vida", t)
        self.barra(tela, 20, y + 26, j.fome, FOME_MAX, COR_FOME, "fome", t)
        self.barra(tela, 20, y + 52, j.sede, SEDE_MAX, COR_SEDE, "sede", t)
        self.barra(tela, 20, y + 78, j.energia, ENERGIA_MAX, COR_ENERGIA, "energia", t)
        if mostrar_ar:
            self.barra(tela, 20, y + 104, j.ar, AR_MAX, COR_AR, "ar", t)
        yy = painel.bottom - 30
        tela.blit(self.hud_peq["dano"], (20, yy))
        self.texto(tela, str(inv.dano()), (40, yy), self.fonte_peq)
        tela.blit(self.hud_peq["defesa"], (70, yy))
        self.texto(tela, str(inv.defesa()), (90, yy), self.fonte_peq)
        tela.blit(self.hud_peq["temp"], (120, yy))
        temp, efeito = jogo.temperatura_atual()
        cor_t = (150, 200, 255) if temp < 3 else (255, 150, 100) if temp > 27 else (220, 236, 210)
        self.texto(tela, f"{temp:.0f}°C {efeito}", (140, yy), self.fonte_peq, cor_t)

        self.desenhar_relogio(tela, jogo)
        self.desenhar_minimapa(tela, jogo)
        self.desenhar_barra_rapida(tela, jogo)
        z = jogo.camadas.z
        if z < 0:
            from camadas import nome_camada
            self.texto(tela, f"Camada {z}: {nome_camada(z)}", (LARGURA_TELA // 2, 14), self.fonte_media,
                       (255, 190, 120) if z <= -4 else (190, 210, 255), centro=True, contorno=True)

        dica = jogo.dica_interacao()
        if dica:
            self.texto(tela, dica, (LARGURA_TELA // 2, ALTURA_TELA - 112), self.fonte_media,
                       (255, 240, 150), centro=True, contorno=True)
        if jogo.estado == "jogando":
            y = ALTURA_TELA - 150
            for msg, resta in reversed(jogo.mensagens[-4:]):
                img = self.fonte.render(msg, False, COR_TEXTO)
                fundo = pygame.Surface((img.get_width() + 16, 24), pygame.SRCALPHA)
                fundo.fill((16, 14, 24, int(150 * min(1.0, resta))))
                x = LARGURA_TELA // 2 - fundo.get_width() // 2
                tela.blit(fundo, (x, y - 3))
                self.texto(tela, msg, (LARGURA_TELA // 2, y), centro=True)
                y -= 27

    def desenhar_relogio(self, tela, jogo):
        ret = pygame.Rect(LARGURA_TELA - 252, 8, 244, 104)
        self.painel(tela, ret, 205)
        # mostrador: arco do céu com sol/lua andando
        cx, cy, r = ret.x + 46, ret.y + 62, 32
        hora = jogo.hora()
        noite = jogo.e_noite()
        sub = jogo.subterraneo()
        ceu = (52, 44, 50) if sub else (40, 44, 90) if noite else (110, 170, 230)
        pygame.draw.circle(tela, BORDA_ESC, (cx, cy), r + 4)
        pygame.draw.circle(tela, ceu, (cx, cy), r)
        pygame.draw.rect(tela, FUNDO, (cx - r - 5, cy + 1, 2 * r + 10, r + 6))
        pygame.draw.rect(tela, (70, 120, 60), (cx - r, cy - 4, 2 * r, 5))
        ang = math.pi * (1 - ((hora - 6) % 12) / 12.0)
        ix, iy = cx + math.cos(ang) * (r - 10), cy - 6 - math.sin(ang) * (r - 14)
        if not sub:
            icone = self.hud["lua" if (hora < 6 or hora >= 18) else "sol"]
            tela.blit(icone, (int(ix) - 12, int(iy) - 12))
        h, m = int(hora), int((hora % 1) * 60)
        x = ret.x + 92
        self.texto(tela, f"Dia {jogo.dia}   {h:02d}:{m:02d}", (x, ret.y + 12), self.fonte)
        if sub:
            # na masmorra / caverna não se vê o céu: sem estação nem tempo
            z = jogo.camadas.z
            self.texto(tela, "Masmorra" if jogo.estruturas.subterraneo else f"Caverna ({z})", (x, ret.y + 40),
                       self.fonte, (200, 170, 255))
            self.texto(tela, "Subsolo - sem céu", (x, ret.y + 66), self.fonte_peq, (150, 144, 170))
            return
        est = jogo.estacao
        tela.blit(self.hud_peq[est], (x, ret.y + 38))
        dia_est = (jogo.dia - 1) % DIAS_POR_ESTACAO + 1
        self.texto(tela, f"{NOMES_ESTACOES_ANO[est]} {dia_est}/{DIAS_POR_ESTACAO}", (x + 22, ret.y + 38),
                   self.fonte_peq, (230, 220, 180))
        clima = jogo.clima
        ic = "neve" if clima.estado == "chuva" and est == "inverno" else \
            {"chuva": "chuva", "seca": "seca"}.get(clima.estado, "lua" if noite else "sol")
        tela.blit(self.hud_peq[ic], (x, ret.y + 60))
        tx, ty = int(jogo.jogador.x // 16), int(jogo.jogador.y // 16)
        bioma = BIOMAS[jogo.mundo.bioma(tx, ty)]["nome"]
        self.texto(tela, clima.nome(), (x + 22, ret.y + 60), self.fonte_peq)
        self.texto(tela, bioma, (x, ret.y + 82), self.fonte_peq, (190, 210, 170))

    def desenhar_minimapa(self, tela, jogo):
        mm = jogo.minimapa
        from minimapa import TAMANHOS
        lado, px = TAMANHOS[mm.tamanho]
        ret = pygame.Rect(LARGURA_TELA - lado - 14, 120, lado + 6, lado + 6)
        self.ret_minimapa = ret
        tela.blit(self.moldura(ret.w, ret.h, "barra"), ret.topleft)
        if jogo.estruturas.subterraneo:
            dentro = ret.inflate(-6, -6)
            tela.fill((14, 12, 20), dentro)
            self.texto(tela, "Masmorra", (dentro.centerx, dentro.centery - 14), self.fonte_peq, (200, 170, 255),
                       centro=True)
            self.texto(tela, "sem mapa aqui", (dentro.centerx, dentro.centery + 6), self.fonte_peq,
                       (150, 144, 170), centro=True)
            return
        dentro = ret.inflate(-6, -6)
        j = jogo.jogador
        img, origem = mm.desenhar_regiao(jogo.mundo, j.x / 16, j.y / 16, dentro.w, dentro.h, px)
        tela.blit(img, dentro.topleft)
        tela.set_clip(dentro)
        mm.desenhar_marcadores(tela, jogo.marcadores_mapa(), origem, px, dentro, self.hud_peq)
        tela.set_clip(None)
        self.texto(tela, "M tamanho  N mapa", (ret.centerx, ret.bottom + 4), self.fonte_peq, (190, 186, 206),
                   centro=True)

    def desenhar_barra_rapida(self, tela, jogo):
        inv = jogo.jogador.inventario
        fundo = self.ret_barra[0].unionall(self.ret_barra).inflate(16, 14)
        self.painel(tela, fundo, 180)
        for i, ret in enumerate(self.ret_barra):
            sel = i == inv.selecionado
            r = ret.move(0, -4) if sel else ret
            self.espaco(tela, r, inv.espacos[i], sel, str(i + 1))
        # equipamentos (miniaturas à esquerda)
        x = fundo.x - 4 * 30 - 14
        caixa = pygame.Rect(x - 6, fundo.y, 4 * 30 + 12, fundo.h)
        self.painel(tela, caixa, 180)
        for n, slot in enumerate(ORDEM_SLOTS):
            r = pygame.Rect(x + n * 30, caixa.centery - 14, 28, 28)
            tela.blit(self.moldura(28, 28, "espaco"), r.topleft)
            e = inv.equipamento[slot]
            if e:
                tela.blit(self.icones_peq[e[0]], (r.x + 2, r.y + 2))
        # [v0.5] barra de XP e nível
        nivel, frac = jogo.nivel_xp()
        bx, by, bw = fundo.x + 8, fundo.y - 9, fundo.w - 16
        pygame.draw.rect(tela, (16, 14, 22), (bx - 2, by - 2, bw + 4, 8))
        pygame.draw.rect(tela, (40, 60, 30), (bx, by, bw, 4))
        pygame.draw.rect(tela, COR_XP, (bx, by, int(bw * frac), 4))
        if nivel > 0:
            self.texto(tela, str(nivel), (fundo.centerx, by - 18), self.fonte, (170, 255, 110), centro=True,
                       contorno=True)
        item = inv.item_selecionado()
        if item:
            dica = ITENS[item]["nome"]
            tipo = ITENS[item]["tipo"]
            if tipo == "construcao":
                dica += "  (botão direito para colocar)"
            elif tipo in ("comida", "bebida"):
                dica += "  (F ou botão direito)"
            elif item == "vara_pesca":
                dica += "  (botão direito na água)"
            elif item == "arco":
                dica += f"  (clique para atirar - flechas: {inv.quantidade('flecha')})"
            e = inv.espacos[inv.selecionado]
            if e and len(e) > 2:
                dica += f"  [{e[2]}/{ITENS[item].get('durabilidade', e[2])}]"
            self.texto(tela, dica, (LARGURA_TELA // 2, fundo.y - 40), self.fonte_peq, centro=True)

    def desenhar_barra_quebra(self, tela, x, y, fracao):
        larg, alt = 42, 9
        x, y = int(x - larg / 2), int(y)
        tela.blit(self.moldura(larg + 6, alt + 6, "barra"), (x - 3, y - 3))
        pygame.draw.rect(tela, (250, 200, 70), (x, y, int(larg * fracao), alt))
        pygame.draw.rect(tela, (255, 240, 170), (x, y, int(larg * fracao), 3))

    def desenhar_popups(self, tela, popups, cam_x, cam_y):
        for p in popups:
            sx = (p["x"] - cam_x) * ESCALA
            sy = (p["y"] - cam_y) * ESCALA - (1.2 - p["tempo"]) * 30
            if p.get("texto"):
                self.texto(tela, p["texto"], (int(sx), int(sy)), self.fonte, p.get("cor", (255, 245, 170)),
                           centro=True, contorno=True)
            else:
                texto = f"+{p['qtd']} {ITENS[p['item']]['nome']}"
                w = self.fonte.size(texto)[0]
                tela.blit(self.icones_peq[p["item"]], (int(sx) - w // 2 - 28, int(sy) - 4))
                self.texto(tela, texto, (int(sx), int(sy)), self.fonte, (255, 245, 170), centro=True, contorno=True)

    def desenhar_cursor(self, tela, pos, arrastando=None):
        if arrastando:
            tela.blit(self.icones[arrastando[0]], (pos[0] - 16, pos[1] - 16))
            if arrastando[1] > 1:
                self.texto(tela, str(arrastando[1]), (pos[0] + 16, pos[1] + 2), self.fonte_peq, direita=True)
        tela.blit(self.cursor, pos)

    def dica_item(self, tela, item, pos, inv=None):
        """Caixa com nome, tipo e números do item embaixo do mouse."""
        info = ITENS[item]
        tier = _tier(item)
        linhas = [(info["nome"], COR_TIER.get(tier, DOURADO), self.fonte)]
        sub = TIPOS.get(info["tipo"], info["tipo"])
        if tier:
            sub += f"  -  {tier.capitalize()}"
        linhas.append((sub, (170, 164, 190), self.fonte_peq))
        compara = None
        if inv is not None and "slot" in info:
            atual = inv.equipamento.get(info["slot"])
            if atual and atual[0] != item:
                compara = ITENS[atual[0]]
        if "dano" in info:
            txt = f"Dano +{info['dano']}"
            if compara is not None:
                dif = info["dano"] - compara.get("dano", 0)
                txt += f"  ({dif:+d} vs equipado)"
            linhas.append((txt, VERDE, self.fonte_peq))
        if "disparo" in info:
            linhas.append((f"Flechas: dano {info['disparo']}", VERDE, self.fonte_peq))
        if "alcance" in info:
            linhas.append((f"Alcance {info['alcance']} (espada: 10)", VERDE, self.fonte_peq))
        if "defesa" in info:
            txt = f"Defesa +{info['defesa']}  (-{info['defesa'] * 7}% de dano)"
            if compara is not None:
                txt += f"  ({info['defesa'] - compara.get('defesa', 0):+d})"
            linhas.append((txt, VERDE, self.fonte_peq))
        if "ferramenta" in info and info["ferramenta"][0] != "pesca":
            linhas.append((f"Poder {info['ferramenta'][1]} ({info['ferramenta'][0]})", VERDE, self.fonte_peq))
        for chave, nome in (("fome", "Fome"), ("sede", "Sede"), ("vida", "Vida")):
            if chave in info:
                linhas.append((f"{nome} {info[chave]:+d}", VERDE if info[chave] > 0 else VERMELHO, self.fonte_peq))
        if "slot" in info:
            linhas.append((f"Equipa em: {NOMES_SLOTS[info['slot']]}", CINZA_TEXTO, self.fonte_peq))
        if info.get("durabilidade"):
            linhas.append((f"Durabilidade: {info['durabilidade']} usos", (200, 200, 150), self.fonte_peq))
        from blocos import FUNDICAO, COMBUSTIVEL
        if item in FUNDICAO:
            linhas.append((f"Forno: vira {ITENS[FUNDICAO[item]]['nome']}", (255, 180, 110), self.fonte_peq))
        if item in COMBUSTIVEL:
            linhas.append((f"Combustível: {COMBUSTIVEL[item]:.0f} s de fogo", (255, 180, 110), self.fonte_peq))
        if info.get("pilha", 1) > 1:
            linhas.append((f"Pilha até {info['pilha']}", (140, 136, 160), self.fonte_peq))
        if "desc" in info:
            linhas.append((info["desc"], (210, 206, 180), self.fonte_peq))
        larg = max(f.size(l)[0] for l, _, f in linhas) + 26
        alt = 14 + sum(26 if f is self.fonte else 20 for _, _, f in linhas)
        ret = pygame.Rect(pos[0] + 22, pos[1] + 12, larg, alt)
        ret.right = min(ret.right, LARGURA_TELA - 4)
        ret.bottom = min(ret.bottom, ALTURA_TELA - 4)
        self.painel(tela, ret, 248)
        y = ret.y + 8
        for l, cor, f in linhas:
            self.texto(tela, l, (ret.x + 13, y), f, cor)
            y += 26 if f is self.fonte else 20

    # ===========================================================
    # Inventário (I / Tab) e baú
    # ===========================================================
    def _grade(self, tela, jogo, pos_mouse, gx, gy, inv):
        """Mochila 9x3 + barra rápida. Registra os espaços em slots_inventario."""
        self.texto(tela, "Mochila", (gx, gy - 22), self.fonte_peq, CINZA_TEXTO)
        for i in range(TAMANHO_BARRA, TAMANHO_INVENTARIO):
            k = i - TAMANHO_BARRA
            r = pygame.Rect(gx + (k % 9) * (TAM + ESP), gy + (k // 9) * (TAM + ESP), TAM, TAM)
            self.espaco(tela, r, inv.espacos[i], r.collidepoint(pos_mouse))
            self.slots_inventario.append((r, ("inv", i)))
        by = gy + 3 * (TAM + ESP) + 26
        self.texto(tela, "Barra rápida (1-9)", (gx, by - 22), self.fonte_peq, CINZA_TEXTO)
        for i in range(TAMANHO_BARRA):
            r = pygame.Rect(gx + i * (TAM + ESP), by, TAM, TAM)
            self.espaco(tela, r, inv.espacos[i], r.collidepoint(pos_mouse) or i == inv.selecionado, str(i + 1))
            self.slots_inventario.append((r, ("inv", i)))
        return by + TAM

    def desenhar_grade_criacao(self, tela, jogo, pos_mouse, gx, gy, lado):
        """[v0.5] Grade de criação lado x lado + seta + resultado."""
        grade = jogo.grade3 if lado == 3 else jogo.grade2
        self.texto(tela, f"Criação {lado}x{lado}", (gx, gy - 22), self.fonte_peq, CINZA_TEXTO)
        for i in range(lado * lado):
            r = pygame.Rect(gx + (i % lado) * (TAM + ESP), gy + (i // lado) * (TAM + ESP), TAM, TAM)
            self.espaco(tela, r, grade[i], r.collidepoint(pos_mouse))
            self.slots_inventario.append((r, ("grade", i)))
        meio_y = gy + (lado * (TAM + ESP) - ESP) // 2
        sx = gx + lado * (TAM + ESP) + 14
        pygame.draw.polygon(tela, DOURADO, [(sx, meio_y - 8), (sx + 22, meio_y - 8), (sx + 22, meio_y - 16),
                                            (sx + 38, meio_y), (sx + 22, meio_y + 16), (sx + 22, meio_y + 8),
                                            (sx, meio_y + 8)])
        r = pygame.Rect(sx + 50, meio_y - TAM // 2 - 4, TAM + 8, TAM + 8)
        res = jogo.pegar_ref(("saida", 0))
        self.espaco(tela, r, res, r.collidepoint(pos_mouse) and res is not None)
        self.slots_inventario.append((r, ("saida", 0)))
        return r

    def desenhar_inventario(self, tela, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 760, 520)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 22)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "INVENTÁRIO")
        self.slots_inventario = []

        # boneco com a armadura (coluna da esquerda)
        ex, ey = ret.x + 22, ret.y + 40
        fundo = pygame.Rect(ex, ey, 112, 150)
        tela.blit(self.moldura(fundo.w, fundo.h, "espaco"), fundo.topleft)
        j = jogo.jogador
        cab = inv.equipamento["cabeca"][0] if inv.equipamento["cabeca"] else None
        cor = inv.equipamento["corpo"][0] if inv.equipamento["corpo"] else None
        mao = personagem.icone_na_mao(inv, None)
        quadro = int(jogo.tempo_total * 1.5) % 2
        img = self.sprites.jogador("baixo", "parado", quadro, cab, cor, mao)
        tela.blit(pygame.transform.scale(img, (96, 96)), (fundo.x + 8, fundo.y + 18))
        self.texto(tela, f"Dano {inv.dano()}", (ex + 4, fundo.bottom + 8), self.fonte_peq)
        self.texto(tela, f"Defesa {inv.defesa()}", (ex + 4, fundo.bottom + 28), self.fonte_peq)

        # equipamentos
        qx = ex + 124
        self.texto(tela, "Equipamento", (qx, ey - 2), self.fonte_peq, CINZA_TEXTO)
        for n, slot in enumerate(ORDEM_SLOTS):
            r = pygame.Rect(qx, ey + 18 + n * (TAM + 10), TAM, TAM)
            self.espaco(tela, r, inv.equipamento[slot], r.collidepoint(pos_mouse), vazio=self.icones_vazios[slot])
            self.slots_inventario.append((r, ("equip", slot)))

        gx = ret.x + 260
        self.desenhar_grade_criacao(tela, jogo, pos_mouse, gx + 60, ret.y + 62, 2)
        nivel, frac = jogo.nivel_xp()
        self.texto(tela, f"Nível {nivel}  ({int(frac * 100)}%)", (gx + 330, ret.y + 70), self.fonte_peq, COR_XP)
        self.texto(tela, "Bancada: grade 3x3", (gx + 330, ret.y + 94), self.fonte_peq, CINZA_TEXTO)
        self.texto(tela, "C: livro de receitas", (gx + 330, ret.y + 116), self.fonte_peq, CINZA_TEXTO)
        self._grade(tela, jogo, pos_mouse, gx, ret.y + 214, inv)
        self.texto(tela, "Arraste para mover/equipar/criar  -  Botão direito: equipar ou dividir  -  "
                         "Shift+clique: move direto", (ret.centerx, ret.bottom - 26),
                   self.fonte_peq, CINZA_TEXTO, centro=True)
        self._dica_slots(tela, jogo, pos_mouse)

    def _dica_slots(self, tela, jogo, pos_mouse):
        ref = self.no_ponto(self.slots_inventario, pos_mouse)
        if ref and not jogo.arrastando:
            pilha = jogo.pegar_ref(ref)
            if pilha:
                self.dica_item(tela, pilha[0], pos_mouse, jogo.jogador.inventario)

    def desenhar_bau(self, tela, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 560, 470)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 20)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "BAÚ")
        self.slots_inventario = []
        gx = ret.x + (ret.w - (9 * (TAM + ESP) - ESP)) // 2
        gy = ret.y + 44
        bau = jogo.bau_aberto
        self.texto(tela, "Baú", (gx, gy - 22), self.fonte_peq, CINZA_TEXTO)
        for i in range(TAMANHO_BAU):
            r = pygame.Rect(gx + (i % 9) * (TAM + ESP), gy + (i // 9) * (TAM + ESP), TAM, TAM)
            self.espaco(tela, r, bau.conteudo[i] if bau else None, r.collidepoint(pos_mouse))
            self.slots_inventario.append((r, ("bau", i)))
        self._grade(tela, jogo, pos_mouse, gx, gy + 2 * (TAM + ESP) + 40, inv)
        self.texto(tela, "Arraste entre o baú e a mochila  -  Shift+clique move direto  -  E/Esc fecha",
                   (ret.centerx, ret.bottom - 26), self.fonte_peq, CINZA_TEXTO, centro=True)
        self._dica_slots(tela, jogo, pos_mouse)

    def desenhar_bancada(self, tela, jogo, pos_mouse):
        """[v0.5] Bancada: grade 3x3 + mochila."""
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 560, 540)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 16)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "BANCADA")
        self.slots_inventario = []
        gx = ret.x + (ret.w - (9 * (TAM + ESP) - ESP)) // 2
        self.desenhar_grade_criacao(tela, jogo, pos_mouse, gx + 80, ret.y + 56, 3)
        rc = __import__("criacao").casar(jogo.grade3, 3)
        if rc:
            self.texto(tela, ITENS[rc["item"]]["nome"], (gx + 330, ret.y + 200), self.fonte_peq, DOURADO)
        self._grade(tela, jogo, pos_mouse, gx, ret.y + 56 + 3 * (TAM + ESP) + 36, inv)
        self.texto(tela, "Monte a forma na grade e pegue o resultado  -  Shift: cria o máximo  -  C: receitas",
                   (ret.centerx, ret.bottom - 26), self.fonte_peq, CINZA_TEXTO, centro=True)
        self._dica_slots(tela, jogo, pos_mouse)

    def desenhar_forno(self, tela, jogo, pos_mouse):
        """[v0.5] Forno: entrada + combustível -> saída."""
        inv = jogo.jogador.inventario
        forno = jogo.forno_aberto
        ret = pygame.Rect(0, 0, 560, 520)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 20)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "FORNO")
        self.slots_inventario = []
        cx = ret.x + 170
        r_ent = pygame.Rect(cx, ret.y + 50, TAM, TAM)
        r_comb = pygame.Rect(cx, ret.y + 50 + TAM + 44, TAM, TAM)
        r_said = pygame.Rect(cx + 180, ret.y + 50 + (TAM + 44) // 2 - 4, TAM + 8, TAM + 8)
        cont = forno.conteudo if forno else [None, None, None]
        self.texto(tela, "Entrada", (r_ent.x - 80, r_ent.y + 14), self.fonte_peq, CINZA_TEXTO)
        self.texto(tela, "Combustível", (r_comb.x - 104, r_comb.y + 14), self.fonte_peq, CINZA_TEXTO)
        self.texto(tela, "Saída", (r_said.right + 12, r_said.y + 18), self.fonte_peq, CINZA_TEXTO)
        for r, i in ((r_ent, 0), (r_comb, 1), (r_said, 2)):
            self.espaco(tela, r, cont[i], r.collidepoint(pos_mouse))
            self.slots_inventario.append((r, ("forno", i)))
        # fogo (combustível que resta)
        fx, fy = r_ent.centerx, r_ent.bottom + 22
        frac_fogo = (forno.queima / forno.queima_max) if forno and forno.queima > 0 else 0.0
        pygame.draw.rect(tela, (40, 30, 30), (fx - 9, fy - 14, 18, 28))
        if frac_fogo > 0:
            h = int(26 * frac_fogo)
            pygame.draw.rect(tela, (240, 120, 40), (fx - 8, fy + 13 - h, 16, h))
            pygame.draw.rect(tela, (255, 220, 110), (fx - 4, fy + 13 - h // 2, 8, h // 2))
        # seta de progresso
        from blocos import TEMPO_FUNDIR
        prog = (forno.progresso / TEMPO_FUNDIR) if forno else 0.0
        ax, ay = r_ent.right + 24, r_said.centery
        aw = r_said.x - ax - 26
        pygame.draw.rect(tela, (30, 26, 40), (ax, ay - 7, aw, 14))
        pygame.draw.rect(tela, DOURADO, (ax, ay - 5, int(aw * prog), 10))
        pygame.draw.polygon(tela, DOURADO if prog > 0.95 else (90, 84, 110),
                            [(ax + aw, ay - 13), (ax + aw + 16, ay), (ax + aw, ay + 13)])
        from criacao import fundivel as criacao_fundivel
        if forno and cont[0] and not criacao_fundivel(cont[0][0]):
            self.texto(tela, "Isso não derrete", (ax, ay + 18), self.fonte_peq, VERMELHO)
        self._grade(tela, jogo, pos_mouse, ret.x + (ret.w - (9 * (TAM + ESP) - ESP)) // 2, ret.y + 250, inv)
        self.texto(tela, "Minérios, areia, pedregulho, comida crua... + carvão/madeira  -  Shift+clique",
                   (ret.centerx, ret.bottom - 26), self.fonte_peq, CINZA_TEXTO, centro=True)
        self._dica_slots(tela, jogo, pos_mouse)

    # ===========================================================
    # Criação (C)
    # ===========================================================
    def desenhar_criacao(self, tela, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 780, 524)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 4)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "CRIAÇÃO")

        self.ret_abas = []
        larg_aba = (ret.w - 32) // len(CATEGORIAS)
        for n, cat in enumerate(CATEGORIAS):
            r = pygame.Rect(ret.x + 16 + n * larg_aba, ret.y + 30, larg_aba - 4, 34)
            ativa = cat == jogo.categoria
            estilo = "botao_sel" if ativa else "botao"
            if r.collidepoint(pos_mouse) and not ativa:
                r = r.move(0, -2)
            tela.blit(self.moldura(r.w, r.h, estilo, 245), r.topleft)
            self.texto(tela, cat, (r.centerx, r.y + 10), self.fonte_peq,
                       (255, 240, 160) if ativa else (226, 220, 240), centro=True)
            self.ret_abas.append((r, cat))

        self.ret_receitas = []
        receitas = [(i, rc) for i, rc in enumerate(RECEITAS) if rc["categoria"] == jogo.categoria]
        y0 = ret.y + 74
        larg = (ret.w - 40) // 2
        alt = 48
        por_coluna = 8
        for n, (indice, rc) in enumerate(receitas[:por_coluna * 2]):
            col, lin = n // por_coluna, n % por_coluna
            r = pygame.Rect(ret.x + 16 + col * (larg + 8), y0 + lin * (alt + 2), larg, alt)
            pode, motivo = jogo.pode_criar(rc)
            sel = r.collidepoint(pos_mouse) or jogo.selecao_criacao == indice
            tela.blit(self.moldura(r.w, r.h, "botao_sel" if sel else "espaco", 230), r.topleft)
            tela.blit(self.icones[rc["item"]], (r.x + 8, r.y + 8))
            cor = COR_TIER.get(_tier(rc["item"]), COR_TEXTO) if pode else (150, 146, 160)
            nome = ITENS[rc["item"]]["nome"] + (f" x{rc.get('qtd', 1)}" if rc.get("qtd", 1) > 1 else "")
            self.texto(tela, nome, (r.x + 48, r.y + 6), self.fonte_peq, cor)
            est = rc.get("estacao")
            if est:
                perto = jogo.estacao_perto(est) or (est == "bancada" and jogo.estado == "bancada")
                self.texto(tela, f"{NOMES_ESTACOES[est]}", (r.x + 48, r.y + 26), self.fonte_peq,
                           VERDE if perto else VERMELHO)
            elif "forma" in rc or "sem_forma" in rc:
                self.texto(tela, "Grade 2x2", (r.x + 48, r.y + 26), self.fonte_peq, (170, 200, 170))
            # forma da receita (mini grade 3x3) ou custo
            if "forma" in rc:
                from blocos import CHAVES
                cel = 14
                gx = r.right - 3 * cel - 8
                gy = r.y + (alt - 3 * cel) // 2
                for jj in range(3):
                    for ii in range(3):
                        pygame.draw.rect(tela, (26, 22, 36), (gx + ii * cel, gy + jj * cel, cel - 1, cel - 1))
                for jj, linha in enumerate(rc["forma"]):
                    for ii, letra in enumerate(linha):
                        if letra != " ":
                            tela.blit(self.icones_mini[CHAVES[letra]], (gx + ii * cel, gy + jj * cel))
                cx = gx - 8
            else:
                cx = r.right - 10
            for item, qtd in reversed(list(rc["custo"].items())):
                tem = inv.quantidade(item)
                txt = f"{tem}/{qtd}"
                cx -= self.fonte_peq.size(txt)[0]
                self.texto(tela, txt, (cx, r.y + 26), self.fonte_peq, VERDE if tem >= qtd else VERMELHO)
                if "forma" not in rc:
                    cx -= 26
                    tela.blit(self.icones_peq[item], (cx, r.y + 20))
                cx -= 8
            self.ret_receitas.append((r, indice))
        self.texto(tela, "Clique numa receita para criar  -  Clique nas abas para mudar de categoria  -  C/Esc fecha",
                   (ret.centerx, ret.bottom - 26), self.fonte_peq, CINZA_TEXTO, centro=True)
        indice = self.no_ponto(self.ret_receitas, pos_mouse)
        if indice is not None:
            self.dica_item(tela, RECEITAS[indice]["item"], pos_mouse, inv)

    # ===========================================================
    # Tela inicial, pausa e controles
    # ===========================================================
    def _titulo_jogo(self, tela, y, jogo):
        texto = "SOBREVIVÊNCIA PIXEL"
        onda = int(math.sin(jogo.tempo_total * 2) * 3)
        self.texto(tela, texto, (LARGURA_TELA // 2, y + onda), self.fonte_titulo, (255, 214, 100),
                   centro=True, contorno=True)

    def desenhar_menu_inicial(self, tela, jogo, pos_mouse):
        self.botoes = {}
        ret = pygame.Rect(0, 0, 580, 400)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 + 40)
        self._titulo_jogo(tela, ret.y - 110, jogo)
        self.texto(tela, "v0.5 - blocos, cavernas, minérios e criação em grade", (LARGURA_TELA // 2, ret.y - 40),
                   self.fonte, (230, 226, 246), centro=True, contorno=True)
        self.painel(tela, ret, 238)
        self.texto(tela, "Semente do mundo:", (ret.x + 50, ret.y + 24), self.fonte)
        caixa = pygame.Rect(ret.x + 50, ret.y + 50, ret.w - 100, 46)
        tela.blit(self.moldura(caixa.w, caixa.h, "espaco_sel"), caixa.topleft)
        cursor = "_" if int(jogo.tempo_total * 2) % 2 == 0 else " "
        if jogo.texto_semente:
            self.texto(tela, jogo.texto_semente + cursor, (caixa.x + 14, caixa.y + 11), self.fonte_media)
        else:
            self.texto(tela, "(vazio = aleatória)" + cursor, (caixa.x + 14, caixa.y + 13), self.fonte,
                       (140, 130, 120))
        self.texto(tela, "Digite números ou palavras. A mesma semente gera o mesmo mundo.",
                   (ret.centerx, caixa.bottom + 10), self.fonte_peq, CINZA_TEXTO, centro=True)
        largura = (ret.w - 120) // 2
        self.botao(tela, "jogar", pygame.Rect(ret.x + 50, ret.y + 140, largura, 48), "Jogar (Enter)", pos_mouse)
        self.botao(tela, "aleatoria", pygame.Rect(ret.x + 70 + largura, ret.y + 140, largura, 48),
                   "Semente aleatória", pos_mouse)
        self.botao(tela, "carregar", pygame.Rect(ret.x + 50, ret.y + 198, ret.w - 100, 48),
                   "Carregar jogo salvo (F9)", pos_mouse, ativo=jogo.tem_save)
        self.botao(tela, "controles", pygame.Rect(ret.x + 50, ret.y + 256, largura, 48), "Controles", pos_mouse)
        self.botao(tela, "sair", pygame.Rect(ret.x + 70 + largura, ret.y + 256, largura, 48), "Sair", pos_mouse)
        if jogo.mensagens:
            self.texto(tela, jogo.mensagens[-1][0], (ret.centerx, ret.bottom - 40), self.fonte_peq,
                       (255, 160, 150), centro=True)
        gp = jogo.controles.joystick
        if gp is not None:
            self.texto(tela, f"Controle conectado: {gp.get_name()}", (ret.centerx, ret.bottom + 10),
                       self.fonte_peq, VERDE, centro=True, contorno=True)

    def desenhar_pausa(self, tela, jogo, pos_mouse):
        self.texto(tela, f"Semente do mundo: {jogo.mundo.semente}", (LARGURA_TELA // 2, ALTURA_TELA - 30),
                   self.fonte_peq, (200, 194, 220), centro=True)
        self.botoes = {}
        escuro = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        escuro.fill((10, 8, 20, 140))
        tela.blit(escuro, (0, 0))
        ret = pygame.Rect(0, 0, 360, 330)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.ret_painel = ret
        self.painel(tela, ret, 245)
        self.titulo_painel(tela, ret, "PAUSA")
        nomes = [("continuar", "Continuar (Esc)"), ("controles", "Controles"), ("ajuda", "Ajuda (H)"),
                 ("salvar", "Salvar (F5)"), ("menu", "Menu inicial")]
        for n, (nome, rotulo) in enumerate(nomes):
            self.botao(tela, nome, pygame.Rect(ret.x + 40, ret.y + 34 + n * 56, ret.w - 80, 46), rotulo, pos_mouse)

    def desenhar_controles(self, tela, jogo, pos_mouse):
        self.botoes = {}
        ret = pygame.Rect(0, 0, 640, 560)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 + 6)
        self.ret_painel = ret
        self.painel(tela, ret, 248)
        self.titulo_painel(tela, ret, "CONTROLES")
        self.ret_controles = []
        y = ret.y + 30
        for acao, nome, _ in ACOES:
            r = pygame.Rect(ret.x + 24, y, ret.w - 48, 27)
            esperando = jogo.esperando_tecla == acao
            if esperando or r.collidepoint(pos_mouse):
                tela.blit(self.moldura(r.w, r.h, "botao_sel" if esperando else "botao", 230), r.topleft)
            self.texto(tela, nome, (r.x + 12, r.y + 6), self.fonte_peq)
            txt = "Aperte uma tecla... (Esc cancela)" if esperando else jogo.controles.texto(acao)
            self.texto(tela, txt, (r.right - 12, r.y + 6), self.fonte_peq,
                       (255, 230, 130) if esperando else (180, 220, 255), direita=True)
            self.ret_controles.append((r, acao))
            y += 29
        self.texto(tela, "Clique numa ação e aperte a nova tecla.  Barra rápida: 1-9 / roda do mouse.",
                   (ret.centerx, y + 6), self.fonte_peq, CINZA_TEXTO, centro=True)
        gp = jogo.controles.joystick
        txt = (f"Controle: {gp.get_name()}  (analógico anda, A interage, B rola, X ataca, Y inventário, "
               f"LB/RB barra, LT corre)") if gp else "Nenhum controle (gamepad) conectado"
        self.texto(tela, txt, (ret.centerx, y + 24), self.fonte_peq, VERDE if gp else (150, 146, 160), centro=True)
        largura = (ret.w - 80) // 2
        self.botao(tela, "padrao", pygame.Rect(ret.x + 30, ret.bottom - 62, largura, 44), "Restaurar padrão", pos_mouse)
        self.botao(tela, "voltar", pygame.Rect(ret.x + 50 + largura, ret.bottom - 62, largura, 44), "Voltar (Esc)",
                   pos_mouse)

    # ===========================================================
    # Mapa completo (N)
    # ===========================================================
    def desenhar_mapa(self, tela, jogo, pos_mouse):
        ret = pygame.Rect(30, 40, LARGURA_TELA - 60, ALTURA_TELA - 70)
        self.ret_painel = ret
        self.painel(tela, ret, 250)
        self.titulo_painel(tela, ret, "MAPA")
        dentro = ret.inflate(-24, -60).move(0, 6)
        mm = jogo.minimapa
        px = jogo.zoom_mapa
        img, origem = mm.desenhar_regiao(jogo.mundo, jogo.mapa_centro[0], jogo.mapa_centro[1], dentro.w, dentro.h, px)
        tela.blit(img, dentro.topleft)
        pygame.draw.rect(tela, BORDA_ESC, dentro, 3)
        tela.set_clip(dentro)
        mm.desenhar_marcadores(tela, jogo.marcadores_mapa(), origem, px, dentro, self.hud)
        tela.set_clip(None)
        legenda = "Arraste / WASD: mover   Roda: zoom   Espaço: centralizar   N/Esc: fechar"
        self.texto(tela, legenda, (ret.centerx, ret.bottom - 26), self.fonte_peq, CINZA_TEXTO, centro=True)
        self.texto(tela, f"Chunks explorados: {len(mm.explorados)}   Zoom: {px}x", (dentro.x + 6, dentro.y + 6),
                   self.fonte_peq, contorno=True)

    # ===========================================================
    # Ajuda, morte e sono
    # ===========================================================
    def desenhar_ajuda(self, tela, jogo=None):
        ret = pygame.Rect(0, 0, 820, 560)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 + 6)
        self.painel(tela, ret, 248)
        self.titulo_painel(tela, ret, "COMO JOGAR")
        c = jogo.controles if jogo else None

        def k(acao, padrao):
            return c.texto(acao) if c else padrao
        linhas = [
            (k("cima", "WASD") + " ...", "andar (movimento suave); água funda: você NADA (gasta ar e energia)"),
            (k("correr", "Shift"), "correr (gasta energia)"),
            (k("rolar", "Espaço"), "rolar / esquivar (fica invencível um instante)"),
            ("Esquerdo (segurar)", "minerar blocos, cavar o chão (pá/picareta), atacar, atirar com o arco"),
            ("Direito", "colocar QUALQUER bloco, comer/beber, pescar, abrir baú/bancada/forno"),
            (k("interagir", "E"), "descer pelo buraco / subir a escada, beber, abrir bancada/forno/baú"),
            (k("espiar", "V"), "debaixo da terra: ver a camada de cima (transparente)"),
            (k("comer", "F") + " / " + k("atacar", "J"), "comer / atacar com o teclado"),
            (k("inventario", "I") + " / " + k("criar", "C"), "inventário / criação"),
            (k("minimapa", "M") + " / " + k("mapa", "N"), "tamanho do minimapa / mapa completo"),
            ("F5 / F9 / Esc", "salvar / carregar / pausa (controles configuráveis)"),
        ]
        y = ret.y + 32
        for tecla, acao in linhas:
            self.texto(tela, tecla, (ret.x + 30, y), self.fonte, (255, 220, 120))
            self.texto(tela, acao, (ret.x + 250, y), self.fonte_peq)
            y += 30
        dicas = ["Tora -> 4 tábuas -> gravetos -> bancada (grade 3x3) -> picareta de madeira -> pedra -> ferro -> diamante.",
                 "Cave o chão com a pá: abre um BURACO; E em cima desce uma camada (até -4). Lá embaixo é escuro: tochas!",
                 "Minérios: carvão e ferro (-1), ouro (-2), cristal (-3) e diamante (-4, perto da lava). Derreta no forno.",
                 "Fome: correr, minerar e lutar cansam. Comida cheia cura. Noite: zumbis, esqueletos e o Explosivo.",
                 "Estações, clima, vilas, castelos e masmorras continuam. Ferramentas gastam (barrinha no ícone)."]
        for n, d in enumerate(dicas):
            self.texto(tela, d, (ret.centerx, ret.bottom - 160 + n * 22), self.fonte_peq, (200, 232, 200), centro=True)
        self.texto(tela, "Pressione qualquer tecla ou clique para continuar",
                   (ret.centerx, ret.bottom - 40), self.fonte, (255, 240, 150), centro=True)

    def desenhar_morte(self, tela, jogo, pos_mouse):
        self.botoes = {}
        escuro = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        escuro.fill((60, 0, 0, 170))
        tela.blit(escuro, (0, 0))
        meio = LARGURA_TELA // 2
        self.texto(tela, "VOCÊ MORREU", (meio, 150), self.fonte_titulo, (255, 90, 90), centro=True, contorno=True)
        self.texto(tela, f"Sobreviveu até o dia {jogo.dia}  -  criaturas derrotadas: {jogo.derrotados}",
                   (meio, 235), self.fonte_media, centro=True, contorno=True)
        onde = "na cama" if jogo.ponto_renascer else "no início"
        self.botao(tela, "renascer", pygame.Rect(meio - 250, 290, 500, 48), f"Renascer {onde} (R)", pos_mouse)
        self.botao(tela, "mesma", pygame.Rect(meio - 250, 348, 240, 48), "Recomeçar mundo", pos_mouse)
        self.botao(tela, "novo", pygame.Rect(meio + 10, 348, 240, 48), "Novo mundo", pos_mouse)
        self.texto(tela, "Seus itens ficam onde você caiu. F9 carrega o último save.", (meio, 414),
                   self.fonte, centro=True, contorno=True)

    def desenhar_sono(self, tela, fracao):
        """Tela escurece enquanto dorme (fracao 0..1..0)."""
        a = int(255 * min(1.0, math.sin(fracao * math.pi) * 1.4))
        s = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        s.fill((6, 6, 16, max(0, min(255, a))))
        tela.blit(s, (0, 0))
        if a > 180:
            self.texto(tela, "Zzz...", (LARGURA_TELA // 2, ALTURA_TELA // 2 - 20), self.fonte_grande,
                       (220, 220, 255), centro=True)
