# -*- coding: utf-8 -*-
"""
minimapa.py - Minimapa no canto da tela e mapa completo.

- Cada chunk que o jogador já viu fica "explorado" e ganha uma imagenzinha
  (1 pixel por bloco). O que não foi explorado aparece escuro (névoa).
- M troca o tamanho do minimapa (pequeno / grande); N abre o mapa completo
  (arraste com o mouse ou WASD para mover, roda do mouse para zoom).
- Marcadores: jogador, cama, baús e estruturas (jogo.marcadores_mapa()).
"""
import math
import pygame

from config import (TILE, TAMANHO_CHUNK, AGUA_FUNDA, AGUA_RASA, LAMA, AREIA, GRAMA,
                    GRAMA_FLORESTA, GRAMA_PANTANO, NEVE, ROCHA)

CH = TAMANHO_CHUNK
CORES_CHAO = {
    AGUA_FUNDA: (40, 84, 168), AGUA_RASA: (78, 142, 208), LAMA: (118, 90, 60), AREIA: (222, 200, 138),
    GRAMA: (96, 168, 72), GRAMA_FLORESTA: (62, 126, 56), GRAMA_PANTANO: (92, 112, 62),
    NEVE: (232, 238, 248), ROCHA: (126, 122, 118),
}
CORES_INVERNO = {GRAMA: (226, 234, 244), GRAMA_FLORESTA: (214, 224, 238), GRAMA_PANTANO: (200, 212, 220)}
CORES_OUTONO = {GRAMA: (160, 148, 64), GRAMA_FLORESTA: (150, 96, 42)}
CORES_OBJETO = {
    "arvore": (34, 92, 40), "arvore_pantano": (60, 82, 40), "pinheiro": (30, 80, 56), "cacto": (60, 140, 60),
    "pedra": (90, 92, 104), "minerio_ferro": (200, 120, 80), "arbusto": (180, 40, 60),
}
COR_CONSTRUCAO = (170, 110, 60)
NEVOA = (14, 12, 22)
TAMANHOS = {"pequeno": (150, 2), "grande": (282, 3)}    # (lado em pixels de tela, pixels por bloco)


class Minimapa:
    def __init__(self):
        self.explorados = set()
        self.imagens = {}                # (cx, cy) -> Surface 16x16
        self.estacao_imagens = {}        # (cx, cy) -> estação usada na imagem
        self.tamanho = "pequeno"
        self.tempo = 0.0
        self.ret = pygame.Rect(0, 0, 0, 0)

    # ---------------- exploração ----------------
    def trocar_tamanho(self):
        self.tamanho = "grande" if self.tamanho == "pequeno" else "pequeno"

    def imagem_de(self, ch, estacao):
        s = pygame.Surface((CH, CH))
        cores = dict(CORES_CHAO)
        if estacao == "inverno":
            cores.update(CORES_INVERNO)
        elif estacao == "outono":
            cores.update(CORES_OUTONO)
        x0, y0 = ch.cx * CH, ch.cy * CH
        for j in range(CH):
            for i in range(CH):
                s.set_at((i, j), cores[ch.chao[j * CH + i]])
        for (tx, ty), o in ch.objetos.items():
            cor = CORES_OBJETO.get(o.tipo)
            if cor is None and o.construcao:
                cor = COR_CONSTRUCAO
            if cor:
                s.set_at((tx - x0, ty - y0), cor)
        for (tx, ty) in ch.pisos:
            s.set_at((tx - x0, ty - y0), COR_CONSTRUCAO)
        return s

    def atualizar(self, dt, jogo):
        j = jogo.jogador
        mundo = jogo.mundo
        estacao = getattr(jogo, "estacao", "verao")
        self.estacao = estacao
        pcx, pcy = int(j.x // TILE) // CH, int(j.y // TILE) // CH
        for cy in range(pcy - 1, pcy + 2):
            for cx in range(pcx - 1, pcx + 2):
                if (cx, cy) not in self.explorados and (cx, cy) in mundo.chunks:
                    self.explorados.add((cx, cy))
                    self.imagens[(cx, cy)] = self.imagem_de(mundo.chunks[(cx, cy)], estacao)
                    self.estacao_imagens[(cx, cy)] = estacao
        # de tempos em tempos, redesenha os chunks em volta (árvores cortadas, construções, água)
        self.tempo -= dt
        if self.tempo <= 0:
            self.tempo = 1.0
            for cy in range(pcy - 2, pcy + 3):
                for cx in range(pcx - 2, pcx + 3):
                    if (cx, cy) in self.explorados and (cx, cy) in mundo.chunks:
                        self.imagens[(cx, cy)] = self.imagem_de(mundo.chunks[(cx, cy)], estacao)
                        self.estacao_imagens[(cx, cy)] = estacao

    def _imagem(self, c, mundo, orcamento):
        img = self.imagens.get(c)
        estacao = getattr(self, "estacao", "verao")
        velha = img is not None and self.estacao_imagens.get(c) != estacao
        if (img is None or velha) and orcamento[0] > 0:
            # chunk explorado mas fora da memória (jogo carregado) ou de outra estação: gera de novo
            ch = mundo.chunks.get(c)
            if ch is None and velha:
                # recolorir um chunk descarregado custa gerar ele de novo: poucos por quadro
                orcamento[0] -= 1
            orcamento[0] -= 1
            ch = ch or mundo.gerador.gerar_chunk(*c)
            img = self.imagem_de(ch, estacao)
            self.imagens[c] = img
            self.estacao_imagens[c] = estacao
        return img

    # ---------------- desenho ----------------
    def desenhar_regiao(self, mundo, centro_tx, centro_ty, w, h, px):
        """Superfície (w x h pixels de tela) do mapa em volta de (centro_tx, centro_ty)."""
        larg_t, alt_t = int(math.ceil(w / px)) + 2, int(math.ceil(h / px)) + 2
        tx0 = int(centro_tx - larg_t / 2)
        ty0 = int(centro_ty - alt_t / 2)
        base = pygame.Surface((larg_t, alt_t))
        base.fill(NEVOA)
        orcamento = [3]
        for cy in range(ty0 // CH, (ty0 + alt_t) // CH + 1):
            for cx in range(tx0 // CH, (tx0 + larg_t) // CH + 1):
                if (cx, cy) in self.explorados:
                    img = self._imagem((cx, cy), mundo, orcamento)
                    if img:
                        base.blit(img, (cx * CH - tx0, cy * CH - ty0))
        grande = pygame.transform.scale(base, (larg_t * px, alt_t * px))
        # deslocamento fracionário para centralizar bem
        ox = int((centro_tx - tx0) * px - w / 2)
        oy = int((centro_ty - ty0) * px - h / 2)
        final = pygame.Surface((w, h))
        final.blit(grande, (-ox, -oy))
        return final, (tx0 * px + ox, ty0 * px + oy)

    def desenhar_marcadores(self, tela, marcadores, origem, px, ret, icones):
        """origem = (x, y) em 'pixels de mapa' do canto de cima-esquerda do ret."""
        ox, oy = origem
        for m in marcadores:
            sx = ret.x + m["tx"] * px - ox
            sy = ret.y + m["ty"] * px - oy
            if not ret.inflate(-4, -4).collidepoint(sx, sy):
                if m["tipo"] != "jogador":
                    continue
                sx = max(ret.left + 4, min(ret.right - 5, sx))
                sy = max(ret.top + 4, min(ret.bottom - 5, sy))
            if m["tipo"] == "jogador":
                _seta(tela, sx, sy, m.get("direcao", "baixo"))
            else:
                ic = icones.get(m["tipo"])
                if ic:
                    tela.blit(ic, (sx - ic.get_width() // 2, sy - ic.get_height() // 2))
                else:
                    pygame.draw.rect(tela, (20, 18, 28), (sx - 4, sy - 4, 9, 9))
                    pygame.draw.rect(tela, m.get("cor", (250, 200, 80)), (sx - 3, sy - 3, 7, 7))


def _seta(tela, x, y, direcao):
    pontos = {"cima": [(0, -6), (5, 4), (0, 2), (-5, 4)], "baixo": [(0, 6), (5, -4), (0, -2), (-5, -4)],
              "esquerda": [(-6, 0), (4, -5), (2, 0), (4, 5)], "direita": [(6, 0), (-4, -5), (-2, 0), (-4, 5)]}[direcao]
    pts = [(x + dx, y + dy) for dx, dy in pontos]
    pygame.draw.polygon(tela, (255, 70, 60), pts)
    pygame.draw.polygon(tela, (255, 255, 255), pts, 2)
