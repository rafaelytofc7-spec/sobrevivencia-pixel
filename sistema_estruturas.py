# -*- coding: utf-8 -*-
"""
sistema_estruturas.py - Liga as ESTRUTURAS ao jogo (main.py chama estas
funções em poucos "ganchos" marcados com  # [ESTRUTURAS]).

Cuida de: NPCs aparecendo quando o chunk da estrutura carrega, abrir baús,
trocas com aldeões, entrar/sair das masmorras, luz das tochas, escuridão
lá embaixo, barra de vida dos chefes, avisos de "você encontrou..." e a
parte do save (baús abertos, chefes derrotados, se você está na masmorra).
"""
import math
import random

import pygame

from config import TILE, LARGURA_INTERNA, ALTURA_INTERNA, LARGURA_TELA, ESCURIDAO_MAXIMA, RAIO_LUZ_FOGUEIRA
from dados import ITENS, NOMES_OBJETOS
from sprites import gradiente_luz
from mundo import chunk_do_bloco
import arte_estruturas
import baus
from dados_estruturas import INQUEBRAVEIS
from estruturas import NOMES_ESTRUTURAS
from npcs import NPC, Aldeao, Guarda, MenuTroca, criar_npc, falar
from dungeon import MundoMasmorra, EcossistemaMasmorra

ALCANCE_NPC = 26
ALCANCE_OBJ = 26
RAIO_LUZ_TOCHA = 40


class SistemaEstruturas:
    def __init__(self, jogo):
        self.jogo = jogo
        arte_estruturas.instalar(jogo.sprites)
        self.superficie = jogo.mundo
        self.plano = jogo.mundo.gerador.estruturas
        self.baus_abertos = self.plano.abertos          # o mesmo conjunto (o carimbo consulta)
        self.chefes = set()                             # ids dos chefes derrotados
        self.descobertas = set()                        # ids das estruturas já vistas
        self.masmorra = None                            # MundoMasmorra atual (ou None)
        self.volta = None                               # (x, y) na superfície para sair
        self._eco_superficie = None
        self._criaturas_superficie = None
        self.masmorras = {}                             # cache: id -> MundoMasmorra
        self.troca = None
        self.espera_escada = 0.0
        self.tempo_checar = 0.0
        self._chefes_ativos = {}                        # npc_id -> criatura (chefes por perto)
        anterior = jogo.mundo.ao_carregar

        def ao_carregar(ch):
            if anterior:
                anterior(ch)
            self.ao_carregar_chunk(ch)
        jogo.mundo.ao_carregar = ao_carregar

    # ===========================================================
    # Consultas úteis (ex.: para um minimapa)
    # ===========================================================
    @property
    def subterraneo(self):
        return self.masmorra is not None

    def estruturas_perto(self, tx, ty, raio):
        """Estruturas cuja caixa encosta no quadrado (tx±raio, ty±raio). Lista de Estrutura."""
        return self.plano.estruturas_na_caixa(tx - raio, ty - raio, tx + raio, ty + raio)

    # ===========================================================
    # NPCs
    # ===========================================================
    def _ids_vivos(self):
        return {c.npc_id for c in self.jogo.criaturas if isinstance(c, NPC)}

    def ao_carregar_chunk(self, ch):
        if self.jogo.mundo is not self.superficie and self.masmorra is not None:
            return
        x0, y0 = ch.cx * 16, ch.cy * 16
        lista = self.plano.estruturas_na_caixa(x0, y0, x0 + 15, y0 + 15)
        if not lista:
            return
        vivos = self._ids_vivos()
        for est in lista:
            for d in est.npcs:
                if chunk_do_bloco(d["x"], d["y"]) != (ch.cx, ch.cy):
                    continue
                if d["id"] in vivos or (d.get("chefe") and d["id"] in self.chefes):
                    continue
                self._adicionar(criar_npc(d))

    def _adicionar(self, npc):
        self.jogo.criaturas.append(npc)
        if npc.chefe:
            self._chefes_ativos[npc.npc_id] = npc

    def npc_perto(self, alcance=ALCANCE_NPC):
        jx, jy = self.jogo.jogador.centro
        melhor, md = None, alcance
        for c in self.jogo.criaturas:
            if isinstance(c, (Aldeao, Guarda)):
                d = math.hypot(c.centro[0] - jx, c.centro[1] - jy)
                if d < md:
                    melhor, md = c, d
        return melhor

    def npc_no_mouse(self):
        jogo = self.jogo
        if not jogo.mouse_no_mundo():
            return None
        wx, wy = jogo.mouse_mundo()
        for c in jogo.criaturas:
            if isinstance(c, (Aldeao, Guarda)):
                cx, cy = c.centro
                if math.hypot(cx - wx, cy - wy) < 10 and jogo.no_alcance(cx, cy, folga=8):
                    return c
        return None

    def conversar(self, npc):
        jogo = self.jogo
        npc.olhando = "direita" if jogo.jogador.x > npc.x else "esquerda"
        if isinstance(npc, Aldeao) and npc.ofertas:
            self.troca = MenuTroca(npc)
            npc.estado, npc.tempo_estado = "conversar", 9999
            npc.direcao = (0.0, 0.0)
            jogo.estado = "trocando"
        else:
            jogo.popup_texto(falar(npc), npc.x, npc.y - 22)

    def fechar_troca(self):
        if self.troca:
            self.troca.npc.tempo_estado = 1.0
        self.troca = None
        if self.jogo.estado == "trocando":
            self.jogo.estado = "jogando"

    # ===========================================================
    # Baús, escadas, poço
    # ===========================================================
    def _id_bau(self, obj):
        base = f"{obj.tx},{obj.ty}"
        return f"{self.masmorra.id}|{base}" if self.masmorra else base

    def abrir_bau(self, obj):
        jogo = self.jogo
        ident = self._id_bau(obj)
        if self.masmorra:
            nivel = self.masmorra.planta.baus.get((obj.tx, obj.ty), 2)
            bioma = self._bioma_entrada()
        else:
            est = self.plano.estrutura_em(obj.tx, obj.ty)
            nivel = est.baus.get((obj.tx, obj.ty), 1) if est else 1
            bioma = jogo.mundo.bioma(obj.tx, obj.ty)
        itens = baus.conteudo(jogo.mundo.semente, ident, bioma, nivel)
        obj.tipo = "bau_tesouro_aberto"
        obj.vida = obj.vida_max
        jogo.mundo.marcar_modificado(obj)
        self.baus_abertos.add(ident)
        inv = jogo.jogador.inventario
        cx, cy = obj.centro
        for item, qtd in itens:
            sobra = inv.adicionar(item, qtd)
            if qtd - sobra:
                jogo.popup(item, qtd - sobra)
            if sobra:
                jogo.soltar_itens([(item, sobra)], cx, cy)
        jogo.soltar_lascas(obj.centro, "bancada", 8)
        nomes = ", ".join(f"{q}x {ITENS[i]['nome']}" for i, q in itens)
        jogo.avisar(f"Baú aberto: {nomes}", 4)
        return True

    def _bioma_entrada(self):
        est = self.plano.por_id(self.masmorra.id) if self.masmorra else None
        return est.bioma if est else "montanha"

    def usar_escada(self, obj):
        if self.espera_escada > 0:
            return True
        if obj.tipo == "escada_descer":
            est = self.plano.estrutura_em(obj.tx, obj.ty)
            ident = est.id if est else f"masmorra:{obj.tx},{obj.ty}"
            self.entrar_masmorra(ident, (obj.tx * TILE + 8, (obj.ty + 1) * TILE + 12))
        elif obj.tipo == "escada_subir":
            self.sair_masmorra()
        return True

    def acao_objeto(self, obj):
        """Ação de E / botão direito num objeto. True se fez algo."""
        if obj.tipo == "bau_tesouro":
            return self.abrir_bau(obj)
        if obj.tipo in ("escada_descer", "escada_subir"):
            return self.usar_escada(obj)
        if obj.tipo == "poco":
            self.jogo.beber_agua()
            return True
        return False

    def objeto_perto(self):
        cx, cy = self.jogo.jogador.centro
        return self.jogo.mundo.objeto_mais_proximo(cx, cy, ALCANCE_OBJ,
                                                   tipos=("bau_tesouro", "escada_descer", "escada_subir", "poco"))

    # ===========================================================
    # Masmorras
    # ===========================================================
    def entrar_masmorra(self, ident, volta, posicao=None):
        jogo = self.jogo
        m = self.masmorras.get(ident)
        if m is None:
            m = MundoMasmorra(self.superficie, ident, self.baus_abertos)
            self.masmorras[ident] = m
        m.carregar_tudo()
        self._eco_superficie = jogo.ecossistema
        self._criaturas_superficie = jogo.criaturas
        self.masmorra = m
        self.volta = volta
        jogo.mundo = m
        jogo.ecossistema = EcossistemaMasmorra(jogo)
        jogo.criaturas = []
        for n, (tipo, x, y, chefe) in enumerate(m.planta.monstros):
            nid = f"{ident}@chefe" if chefe else f"{ident}@{n}"
            if chefe and nid in self.chefes:
                continue
            self._adicionar(criar_npc({"id": nid, "tipo": tipo, "x": x, "y": y,
                                       "raio": 6 if chefe else 7, "chefe": chefe, "estrutura": ident}))
        j = jogo.jogador
        if posicao:
            j.x, j.y = posicao
        else:
            j.x, j.y = m.planta.chegada[0] * TILE + 8, m.planta.chegada[1] * TILE + 12
        jogo.pesca = None
        jogo.gotas = []
        self.espera_escada = 1.0
        jogo.centralizar_camera()
        jogo.avisar("Você desceu para a masmorra... cuidado!", 3)

    def sair_masmorra(self):
        jogo = self.jogo
        if not self.masmorra:
            return
        jogo.mundo = self.superficie
        jogo.ecossistema = self._eco_superficie or jogo.ecossistema
        jogo.criaturas = self._criaturas_superficie if self._criaturas_superficie is not None else []
        self.masmorra = None
        j = jogo.jogador
        j.x, j.y = self.volta
        jogo.mundo.atualizar_chunks(j.x, j.y, limite=99)
        jogo.pesca = None
        self.espera_escada = 1.0
        jogo.centralizar_camera()
        jogo.avisar("Você voltou para a superfície", 2.5)

    # ===========================================================
    # Ganchos chamados por main.py
    # ===========================================================
    def interagir(self):
        """Tecla E. True = já tratou (main.py não faz mais nada)."""
        npc = self.npc_perto()
        if npc:
            self.conversar(npc)
            return True
        obj = self.objeto_perto()
        if obj:
            return self.acao_objeto(obj)
        return False

    def clique_direito(self):
        npc = self.npc_no_mouse()
        if npc:
            self.conversar(npc)
            return True
        obj, alcanca = self.jogo.alvo_mouse()
        if obj and alcanca and obj.tipo in ("bau_tesouro", "escada_descer", "escada_subir", "poco"):
            return self.acao_objeto(obj)
        return False

    def golpear(self, obj):
        """Botão esquerdo / E num objeto. True = não quebrar do jeito normal."""
        jogo = self.jogo
        if obj.tipo == "bau_tesouro":
            return self.abrir_bau(obj)
        if obj.tipo in ("escada_descer", "escada_subir"):
            jogo.avisar("Aperte E ou o botão direito para usar a escada", 1.5)
            return True
        if obj.tipo in INQUEBRAVEIS:
            jogo.avisar(f"Não dá para quebrar: {NOMES_OBJETOS.get(obj.tipo, obj.tipo)}", 1.2)
            return True
        if self.masmorra and obj.tipo == "parede_pedra" and obj.variante == 2:
            obj.tremor = 0.15
            jogo.avisar("As paredes da masmorra são duras demais", 1.2)
            return True
        return False

    def dica(self):
        jogo = self.jogo
        if jogo.estado != "jogando":
            return ""
        npc = self.npc_no_mouse() or self.npc_perto()
        if npc:
            acao = "Negociar com" if isinstance(npc, Aldeao) else "Falar com"
            return f"[E / Botão direito] {acao} {npc.info['nome']}"
        obj, alcanca = jogo.alvo_mouse()
        if not (obj and alcanca and obj.tipo in ("bau_tesouro", "escada_descer", "escada_subir", "poco")):
            obj = self.objeto_perto()
        if obj:
            return {"bau_tesouro": "[Clique / E] Abrir baú", "poco": "[E] Beber água do poço",
                    "escada_descer": "[E / Botão direito] Descer para a masmorra",
                    "escada_subir": "[E / Botão direito] Subir para a superfície"}.get(obj.tipo, "")
        return ""

    def tratar_evento(self, ev):
        """Eventos enquanto a janela de trocas está aberta. True = consumido."""
        jogo = self.jogo
        if jogo.estado != "trocando":
            return False
        if ev.type == pygame.MOUSEMOTION:
            jogo.pos_mouse = ev.pos
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3) and self.troca:
            jogo.pos_mouse = ev.pos
            i = self.troca.clique(ev.pos)
            if i is not None:
                self.troca.trocar(jogo, i)
            elif not self.troca.ret.collidepoint(ev.pos):
                self.fechar_troca()
        elif ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_i, pygame.K_TAB):
                self.fechar_troca()
            elif pygame.K_1 <= ev.key <= pygame.K_9 and self.troca:
                i = ev.key - pygame.K_1
                if i < len(self.troca.npc.ofertas):
                    self.troca.trocar(jogo, i)
        return True

    def atualizar(self, dt):
        jogo = self.jogo
        self.espera_escada = max(0.0, self.espera_escada - dt)
        if self.masmorra:
            jogo.gotas = []                 # não chove lá embaixo
        # chefes derrotados (guarda referência: o ecossistema tira os mortos da lista antes daqui)
        for c in jogo.criaturas:
            if isinstance(c, NPC) and c.chefe:
                self._chefes_ativos[c.npc_id] = c
        for nid, c in list(self._chefes_ativos.items()):
            if c.vida <= 0:
                del self._chefes_ativos[nid]
                if nid not in self.chefes:
                    self.chefes.add(nid)
                    jogo.avisar(f"Você derrotou {c.info['nome']}!", 5)
            elif c not in jogo.criaturas:
                del self._chefes_ativos[nid]       # sumiu (chunk descarregado / saiu da masmorra)
        # "você encontrou..."
        self.tempo_checar -= dt
        if self.tempo_checar <= 0 and not self.masmorra:
            self.tempo_checar = 0.5
            j = jogo.jogador
            est = self.plano.estrutura_em(int(j.x // TILE), int(j.y // TILE), folga=4)
            if est and est.id not in self.descobertas:
                self.descobertas.add(est.id)
                jogo.avisar(f"Você encontrou {NOMES_ESTRUTURAS[est.tipo]}!", 4)

    def escuridao(self):
        """Lá embaixo é sempre escuro (None = usar a hora do dia)."""
        return ESCURIDAO_MAXIMA if self.masmorra else None

    def _luzes_visiveis(self, cx, cy):
        """[(x, y, raio)] na tela: fogueiras acesas e tochas."""
        jogo = self.jogo
        m = jogo.mundo
        luzes = []
        if hasattr(m, "lista_luzes"):                  # mundo.py novo já lista tochas/fornos
            for o, raio in m.lista_luzes():
                luzes.append((o.centro[0] - cx, o.centro[1] - cy, raio))
            return luzes
        for f in m.lista_fogueiras():
            luzes.append((f.centro[0] - cx, f.centro[1] - cy, RAIO_LUZ_FOGUEIRA))
        margem = RAIO_LUZ_TOCHA // TILE + 1
        for ty in range(cy // TILE - margem, (cy + ALTURA_INTERNA) // TILE + margem + 1):
            for tx in range(cx // TILE - margem, (cx + LARGURA_INTERNA) // TILE + margem + 1):
                o = m.objeto(tx, ty)
                if o is not None and o.tipo == "tocha":
                    luzes.append((tx * TILE + 8 - cx, ty * TILE + 4 - cy, RAIO_LUZ_TOCHA))
        return luzes

    def desenhar_luzes(self, mascara, cx, cy):
        """Na masmorra: escuridão quase total + sua luz + tochas/fogueiras.
        Na superfície: só soma a luz das tochas (se o mundo.py ainda não faz isso)."""
        jogo = self.jogo
        pisca = 2 if int(jogo.tempo_total * 6) % 2 else 0
        if self.masmorra:
            mascara.fill((16, 14, 24))
            jx, jy = int(jogo.jogador.x - cx), int(jogo.jogador.y - 6 - cy)
            r = 62 + pisca
            mascara.blit(gradiente_luz(r, (210, 170, 120)), (jx - r, jy - r), special_flags=pygame.BLEND_RGB_ADD)
            luzes = self._luzes_visiveis(cx, cy)
        elif hasattr(jogo.mundo, "lista_luzes"):
            return                                     # main.py novo já desenha as tochas
        else:
            luzes = [l for l in self._luzes_visiveis(cx, cy) if l[2] == RAIO_LUZ_TOCHA]
        for (x, y, raio) in luzes:
            if -raio < x < LARGURA_INTERNA + raio and -raio < y < ALTURA_INTERNA + raio:
                r = int(raio) + pisca
                cor = (255, 200, 140) if raio != RAIO_LUZ_TOCHA else (255, 190, 120)
                mascara.blit(gradiente_luz(r, cor), (int(x) - r, int(y) - r), special_flags=pygame.BLEND_RGB_ADD)

    def desenhar_interface(self, tela):
        jogo = self.jogo
        sp = jogo.sprites
        if hasattr(sp, "tocha_quadros"):
            sp.objetos["tocha"][0] = sp.tocha_quadros[int(jogo.tempo_total * 7) % 3]
        if jogo.estado == "menu_inicial":
            return
        ui = jogo.interface
        if self.masmorra:
            ui.texto(tela, "Masmorra", (LARGURA_TELA // 2, 14), ui.fonte_media, (200, 170, 255), centro=True)
        # barra de vida do chefe por perto
        j = jogo.jogador
        for c in jogo.criaturas:
            if isinstance(c, NPC) and c.chefe and c.vida > 0 and math.hypot(c.x - j.x, c.y - j.y) < 170:
                larg = 360
                x, y = (LARGURA_TELA - larg) // 2, 48
                ui.texto(tela, c.info["nome"], (LARGURA_TELA // 2, y - 4), ui.fonte, (255, 200, 120), centro=True)
                pygame.draw.rect(tela, (20, 18, 28), (x - 3, y + 19, larg + 6, 18))
                pygame.draw.rect(tela, (70, 30, 40), (x, y + 22, larg, 12))
                pygame.draw.rect(tela, (220, 50, 70), (x, y + 22, int(larg * c.vida / c.info["vida"]), 12))
                break
        if jogo.estado == "trocando" and self.troca:
            self.troca.desenhar(tela, ui, jogo, jogo.pos_mouse)

    # ===========================================================
    # Save
    # ===========================================================
    def para_dict(self):
        d = {"baus": sorted(self.baus_abertos), "chefes": sorted(self.chefes),
             "descobertas": sorted(self.descobertas)}
        if self.masmorra:
            d["masmorra"] = {"id": self.masmorra.id, "volta": list(self.volta)}
        return d

    def carregar_dict(self, d):
        self.baus_abertos.clear()
        self.baus_abertos.update(d.get("baus", []))
        self.chefes = set(d.get("chefes", []))
        self.descobertas = set(d.get("descobertas", []))
        sub = d.get("masmorra")
        if sub:
            j = self.jogo.jogador
            self.entrar_masmorra(sub["id"], tuple(sub["volta"]), posicao=(j.x, j.y))
