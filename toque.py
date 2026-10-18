# -*- coding: utf-8 -*-
"""
toque.py - Controles de toque (celular / versão web).

Liga sozinho no primeiro toque na tela (ou com SP_TOQUE=1 para testar no PC).
- Esquerda: joystick virtual (arraste para andar).
- Direita: botões Minerar (segure), Colocar/usar, E, Correr, Rolar, Comer.
- Em cima: Menu, Mochila, Receitas, Mapa (e "Ver cima" nas cavernas).
- Tocar num bloco do mundo: segura = minera/ataca ali; com bloco na mão = coloca.
- Nas janelas (inventário, bancada, menus) o dedo vira o mouse; o X fecha.
"""
import math
import os
import time

import pygame

from config import LARGURA_TELA, ALTURA_TELA, ESCALA, TILE, ALCANCE_MOUSE
from dados import ITENS

W, H = LARGURA_TELA, ALTURA_TELA

# botões redondos: nome -> (x, y, raio, texto, texto pequeno); x medido numa tela de 960 e
# encostado na direita (a tela do celular pode ser mais larga)
_BOTOES_960 = {
    "minerar": (878, 468, 54, "Minerar", "segure"),
    "colocar": (770, 527, 38, "Colocar", "usar"),
    "interagir": (774, 418, 33, "E", "usar/descer"),
    "correr": (885, 352, 30, "Correr", ""),
    "rolar": (790, 330, 26, "Rolar", ""),
    "comer": (916, 567, 25, "Comer", ""),
}
BOTOES = {n: (x + W - 960, y, r, t, st) for n, (x, y, r, t, st) in _BOTOES_960.items()}
# botões de cima (retângulos): nome -> (x, y, w, h, texto)
PILULAS = [
    ("menu", 312, 8, 78, 38, "Menu"),
    ("inventario", 396, 8, 96, 38, "Mochila"),
    ("criar", 498, 8, 100, 38, "Receitas"),
    ("mapa", 604, 8, 78, 38, "Mapa"),
]
PILULA_ESPIAR = ("espiar", 312, 52, 110, 34, "Ver cima")
FECHAR = pygame.Rect(W - 62, 8, 54, 46)
DIREITO = pygame.Rect(W - 150, 62, 142, 40)     # nas janelas de itens: toque vira "botão direito"
ESTADOS_SLOTS = ("inventario", "bau", "bancada", "forno")
ZOOM_MAIS = pygame.Rect(W - 62, 62, 54, 46)
ZOOM_MENOS = pygame.Rect(W - 62, 114, 54, 46)
ZONA_JOYSTICK_X = 400
ZONA_JOYSTICK_Y = 170
RAIO_BASE = 64
RAIO_PINO = 28
INTERATIVOS = ("bau", "bancada", "forno", "fogueira", "cama")
NAO_MINERAR = INTERATIVOS + ("buraco", "escada")
ESPERA_MOUSE_FALSO = 0.8     # ignora o "mouse de mentira" que o navegador manda depois do toque


class Toque:
    def __init__(self, jogo):
        self.jogo = jogo
        self.ativo = os.environ.get("SP_TOQUE") == "1"
        self.dedos = {}               # id do dedo -> papel ("joy", "botao:x", "mundo", "ui", "nada")
        self.joy_base = None
        self.joy_pos = None
        self.vetor = (0.0, 0.0)
        self.correr = False
        self.mundo_pos = None
        self.mundo_botao = 1
        self.ui_pos = (W // 2, H // 2)
        self.ui_apertado = False
        self.ultimo_toque = -10.0
        self.minerando = False
        self.modo_direito = False
        pygame.font.init()
        self.fonte = pygame.font.Font(None, 26)
        self.fonte_peq = pygame.font.Font(None, 18)
        self.fonte_grande = pygame.font.Font(None, 40)
        self._cache = {}
        if self.ativo:
            self.ligar()

    def ligar(self):
        self.ativo = True
        self.jogo.interface.sem_cursor = True

    # ===========================================================
    # Eventos
    # ===========================================================
    def _pos(self, ev):
        return (max(0, min(W - 1, int(ev.x * W))), max(0, min(H - 1, int(ev.y * H))))

    def _mouse(self, tipo, pos, **kw):
        self.jogo.tratar_evento(pygame.event.Event(tipo, pos=pos, **kw))

    def tratar(self, ev):
        """Devolve True se o evento foi usado aqui (o jogo não deve tratar)."""
        t = ev.type
        if t in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            if not self.ativo:
                self.ligar()
            self.ultimo_toque = time.time()
            fid = (getattr(ev, "touch_id", 0), ev.finger_id)
            pos = self._pos(ev)
            if t == pygame.FINGERDOWN:
                self.dedo_desceu(fid, pos)
            elif t == pygame.FINGERMOTION:
                self.dedo_moveu(fid, pos)
            else:
                self.dedo_subiu(fid, pos)
            return True
        if t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
            if getattr(ev, "touch", False):         # mouse "de mentira" criado pelo toque: o dedo já cuida
                if not self.ativo:
                    self.ligar()
                self.ultimo_toque = time.time()
                return True
            if self.ativo and time.time() - self.ultimo_toque < ESPERA_MOUSE_FALSO:
                return True
        return False

    def jogando(self):
        return self.jogo.estado == "jogando"

    def botao_no_ponto(self, pos):
        for nome, (x, y, r, _, _) in BOTOES.items():
            if math.hypot(pos[0] - x, pos[1] - y) <= r + 8:
                return nome
        return None

    def pilulas(self):
        lista = list(PILULAS)
        if self.jogo.camadas.z < 0:
            lista.append(PILULA_ESPIAR)
        return lista

    def pilula_no_ponto(self, pos):
        for nome, x, y, w, h, _ in self.pilulas():
            if pygame.Rect(x, y, w, h).inflate(6, 6).collidepoint(pos):
                return nome
        return None

    def mostra_fechar(self):
        return self.jogo.estado not in ("jogando", "menu_inicial", "morto")

    def dedo_desceu(self, fid, pos):
        jogo = self.jogo
        if not self.jogando():
            if self.mostra_fechar() and FECHAR.collidepoint(pos):
                self.dedos[fid] = "nada"
                self.tecla(pygame.K_ESCAPE)
                return
            if self.jogo.estado == "mapa" and (ZOOM_MAIS.collidepoint(pos) or ZOOM_MENOS.collidepoint(pos)):
                self.dedos[fid] = "nada"
                passo = 1 if ZOOM_MAIS.collidepoint(pos) else -1
                self.jogo.zoom_mapa = max(1, min(6, self.jogo.zoom_mapa + passo))
                return
            if self.jogo.estado in ESTADOS_SLOTS and DIREITO.collidepoint(pos):
                self.dedos[fid] = "nada"
                self.modo_direito = not self.modo_direito
                return
            if "ui" in self.dedos.values():
                self.dedos[fid] = "nada"
                return
            self.dedos[fid] = "ui"
            self.ui_pos = pos
            self.ui_apertado = True
            jogo.pos_mouse = pos
            self._mouse(pygame.MOUSEMOTION, pos, rel=(0, 0), buttons=(1, 0, 0))
            self.botao_ui = 3 if (self.modo_direito and jogo.estado in ESTADOS_SLOTS) else 1
            self._mouse(pygame.MOUSEBUTTONDOWN, pos, button=self.botao_ui)
            return
        b = self.botao_no_ponto(pos)
        if b:
            self.dedos[fid] = "botao:" + b
            self.apertar(b)
            return
        p = self.pilula_no_ponto(pos)
        if p:
            self.dedos[fid] = "nada"
            self.apertar(p)
            return
        ui = jogo.interface
        espaco = ui.espaco_barra_no_ponto(pos)
        if espaco is not None:
            self.dedos[fid] = "nada"
            jogo.jogador.inventario.selecionado = espaco
            return
        if ui.ret_minimapa.collidepoint(pos):
            self.dedos[fid] = "nada"
            jogo.abrir_mapa()
            return
        if pos[0] < ZONA_JOYSTICK_X and pos[1] > ZONA_JOYSTICK_Y and self.joy_base is None:
            self.dedos[fid] = "joy"
            self.joy_base = pos
            self.joy_pos = pos
            self.vetor = (0.0, 0.0)
            return
        if "mundo" in self.dedos.values():
            self.dedos[fid] = "nada"
            return
        # toque no mundo: segura = minerar/atacar; bloco na mão ou baú/bancada = colocar/usar
        self.dedos[fid] = "mundo"
        self.mundo_pos = pos
        jogo.pos_mouse = pos
        botao = 1
        obj = jogo.mundo.objeto_no_ponto(*jogo.mouse_mundo())
        item = jogo.jogador.inventario.item_selecionado()
        tipo = ITENS[item]["tipo"] if item else None
        if (obj is not None and obj.tipo in INTERATIVOS) or tipo in ("construcao", "comida", "bebida") \
                or (obj is None and jogo.tem_vara()):
            botao = 3
        self.mundo_botao = botao
        jogo.clique(botao, pos)

    def dedo_moveu(self, fid, pos):
        papel = self.dedos.get(fid)
        if papel == "joy":
            bx, by = self.joy_base
            dx, dy = pos[0] - bx, pos[1] - by
            d = math.hypot(dx, dy)
            if d > RAIO_BASE * 1.6:                 # a base segue o dedo (joystick flutuante)
                k = (d - RAIO_BASE * 1.6) / d
                self.joy_base = (bx + dx * k, by + dy * k)
            bx, by = self.joy_base
            dx, dy = pos[0] - bx, pos[1] - by
            d = math.hypot(dx, dy)
            self.joy_pos = pos
            if d < 8:
                self.vetor = (0.0, 0.0)
            else:
                f = min(1.0, d / RAIO_BASE)
                self.vetor = (dx / d * f, dy / d * f)
        elif papel == "mundo":
            self.mundo_pos = pos
        elif papel == "ui":
            self.ui_pos = pos
            self.jogo.pos_mouse = pos
            self._mouse(pygame.MOUSEMOTION, pos, rel=(0, 0), buttons=(1, 0, 0))

    def dedo_subiu(self, fid, pos):
        papel = self.dedos.pop(fid, None)
        if papel == "joy":
            self.joy_base = self.joy_pos = None
            self.vetor = (0.0, 0.0)
        elif papel == "mundo":
            self.mundo_pos = None
        elif papel == "ui":
            self.ui_pos = pos
            self.ui_apertado = False
            self.jogo.pos_mouse = pos
            self._mouse(pygame.MOUSEBUTTONUP, pos, button=getattr(self, "botao_ui", 1))
        elif papel == "botao:minerar":
            self.minerando = False

    def soltar_tudo(self):
        for fid, papel in list(self.dedos.items()):
            if papel != "ui":
                self.dedos[fid] = "nada"
        self.joy_base = self.joy_pos = None
        self.vetor = (0.0, 0.0)
        self.mundo_pos = None
        self.minerando = False

    def tecla(self, k, uni=""):
        self.jogo.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=uni, mod=0, scancode=0))

    def apertar(self, nome):
        jogo = self.jogo
        if nome == "minerar":
            self.minerando = True
        elif nome == "colocar":
            self.usar()
        elif nome == "correr":
            self.correr = not self.correr
        elif nome == "menu":
            self.tecla(pygame.K_ESCAPE)
        elif nome in ("interagir", "rolar", "comer", "inventario", "criar", "mapa", "espiar"):
            jogo.tecla_jogando(0, nome)
        if not self.jogando():
            self.soltar_tudo()

    # ===========================================================
    # Mira automática (botões Minerar e Colocar)
    # ===========================================================
    def direcao(self):
        vx, vy = self.vetor
        d = math.hypot(vx, vy)
        if d > 0.3:
            return vx / d, vy / d
        return self.jogo.jogador.VETORES[self.jogo.jogador.direcao]

    def mira_minerar(self):
        """Ponto do mundo que o botão Minerar acerta: monstro perto, depois o bloco na frente."""
        jogo = self.jogo
        j = jogo.jogador
        cx, cy = j.centro
        dx, dy = self.direcao()
        melhor, nota_melhor = None, 1e9
        for c in jogo.criaturas:
            ccx, ccy = c.centro
            dist = math.hypot(ccx - cx, ccy - cy)
            if dist > ALCANCE_MOUSE - 2 or dist < 0.1:
                continue
            frente = ((ccx - cx) * dx + (ccy - cy) * dy) / dist
            nota = dist - 14 * frente - (25 if c.comportamento != "passivo" else 0)
            if nota < nota_melhor:
                melhor, nota_melhor = (ccx, ccy), nota
        if melhor and nota_melhor < 30:
            return melhor
        ptx, pty = int(cx // TILE), int(cy // TILE)
        for ty in range(pty - 3, pty + 4):
            for tx in range(ptx - 3, ptx + 4):
                obj = jogo.mundo.objeto(tx, ty)
                if obj is None or obj.tipo in NAO_MINERAR:
                    continue
                ox, oy = tx * TILE + 8, ty * TILE + 8
                dist = math.hypot(ox - cx, oy - cy)
                if dist > ALCANCE_MOUSE - 2:
                    continue
                frente = ((ox - cx) * dx + (oy - cy) * dy) / max(dist, 0.1)
                if frente < 0.35 and dist > 12:
                    continue                      # só o que está na frente (não quebra a casa atrás)
                nota = dist - 10 * frente
                if nota < nota_melhor:
                    melhor, nota_melhor = (ox, oy), nota
        if melhor:
            return melhor
        # nada na frente: cava o chão do bloco à frente
        fx, fy = cx + dx * 14, cy + dy * 14
        return (int(fx // TILE) * TILE + 8, int(fy // TILE) * TILE + 8)

    def mira_usar(self):
        jogo = self.jogo
        j = jogo.jogador
        cx, cy = j.centro
        dx, dy = self.direcao()
        ptx, pty = int(cx // TILE), int(cy // TILE)
        melhor, nota_melhor = None, 1e9
        for ty in range(pty - 3, pty + 4):
            for tx in range(ptx - 3, ptx + 4):
                obj = jogo.mundo.objeto(tx, ty)
                if obj is None or obj.tipo not in INTERATIVOS:
                    continue
                ox, oy = obj.centro
                dist = math.hypot(ox - cx, oy - cy)
                if dist <= ALCANCE_MOUSE - 2 and dist < nota_melhor:
                    melhor, nota_melhor = (ox, oy), dist
        item = j.inventario.item_selecionado()
        tipo = ITENS[item]["tipo"] if item else None
        if melhor and tipo != "construcao":
            return melhor
        fx, fy = cx + dx * 15, cy + dy * 15
        ftx, fty = int(fx // TILE), int(fy // TILE)
        if (ftx, fty) == (ptx, pty):
            ftx, fty = ptx + int(round(dx)), pty + int(round(dy))
        return (ftx * TILE + 8, fty * TILE + 8)

    def tela_de(self, ponto):
        jogo = self.jogo
        return (int((ponto[0] - jogo.camera_x) * ESCALA), int((ponto[1] - jogo.camera_y) * ESCALA))

    def usar(self):
        jogo = self.jogo
        pos = self.tela_de(self.mira_usar())
        jogo.pos_mouse = pos
        jogo.clique(3, pos)

    # ===========================================================
    # A cada quadro
    # ===========================================================
    def entrada(self):
        """(pos, botões) do "mouse" para jogo.atualizar(), ou None sem toque."""
        if not self.ativo:
            return None
        jogo = self.jogo
        jogo.controles.vetor_toque = self.vetor if self.jogando() else (0.0, 0.0)
        jogo.controles.correr_toque = self.correr and self.jogando()
        if not self.jogando():
            if jogo.estado != "mapa":
                self.vetor = (0.0, 0.0)
            return (self.ui_pos, (self.ui_apertado, False, False))
        if self.mundo_pos is not None:
            b = self.mundo_botao
            return (self.mundo_pos, (b == 1, False, b == 3))
        try:
            pos = self.tela_de(self.mira_minerar())
        except AttributeError:
            pos = (W // 2, H // 2)
        return (pos, (self.minerando, False, False))

    # ===========================================================
    # Desenho
    # ===========================================================
    def _circulo(self, r, cor, alfa):
        k = ("c", r, cor, alfa)
        s = self._cache.get(k)
        if s is None:
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, cor + (alfa,), (r + 2, r + 2), r)
            pygame.draw.circle(s, (255, 255, 255, min(255, alfa + 70)), (r + 2, r + 2), r, 3)
            self._cache[k] = s
        return s

    def _texto(self, msg, fonte, cor=(255, 255, 255)):
        k = ("t", msg, id(fonte), cor)
        s = self._cache.get(k)
        if s is None:
            sombra = fonte.render(msg, True, (0, 0, 0))
            frente = fonte.render(msg, True, cor)
            s = pygame.Surface((frente.get_width() + 2, frente.get_height() + 2), pygame.SRCALPHA)
            s.blit(sombra, (2, 2))
            s.blit(frente, (0, 0))
            self._cache[k] = s
        return s

    def _texto_centro(self, tela, msg, fonte, centro, cor=(255, 255, 255)):
        s = self._texto(msg, fonte, cor)
        tela.blit(s, s.get_rect(center=centro))

    def _caixa(self, w, h, apertado=False):
        k = ("r", w, h, apertado)
        s = self._cache.get(k)
        if s is None:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s, (40, 36, 60, 200 if apertado else 150), (0, 0, w, h), border_radius=10)
            pygame.draw.rect(s, (255, 255, 255, 170), (0, 0, w, h), 2, border_radius=10)
            self._cache[k] = s
        return s

    def desenhar(self, tela):
        if not self.ativo:
            return
        jogo = self.jogo
        if jogo.estado == "menu_inicial":
            self._texto_centro(tela, "Toque em Jogar para começar", self.fonte, (W // 2, H - 22), (255, 236, 140))
            return
        if self.mostra_fechar():
            tela.blit(self._caixa(FECHAR.w, FECHAR.h), FECHAR.topleft)
            self._texto_centro(tela, "X", self.fonte_grande, FECHAR.center)
            if jogo.estado == "mapa":
                for r, txt in ((ZOOM_MAIS, "+"), (ZOOM_MENOS, "-")):
                    tela.blit(self._caixa(r.w, r.h), r.topleft)
                    self._texto_centro(tela, txt, self.fonte_grande, r.center)
            if jogo.estado in ESTADOS_SLOTS:
                tela.blit(self._caixa(DIREITO.w, DIREITO.h, self.modo_direito), DIREITO.topleft)
                cor = (255, 220, 90) if self.modo_direito else (255, 255, 255)
                self._texto_centro(tela, "Dividir/equipar" + (": SIM" if self.modo_direito else ""),
                                   self.fonte_peq, DIREITO.center, cor)
            if jogo.estado == "ajuda":
                faixa = pygame.Surface((W, 54), pygame.SRCALPHA)
                faixa.fill((10, 8, 20, 215))
                tela.blit(faixa, (0, H - 54))
                self._texto_centro(tela, "Celular: arraste à esquerda para andar  •  segure Minerar  •  "
                                   "toque num bloco para minerar ou colocar", self.fonte_peq, (W // 2, H - 38),
                                   (255, 236, 140))
                self._texto_centro(tela, "Toque na tela para continuar", self.fonte, (W // 2, H - 16))
            return
        if not self.jogando():
            return
        apertados = {p[7:] for p in self.dedos.values() if p.startswith("botao:")}
        for nome, (x, y, r, txt, sub) in BOTOES.items():
            ligado = nome in apertados or (nome == "correr" and self.correr) or (nome == "minerar" and self.minerando)
            cor = (230, 190, 70) if ligado else ((170, 60, 50) if nome == "minerar" else (40, 36, 60))
            tela.blit(self._circulo(r, cor, 190 if ligado else 120), (x - r - 2, y - r - 2))
            f = self.fonte_grande if txt == "E" else (self.fonte if r >= 33 else self.fonte_peq)
            self._texto_centro(tela, txt, f, (x, y - (7 if sub else 0)))
            if sub:
                self._texto_centro(tela, sub, self.fonte_peq, (x, y + 14), (230, 225, 200))
        for nome, x, y, w, h, txt in self.pilulas():
            tela.blit(self._caixa(w, h), (x, y))
            self._texto_centro(tela, txt, self.fonte, (x + w // 2, y + h // 2))
        if self.joy_base is not None:
            bx, by = int(self.joy_base[0]), int(self.joy_base[1])
            tela.blit(self._circulo(RAIO_BASE, (40, 36, 60), 90), (bx - RAIO_BASE - 2, by - RAIO_BASE - 2))
            px = bx + int(self.vetor[0] * RAIO_BASE)
            py = by + int(self.vetor[1] * RAIO_BASE)
            tela.blit(self._circulo(RAIO_PINO, (220, 220, 235), 170), (px - RAIO_PINO - 2, py - RAIO_PINO - 2))
        else:
            bx, by = 150, 410
            tela.blit(self._circulo(RAIO_BASE, (40, 36, 60), 55), (bx - RAIO_BASE - 2, by - RAIO_BASE - 2))
            tela.blit(self._circulo(RAIO_PINO, (220, 220, 235), 80), (bx - RAIO_PINO - 2, by - RAIO_PINO - 2))
            self._texto_centro(tela, "arraste para andar", self.fonte_peq, (bx, by + RAIO_BASE + 12), (230, 225, 200))
