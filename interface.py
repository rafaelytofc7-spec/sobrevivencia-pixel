# -*- coding: utf-8 -*-
"""
interface.py - Telas e HUD: barras de status, barra rápida, inventário com
arrastar-e-soltar, menu de criação com categorias, tela inicial (semente),
ajuda e tela de morte. Desenhado na tela grande para o texto ficar legível.
"""
import pygame

from config import (LARGURA_TELA, ALTURA_TELA, COR_TEXTO, COR_SOMBRA, COR_PAINEL,
                    COR_BORDA, COR_DESTAQUE, COR_VIDA, COR_FOME, COR_SEDE, VIDA_MAX,
                    FOME_MAX, SEDE_MAX, ESCALA, TAMANHO_BARRA, TAMANHO_INVENTARIO)
from dados import ITENS, RECEITAS, CATEGORIAS, NOMES_SLOTS, ORDEM_SLOTS, NOMES_ESTACOES, BIOMAS

TAM = 48          # tamanho de um espaço de item
ESP = 6           # espaço entre eles


class Interface:
    def __init__(self, sprites):
        pygame.font.init()
        self.fonte = pygame.font.Font(None, 24)
        self.fonte_peq = pygame.font.Font(None, 20)
        self.fonte_media = pygame.font.Font(None, 32)
        self.fonte_grande = pygame.font.Font(None, 72)
        self.icones = {n: pygame.transform.scale(img, (32, 32)) for n, img in sprites.icones.items()}
        self.cursor = sprites.cursor
        self.sprites = sprites
        # áreas clicáveis (preenchidas ao desenhar cada tela)
        self.ret_barra = self._espacos_barra()
        self.slots_inventario = []       # [(rect, ref)]
        self.ret_painel = pygame.Rect(0, 0, 0, 0)
        self.ret_abas = []               # [(rect, categoria)]
        self.ret_receitas = []           # [(rect, indice em RECEITAS)]
        self.botoes = {}                 # nome -> rect

    # ===========================================================
    # Utilidades
    # ===========================================================
    def _espacos_barra(self):
        total = TAMANHO_BARRA * (TAM + ESP) - ESP
        x0 = (LARGURA_TELA - total) // 2
        y0 = ALTURA_TELA - TAM - 12
        return [pygame.Rect(x0 + i * (TAM + ESP), y0, TAM, TAM) for i in range(TAMANHO_BARRA)]

    def texto(self, tela, msg, pos, fonte=None, cor=COR_TEXTO, centro=False, direita=False):
        fonte = fonte or self.fonte
        img = fonte.render(msg, False, cor)
        x, y = pos
        if centro:
            x -= img.get_width() // 2
        elif direita:
            x -= img.get_width()
        tela.blit(fonte.render(msg, False, COR_SOMBRA), (x + 2, y + 2))
        tela.blit(img, (x, y))
        return img.get_width()

    def painel(self, tela, ret, alfa=225):
        s = pygame.Surface((ret.w, ret.h), pygame.SRCALPHA)
        s.fill((*COR_PAINEL, alfa))
        tela.blit(s, ret.topleft)
        pygame.draw.rect(tela, COR_BORDA, ret, 3)

    def botao(self, tela, nome, ret, rotulo, pos_mouse, ativo=True):
        self.botoes[nome] = ret
        em_cima = ativo and pos_mouse is not None and ret.collidepoint(pos_mouse)
        fundo = pygame.Surface(ret.size, pygame.SRCALPHA)
        fundo.fill((80, 72, 110, 240) if em_cima else (50, 46, 70, 240))
        tela.blit(fundo, ret.topleft)
        pygame.draw.rect(tela, COR_DESTAQUE if em_cima else COR_BORDA, ret, 3)
        cor = (255, 240, 150) if ativo else (130, 126, 140)
        self.texto(tela, rotulo, (ret.centerx, ret.centery - 10), self.fonte, cor, centro=True)

    def espaco(self, tela, ret, pilha, destaque=False, rotulo=None):
        fundo = pygame.Surface(ret.size, pygame.SRCALPHA)
        fundo.fill((30, 28, 42, 210))
        tela.blit(fundo, ret.topleft)
        pygame.draw.rect(tela, COR_DESTAQUE if destaque else COR_BORDA, ret, 3)
        if rotulo:
            self.texto(tela, rotulo, (ret.x + 4, ret.y + 3), self.fonte_peq, (190, 186, 200))
        if pilha:
            tela.blit(self.icones[pilha[0]], (ret.x + 8, ret.y + 8))
            if pilha[1] > 1:
                self.texto(tela, str(pilha[1]), (ret.right - 4, ret.bottom - 18), self.fonte_peq,
                           direita=True)

    def no_ponto(self, lista, pos):
        for ret, valor in lista:
            if ret.collidepoint(pos):
                return valor
        return None

    def mouse_sobre_interface(self, pos, estado):
        if estado != "jogando":
            return True
        return any(r.collidepoint(pos) for r in self.ret_barra)

    def espaco_barra_no_ponto(self, pos):
        for i, r in enumerate(self.ret_barra):
            if r.collidepoint(pos):
                return i
        return None

    # ===========================================================
    # HUD
    # ===========================================================
    def barra(self, tela, x, y, valor, maximo, cor, rotulo):
        largura, altura = 160, 16
        self.texto(tela, rotulo, (x, y), self.fonte_peq)
        bx = x + 48
        pygame.draw.rect(tela, COR_SOMBRA, (bx - 3, y - 3, largura + 6, altura + 6))
        pygame.draw.rect(tela, (60, 56, 70), (bx, y, largura, altura))
        cheio = int(largura * max(0.0, valor) / maximo)
        pygame.draw.rect(tela, cor, (bx, y, cheio, altura))
        pygame.draw.rect(tela, tuple(min(255, c + 60) for c in cor), (bx, y, cheio, 4))
        self.texto(tela, str(int(valor)), (bx + largura + 10, y), self.fonte_peq)

    def desenhar_hud(self, tela, jogo):
        j = jogo.jogador
        inv = j.inventario
        self.painel(tela, pygame.Rect(8, 8, 296, 110), 170)
        self.barra(tela, 18, 18, j.vida, VIDA_MAX, COR_VIDA, "Vida")
        self.barra(tela, 18, 43, j.fome, FOME_MAX, COR_FOME, "Fome")
        self.barra(tela, 18, 68, j.sede, SEDE_MAX, COR_SEDE, "Sede")
        self.texto(tela, f"Dano {inv.dano()}   Defesa {inv.defesa()}", (18, 93), self.fonte_peq,
                   (210, 206, 220))

        # informações do mundo
        hora = jogo.hora()
        h, m = int(hora), int((hora % 1) * 60)
        tx, ty = int(j.x // 16), int(j.y // 16)
        bioma = BIOMAS[jogo.mundo.bioma(tx, ty)]["nome"]
        painel = pygame.Rect(LARGURA_TELA - 290, 8, 282, 86)
        self.painel(tela, painel, 170)
        periodo = "Noite" if jogo.e_noite() else "Dia"
        self.texto(tela, f"Dia {jogo.dia}  {h:02d}:{m:02d} ({periodo})", (painel.x + 12, painel.y + 10))
        self.texto(tela, f"{bioma}  -  {jogo.clima.nome()}", (painel.x + 12, painel.y + 35))
        self.texto(tela, f"Semente: {jogo.mundo.semente}", (painel.x + 12, painel.y + 60),
                   self.fonte_peq, (200, 196, 210))
        self.texto(tela, "H ajuda  I inventário  C criar", (LARGURA_TELA - 12, 100),
                   self.fonte_peq, (220, 216, 230), direita=True)

        # barra rápida
        for i, ret in enumerate(self.ret_barra):
            self.espaco(tela, ret, inv.espacos[i], i == inv.selecionado, str(i + 1))
        item = inv.item_selecionado()
        if item:
            dica = ITENS[item]["nome"]
            if ITENS[item]["tipo"] == "construcao":
                dica += "  (botão direito para colocar)"
            elif ITENS[item]["tipo"] in ("comida", "bebida"):
                dica += "  (F ou botão direito para consumir)"
            elif item == "vara_pesca":
                dica += "  (botão direito na água)"
            self.texto(tela, dica, (LARGURA_TELA // 2, self.ret_barra[0].y - 22), self.fonte_peq, centro=True)

        dica = jogo.dica_interacao()
        if dica:
            self.texto(tela, dica, (LARGURA_TELA // 2, ALTURA_TELA - 104), self.fonte_media,
                       (255, 240, 150), centro=True)
        if jogo.estado == "jogando":
            y = ALTURA_TELA - 140
            for msg, _ in reversed(jogo.mensagens[-3:]):
                self.texto(tela, msg, (LARGURA_TELA // 2, y), centro=True)
                y -= 24

    def desenhar_barra_quebra(self, tela, x, y, fracao):
        larg, alt = 40, 8
        x, y = int(x - larg / 2), int(y)
        pygame.draw.rect(tela, COR_SOMBRA, (x - 2, y - 2, larg + 4, alt + 4))
        pygame.draw.rect(tela, (70, 64, 80), (x, y, larg, alt))
        pygame.draw.rect(tela, (250, 210, 80), (x, y, int(larg * fracao), alt))
        pygame.draw.rect(tela, (255, 240, 170), (x, y, int(larg * fracao), 2))

    def desenhar_popups(self, tela, popups, cam_x, cam_y):
        for p in popups:
            sx = (p["x"] - cam_x) * ESCALA
            sy = (p["y"] - cam_y) * ESCALA - (1.2 - p["tempo"]) * 30
            texto = p.get("texto") or f"+{p['qtd']} {ITENS[p['item']]['nome']}"
            self.texto(tela, texto, (int(sx), int(sy)), self.fonte, p.get("cor", (255, 245, 170)), centro=True)

    def desenhar_cursor(self, tela, pos, arrastando=None):
        if arrastando:
            tela.blit(self.icones[arrastando[0]], (pos[0] - 16, pos[1] - 16))
            if arrastando[1] > 1:
                self.texto(tela, str(arrastando[1]), (pos[0] + 16, pos[1] + 2), self.fonte_peq, direita=True)
        tela.blit(self.cursor, pos)

    def dica_item(self, tela, item, pos):
        """Caixinha com nome e informações do item embaixo do mouse."""
        info = ITENS[item]
        linhas = [info["nome"]]
        if "dano" in info:
            linhas.append(f"Dano +{info['dano']}")
        if "defesa" in info:
            linhas.append(f"Defesa +{info['defesa']}")
        if "ferramenta" in info and info["ferramenta"][0] != "pesca":
            linhas.append(f"Poder {info['ferramenta'][1]} ({info['ferramenta'][0]})")
        for chave, nome in (("fome", "Fome"), ("sede", "Sede"), ("vida", "Vida")):
            if chave in info:
                linhas.append(f"{nome} {info[chave]:+d}")
        if "slot" in info:
            linhas.append(f"Equipa em: {NOMES_SLOTS[info['slot']]}")
        if "desc" in info:
            linhas.append(info["desc"])
        larg = max(self.fonte_peq.size(l)[0] for l in linhas) + 20
        ret = pygame.Rect(pos[0] + 20, pos[1] + 10, larg, 10 + 20 * len(linhas))
        ret.right = min(ret.right, LARGURA_TELA - 4)
        ret.bottom = min(ret.bottom, ALTURA_TELA - 4)
        self.painel(tela, ret, 245)
        for n, l in enumerate(linhas):
            self.texto(tela, l, (ret.x + 10, ret.y + 6 + n * 20), self.fonte_peq,
                       COR_DESTAQUE if n == 0 else COR_TEXTO)

    # ===========================================================
    # Inventário (I / Tab)
    # ===========================================================
    def desenhar_inventario(self, tela, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 700, 380)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 30)
        self.ret_painel = ret
        self.painel(tela, ret, 240)
        self.texto(tela, "INVENTÁRIO", (ret.centerx, ret.y + 12), self.fonte_media, centro=True)
        self.slots_inventario = []

        # equipamentos (coluna da esquerda)
        ex, ey = ret.x + 24, ret.y + 52
        self.texto(tela, "Equipamento", (ex, ey - 4), self.fonte_peq, (200, 196, 210))
        for n, slot in enumerate(ORDEM_SLOTS):
            r = pygame.Rect(ex, ey + 18 + n * (TAM + 14), TAM, TAM)
            self.espaco(tela, r, inv.equipamento[slot], r.collidepoint(pos_mouse))
            if not inv.equipamento[slot]:
                self.texto(tela, NOMES_SLOTS[slot][:4], (r.centerx, r.centery - 8), self.fonte_peq,
                           (110, 106, 124), centro=True)
            self.texto(tela, NOMES_SLOTS[slot], (r.right + 8, r.y + 16), self.fonte_peq)
            self.slots_inventario.append((r, ("equip", slot)))
        self.texto(tela, f"Dano: {inv.dano()}", (ex, ret.bottom - 70), self.fonte_peq)
        self.texto(tela, f"Defesa: {inv.defesa()}", (ex, ret.bottom - 52), self.fonte_peq)

        # mochila 9x3 + barra rápida
        gx, gy = ret.x + 190, ret.y + 70
        self.texto(tela, "Mochila", (gx, gy - 22), self.fonte_peq, (200, 196, 210))
        for i in range(TAMANHO_BARRA, TAMANHO_INVENTARIO):
            k = i - TAMANHO_BARRA
            r = pygame.Rect(gx + (k % 9) * (TAM + ESP), gy + (k // 9) * (TAM + ESP), TAM, TAM)
            self.espaco(tela, r, inv.espacos[i], r.collidepoint(pos_mouse))
            self.slots_inventario.append((r, ("inv", i)))
        by = gy + 3 * (TAM + ESP) + 26
        self.texto(tela, "Barra rápida (1-9)", (gx, by - 22), self.fonte_peq, (200, 196, 210))
        for i in range(TAMANHO_BARRA):
            r = pygame.Rect(gx + i * (TAM + ESP), by, TAM, TAM)
            self.espaco(tela, r, inv.espacos[i], r.collidepoint(pos_mouse) or i == inv.selecionado, str(i + 1))
            self.slots_inventario.append((r, ("inv", i)))

        self.texto(tela, "Arraste para mover/equipar  -  Botão direito: equipar ou dividir  -  "
                         "Solte fora para jogar no chão", (ret.centerx, ret.bottom - 26),
                   self.fonte_peq, (200, 196, 210), centro=True)
        # dica do item embaixo do mouse
        ref = self.no_ponto(self.slots_inventario, pos_mouse)
        if ref and not jogo.arrastando:
            pilha = inv.pegar(ref)
            if pilha:
                self.dica_item(tela, pilha[0], pos_mouse)

    # ===========================================================
    # Criação (C)
    # ===========================================================
    def desenhar_criacao(self, tela, jogo, pos_mouse):
        inv = jogo.jogador.inventario
        ret = pygame.Rect(0, 0, 740, 520)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2 - 10)
        self.ret_painel = ret
        self.painel(tela, ret, 242)
        self.texto(tela, "CRIAÇÃO", (ret.centerx, ret.y + 12), self.fonte_media, centro=True)

        # abas de categorias
        self.ret_abas = []
        larg_aba = (ret.w - 32) // len(CATEGORIAS)
        for n, cat in enumerate(CATEGORIAS):
            r = pygame.Rect(ret.x + 16 + n * larg_aba, ret.y + 44, larg_aba - 6, 34)
            ativa = cat == jogo.categoria
            fundo = pygame.Surface(r.size, pygame.SRCALPHA)
            fundo.fill((80, 72, 110, 240) if ativa or r.collidepoint(pos_mouse) else (45, 42, 62, 240))
            tela.blit(fundo, r.topleft)
            pygame.draw.rect(tela, COR_DESTAQUE if ativa else COR_BORDA, r, 2)
            self.texto(tela, cat, (r.centerx, r.y + 9), self.fonte_peq, centro=True)
            self.ret_abas.append((r, cat))

        # receitas da categoria
        self.ret_receitas = []
        receitas = [(i, rc) for i, rc in enumerate(RECEITAS) if rc["categoria"] == jogo.categoria]
        y = ret.y + 88
        for n, (indice, rc) in enumerate(receitas):
            r = pygame.Rect(ret.x + 16, y + n * 50, ret.w - 32, 46)
            pode, motivo = jogo.pode_criar(rc)
            if r.collidepoint(pos_mouse) or jogo.selecao_criacao == indice:
                pygame.draw.rect(tela, (70, 64, 96), r)
                pygame.draw.rect(tela, COR_DESTAQUE, r, 2)
            tela.blit(self.icones[rc["item"]], (r.x + 8, r.y + 7))
            cor = COR_TEXTO if pode else (150, 146, 160)
            nome = ITENS[rc["item"]]["nome"] + (f" x{rc.get('qtd', 1)}" if rc.get("qtd", 1) > 1 else "")
            self.texto(tela, nome, (r.x + 52, r.y + 5), self.fonte, cor)
            est = rc.get("estacao")
            if est:
                perto = jogo.estacao_perto(est)
                self.texto(tela, f"Precisa: {NOMES_ESTACOES[est]} por perto",
                           (r.x + 52, r.y + 26), self.fonte_peq,
                           (140, 230, 120) if perto else (240, 110, 100))
            # custo
            cx = r.right - 10
            for item, qtd in reversed(list(rc["custo"].items())):
                tem = inv.quantidade(item)
                txt = f"{tem}/{qtd}"
                cx -= self.fonte.size(txt)[0]
                self.texto(tela, txt, (cx, r.y + 14), self.fonte,
                           (140, 230, 120) if tem >= qtd else (240, 110, 100))
                cx -= 36
                tela.blit(self.icones[item], (cx, r.y + 7))
                cx -= 14
            self.ret_receitas.append((r, indice))
        self.texto(tela, "Clique numa receita para criar  -  Clique nas abas para mudar de categoria  -  C/Esc fecha",
                   (ret.centerx, ret.bottom - 26), self.fonte_peq, (200, 196, 210), centro=True)
        indice = self.no_ponto(self.ret_receitas, pos_mouse)
        if indice is not None:
            self.dica_item(tela, RECEITAS[indice]["item"], pos_mouse)

    # ===========================================================
    # Tela inicial (semente)
    # ===========================================================
    def desenhar_menu_inicial(self, tela, jogo, pos_mouse):
        self.botoes = {}
        ret = pygame.Rect(0, 0, 560, 420)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.painel(tela, ret, 235)
        self.texto(tela, "SOBREVIVÊNCIA PIXEL", (ret.centerx, ret.y + 26), self.fonte_grande,
                   (255, 220, 110), centro=True)
        self.texto(tela, "v0.3 - mundo infinito", (ret.centerx, ret.y + 86), self.fonte, centro=True)
        self.texto(tela, "Semente do mundo:", (ret.x + 50, ret.y + 130), self.fonte)
        caixa = pygame.Rect(ret.x + 50, ret.y + 156, ret.w - 100, 44)
        pygame.draw.rect(tela, (20, 18, 30), caixa)
        pygame.draw.rect(tela, COR_DESTAQUE, caixa, 3)
        cursor = "_" if int(jogo.tempo_total * 2) % 2 == 0 else " "
        mostra = jogo.texto_semente if jogo.texto_semente else ""
        if mostra:
            self.texto(tela, mostra + cursor, (caixa.x + 12, caixa.y + 10), self.fonte_media)
        else:
            self.texto(tela, "(vazio = aleatória)" + cursor, (caixa.x + 12, caixa.y + 12), self.fonte,
                       (130, 126, 140))
        self.texto(tela, "Digite números ou palavras. A mesma semente gera o mesmo mundo.",
                   (ret.centerx, caixa.bottom + 10), self.fonte_peq, (200, 196, 210), centro=True)
        largura = (ret.w - 120) // 2
        self.botao(tela, "jogar", pygame.Rect(ret.x + 50, ret.y + 250, largura, 48), "Jogar (Enter)", pos_mouse)
        self.botao(tela, "aleatoria", pygame.Rect(ret.x + 70 + largura, ret.y + 250, largura, 48),
                   "Semente aleatória", pos_mouse)
        self.botao(tela, "carregar", pygame.Rect(ret.x + 50, ret.y + 312, ret.w - 100, 48),
                   "Carregar jogo salvo (F9)", pos_mouse, ativo=jogo.tem_save)
        if jogo.mensagens:
            self.texto(tela, jogo.mensagens[-1][0], (ret.centerx, ret.bottom - 34), self.fonte_peq,
                       (255, 150, 140), centro=True)

    # ===========================================================
    # Ajuda e morte
    # ===========================================================
    def desenhar_ajuda(self, tela):
        ret = pygame.Rect(0, 0, 780, 540)
        ret.center = (LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.painel(tela, ret, 242)
        self.texto(tela, "COMO JOGAR", (ret.centerx, ret.y + 14), self.fonte_media, (255, 230, 120), centro=True)
        linhas = [
            ("WASD / setas", "andar (água rasa deixa mais lento)"),
            ("Esquerdo (segurar)", "quebrar recurso/construção, atacar bichos"),
            ("Direito", "construir, comer/beber o item da mão, pescar (vara na água)"),
            ("E", "beber água + encher cantil, assar carne/peixe, lenha na fogueira"),
            ("F", "comer/beber o item da mão (ou a melhor comida)"),
            ("Espaço", "atacar na direção que você olha"),
            ("I ou Tab", "inventário (arrastar e soltar, equipar)"),
            ("C", "criação (bancada e fogueira por perto liberam receitas)"),
            ("1-9 / roda", "escolher item da barra rápida"),
            ("F5 / F9", "salvar / carregar"),
            ("H / Esc", "ajuda / fechar janelas"),
        ]
        y = ret.y + 52
        for tecla, acao in linhas:
            self.texto(tela, tecla, (ret.x + 30, y), self.fonte, (255, 220, 120))
            self.texto(tela, acao, (ret.x + 220, y), self.fonte)
            y += 30
        dicas = ["Biomas: Floresta, Planície, Deserto, Pântano, Neve e Montanha (ferro!).",
                 "Chuva enche lagos e rios; na seca eles encolhem e viram lama.",
                 "Lobos caçam animais e você. À noite: slimes e aranhas. No deserto: escorpiões."]
        for n, d in enumerate(dicas):
            self.texto(tela, d, (ret.centerx, ret.bottom - 112 + n * 22), self.fonte_peq,
                       (200, 230, 200), centro=True)
        self.texto(tela, "Pressione qualquer tecla ou clique para continuar",
                   (ret.centerx, ret.bottom - 36), self.fonte, (255, 240, 150), centro=True)

    def desenhar_morte(self, tela, jogo, pos_mouse):
        self.botoes = {}
        escuro = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        escuro.fill((60, 0, 0, 170))
        tela.blit(escuro, (0, 0))
        meio = LARGURA_TELA // 2
        self.texto(tela, "VOCÊ MORREU", (meio, 170), self.fonte_grande, (255, 90, 90), centro=True)
        self.texto(tela, f"Sobreviveu até o dia {jogo.dia}  -  criaturas derrotadas: {jogo.derrotados}",
                   (meio, 255), self.fonte_media, centro=True)
        self.botao(tela, "mesma", pygame.Rect(meio - 250, 320, 240, 48), "Mesma semente (R)", pos_mouse)
        self.botao(tela, "novo", pygame.Rect(meio + 10, 320, 240, 48), "Novo mundo", pos_mouse)
        self.texto(tela, "ou F9 para carregar o último save", (meio, 390), self.fonte, centro=True)
