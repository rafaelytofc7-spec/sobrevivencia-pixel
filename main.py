# -*- coding: utf-8 -*-
"""
main.py - Arquivo principal. Rode com:  python main.py

A classe Jogo junta tudo: tela inicial (semente), mundo infinito em chunks,
clima e estações, ecossistema, jogador (correr, rolar, nadar), inventário,
baús, criação, construção, pesca, arco, cama, minimapa, controles
configuráveis, desenho (com cache das imagens dos chunks) e o loop principal.
"""
import asyncio
import math
import random
import sys

import pygame

from config import *          # noqa: F401,F403  (constantes)
import blocos                                          # noqa: F401  [v0.5] registra blocos/receitas
from dados import ITENS, OBJETOS, RECEITAS, CATEGORIAS, CRIATURAS, NOMES_OBJETOS
from sprites import Sprites, gradiente_luz
from mundo import Mundo, Objeto
from clima import Clima
from entidades import Jogador, ItemChao, Flecha, DURACAO_GOLPE
from ecossistema import Ecossistema
from interface import Interface
from controles import Controles
from minimapa import Minimapa
import estacoes
import personagem
from ruido import semente_de_texto
from salvar import salvar_jogo, carregar_jogo, existe_save
from sistema_estruturas import SistemaEstruturas      # [ESTRUTURAS]
from estruturas import NOMES_ESTRUTURAS
from camadas import SistemaCamadas, nome_camada                 # [v0.5] camadas (Z) e cavernas
import criacao                                                  # [v0.5] grade de criação e forno
from blocos import picareta_para, COMBUSTIVEL, FUNDICAO, TIPOS_BLOCO

CH = TAMANHO_CHUNK
PX_CHUNK = CH * TILE         # 256 pixels por chunk

# cor das lasquinhas de cada objeto
COR_LASCAS = {
    "arvore": [(120, 78, 44), (56, 140, 62)], "arvore_pantano": [(120, 78, 44), (80, 104, 54)],
    "pinheiro": [(110, 72, 42), (42, 108, 72)], "cacto": [(70, 150, 70), (230, 230, 190)],
    "pedra": [(132, 134, 148), (176, 178, 190)], "minerio_ferro": [(132, 134, 148), (214, 140, 90)],
    "arbusto": [(62, 150, 66), (214, 40, 60)], "capim": [(70, 140, 60)], "junco": [(80, 130, 60)],
    "fogueira": [(232, 80, 36)], "bancada": [(178, 128, 76)],
    "parede_madeira": [(150, 100, 58)], "parede_pedra": [(132, 134, 148)], "piso": [(178, 130, 82)],
    "trigo": [(220, 186, 80), (120, 170, 70)], "plantacao": [(220, 186, 80), (110, 76, 48)],
    "tocha": [(240, 120, 40)], "forno": [(132, 134, 148)], "bau": [(160, 106, 58)], "cama": [(190, 60, 60)],
    # [v0.5] blocos e chão cavado
    "bloco_pedra": [(122, 122, 132), (96, 96, 108)], "bloco_pedregulho": [(130, 130, 140)],
    "bloco_pedra_lisa": [(160, 160, 166)], "bloco_terra": [(134, 94, 60)], "bloco_areia": [(222, 204, 146)],
    "bloco_tora": [(150, 106, 62)], "bloco_tabuas": [(184, 140, 86)], "bloco_vidro": [(210, 240, 250)],
    "min_carvao": [(122, 122, 132), (34, 32, 38)], "min_ferro": [(122, 122, 132), (214, 168, 128)],
    "min_ouro": [(122, 122, 132), (246, 206, 60)], "min_cristal": [(122, 122, 132), (230, 50, 80)],
    "min_diamante": [(122, 122, 132), (90, 236, 230)], "lampada": [(250, 226, 150)],
    "escada": [(176, 128, 74)], "chao_terra": [(134, 94, 60), (96, 66, 40)], "chao_areia": [(222, 204, 146)],
    "chao_pedra": [(122, 122, 132), (90, 88, 96)], "explosao": [(255, 220, 120), (240, 120, 40), (90, 86, 90)],
}
PLANOS = ("buraco", "escada")      # [v0.5] desenhados rente ao chão (você fica por cima)
XP_ORBE = 3                        # pontos por bolinha de XP
CORES_ESTRUTURAS = {"vila": (240, 200, 90), "cidadela": (200, 200, 220), "castelo": (230, 90, 90),
                    "masmorra": (170, 110, 230), "ruina": (150, 170, 130), "tesouro": (255, 230, 80)}
CHAO_PLANTAVEL = (GRAMA, GRAMA_FLORESTA, GRAMA_PANTANO, LAMA)
ESTADOS_SLOTS = ("inventario", "bau", "bancada", "forno")     # telas com espaços de itens
# [v0.5] fome estilo Minecraft: exaustão por segundo (4 de exaustão = -5 de saturação/fome)
EXAUSTAO_BASE = 0.16
EXAUSTAO_ANDAR = 0.08
EXAUSTAO_CORRER = 0.24
EXAUSTAO_NADAR = 0.15
ANIMADOS = ("capim", "junco", "trigo", "plantacao", "arvore", "arvore_pantano", "pinheiro")
COMIDA_CRUA = {"carne_crua": "carne_assada", "peixe": "peixe_assado"}


class Jogo:
    def __init__(self, tela):
        self.tela = tela
        self.cena = pygame.Surface((LARGURA_INTERNA, ALTURA_INTERNA))
        self.mascara_luz = pygame.Surface((LARGURA_INTERNA, ALTURA_INTERNA))
        self.sprites = Sprites()
        for est in estacoes.ORDEM:           # prepara os tiles das 4 estações (evita travadinha na troca)
            self.sprites.texturas.tiles(est)
        self.interface = Interface(self.sprites)
        self.pos_mouse = (LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.botoes_mouse = (False, False, False)
        self.tempo_total = 0.0
        self.mensagens = []
        self.texto_semente = ""
        self.arrastando = None          # pilha [item, qtd] presa no mouse (inventário)
        self.grade2 = [None] * 4        # [v0.5] grade 2x2 do inventário
        self.grade3 = [None] * 9        # [v0.5] grade 3x3 da bancada
        self.forno_aberto = None
        self.tremor_tela = 0.0
        self.origem_arrasto = None
        self.categoria = CATEGORIAS[0]
        self.selecao_criacao = None
        self.estado_anterior = "jogando"
        self.tem_save = existe_save()
        self.controles = Controles()
        self.esperando_tecla = None      # ação esperando nova tecla (tela de controles)
        self.volta_controles = "menu_inicial"
        self.zoom_mapa = 2
        self.mapa_centro = [0.0, 0.0]
        self.arrastando_mapa = None
        self.rodando = True
        # um mundo aleatório aparece no fundo da tela inicial
        self.novo_jogo(random.randrange(1, 1_000_000))
        self.estado = "menu_inicial"

    # ===========================================================
    # Começar / reiniciar / carregar
    # ===========================================================
    def _preparar(self, semente):
        self.mundo = Mundo(semente)
        self.criaturas = []
        self.ecossistema = Ecossistema(self)
        self.mundo.ao_carregar = self.ecossistema.ao_carregar_chunk
        self.estruturas = SistemaEstruturas(self)            # [ESTRUTURAS]
        self.clima = Clima(semente)
        self.orbes = []                                      # [v0.5] bolinhas de XP
        self.popups = []
        self.particulas = []
        self.gotas = []
        self.pesca = None
        self.derrotados = 0
        self.mensagens = []
        self.minimapa = Minimapa()
        self.flechas = []
        self.ponto_renascer = None       # (x, y) da cama
        self.bau_aberto = None
        self.sono = 0.0                  # > 0 enquanto dorme (animação)
        self.dia = 1
        self.estacao = "primavera"
        self.mult_caca_lobo = 1.0
        self._temp = (15.0, "Agradável")
        self.marcadores_extra = []       # outros sistemas podem pôr marcadores no mapa aqui
        self.camadas = SistemaCamadas(self)                  # [v0.5] superfície + cavernas
        self.forno_aberto = None
        self.grade2 = [None] * 4
        self.grade3 = [None] * 9

    def novo_jogo(self, semente):
        self._preparar(semente)
        tx, ty = self.mundo.ponto_inicial()
        self.jogador = Jogador(tx * TILE + 8, ty * TILE + 14)
        self.mundo.atualizar_chunks(self.jogador.x, self.jogador.y, limite=99)
        self.mundo.limpar_area(tx, ty, 2)
        self.tempo = HORA_INICIAL / 24.0 * DURACAO_DIA
        self.dia = 1
        self.estado = "jogando"
        self.centralizar_camera()

    def iniciar_pelo_menu(self):
        semente = semente_de_texto(self.texto_semente)
        if semente is None:
            semente = random.randrange(1, 1_000_000)
        self.novo_jogo(semente)
        self.estado = "ajuda"
        self.estado_anterior = "jogando"

    def carregar(self):
        dados, erro = carregar_jogo()
        if not dados:
            self.avisar(erro)
            return
        self._preparar(dados["semente"])
        self.mundo.salvos = dict(dados.get("chunks", {}))
        self.clima.carregar_dict(dados.get("clima", {}))
        self.mundo.deslocamento_agua = round(self.clima.nivel / 0.0025) * 0.0025
        self.jogador = Jogador(0, 0)
        self.jogador.carregar_dict(dados["jogador"])
        self.tempo = dados.get("tempo", 0.0)
        self.dia = dados.get("dia", 1)
        self.derrotados = dados.get("derrotados", 0)
        self.carregar_extras(dados)
        self.estruturas.carregar_dict(dados.get("estruturas", {}))   # [ESTRUTURAS]
        self.mundo.atualizar_chunks(self.jogador.x, self.jogador.y, limite=99)
        self.estado = "jogando"
        self.centralizar_camera()
        self.avisar("Jogo carregado!")

    def carregar_extras(self, dados):
        """Partes do save que vieram na v0.4 (saves antigos não têm)."""
        self.minimapa.explorados = {tuple(int(v) for v in c.split(",")) for c in dados.get("explorados", [])}
        r = dados.get("renascer")
        self.ponto_renascer = tuple(r) if r else None
        self.estacao = estacoes.estacao_do_dia(self.dia)
        self.camadas.carregar_dict(dados.get("camadas", {}))          # [v0.5]

    def dados_extras(self):
        sup = self.camadas.minimapas.get(0, self.minimapa)
        return {"explorados": [f"{cx},{cy}" for cx, cy in sup.explorados],
                "renascer": list(self.ponto_renascer) if self.ponto_renascer else None,
                "camadas": self.camadas.para_dict()}

    def salvar(self):
        try:
            salvar_jogo(self)
            self.tem_save = True
            self.avisar("Jogo salvo!")
        except OSError as erro:
            self.avisar(f"Erro ao salvar: {erro}")

    def avisar(self, texto, duracao=2.5):
        if self.mensagens and self.mensagens[-1][0] == texto:
            self.mensagens[-1][1] = duracao
            return
        self.mensagens.append([texto, duracao])
        self.mensagens = self.mensagens[-6:]

    # ===========================================================
    # Dia e noite
    # ===========================================================
    def hora(self):
        return self.tempo / DURACAO_DIA * 24.0

    def nivel_escuridao(self):
        if self.camadas.escuridao() is not None:              # [v0.5] cavernas
            return self.camadas.escuridao()
        if self.estruturas.escuridao() is not None:         # [ESTRUTURAS] masmorra
            return self.estruturas.escuridao()
        luz = 0.5 - 0.5 * math.cos(2 * math.pi * self.hora() / 24.0)
        return max(0.0, min(1.0, (0.55 - luz) / 0.55)) * ESCURIDAO_MAXIMA

    def e_noite(self):
        return self.nivel_escuridao() > 0.45

    # ===========================================================
    # Mouse
    # ===========================================================
    def mouse_mundo(self):
        mx, my = self.pos_mouse
        return (self.camera_x + mx / ESCALA, self.camera_y + my / ESCALA)

    def bloco_mouse(self):
        wx, wy = self.mouse_mundo()
        return int(wx // TILE), int(wy // TILE)

    def mouse_no_mundo(self):
        return not self.interface.mouse_sobre_interface(self.pos_mouse, self.estado)

    def no_alcance(self, x, y, folga=0):
        jx, jy = self.jogador.centro
        return math.hypot(x - jx, y - jy) <= ALCANCE_MOUSE + folga

    def alvo_mouse(self):
        if not self.mouse_no_mundo():
            return None, False
        obj = self.mundo.objeto_no_ponto(*self.mouse_mundo())
        if obj is None:
            return None, False
        return obj, self.no_alcance(*obj.centro)

    def criatura_no_mouse(self):
        wx, wy = self.mouse_mundo()
        for c in self.criaturas:
            cx, cy = c.centro
            if math.hypot(cx - wx, cy - wy) < 9 and self.no_alcance(cx, cy):
                return c
        return None

    def tem_vara(self):
        inv = self.jogador.inventario
        eq = inv.equipamento["ferramenta"]
        return inv.item_selecionado() == "vara_pesca" or (eq and eq[0] == "vara_pesca")

    # ===========================================================
    # Eventos
    # ===========================================================
    def tratar_evento(self, ev):
        if self.estruturas.tratar_evento(ev):               # [ESTRUTURAS] janela de trocas
            return
        if ev.type == pygame.MOUSEMOTION:
            if self.estado == "mapa" and self.arrastando_mapa:
                mx, my = ev.pos
                ax, ay = self.arrastando_mapa
                self.mapa_centro[0] -= (mx - ax) / self.zoom_mapa
                self.mapa_centro[1] -= (my - ay) / self.zoom_mapa
                self.arrastando_mapa = ev.pos
            self.pos_mouse = ev.pos
            return
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.pos_mouse = ev.pos
            self.clique(ev.button, ev.pos)
            return
        if ev.type == pygame.MOUSEBUTTONUP:
            self.pos_mouse = ev.pos
            self.arrastando_mapa = None
            if self.estado in ESTADOS_SLOTS:
                self.soltar_arrasto(ev.pos)
            return
        if ev.type == pygame.MOUSEWHEEL:
            if self.estado == "jogando":
                inv = self.jogador.inventario
                inv.selecionado = (inv.selecionado - ev.y) % TAMANHO_BARRA
            elif self.estado == "mapa":
                self.zoom_mapa = max(1, min(6, self.zoom_mapa + (1 if ev.y > 0 else -1)))
            return
        if ev.type in (getattr(pygame, "JOYDEVICEADDED", -1), getattr(pygame, "JOYDEVICEREMOVED", -1)):
            self.controles.procurar_gamepad()
            return
        if ev.type == pygame.JOYBUTTONDOWN:
            self.botao_gamepad(self.controles.acao_do_botao(ev.button))
            return
        if ev.type != pygame.KEYDOWN:
            return

        tecla = ev.key
        if self.estado == "controles":
            self.tecla_controles(tecla)
            return
        if self.estado == "menu_inicial":
            self.tecla_menu(ev)
            return
        if tecla == pygame.K_F5 and self.estado in ("jogando", "criando", "pausa") + ESTADOS_SLOTS:
            self.salvar()
            return
        if tecla == pygame.K_F9:
            self.carregar()
            return
        acao = self.controles.acao_da_tecla(tecla)
        if self.estado == "ajuda":
            self.estado = self.estado_anterior
        elif self.estado == "morto":
            if tecla == pygame.K_r:
                self.renascer()
        elif self.estado == "pausa":
            if tecla == pygame.K_ESCAPE:
                self.estado = "jogando"
        elif self.estado == "mapa":
            if tecla == pygame.K_ESCAPE or acao == "mapa":
                self.estado = "jogando"
            elif tecla == pygame.K_SPACE:
                self.centralizar_mapa()
        elif self.estado == "criando":
            if tecla == pygame.K_ESCAPE or acao == "criar":
                self.estado = "jogando"
        elif self.estado in ESTADOS_SLOTS:
            if tecla == pygame.K_ESCAPE or acao in ("inventario", "interagir"):
                self.fechar_inventario()
        elif self.estado == "jogando":
            self.tecla_jogando(tecla, acao)

    def tecla_menu(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.iniciar_pelo_menu()
        elif ev.key == pygame.K_BACKSPACE:
            self.texto_semente = self.texto_semente[:-1]
        elif ev.key == pygame.K_F9:
            self.carregar()
        elif ev.unicode and ev.unicode.isprintable() and len(self.texto_semente) < 24:
            self.texto_semente += ev.unicode

    def tecla_controles(self, tecla):
        if self.esperando_tecla:
            if tecla != pygame.K_ESCAPE:
                self.controles.definir(self.esperando_tecla, tecla)
            self.esperando_tecla = None
        elif tecla == pygame.K_ESCAPE:
            self.estado = self.volta_controles

    def tecla_jogando(self, tecla, acao=None):
        inv = self.jogador.inventario
        if acao is None:
            acao = self.controles.acao_da_tecla(tecla)
        if tecla == pygame.K_ESCAPE:
            self.estado = "pausa"
        elif pygame.K_1 <= tecla <= pygame.K_9:
            inv.selecionado = tecla - pygame.K_1
        elif acao == "interagir":
            self.interagir()
        elif acao == "comer":
            self.comer()
        elif acao == "atacar":
            self.atacar(self.mouse_mundo() if self.mouse_no_mundo() else None)
        elif acao == "rolar":
            self.jogador.rolar()
        elif acao == "criar":
            self.estado = "criando"
        elif acao == "inventario":
            self.estado = "inventario"
        elif acao == "minimapa":
            self.minimapa.trocar_tamanho()
        elif acao == "mapa":
            self.abrir_mapa()
        elif acao == "ajuda":
            self.estado_anterior = "jogando"
            self.estado = "ajuda"
        elif acao == "espiar":                                # [v0.5] ver a camada de cima
            if self.camadas.z < 0:
                self.camadas.espiar = not self.camadas.espiar
                self.avisar("Vendo a camada de cima" if self.camadas.espiar else "Visão normal", 1.2)
            else:
                self.avisar("Só funciona debaixo da terra", 1.2)

    def botao_gamepad(self, acao):
        """Botões do controle (gamepad)."""
        if acao is None:
            return
        inv = self.jogador.inventario
        if self.estado == "menu_inicial":
            if acao in ("interagir", "pausa"):
                self.iniciar_pelo_menu()
            return
        if self.estado in ("ajuda",):
            self.estado = self.estado_anterior
            return
        if self.estado == "morto":
            if acao in ("interagir", "pausa"):
                self.renascer()
            return
        if self.estado != "jogando":
            if acao in ("pausa", "rolar", "inventario", "mapa", "criar"):
                self.fechar_inventario()
            return
        if acao == "barra_anterior":
            inv.selecionado = (inv.selecionado - 1) % TAMANHO_BARRA
        elif acao == "barra_proxima":
            inv.selecionado = (inv.selecionado + 1) % TAMANHO_BARRA
        elif acao == "pausa":
            self.estado = "pausa"
        elif acao == "atacar":
            self.atacar(self.mira_gamepad())
        else:
            self.tecla_jogando(None, acao)

    def mira_gamepad(self):
        j = self.jogador
        d = self.controles.mira_gamepad() or Jogador.VETORES[j.direcao]
        cx, cy = j.centro
        return (cx + d[0] * 20, cy + d[1] * 20)

    def abrir_mapa(self):
        if self.estruturas.subterraneo:
            self.avisar("O mapa não funciona debaixo da terra", 1.5)
            return
        self.estado = "mapa"
        self.centralizar_mapa()

    def centralizar_mapa(self):
        self.mapa_centro = [self.jogador.x / TILE, self.jogador.y / TILE]

    def clique(self, botao, pos):
        if botao not in (1, 3):
            return
        botoes = self.interface.botoes
        if self.estado == "menu_inicial":
            if botoes.get("jogar") and botoes["jogar"].collidepoint(pos):
                self.iniciar_pelo_menu()
            elif botoes.get("aleatoria") and botoes["aleatoria"].collidepoint(pos):
                self.texto_semente = str(random.randrange(1, 1_000_000))
            elif botoes.get("carregar") and botoes["carregar"].collidepoint(pos) and self.tem_save:
                self.carregar()
            elif botoes.get("controles") and botoes["controles"].collidepoint(pos):
                self.volta_controles = "menu_inicial"
                self.estado = "controles"
            elif botoes.get("sair") and botoes["sair"].collidepoint(pos):
                if WEB:
                    self.avisar("No navegador é só fechar a aba (o jogo salva sozinho)", 3)
                else:
                    self.rodando = False
        elif self.estado == "controles":
            acao = self.interface.no_ponto(self.interface.ret_controles, pos)
            if acao:
                self.esperando_tecla = acao
            elif botoes.get("padrao") and botoes["padrao"].collidepoint(pos):
                self.controles.restaurar_padrao()
            elif botoes.get("voltar") and botoes["voltar"].collidepoint(pos):
                self.esperando_tecla = None
                self.estado = self.volta_controles
        elif self.estado == "pausa":
            if botoes.get("continuar") and botoes["continuar"].collidepoint(pos):
                self.estado = "jogando"
            elif botoes.get("controles") and botoes["controles"].collidepoint(pos):
                self.volta_controles = "pausa"
                self.estado = "controles"
            elif botoes.get("ajuda") and botoes["ajuda"].collidepoint(pos):
                self.estado_anterior = "pausa"
                self.estado = "ajuda"
            elif botoes.get("salvar") and botoes["salvar"].collidepoint(pos):
                self.salvar()
            elif botoes.get("menu") and botoes["menu"].collidepoint(pos):
                self.texto_semente = ""
                self.estado = "menu_inicial"
        elif self.estado == "mapa":
            if self.interface.ret_painel.collidepoint(pos):
                self.arrastando_mapa = pos
            else:
                self.estado = "jogando"
        elif self.estado == "ajuda":
            self.estado = self.estado_anterior
        elif self.estado == "morto":
            if botoes.get("renascer") and botoes["renascer"].collidepoint(pos):
                self.renascer()
            elif botoes.get("mesma") and botoes["mesma"].collidepoint(pos):
                self.novo_jogo(self.mundo.semente)
            elif botoes.get("novo") and botoes["novo"].collidepoint(pos):
                self.texto_semente = ""
                self.estado = "menu_inicial"
        elif self.estado == "criando":
            cat = self.interface.no_ponto(self.interface.ret_abas, pos)
            if cat:
                self.categoria = cat
                return
            indice = self.interface.no_ponto(self.interface.ret_receitas, pos)
            if indice is not None:
                self.selecao_criacao = indice
                self.criar(indice)
            elif not self.interface.ret_painel.collidepoint(pos):
                self.estado = "jogando"
        elif self.estado in ESTADOS_SLOTS:
            mods = pygame.key.get_mods() if pygame.display.get_init() else 0
            if mods & pygame.KMOD_SHIFT:
                self.mover_rapido(pos)
            else:
                self.pegar_arrasto(botao, pos)
        elif self.estado == "jogando":
            espaco = self.interface.espaco_barra_no_ponto(pos)
            if espaco is not None:
                self.jogador.inventario.selecionado = espaco
            elif self.interface.ret_minimapa.collidepoint(pos):
                self.abrir_mapa()
            elif self.pesca:
                self.fisgar()
            elif botao == 3:
                self.clique_direito()

    # ===========================================================
    # Inventário: arrastar e soltar
    # ===========================================================
    # refs: ("inv", i), ("equip", slot), ("bau", i),
    #       [v0.5] ("grade", i), ("saida", 0) e ("forno", 0 entrada / 1 combustível / 2 saída)
    def grade_atual(self):
        return (self.grade3, 3) if self.estado == "bancada" else (self.grade2, 2)

    def pegar_ref(self, ref):
        if ref[0] == "bau":
            return self.bau_aberto.conteudo[ref[1]] if self.bau_aberto else None
        if ref[0] == "grade":
            return self.grade_atual()[0][ref[1]]
        if ref[0] == "saida":
            return criacao.resultado(*self.grade_atual())
        if ref[0] == "forno":
            return self.forno_aberto.conteudo[ref[1]] if self.forno_aberto else None
        return self.jogador.inventario.pegar(ref)

    def por_ref(self, ref, valor):
        if ref[0] == "bau":
            if self.bau_aberto:
                self.bau_aberto.conteudo[ref[1]] = valor
                self.mundo.marcar_modificado(self.bau_aberto)
            return
        if ref[0] == "grade":
            self.grade_atual()[0][ref[1]] = valor
            return
        if ref[0] == "saida":
            return
        if ref[0] == "forno":
            if self.forno_aberto:
                self.forno_aberto.conteudo[ref[1]] = valor
                self.mundo.marcar_modificado(self.forno_aberto)
                self.mundo._sujar()
            return
        self.jogador.inventario.por(ref, valor)

    def cabe_ref(self, ref, pilha):
        if ref[0] in ("bau", "grade"):
            return True
        if ref[0] == "saida":
            return pilha is None
        if ref[0] == "forno":
            if pilha is None:
                return True
            if ref[1] == 0:
                return criacao.fundivel(pilha[0])
            if ref[1] == 1:
                return criacao.combustivel(pilha[0])
            return False
        return self.jogador.inventario.cabe_no(ref, pilha)

    def criar_da_grade(self, tudo=False):
        """Pega o resultado da grade. tudo=True (Shift): cria o máximo e manda para a mochila."""
        grade, lado = self.grade_atual()
        res = criacao.resultado(grade, lado)
        if res is None:
            return
        inv = self.jogador.inventario
        if tudo:
            vezes = 0
            while res is not None and vezes < 64:
                if inv.adicionar(res[0], res[1]):
                    self.jogar_no_chao([res[0], res[1]])
                criacao.consumir(grade)
                vezes += 1
                novo = criacao.resultado(grade, lado)
                if novo is None or novo[0] != res[0]:
                    break
                res = novo
            self.avisar(f"Você criou {ITENS[res[0]]['nome']} x{vezes * res[1]}")
            return
        mao = self.arrastando
        if mao is None:
            self.arrastando = res
            self.origem_arrasto = ("saida", 0)
        elif mao[0] == res[0] and ITENS[res[0]]["pilha"] >= mao[1] + res[1]:
            mao[1] += res[1]
        else:
            return
        criacao.consumir(grade)

    def pegar_arrasto(self, botao, pos):
        inv = self.jogador.inventario
        ref = self.interface.no_ponto(self.interface.slots_inventario, pos)
        if ref is not None and ref[0] == "saida":
            self.criar_da_grade()
            return
        if ref is None or self.arrastando:
            return
        pilha = self.pegar_ref(ref)
        if pilha is None:
            return
        if botao == 3:
            if ref[0] == "inv" and "slot" in ITENS[pilha[0]]:
                inv.equipar(ref[1])
                return
            if ref[0] == "equip":
                if not inv.desequipar(ref[1]):
                    self.avisar("Inventário cheio!")
                return
            if pilha[1] > 1:   # divide a pilha ao meio
                metade = pilha[1] // 2
                pilha[1] -= metade
                self.arrastando = [pilha[0], metade]
                self.origem_arrasto = ref
                if ref[0] == "bau":
                    self.mundo.marcar_modificado(self.bau_aberto)
                elif ref[0] == "forno" and self.forno_aberto:
                    self.mundo.marcar_modificado(self.forno_aberto)
                return
        self.arrastando = pilha
        self.origem_arrasto = ref
        self.por_ref(ref, None)

    def soltar_arrasto(self, pos):
        if not self.arrastando:
            return
        mao = self.arrastando
        ref = self.interface.no_ponto(self.interface.slots_inventario, pos)
        if ref is not None and ref[0] == "saida":
            self.devolver_arrasto()                 # soltou na saída: vai para a mochila
            return
        if ref is None:
            if not self.interface.ret_painel.collidepoint(pos):
                self.jogar_no_chao(mao)           # soltou fora: joga no chão
                self.arrastando = None
            else:
                self.devolver_arrasto()
            return
        if not self.cabe_ref(ref, mao):
            self.avisar("Esse item não vai nesse espaço")
            self.devolver_arrasto()
            return
        alvo = self.pegar_ref(ref)
        if alvo is None:
            self.por_ref(ref, mao)
        elif alvo[0] == mao[0] and ITENS[mao[0]]["pilha"] > 1:
            cabe = min(ITENS[mao[0]]["pilha"] - alvo[1], mao[1])
            alvo[1] += cabe
            mao[1] -= cabe
            self.por_ref(ref, alvo)
            if mao[1] > 0:
                self.devolver_arrasto()
                return
        else:
            # troca de lugar (se o que estava lá couber na origem)
            if self.pegar_ref(self.origem_arrasto) is None and self.cabe_ref(self.origem_arrasto, alvo):
                self.por_ref(ref, mao)
                self.por_ref(self.origem_arrasto, alvo)
            else:
                self.devolver_arrasto()
                return
        self.arrastando = None

    def devolver_arrasto(self):
        inv = self.jogador.inventario
        mao = self.arrastando
        self.arrastando = None
        if mao is None:
            return
        origem = self.origem_arrasto
        o = self.pegar_ref(origem) if origem and origem[0] != "saida" else None
        if origem and origem[0] != "saida" and o is None and self.cabe_ref(origem, mao):
            self.por_ref(origem, mao)
        elif o is not None and o[0] == mao[0] and len(mao) < 3:
            o[1] += mao[1]
        else:
            sobra = inv.adicionar(mao[0], mao[1], mao[2] if len(mao) > 2 else None)
            if sobra:
                self.jogar_no_chao([mao[0], sobra] + mao[2:])

    def mover_rapido(self, pos):
        """Shift+clique: manda a pilha direto para o outro lado (baú, forno, grade, mochila)."""
        ref = self.interface.no_ponto(self.interface.slots_inventario, pos)
        if ref is None:
            return
        if ref[0] == "saida":
            self.criar_da_grade(tudo=True)
            return
        pilha = self.pegar_ref(ref)
        if not pilha:
            return
        inv = self.jogador.inventario
        extra = pilha[2:]
        if ref[0] in ("bau", "grade", "forno"):
            sobra = inv.adicionar(pilha[0], pilha[1], extra[0] if extra else None)
            self.por_ref(ref, [pilha[0], sobra] + extra if sobra else None)
        elif self.estado == "bau" and self.bau_aberto is not None:
            sobra = self.guardar_em(self.bau_aberto.conteudo, pilha)
            self.mundo.marcar_modificado(self.bau_aberto)
            self.por_ref(ref, [pilha[0], sobra] + extra if sobra else None)
        elif self.estado == "forno" and self.forno_aberto is not None:
            k = 0 if criacao.fundivel(pilha[0]) else (1 if criacao.combustivel(pilha[0]) else None)
            if k is None:
                self.avisar("Isso não vai no forno", 1.2)
                return
            sobra = self.guardar_em(self.forno_aberto.conteudo, pilha, so=k)
            self.mundo.marcar_modificado(self.forno_aberto)
            self.mundo._sujar()
            self.por_ref(ref, [pilha[0], sobra] + extra if sobra else None)
        elif ref[0] == "inv":
            # mochila <-> barra rápida
            alvo = range(9, 36) if ref[1] < 9 else range(0, 9)
            for i in alvo:
                if inv.espacos[i] is None:
                    inv.espacos[i] = pilha
                    inv.espacos[ref[1]] = None
                    break

    def guardar_em(self, cont, pilha, so=None):
        """Põe a pilha numa lista de espaços (baú/forno). Retorna quanto sobrou."""
        item, qtd = pilha[0], pilha[1]
        maximo = ITENS[item]["pilha"]
        indices = [so] if so is not None else range(len(cont))
        for i in indices:
            e = cont[i]
            if e and e[0] == item and e[1] < maximo and len(e) < 3:
                cabe = min(qtd, maximo - e[1])
                e[1] += cabe
                qtd -= cabe
        for i in indices:
            if qtd and cont[i] is None:
                cabe = min(qtd, maximo)
                cont[i] = [item, cabe] + list(pilha[2:])
                qtd -= cabe
        return qtd

    def guardar_no_bau(self, item, qtd):
        sobra = self.guardar_em(self.bau_aberto.conteudo, [item, qtd])
        self.mundo.marcar_modificado(self.bau_aberto)
        return sobra

    def abrir_bau(self, bau):
        self.bau_aberto = bau
        self.estado = "bau"

    def abrir_bancada(self, bancada):
        self.estado = "bancada"

    def abrir_forno(self, forno):
        self.forno_aberto = forno
        self.estado = "forno"

    def fechar_inventario(self):
        self.devolver_arrasto()
        # [v0.5] o que ficou nas grades volta para a mochila
        inv = self.jogador.inventario
        for grade in (self.grade2, self.grade3):
            for i, e in enumerate(grade):
                if e:
                    sobra = inv.adicionar(e[0], e[1], e[2] if len(e) > 2 else None)
                    if sobra:
                        self.jogar_no_chao([e[0], sobra] + e[2:])
                    grade[i] = None
        self.bau_aberto = None
        self.forno_aberto = None
        self.estado = "jogando"

    def jogar_no_chao(self, pilha):
        j = self.jogador
        fx, fy = j.ponto_frente(14)
        it = ItemChao(pilha[0], fx, fy + 4, pilha[1])
        it.usos = pilha[2] if len(pilha) > 2 else None
        it.idade = -1.0              # demora um pouco para ser puxado de volta
        self.mundo.itens.append(it)
        self.avisar(f"Você jogou {pilha[1]}x {ITENS[pilha[0]]['nome']}")

    # ===========================================================
    # Criação
    # ===========================================================
    def estacao_perto(self, estacao):
        cx, cy = self.jogador.centro
        return self.mundo.estacao_perto(estacao, cx, cy, RAIO_ESTACAO) is not None

    def pode_criar(self, rc):
        inv = self.jogador.inventario
        est = rc.get("estacao")
        if est == "bancada" and self.estado == "bancada":
            est = None
        if est and not self.estacao_perto(est):
            return False, "Precisa de " + {"bancada": "uma bancada", "forno": "um forno"}.get(est, "uma fogueira acesa") + " por perto"
        for item, qtd in rc["custo"].items():
            if not inv.tem(item, qtd):
                return False, f"Faltam materiais: {ITENS[item]['nome']}"
        return True, ""

    def criar(self, indice):
        rc = RECEITAS[indice]
        ok, motivo = self.pode_criar(rc)
        if not ok:
            self.avisar(motivo)
            return False
        inv = self.jogador.inventario
        for item, qtd in rc["custo"].items():
            inv.remover(item, qtd)
        sobra = inv.adicionar(rc["item"], rc.get("qtd", 1))
        if sobra:
            self.jogar_no_chao([rc["item"], sobra])
        self.avisar(f"Você criou: {ITENS[rc['item']]['nome']}!")
        self.jogador.exaustao += 0.05
        return True

    # ===========================================================
    # Quebrar, drops e coleta
    # ===========================================================
    def golpear(self, obj):
        j = self.jogador
        if self.estruturas.golpear(obj):                    # [ESTRUTURAS] baú, escada...
            return
        if obj.tipo == "buraco":                            # [v0.5]
            self.avisar("Fique em cima do buraco e aperte E para descer (ou tape com um bloco)", 2)
            return
        info = OBJETOS[obj.tipo]
        ferramenta = info.get("ferramenta")
        poder = j.inventario.poder_ferramenta(ferramenta) if ferramenta else 1
        if not j.pode_usar_ferramentas():
            self.avisar("Você não pode usar ferramentas nadando", 1.2)
            return
        obj.tremor = 0.2
        self.mundo.golpeado(obj)
        j.tempo_golpe = DURACAO_GOLPE
        if poder < info.get("poder_min", 0):
            if ferramenta == "picareta":
                self.avisar(f"Precisa de {picareta_para(info['poder_min'])} (ou melhor)", 1.5)
            else:
                self.avisar("Precisa de uma ferramenta melhor", 1.5)
            return
        obj.vida -= poder
        obj.tempo_sem_golpe = 0.0
        j.exaustao += 0.05
        if ferramenta and poder > 1:
            self.gastar_ferramenta(ferramenta)
        self.soltar_lascas(obj.centro, obj.tipo, 4)
        if obj.vida <= 0:
            self.quebrar(obj)

    def quebrar(self, obj):
        info = OBJETOS[obj.tipo]
        if obj.tipo == "arbusto" and obj.tem_frutas:
            obj.tem_frutas = False
            obj.tempo_frutas = 0.0
            obj.vida = obj.vida_max
            drops = info["drops"]
            self.mundo.marcar_modificado(obj)
        else:
            drops = info["drops_vazio"] if obj.tipo == "arbusto" else info["drops"]
            if obj.maduro:
                drops = info["drops_maduro"]
            if obj.conteudo:                 # baú/forno quebrado solta o que tinha dentro
                drops = drops + [tuple(e) for e in obj.conteudo if e]
            if info.get("xp"):               # [v0.5] minérios dão XP
                self.soltar_xp(obj.centro, info["xp"])
            if obj.tipo == "cama" and self.ponto_renascer == (obj.tx, obj.ty):
                self.ponto_renascer = None
                self.avisar("Sua cama foi desmontada: você vai renascer no início")
            self.mundo.remover(obj)
        self.soltar_lascas(obj.centro, obj.tipo, 10)
        self.soltar_itens(drops, *obj.centro)

    def soltar_itens(self, drops, x, y):
        for d in drops:
            item, qtd = d[0], d[1]
            if len(d) > 2:                   # ferramenta com durabilidade: sai inteira
                it = ItemChao(item, x + random.uniform(-3, 3), y + random.uniform(-2, 4), qtd)
                it.usos = d[2]
                self.mundo.itens.append(it)
                continue
            for _ in range(qtd):
                self.mundo.itens.append(ItemChao(item, x + random.uniform(-3, 3), y + random.uniform(-2, 4)))

    # ===========================================================
    # [v0.5] Durabilidade, XP e explosões
    # ===========================================================
    def _ref_ferramenta(self, tipo):
        """Onde está a melhor ferramenta desse tipo (na mão ou equipada)."""
        inv = self.jogador.inventario
        melhor, poder = None, 0
        for ref in (("inv", inv.selecionado), ("equip", "ferramenta"), ("equip", "arma")):
            e = inv.pegar(ref)
            f = ITENS[e[0]].get("ferramenta") if e else None
            if f and f[0] == tipo and f[1] > poder:
                melhor, poder = ref, f[1]
        return melhor

    def _ref_arma(self):
        inv = self.jogador.inventario
        melhor, dano = None, 0
        for ref in (("inv", inv.selecionado), ("equip", "arma")):
            e = inv.pegar(ref)
            d = ITENS[e[0]].get("dano", 0) if e else 0
            if d > dano:
                melhor, dano = ref, d
        return melhor

    def gastar_ref(self, ref, usos=1):
        if ref is None:
            return
        inv = self.jogador.inventario
        e = inv.pegar(ref)
        if not e or len(e) < 3:
            return
        e[2] -= usos
        if e[2] <= 0:
            inv.por(ref, None)
            self.avisar(f"Seu item quebrou: {ITENS[e[0]]['nome']}!", 2.5)
            self.soltar_lascas(self.jogador.centro, "pedra", 8)

    def gastar_ferramenta(self, tipo):
        self.gastar_ref(self._ref_ferramenta(tipo))

    def soltar_xp(self, centro, pontos):
        x, y = centro
        while pontos > 0:
            v = min(XP_ORBE, pontos)
            pontos -= v
            ang = random.uniform(0, math.tau)
            self.orbes.append({"x": x, "y": y, "vx": math.cos(ang) * 30, "vy": math.sin(ang) * 30,
                               "v": v, "t": 0.0})

    def atualizar_orbes(self, dt):
        j = self.jogador
        vivos = []
        for o in self.orbes:
            o["t"] += dt
            dx, dy = j.x - o["x"], (j.y - 6) - o["y"]
            d = math.hypot(dx, dy) or 1.0
            if o["t"] > 0.5 and d < 56:
                vel = 70 + (56 - d) * 4
                o["vx"], o["vy"] = dx / d * vel, dy / d * vel
            else:
                o["vx"] *= 0.9
                o["vy"] *= 0.9
            o["x"] += o["vx"] * dt
            o["y"] += o["vy"] * dt
            if o["t"] > 0.5 and d < 6:
                nivel = self.nivel_xp()[0]
                j.xp += o["v"]
                if self.nivel_xp()[0] > nivel:
                    self.avisar(f"Você subiu para o nível {self.nivel_xp()[0]}!", 2.5)
                    self.popup_texto(f"Nível {self.nivel_xp()[0]}!", j.x, j.y - 24, (170, 255, 120))
                continue
            if o["t"] < 300:
                vivos.append(o)
        self.orbes = vivos

    def nivel_xp(self):
        """(nível, fração até o próximo)."""
        xp, nivel = self.jogador.xp, 0
        while xp >= 7 + 2 * nivel:
            xp -= 7 + 2 * nivel
            nivel += 1
        return nivel, xp / (7 + 2 * nivel)

    def explosao(self, x, y, raio, dano):
        """Explosivo: quebra blocos em volta, machuca e empurra."""
        self.tremor_tela = 0.35
        for _ in range(40):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(30, 120)
            self.particulas.append([x, y, math.cos(ang) * vel, math.sin(ang) * vel - 40,
                                    random.uniform(0.3, 0.8), random.choice(COR_LASCAS["explosao"])])
        rpx = raio * TILE
        j = self.jogador
        d = math.hypot(j.x - x, j.y - 6 - y)
        if d < rpx * 1.4:
            real = j.levar_dano(dano * max(0.15, 1 - d / (rpx * 1.4)))
            if real:
                self.avisar(f"BUM! (-{real})", 2)
                self.gastar_armadura()
            dd = d or 1.0
            j.vx += (j.x - x) / dd * 160
            j.vy += (j.y - y) / dd * 160
        for c in self.criaturas:
            dc = math.hypot(c.x - x, c.y - y)
            if dc < rpx * 1.2:
                c.levar_golpe(dano * 0.4 * (1 - dc / (rpx * 1.2)) + 1, x, y)
        if self.estruturas.subterraneo:
            return
        tx0, ty0 = int(x // TILE), int((y + 4) // TILE)
        r = int(math.ceil(raio))
        protegidos = ("bau", "cama", "forno", "bancada", "buraco", "escada", "bau_tesouro", "bau_tesouro_aberto",
                      "poco", "trono", "escada_descer", "escada_subir", "porta")
        for ty in range(ty0 - r, ty0 + r + 1):
            for tx in range(tx0 - r, tx0 + r + 1):
                if math.hypot(tx - tx0, ty - ty0) > raio:
                    continue
                o = self.mundo.objeto(tx, ty)
                if o is None or o.tipo in protegidos:
                    continue
                self.mundo.remover(o)
                if random.random() < 0.35:
                    drops = OBJETOS[o.tipo].get("drops", [])
                    self.soltar_itens(drops[:1], *o.centro)

    def gastar_armadura(self):
        for slot in ("cabeca", "corpo"):
            self.gastar_ref(("equip", slot))

    def soltar_lascas(self, centro, tipo, quantidade):
        cores = COR_LASCAS.get(tipo, [(220, 220, 220)])
        cx, cy = centro
        for _ in range(quantidade):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(20, 55)
            self.particulas.append([cx, cy - 3, math.cos(ang) * vel, math.sin(ang) * vel - 30,
                                    random.uniform(0.25, 0.5), random.choice(cores)])

    def pegar_itens(self):
        j = self.jogador
        restantes = []
        for it in self.mundo.itens:
            if it.pode_pegar and it.distancia_jogador(j) < RAIO_PEGAR_ITENS:
                sobra = j.inventario.adicionar(it.item, it.quantidade, getattr(it, "usos", None))
                if it.quantidade - sobra:
                    self.popup(it.item, it.quantidade - sobra)
                if sobra:
                    it.quantidade = sobra
                    restantes.append(it)
                    self.avisar("Inventário cheio!", 1.0)
            else:
                restantes.append(it)
        self.mundo.itens = restantes

    def popup(self, item, qtd):
        for p in self.popups:
            if p.get("item") == item and p["tempo"] > 0.7:
                p["qtd"] += qtd
                p["tempo"] = 1.2
                return
        self.popups.append({"item": item, "qtd": qtd, "x": self.jogador.x,
                            "y": self.jogador.y - 20, "tempo": 1.2})

    def popup_texto(self, texto, x, y, cor=(255, 245, 170)):
        self.popups.append({"texto": texto, "x": x, "y": y, "tempo": 1.2, "cor": cor})

    # ===========================================================
    # Construir
    # ===========================================================
    def pode_colocar(self, item, tx, ty):
        m = self.mundo
        if m.chunk(tx, ty) is None:
            return False, "Longe demais"
        if self.jogador.nadando:
            return False, "Não dá para construir nadando"
        bloco = ITENS[item].get("objeto", item) in TIPOS_BLOCO
        if m.tipo_chao(tx, ty) in CHAO_AGUA + (LAVA,) and not bloco:
            return False, "Não dá para construir na água" if m.tipo_chao(tx, ty) != LAVA else "Isso queimaria na lava"
        if item == "sementes_trigo" and m.tipo_chao(tx, ty) not in CHAO_PLANTAVEL:
            return False, "Plante na grama ou na terra"
        if not self.no_alcance(tx * TILE + 8, ty * TILE + 8, folga=6):
            return False, "Longe demais"
        obj = m.objeto(tx, ty)
        if item == "piso":
            if m.piso(tx, ty):
                return False, "Já tem piso aqui"
            if obj and not obj.construcao:
                return False, "Tem algo no caminho"
            return True, ""
        if obj and not (bloco and obj.tipo == "buraco"):
            return False, "Tem algo no caminho"
        if item == "escada" and self.camadas.z >= 0:
            return False, "Escada de mão é para subir das cavernas (para descer: cave com a pá)"
        if bloco and m.piso(tx, ty):
            return False, "Tem um piso aqui"
        ret = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
        if ret.colliderect(self.jogador.retangulo()):
            return False, "Você está no caminho"
        if any(ret.colliderect(c.retangulo()) for c in self.criaturas):
            return False, "Tem um bicho no caminho"
        return True, ""

    def tentar_colocar(self, tx, ty, avisar=False):
        inv = self.jogador.inventario
        item = inv.item_selecionado()
        if not item or ITENS[item]["tipo"] != "construcao":
            return False
        ok, motivo = self.pode_colocar(item, tx, ty)
        if not ok:
            if avisar:
                self.avisar(motivo, 1.5)
            return False
        if item == "escada":                                 # [v0.5] escada abre buraco em cima
            ok, motivo = self.camadas.colocar_escada(tx, ty)
            if not ok:
                if avisar:
                    self.avisar(motivo, 2)
                return False
            inv.remover(item, 1)
            return True
        inv.remover(item, 1)
        tipo = ITENS[item].get("objeto", item)
        velho = self.mundo.objeto(tx, ty)
        if velho is not None and velho.tipo == "buraco":
            self.mundo.remover(velho)                         # tapou o buraco
        ch = self.mundo.chunk(tx, ty)
        k = (ty % CH) * CH + (tx % CH)
        if tipo in TIPOS_BLOCO and ch.chao[k] in CHAO_AGUA + (LAVA,):
            ch.mudar_chao(k, CAVERNA if self.camadas.z < 0 else LAMA)   # aterra a água / apaga a lava
        novo = Objeto(tipo, tx, ty)
        self.mundo.colocar(novo)
        self.soltar_lascas(novo.centro, item, 5)
        self.jogador.olhar_para(*novo.centro)
        if item == "fogueira":
            self.avisar("Fogueira acesa!")
        elif item == "sementes_trigo" and self.estacao == "inverno":
            self.avisar("No inverno as plantas não crescem... espere a primavera")
        elif item == "cama":
            self.ponto_renascer = (tx, ty)
            self.avisar("Cama colocada: você vai renascer aqui")
        return True

    def clique_direito(self):
        """Botão direito: construir, consumir, pescar ou usar a fogueira."""
        if self.estruturas.clique_direito():                # [ESTRUTURAS] NPC, baú, escada
            return
        inv = self.jogador.inventario
        item = inv.item_selecionado()
        tx, ty = self.bloco_mouse()
        tipo = ITENS[item]["tipo"] if item else None
        alvo, alcanca = self.alvo_mouse()
        if alvo and alcanca and alvo.tipo == "bau":
            self.abrir_bau(alvo)
            return
        if alvo and alcanca and alvo.tipo == "bancada":       # [v0.5] grade 3x3
            self.abrir_bancada(alvo)
            return
        if alvo and alcanca and alvo.tipo == "forno":
            self.abrir_forno(alvo)
            return
        if alvo and alcanca and alvo.tipo == "fogueira" and (tipo != "construcao" or item == "madeira"):
            self.usar_fogueira(alvo)
            return
        if alvo and alcanca and alvo.tipo == "cama":
            self.usar_cama(alvo)
            return
        if tipo == "construcao":
            self.tentar_colocar(tx, ty, avisar=True)
            self.jogador.espera_construir = TEMPO_ENTRE_CONSTRUCOES * 2
        elif self.tem_vara() and self.mundo.tipo_chao(tx, ty) in CHAO_AGUA and tipo not in ("comida", "bebida"):
            self.iniciar_pesca(tx, ty)
        elif tipo in ("comida", "bebida"):
            self.consumir(item)
        elif self.tem_vara():
            self.avisar("Clique com o botão direito na água para pescar", 1.5)
        else:
            obj, alcanca = self.alvo_mouse()
            if obj and alcanca and obj.tipo == "fogueira":
                self.usar_fogueira(obj)

    # ===========================================================
    # Comer, beber, fogueira, pesca
    # ===========================================================
    def consumir(self, item):
        j = self.jogador
        info = ITENS[item]
        if not j.inventario.remover(item, 1):
            return False
        j.fome = min(FOME_MAX, j.fome + info.get("fome", 0))
        j.saturacao = min(j.fome, j.saturacao + info.get("saturacao", info.get("fome", 0) * 0.6))
        j.sede = min(SEDE_MAX, j.sede + info.get("sede", 0))
        j.vida = max(1.0, min(VIDA_MAX, j.vida + info.get("vida", 0)))
        if info.get("devolve"):
            j.inventario.adicionar(info["devolve"], 1)
        if info.get("vida", 0) < 0:
            self.avisar(f"Você comeu {info['nome'].lower()}... não caiu bem (asse antes!)")
        else:
            self.avisar(f"Você consumiu: {info['nome']}")
        return True

    def comer(self):
        inv = self.jogador.inventario
        item = inv.item_selecionado()
        if item and ITENS[item]["tipo"] in ("comida", "bebida"):
            self.consumir(item)
            return
        comidas = [e[0] for e in inv.espacos if e and ITENS[e[0]]["tipo"] == "comida"]
        if not comidas:
            self.avisar("Você não tem comida", 1.5)
            return
        melhor = max(comidas, key=lambda i: ITENS[i].get("fome", 0) + ITENS[i].get("vida", 0))
        self.consumir(melhor)

    def usar_fogueira(self, f):
        """Assa comida crua (se tiver) ou coloca lenha."""
        inv = self.jogador.inventario
        if f.acesa:
            crua = inv.item_selecionado() if inv.item_selecionado() in COMIDA_CRUA else None
            if crua is None:
                crua = next((c for c in COMIDA_CRUA if inv.tem(c)), None)
            if crua:
                inv.remover(crua, 1)
                assada = COMIDA_CRUA[crua]
                if inv.adicionar(assada, 1):
                    self.jogar_no_chao([assada, 1])
                self.popup(assada, 1)
                self.soltar_lascas(f.centro, "fogueira", 6)
                return True
        if inv.remover("madeira", 1):
            f.combustivel = min(f.combustivel + COMBUSTIVEL_POR_MADEIRA, 300.0)
            self.mundo.marcar_modificado(f)
            self.avisar("Você colocou lenha na fogueira")
            return True
        self.avisar("Precisa de madeira (ou carne/peixe crus para assar)")
        return False

    def beber_agua(self):
        j = self.jogador
        j.sede = min(SEDE_MAX, j.sede + 30)
        vazios = j.inventario.quantidade("cantil")
        if vazios:
            j.inventario.remover("cantil", vazios)
            j.inventario.adicionar("cantil_cheio", vazios)
            self.avisar("Você bebeu água e encheu o cantil")
        else:
            self.avisar("Você bebeu água")

    def iniciar_pesca(self, tx, ty):
        if not self.no_alcance(tx * TILE + 8, ty * TILE + 8, folga=24):
            self.avisar("A água está longe demais", 1.2)
            return
        espera = random.uniform(2.0, 5.0) * (0.6 if self.clima.estado == "chuva" else 1.0)
        self.pesca = {"x": tx * TILE + 8, "y": ty * TILE + 9, "espera": espera, "mordendo": 0.0}
        self.jogador.olhar_para(tx * TILE + 8, ty * TILE + 8)
        self.avisar("Linha na água... clique quando o peixe morder!", 2)

    def atualizar_pesca(self, dt):
        p = self.pesca
        if not p:
            return
        j = self.jogador
        if not self.tem_vara() or math.hypot(p["x"] - j.x, p["y"] - j.y) > 90:
            self.pesca = None
            return
        if p["mordendo"] > 0:
            p["mordendo"] -= dt
            if p["mordendo"] <= 0:
                self.avisar("O peixe escapou!", 1.5)
                p["espera"] = random.uniform(2.0, 5.0)
        else:
            p["espera"] -= dt
            if p["espera"] <= 0:
                p["mordendo"] = 1.1
                self.popup_texto("!", p["x"], p["y"] - 6, (255, 90, 90))

    def fisgar(self):
        p = self.pesca
        self.pesca = None
        if p and p["mordendo"] > 0:
            j = self.jogador
            dx, dy = j.x - p["x"], j.y - p["y"]
            self.gastar_ferramenta("pesca")
            it = ItemChao("peixe", p["x"], p["y"], 1, vx=dx * 1.8, vy=dy * 1.8)
            it.vz, it.z = 110.0, 1.0           # o peixe pula para fora da água
            self.mundo.itens.append(it)
            self.avisar("Você pescou um peixe!")
        else:
            self.avisar("Você puxou a linha", 1.0)

    # ===========================================================
    # Tecla E e dicas
    # ===========================================================
    def interagir(self):
        j = self.jogador
        if self.camadas.interagir():                        # [v0.5] buraco (descer) / escada (subir)
            return
        if j.espera_coleta > 0:
            return
        j.espera_coleta = TEMPO_ENTRE_GOLPES
        if self.estruturas.interagir():                     # [ESTRUTURAS] NPC, baú, escada
            return
        cx, cy = j.centro
        inv = j.inventario
        estacao = self.mundo.objeto_mais_proximo(cx, cy, 24, tipos=("bancada", "forno"))
        if estacao and estacao.tipo == "bancada":
            self.abrir_bancada(estacao)
            return
        if estacao and estacao.tipo == "forno":
            self.abrir_forno(estacao)
            return
        fogueira = self.mundo.objeto_mais_proximo(cx, cy, 36, tipos=("fogueira",))
        if fogueira and fogueira.acesa and any(inv.tem(c) for c in COMIDA_CRUA):
            self.usar_fogueira(fogueira)
            return
        movel = self.mundo.objeto_mais_proximo(cx, cy, 24, tipos=("bau", "cama"))
        if movel and movel.tipo == "bau":
            self.abrir_bau(movel)
            return
        if movel and movel.tipo == "cama":
            self.usar_cama(movel)
            return
        if self.mundo.perto_de_agua(j.x, j.y - 3):
            self.beber_agua()
            return
        if fogueira:
            self.usar_fogueira(fogueira)
            return
        obj = self.mundo.objeto_mais_proximo(cx, cy, ALCANCE_INTERACAO)
        if obj and not obj.construcao:
            j.olhar_para(*obj.centro)
            self.golpear(obj)
        else:
            self.avisar("Nada por perto", 1.2)

    def dica_interacao(self):
        if self.estado != "jogando":
            return ""
        if self.pesca:
            return "Clique para fisgar!" if self.pesca["mordendo"] > 0 else "Esperando o peixe morder..."
        dica = self.camadas.dica()                          # [v0.5]
        if dica:
            return dica
        dica = self.estruturas.dica()                       # [ESTRUTURAS]
        if dica:
            return dica
        c = self.criatura_no_mouse()
        if c:
            return f"[Clique] Atacar {c.info['nome']}"
        obj, alcanca = self.alvo_mouse()
        if obj and alcanca:
            nome = NOMES_OBJETOS[obj.tipo]
            if obj.tipo == "fogueira":
                return "[Botão direito] Assar / pôr lenha   [Segurar esquerdo] Quebrar"
            if obj.tipo == "arbusto":
                return "[Segure o clique] Colher frutas" if obj.tem_frutas else "[Segure o clique] Arrancar arbusto"
            if obj.tipo == "bau":
                return "[Botão direito / E] Abrir baú   [Segurar esquerdo] Quebrar"
            if obj.tipo == "cama":
                return "[Botão direito / E] Dormir   [Segurar esquerdo] Quebrar"
            if obj.tipo == "bancada":
                return "[Botão direito / E] Grade de criação 3x3   [Segurar esquerdo] Quebrar"
            if obj.tipo == "forno":
                return "[Botão direito / E] Abrir forno   [Segurar esquerdo] Quebrar"
            if obj.tipo == "buraco":
                return "Buraco: fique em cima e aperte E para descer"
            if obj.bloco:
                info = OBJETOS[obj.tipo]
                if self.jogador.inventario.poder_ferramenta(info.get("ferramenta")) < info.get("poder_min", 0):
                    return f"{nome}: precisa de {picareta_para(info['poder_min'])}"
            if obj.tipo == "plantacao":
                return "[Segure o clique] Colher trigo" if obj.maduro else \
                    f"Trigo crescendo ({obj.estagio + 1}/4)" + ("  -  parado no inverno" if self.estacao == "inverno" else "")
            return f"[Segure o clique] Quebrar {nome.lower()}"
        j = self.jogador
        if j.nadando:
            return "Nadando... (sem ferramentas)" if j.ar > 30 else "Saia da água! O ar está acabando"
        cx, cy = j.centro
        f = self.mundo.objeto_mais_proximo(cx, cy, 36, tipos=("fogueira",))
        if f and f.acesa and any(j.inventario.tem(c) for c in COMIDA_CRUA):
            return "[E] Assar comida"
        if self.mundo.perto_de_agua(j.x, j.y - 3):
            return "[E] Beber água" + (" e encher cantil" if j.inventario.tem("cantil") else "")
        if self.tem_vara() and self.mouse_no_mundo():
            tx, ty = self.bloco_mouse()
            if self.mundo.tipo_chao(tx, ty) in CHAO_AGUA:
                return "[Botão direito] Pescar"
        if self.pode_cavar_mouse():
            return "[Segure o clique] Cavar o chão (abre um buraco para descer)"
        if self.mundo.tipo_chao(int(j.x // TILE), int((j.y - 2) // TILE)) == LAVA:
            return "Saia da lava!"
        return ""

    # ===========================================================
    # Combate
    # ===========================================================
    def alcance_arma(self):
        inv = self.jogador.inventario
        return max([ITENS[i].get("alcance", 10) for i in inv._itens_ativos()] + [10])

    def atirar(self, mira):
        j = self.jogador
        inv = j.inventario
        if not inv.tem("flecha"):
            self.avisar("Sem flechas! (crie na bancada)", 1.5)
            j.espera_ataque = 0.4
            return
        inv.remover("flecha", 1)
        cx, cy = j.centro
        if mira is None:
            mira = j.ponto_frente(20)
        j.olhar_para(*mira)
        j.espera_ataque = 0.55
        j.tempo_golpe = DURACAO_GOLPE
        self.flechas.append(Flecha(cx, cy - 1, mira[0] - cx, mira[1] - cy, ITENS["arco"]["disparo"]))
        self.gastar_ref(self._ref_arma() if inv.item_selecionado() == "arco" else None)

    def atacar(self, mira=None):
        j = self.jogador
        if j.espera_ataque > 0:
            return
        if not j.pode_usar_ferramentas():
            return
        if j.inventario.item_selecionado() == "arco":
            self.atirar(mira)
            return
        j.espera_ataque = TEMPO_ENTRE_ATAQUES
        j.tempo_golpe = DURACAO_GOLPE
        cx, cy = j.centro
        alcance = self.alcance_arma()
        if mira:
            j.olhar_para(*mira)
            dx, dy = mira[0] - cx, mira[1] - cy
            d = math.hypot(dx, dy) or 1.0
            fx, fy = cx + dx / d * alcance, cy + dy / d * alcance
        else:
            fx, fy = j.ponto_frente(alcance)
        dano = j.inventario.dano()
        j.exaustao += 0.1
        acertou = False
        for c in self.criaturas:
            sx, sy = c.centro
            perto = math.hypot(sx - fx, sy - fy) < 14 or (alcance > 10 and math.hypot(sx - cx, sy - cy) < alcance + 4
                                                          and math.hypot(sx - fx, sy - fy) < alcance)
            no_mouse = mira is not None and math.hypot(sx - mira[0], sy - mira[1]) < 9 and self.no_alcance(sx, sy)
            if perto or no_mouse:
                c.levar_golpe(dano, j.x, j.y)
                acertou = True
        if acertou:
            self.gastar_ref(self._ref_arma())

    def jogador_atacado(self, criatura):
        real = self.jogador.levar_dano(criatura.info.get("dano", 5))
        if real:
            self.avisar(f"{criatura.info['nome']} te atacou! (-{real})", 1.5)
            self.gastar_armadura()

    def criatura_morreu(self, c):
        self.derrotados += 1
        self.soltar_lascas(c.centro, "", 8)
        if getattr(c, "pavio", 0) > 0 and c.morta:
            return                       # explodiu: não solta nada
        if c.tipo == "slime" and self.nivel_escuridao() < 0.2:
            return                       # derreteu no sol: não solta nada
        self.soltar_itens(CRIATURAS[c.tipo].get("drops", []), *c.centro)
        info = CRIATURAS[c.tipo]
        self.soltar_xp(c.centro, info.get("xp", blocos.XP_CRIATURA_PADRAO.get(info.get("comportamento"), 0)))

    # ===========================================================
    # Cama, renascer, temperatura e mapa
    # ===========================================================
    def usar_cama(self, cama):
        if self.subterraneo():
            self.avisar("Não dá para dormir aqui embaixo!")
            return
        self.ponto_renascer = (cama.tx, cama.ty)
        if not self.e_noite():
            self.avisar("Ponto de renascer marcado. Só dá para dormir à noite.")
            return
        j = self.jogador
        perigo = any(c.comportamento != "passivo" and math.hypot(c.x - j.x, c.y - j.y) < 90 for c in self.criaturas)
        if perigo:
            self.avisar("Não dá para dormir com monstros por perto!")
            return
        self.sono = 2.0
        self.estado = "dormindo"

    def acordar(self):
        """Pula a noite: vai para as 6h da manhã."""
        hora = self.hora()
        if hora >= 6:
            self.dia += 1
        self.tempo = 6.0 / 24.0 * DURACAO_DIA
        j = self.jogador
        j.fome = max(0.0, j.fome - 15)
        j.sede = max(0.0, j.sede - 15)
        j.vida = min(VIDA_MAX, j.vida + 25)
        j.energia = 100.0
        # monstros noturnos vão embora
        self.criaturas = [c for c in self.criaturas if not CRIATURAS[c.tipo].get("noturno")]
        self.avisar(f"Bom dia! Dia {self.dia}", 3)

    def renascer(self):
        """Volta na cama (ou no início). Os itens ficam no chão onde você caiu."""
        j = self.jogador
        inv = j.inventario
        pilhas = [e for e in inv.espacos if e] + [e for e in inv.equipamento.values() if e]
        for e in pilhas:
            it = ItemChao(e[0], j.x + random.uniform(-6, 6), j.y + random.uniform(-4, 4), e[1])
            it.usos = e[2] if len(e) > 2 else None
            it.idade = 0.5
            self.mundo.itens.append(it)
        if j.xp:
            self.soltar_xp((j.x, j.y - 6), j.xp // 2)        # metade do XP fica no chão
        if self.camadas.z != 0:                              # [v0.5] morreu na caverna: volta para cima
            self.camadas.trocar(0, j.x, j.y, aviso=False)
        novo = Jogador(0, 0)
        if self.ponto_renascer and self.mundo.objeto(*self.ponto_renascer) is None:
            self.mundo.atualizar_chunks(self.ponto_renascer[0] * TILE, self.ponto_renascer[1] * TILE, limite=99)
        if self.ponto_renascer and getattr(self.mundo.objeto(*self.ponto_renascer), "tipo", "") == "cama":
            tx, ty = self.ponto_renascer
            novo.x, novo.y = tx * TILE + 8, (ty + 1) * TILE + 12
        else:
            self.ponto_renascer = None
            tx, ty = self.mundo.ponto_inicial()
            novo.x, novo.y = tx * TILE + 8, ty * TILE + 14
        novo.invencivel = 3.0
        self.jogador = novo
        self.mundo.atualizar_chunks(novo.x, novo.y, limite=99)
        self.criaturas = [c for c in self.criaturas if math.hypot(c.x - novo.x, c.y - novo.y) > 120
                          or c.comportamento == "passivo"]
        self.estado = "jogando"
        self.centralizar_camera()
        self.avisar("Você renasceu. Seus itens ficaram onde você caiu.", 4)

    def temperatura_atual(self):
        return self._temp

    def subterraneo(self):
        """Masmorra ou caverna (sem chuva, sem sol, sem dormir)."""
        e = getattr(self, "estruturas", None)
        c = getattr(self, "camadas", None)
        return bool(e and e.subterraneo) or bool(c and c.z < 0)

    def calcular_temperatura(self):
        j = self.jogador
        tx, ty = int(j.x // TILE), int(j.y // TILE)
        cx, cy = j.centro
        fogo = self.mundo.estacao_perto("fogueira", cx, cy, 56) is not None or \
            self.mundo.estacao_perto("forno", cx, cy, 40) is not None
        if self.subterraneo():                      # debaixo da terra é sempre fresco
            t = 12.0 + (16 if fogo else 0)
            if self.camadas.z <= -4:
                t += 8                               # perto da lava é quente
            self._temp = (t, estacoes.efeito_temperatura(t)[0])
            return t
        t = estacoes.temperatura(self.mundo.bioma(tx, ty), self.estacao, self.nivel_escuridao() / ESCURIDAO_MAXIMA,
                                 self.clima.chuva, fogo, j.na_agua)
        if j.inventario.equipamento["corpo"] and t < 10:
            t += 4                                   # roupa esquenta
        if j.inventario.equipamento["cabeca"] and t < 10:
            t += 2
        self._temp = (t, estacoes.efeito_temperatura(t)[0])
        return t

    def estruturas_descobertas(self):
        """Estruturas já vistas (o id é "tipo:rx,ry", então dá para achar a região direto)."""
        e = self.estruturas
        cache = getattr(self, "_cache_descobertas", None)
        if cache and cache[0] is e and cache[1] == len(e.descobertas):
            return cache[2]
        lista = []
        for ident in sorted(e.descobertas):
            try:
                rx, ry = (int(v) for v in ident.split(":", 1)[1].split(","))
            except (ValueError, IndexError):
                continue
            est = e.plano.regiao(rx, ry)
            if est is not None and est.id == ident:
                lista.append(est)
        self._cache_descobertas = (e, len(e.descobertas), lista)
        return lista

    def marcadores_mapa(self):
        """Pontos marcados no mapa e no minimapa."""
        j = self.jogador
        lista = [{"tx": j.x / TILE, "ty": j.y / TILE, "tipo": "jogador", "direcao": j.direcao}]
        if self.ponto_renascer:
            lista.append({"tx": self.ponto_renascer[0] + 0.5, "ty": self.ponto_renascer[1] + 0.5, "tipo": "cama"})
        for ch in self.mundo.chunks.values():
            for o in ch.objetos.values():
                if o.tipo == "bau":
                    lista.append({"tx": o.tx + 0.5, "ty": o.ty + 0.5, "tipo": "bau", "cor": (200, 150, 80)})
        e = getattr(self, "estruturas", None)
        if e is not None and not e.subterraneo and self.camadas.z == 0:
            for est in self.estruturas_descobertas():
                if True:
                    x0, y0, x1, y1 = est.caixa
                    lista.append({"tx": (x0 + x1) / 2 + 0.5, "ty": (y0 + y1) / 2 + 0.5, "tipo": est.tipo,
                                  "nome": NOMES_ESTRUTURAS.get(est.tipo, est.tipo),
                                  "cor": CORES_ESTRUTURAS.get(est.tipo, (250, 200, 80))})
        lista.extend(self.marcadores_extra)
        return lista

    # ===========================================================
    # Atualização
    # ===========================================================
    def atualizar(self, dt, teclas, mouse=None):
        if mouse is None:
            mouse = (pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))
        self.pos_mouse, self.botoes_mouse = mouse
        self.tempo_total += dt
        for m in self.mensagens:
            m[1] -= dt
        self.mensagens = [m for m in self.mensagens if m[1] > 0]
        for p in self.popups:
            p["tempo"] -= dt
        self.popups = [p for p in self.popups if p["tempo"] > 0]
        for pt in self.particulas:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[3] += 160 * dt
            pt[4] -= dt
        self.particulas = [pt for pt in self.particulas if pt[4] > 0]

        if self.estado in ("menu_inicial",) or (self.estado == "controles" and self.volta_controles == "menu_inicial"):
            # a câmera passeia devagar pelo mundo do fundo
            self.jogador.x += 14 * dt
            self.jogador.y += 6 * dt
            self.mundo.atualizar_chunks(self.jogador.x, self.jogador.y, limite=1)
            self.centralizar_camera()
            return
        if self.estado == "mapa":
            mx, my = self.controles.movimento(teclas)
            vel = 40 / self.zoom_mapa * (2 if self.controles.correndo(teclas) else 1)
            self.mapa_centro[0] += mx * vel * dt * 4
            self.mapa_centro[1] += my * vel * dt * 4
            return
        if self.estado == "dormindo":
            antes = self.sono
            self.sono -= dt
            if antes > 1.0 >= self.sono:
                self.acordar()
            if self.sono <= 0:
                self.sono = 0.0
                self.estado = "jogando"
            return
        if self.estado != "jogando":
            return

        self.tempo += dt
        if self.tempo >= DURACAO_DIA:
            self.tempo -= DURACAO_DIA
            self.dia += 1
            self.avisar(f"Começou o dia {self.dia}!", 4)
        self.atualizar_estacao()

        # clima e nível da água
        estado_antes = self.clima.estado
        self.clima.atualizar(dt)
        if self.clima.estado != estado_antes:
            self.avisar({"chuva": "Começou a chover!", "seca": "Uma seca começou... os lagos vão secar",
                         "normal": "O tempo melhorou"}[self.clima.estado], 4)
        self.mundo.definir_nivel_agua(self.clima.nivel)

        j = self.jogador
        mx, my = self.controles.movimento(teclas)
        mira = self.mouse_mundo() if self.mouse_no_mundo() and not self.pesca else None
        if self.controles.mira_gamepad():
            mira = self.mira_gamepad()
        nadava = j.nadando
        j.atualizar(dt, {"mx": mx, "my": my, "correr": self.controles.correndo(teclas), "mira": mira}, self.mundo)
        if j.nadando and not nadava:
            self.pesca = None
            if j.ar >= 99:
                self.avisar("Nadando! Cuidado com o ar (barra azul)", 2.5)
        self.acoes_mouse()
        self.atualizar_pesca(dt)
        self.flechas = [f for f in self.flechas if not self.atualizar_flecha(f, dt)]
        if not self.estruturas.subterraneo:
            self.minimapa.atualizar(dt, self)
        self.mundo.atualizar_chunks(j.x, j.y, limite=CHUNKS_POR_QUADRO)
        self.mundo.atualizar(dt)
        self.mundo.itens = [it for it in self.mundo.itens if not it.atualizar(dt, j, self.mundo)]
        self.pegar_itens()
        self.atualizar_status(dt)
        for c in self.criaturas:
            c.atualizar(dt, self)
        self.ecossistema.atualizar(dt)
        self.atualizar_chuva(dt)
        if self.camadas.z == 0:
            self.estruturas.atualizar(dt)                   # [ESTRUTURAS]
        self.camadas.atualizar(dt)                          # [v0.5]
        self.atualizar_orbes(dt)
        self.tremor_tela = max(0.0, self.tremor_tela - dt)
        self.centralizar_camera()
        if j.vida <= 0:
            self.estado = "morto"
            self.pesca = None

    def atualizar_estacao(self):
        nova = estacoes.estacao_do_dia(self.dia)
        if nova != self.estacao:
            self.estacao = nova
            mundos = {id(self.mundo): self.mundo}
            sup = getattr(getattr(self, "estruturas", None), "superficie", None)
            if sup is not None:
                mundos[id(sup)] = sup
            for m in mundos.values():
                for ch in m.chunks.values():
                    ch.sujo = True                  # redesenha o chão com as cores da estação
            self.avisar(f"Chegou o {estacoes.NOMES[nova].lower()}!" if nova != "primavera"
                        else "Chegou a primavera!", 4)
        self.clima.estacao = nova
        self.mundo.fator_crescimento = estacoes.CRESCIMENTO[nova]
        self.mult_caca_lobo = estacoes.FOME_LOBO[nova]

    def atualizar_flecha(self, f, dt):
        """Move a flecha; devolve True quando ela some."""
        if f.atualizar(dt, self.mundo):
            return True
        if getattr(f, "hostil", False):                     # [v0.5] flecha de esqueleto
            jx, jy = self.jogador.centro
            if math.hypot(jx - f.x, jy - f.y) < 7:
                if f.dono is not None:
                    self.jogador_atacado(f.dono)
                return True
            return False
        for c in self.criaturas:
            sx, sy = c.centro
            if math.hypot(sx - f.x, sy - f.y) < 7:
                c.levar_golpe(f.dano, f.x - f.vx * 0.05, f.y - f.vy * 0.05)
                return True
        return False

    def acoes_mouse(self):
        if not self.mouse_no_mundo() or self.pesca:
            return
        j = self.jogador
        if j.nadando or j.rolando > 0:
            return
        esquerdo, _, direito = self.botoes_mouse
        if esquerdo:
            mira = self.mouse_mundo()
            alvo_c = self.criatura_no_mouse()
            obj, alcanca = self.alvo_mouse()
            if alvo_c is not None:
                self.atacar(mira)
            elif obj is not None and alcanca:
                if j.espera_coleta <= 0:
                    j.espera_coleta = TEMPO_ENTRE_GOLPES
                    j.olhar_para(*obj.centro)
                    self.golpear(obj)
            elif self.pode_cavar_mouse():                   # [v0.5] cavar o chão
                if j.espera_coleta <= 0:
                    j.espera_coleta = TEMPO_ENTRE_GOLPES
                    tx, ty = self.bloco_mouse()
                    j.olhar_para(tx * TILE + 8, ty * TILE + 8)
                    j.tempo_golpe = DURACAO_GOLPE
                    inv = j.inventario
                    if self.camadas.cavar(tx, ty, inv.poder_ferramenta):
                        j.exaustao += 0.05
                        tipo = "pa" if inv.poder_ferramenta("pa") > 1 else "picareta"
                        self.gastar_ferramenta(tipo)
            else:
                self.atacar(mira)
        elif direito and j.espera_construir <= 0:
            item = j.inventario.item_selecionado()
            if item and ITENS[item]["tipo"] == "construcao":
                j.espera_construir = TEMPO_ENTRE_CONSTRUCOES
                self.tentar_colocar(*self.bloco_mouse())

    def pode_cavar_mouse(self):
        """[v0.5] Mouse num chão cavável, com pá/picareta, no alcance?"""
        if not self.mouse_no_mundo() or self.estado != "jogando":
            return False
        inv = self.jogador.inventario
        mao = inv.item_selecionado()
        if mao and ITENS[mao]["tipo"] == "arma":
            return False
        if inv.poder_ferramenta("pa") <= 1 and inv.poder_ferramenta("picareta") <= 1:
            return False
        tx, ty = self.bloco_mouse()
        if not self.no_alcance(tx * TILE + 8, ty * TILE + 8, folga=6):
            return False
        if self.mundo.objeto(tx, ty) is not None:
            return False
        return self.camadas.pode_cavar(tx, ty)[0]

    def atualizar_status(self, dt):
        """[v0.5] Fome estilo Minecraft: o cansaço (exaustão) gasta primeiro a saturação
        (escondida) e depois a barra de fome. Com fome alta você se cura; com fome zero, perde vida."""
        j = self.jogador
        _, mf, ms, dano_frio = estacoes.efeito_temperatura(self.calcular_temperatura())
        sede = SEDE_POR_SEGUNDO * (1.3 if self.clima.estado == "seca" else 1.0) * ms
        j.exaustao += EXAUSTAO_BASE * mf * dt
        if j.andando:
            j.exaustao += EXAUSTAO_ANDAR * dt
        if j.correndo:
            j.exaustao += EXAUSTAO_CORRER * dt
        if j.nadando:
            j.exaustao += EXAUSTAO_NADAR * dt
        while j.exaustao >= 4.0:
            j.exaustao -= 4.0
            if j.saturacao > 0:
                j.saturacao = max(0.0, j.saturacao - 5.0)
            else:
                j.fome = max(0.0, j.fome - 5.0)
        j.sede = max(0.0, j.sede - sede * dt)
        if dano_frio and not j.inventario.equipamento["corpo"]:
            j.vida = max(0.0, j.vida - dano_frio * dt)
        j.tempo_regen += dt
        if j.fome <= 0 or j.sede <= 0:
            if j.tempo_regen >= 2.0:
                j.tempo_regen = 0.0
                j.vida = max(0.0, j.vida - 5.0)
                self.avisar("Você está morrendo de " + ("fome!" if j.fome <= 0 else "sede!"), 1.5)
        elif j.fome >= 90 and j.sede > 30 and 0 < j.vida < VIDA_MAX:
            rapido = j.fome >= FOME_MAX and j.saturacao > 0
            if j.tempo_regen >= (1.0 if rapido else 3.0):
                j.tempo_regen = 0.0
                j.vida = min(VIDA_MAX, j.vida + 5.0)
                j.exaustao += 3.0
        elif j.tempo_regen > 4.0:
            j.tempo_regen = 0.0
        # [v0.5] lava queima
        if self.mundo.tipo_chao(int(j.x // TILE), int((j.y - 2) // TILE)) == LAVA:
            j.vida = max(0.0, j.vida - 14.0 * dt)
            if int(self.tempo_total * 4) % 2:
                self.soltar_lascas((j.x, j.y - 4), "explosao", 1)
            self.avisar("Você está na lava!", 0.6)

    def atualizar_chuva(self, dt):
        neve = self.estacao == "inverno"
        alvo = 0 if self.subterraneo() else int(110 * self.clima.chuva)
        while len(self.gotas) < alvo:
            self.gotas.append([random.uniform(0, LARGURA_INTERNA + 40), random.uniform(-20, ALTURA_INTERNA),
                               random.uniform(0, 6.3)])
        del self.gotas[alvo:]
        for g in self.gotas:
            if neve:      # flocos caem devagar e balançam
                g[2] += dt * 2
                g[0] += math.sin(g[2]) * 14 * dt - 8 * dt
                g[1] += 34 * dt
            else:
                g[0] -= 60 * dt
                g[1] += 230 * dt
            if g[1] > ALTURA_INTERNA or g[0] < -4:
                g[0] = random.uniform(0, LARGURA_INTERNA + 40)
                g[1] = random.uniform(-20, 0)

    def centralizar_camera(self):
        j = self.jogador
        self.camera_x = int(j.x - LARGURA_INTERNA / 2)
        self.camera_y = int(j.y - 6 - ALTURA_INTERNA / 2)
        if getattr(self, "tremor_tela", 0) > 0:
            self.camera_x += random.randint(-2, 2)
            self.camera_y += random.randint(-2, 2)

    # ===========================================================
    # Desenho
    # ===========================================================
    def desenhar_chunk(self, ch):
        """Desenha (uma vez) a imagem do chão de um chunk e guarda em cache."""
        if ch.superficie is None:
            ch.superficie = pygame.Surface((PX_CHUNK, PX_CHUNK))
        sup = ch.superficie
        self.sprites.texturas.extras = self.sprites.chao
        self.sprites.texturas.desenhar_chunk(sup, ch, self.mundo, self.estacao)
        x0, y0 = ch.cx * CH, ch.cy * CH
        for (tx, ty), p in ch.pisos.items():                # [ESTRUTURAS] pisos variados
            sup.blit(self.sprites.sprite_objeto(p), ((tx - x0) * TILE, (ty - y0) * TILE))
        ch.sujo = False

    def desenhar(self):
        cena = self.cena
        cx, cy = self.camera_x, self.camera_y
        cena.fill((0, 0, 0))

        # 1) chão: imagens prontas dos chunks visíveis
        redesenhos = 0
        for ccy in range(cy // PX_CHUNK, (cy + ALTURA_INTERNA) // PX_CHUNK + 1):
            for ccx in range(cx // PX_CHUNK, (cx + LARGURA_INTERNA) // PX_CHUNK + 1):
                ch = self.mundo.chunks.get((ccx, ccy))
                if ch is None:
                    ch = self.mundo.gerar(ccx, ccy)
                if ch.superficie is None or (ch.sujo and redesenhos < 6):
                    self.desenhar_chunk(ch)
                    redesenhos += 1
                cena.blit(ch.superficie, (ccx * PX_CHUNK - cx, ccy * PX_CHUNK - cy))
        self.sprites.texturas.desenhar_ondas(cena, self.mundo, cx, cy, LARGURA_INTERNA, ALTURA_INTERNA,
                                             self.tempo_total)
        # seca: chão amarelado
        s = self.clima.secura
        if s > 0.01:
            cena.fill((255, int(255 - 35 * s), int(255 - 120 * s)), special_flags=pygame.BLEND_RGB_MULT)

        # 2) objetos, itens e bichos ordenados pela altura na tela
        tx0, ty0 = cx // TILE - 1, cy // TILE - 1
        tx1, ty1 = (cx + LARGURA_INTERNA) // TILE + 1, (cy + ALTURA_INTERNA) // TILE + 2
        lista, visiveis = [], []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                obj = self.mundo.objeto(tx, ty)
                if obj:
                    lista.append((obj.ty * TILE if obj.tipo in PLANOS else obj.base_y, 0, obj))
                    visiveis.append(obj)
                p = self.mundo.piso(tx, ty)
                if p and p.vida < p.vida_max:
                    visiveis.append(p)
        for it in self.mundo.itens:
            if cx - 16 < it.x < cx + LARGURA_INTERNA + 16 and cy - 16 < it.y < cy + ALTURA_INTERNA + 16:
                lista.append((it.y - 3, 1, it))
        for c in self.criaturas:
            if cx - 16 < c.x < cx + LARGURA_INTERNA + 16 and cy - 16 < c.y < cy + ALTURA_INTERNA + 24:
                lista.append((c.y, 2, c))
        if self.estado not in ("menu_inicial", "controles") or self.volta_controles != "menu_inicial":
            if self.estado != "menu_inicial":
                lista.append((self.jogador.y, 3, self.jogador))
        for f in self.flechas:
            lista.append((f.y + 4, 4, f))
        cav = self.camadas.fracao_cavando()                 # [v0.5] rachaduras no chão
        if cav:
            est = min(3, 1 + int(cav[2] * 3))
            cena.blit(self.sprites.rachaduras_chao[est], (cav[0] * TILE - cx, cav[1] * TILE - cy))
        lista.sort(key=lambda e: (e[0], e[1]))
        for _, tipo, coisa in lista:
            if tipo == 0:
                self.desenhar_objeto(cena, coisa, cx, cy)
            elif tipo == 1:
                self.desenhar_item_chao(cena, coisa, cx, cy)
            elif tipo == 2:
                self.desenhar_criatura(cena, coisa, cx, cy)
            elif tipo == 3:
                self.desenhar_jogador(cena, cx, cy)
            else:
                self.desenhar_flecha(cena, coisa, cx, cy)
        for o in self.orbes:                                # [v0.5] XP
            r = 2 if int(self.tempo_total * 6 + o["x"]) % 2 else 1
            pygame.draw.circle(cena, (120, 230, 60), (int(o["x"] - cx), int(o["y"] - cy)), r + 1)
            pygame.draw.circle(cena, (230, 255, 140), (int(o["x"] - cx), int(o["y"] - cy)), r)
        for pt in self.particulas:
            cena.fill(pt[5], (int(pt[0] - cx), int(pt[1] - cy), 1, 1))
        if self.pesca:
            self.desenhar_pesca(cena, cx, cy)

        # 3) luz, chuva e mira
        self.desenhar_luz(cena, cx, cy)
        self.camadas.desenhar_espiar(cena, cx, cy)          # [v0.5] V: camada de cima
        if self.estacao == "inverno":
            for g in self.gotas:
                cena.fill((240, 244, 255), (int(g[0]), int(g[1]), 1 + (int(g[2] * 10) % 3 == 0), 1))
        else:
            for g in self.gotas:
                pygame.draw.line(cena, (170, 190, 235), (int(g[0]), int(g[1])), (int(g[0]) - 1, int(g[1]) + 3))
        if self.estado == "jogando":
            self.desenhar_mira(cena, cx, cy)

        # 4) amplia para a tela e desenha a interface
        pygame.transform.scale(cena, (LARGURA_TELA, ALTURA_TELA), self.tela)
        ui = self.interface
        if self.estado == "menu_inicial" or (self.estado == "controles" and self.volta_controles == "menu_inicial"):
            escuro = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            escuro.fill((10, 10, 20, 120))
            self.tela.blit(escuro, (0, 0))
            if self.estado == "controles":
                ui.desenhar_controles(self.tela, self, self.pos_mouse)
            else:
                ui.desenhar_menu_inicial(self.tela, self, self.pos_mouse)
            ui.desenhar_cursor(self.tela, self.pos_mouse)
            return
        for obj in visiveis:
            if obj.vida < obj.vida_max:
                sx = (obj.tx * TILE + 8 - cx) * ESCALA
                sy = (obj.retangulo_desenho().top - cy) * ESCALA - 16
                ui.desenhar_barra_quebra(self.tela, sx, sy, 1 - obj.vida / obj.vida_max)
        ui.desenhar_popups(self.tela, self.popups, cx, cy)
        ui.desenhar_hud(self.tela, self)
        if self.estado == "criando":
            ui.desenhar_criacao(self.tela, self, self.pos_mouse)
        elif self.estado == "inventario":
            ui.desenhar_inventario(self.tela, self, self.pos_mouse)
        elif self.estado == "bau":
            ui.desenhar_bau(self.tela, self, self.pos_mouse)
        elif self.estado == "bancada":
            ui.desenhar_bancada(self.tela, self, self.pos_mouse)
        elif self.estado == "forno":
            ui.desenhar_forno(self.tela, self, self.pos_mouse)
        elif self.estado == "ajuda":
            ui.desenhar_ajuda(self.tela, self)
        elif self.estado == "morto":
            ui.desenhar_morte(self.tela, self, self.pos_mouse)
        elif self.estado == "pausa":
            ui.desenhar_pausa(self.tela, self, self.pos_mouse)
        elif self.estado == "controles":
            ui.desenhar_controles(self.tela, self, self.pos_mouse)
        elif self.estado == "mapa":
            ui.desenhar_mapa(self.tela, self, self.pos_mouse)
        elif self.estado == "dormindo":
            ui.desenhar_sono(self.tela, 1 - abs(self.sono - 1.0))
        self.estruturas.desenhar_interface(self.tela)       # [ESTRUTURAS] trocas, chefe
        ui.desenhar_cursor(self.tela, self.pos_mouse, self.arrastando)

    def desenhar_objeto(self, cena, obj, cx, cy):
        sp = self.sprites
        px, py = obj.tx * TILE - cx, obj.ty * TILE - cy
        treme = int(math.sin(obj.tremor * 60) * 1.5) if obj.tremor > 0 else 0
        sombra = sp.sombras.get(obj.tipo)
        if sombra:
            cena.blit(sombra, (px + 8 - sombra.get_width() // 2, py + 15 - sombra.get_height() // 2))
        if obj.tipo == "fogueira" and obj.acesa:
            img = sp.fogueira[int(self.tempo_total * 8) % 3]
        elif obj.tipo == "tocha":
            img = sp.tocha[int(self.tempo_total * 7 + obj.tx) % 3]
        elif obj.tipo == "forno":
            img = sp.forno[int(self.tempo_total * 5) % 2] if obj.queima > 0 else sp.forno_apagado
        else:
            balanco = 0
            if obj.tipo in ANIMADOS and obj.tremor <= 0:
                vento = 1.6 if self.clima.chuva > 0.3 else 1.0
                v = math.sin(self.tempo_total * 1.7 * vento + obj.tx * 0.7 + obj.ty * 0.45)
                balanco = 1 if v > 0.55 else (-1 if v < -0.75 and vento > 1 else 0)
            base = sp.sprite_objeto(obj, self.estacao, balanco)
            img = sp.rachado((obj.tipo, obj.variante, obj.tem_frutas, obj.estagio, self.estacao, balanco),
                             base, obj.estagio_dano)
        sobe = img.get_height() - TILE
        cena.blit(img, (px + treme + (TILE - img.get_width()) // 2 if img.get_width() != TILE else px + treme,
                        py - sobe))

    def desenhar_flecha(self, cena, f, cx, cy):
        x, y = f.x - cx, f.y - cy
        ang = math.radians(f.angulo)
        dx, dy = math.cos(ang), -math.sin(ang)
        cena.fill((0, 0, 0), (int(x), int(y + 5), 2, 1))
        pygame.draw.line(cena, (150, 105, 60), (int(x - dx * 5), int(y - dy * 5)), (int(x), int(y)))
        cena.fill((200, 205, 215), (int(x + dx), int(y + dy), 1, 1))
        cena.fill((235, 235, 240), (int(x - dx * 5), int(y - dy * 5), 1, 1))

    def desenhar_item_chao(self, cena, it, cx, cy):
        img = self.sprites.itens_chao[it.item]
        w, h = img.get_size()
        x, y = int(it.x - cx), int(it.y - cy)
        balanco = 1 if it.z <= 0 and it.idade > 1.0 and math.sin(it.idade * 4 + it.x) > 0.3 else 0
        cena.blit(self.sprites.sombra_item, (x - 4, y - 1))
        cena.blit(img, (x - w // 2, y - h - int(it.z) - balanco))
        if it.quantidade > 1:
            cena.blit(img, (x - w // 2 + 2, y - h - int(it.z) - balanco - 2))

    def desenhar_criatura(self, cena, c, cx, cy):
        imgs = self.sprites.criaturas[c.tipo]
        img = imgs["branco"] if c.piscar > 0 else imgs[c.olhando][c.quadro()]
        if getattr(c, "pavio", 0) > 0 and c.piscar <= 0:
            img = pygame.transform.scale(img, (17, 17))    # Explosivo inchando
        if c.piscar > 0 and c.olhando == "esquerda":
            img = pygame.transform.flip(img, True, False)
        x, y = int(c.x - 8 - cx), int(c.y - 15 - cy)
        cena.blit(self.sprites.sombra, (x + 2, y + 13))
        cena.blit(img, (x, y))

    def desenhar_jogador(self, cena, cx, cy):
        j = self.jogador
        x, y = int(j.x - cx), int(j.y - cy)
        if not j.na_agua:
            cena.blit(self.sprites.sombra, (x - 6, y - 3))
        if j.invencivel > 0 and j.rolando <= 0 and int(j.invencivel * 12) % 2 == 0:
            return
        inv = j.inventario
        anim, quadro = j.animacao()
        img = self.sprites.jogador(j.direcao, anim, quadro, inv.equipamento["cabeca"] and inv.equipamento["cabeca"][0],
                                   inv.equipamento["corpo"] and inv.equipamento["corpo"][0],
                                   personagem.icone_na_mao(inv, None))
        if j.nadando:
            cena.blit(img, (x - 16, y - 28))
            fase = int(self.tempo_total * 4) % 2
            pygame.draw.ellipse(cena, (190, 225, 250), (x - 7 - fase, y - 5, 14 + fase * 2, 4), 1)
        elif j.na_agua:      # na água rasa, os pés ficam escondidos
            cena.blit(img, (x - 16, y - 27), (0, 0, 32, 25))
            pygame.draw.line(cena, (170, 210, 245), (x - 5, y - 2), (x + 4, y - 2))
        else:
            cena.blit(img, (x - 16, y - 28))

    def desenhar_pesca(self, cena, cx, cy):
        p = self.pesca
        jx, jy = self.jogador.centro
        bx, by = int(p["x"] - cx), int(p["y"] - cy)
        if p["mordendo"] > 0:
            by += 1 if int(self.tempo_total * 12) % 2 else 2       # boia afundando
        else:
            by += 1 if math.sin(self.tempo_total * 3) > 0 else 0
        pygame.draw.line(cena, (230, 230, 235), (int(jx - cx), int(jy - cy - 4)), (bx, by))
        cena.fill((230, 40, 40), (bx - 1, by - 1, 2, 1))
        cena.fill((250, 250, 250), (bx - 1, by, 2, 1))

    def desenhar_mira(self, cena, cx, cy):
        if not self.mouse_no_mundo() or self.pesca:
            return
        item = self.jogador.inventario.item_selecionado()
        if item and ITENS[item]["tipo"] == "construcao":
            tx, ty = self.bloco_mouse()
            ok, _ = self.pode_colocar(item, tx, ty)
            fantasma = self.sprites.fantasma(item, ok)
            px, py = tx * TILE - cx, ty * TILE - cy
            cena.blit(fantasma, (px, py - (fantasma.get_height() - TILE)))
            pygame.draw.rect(cena, (110, 240, 110) if ok else (240, 90, 90), (px, py, TILE, TILE), 1)
            return
        if self.tem_vara():
            tx, ty = self.bloco_mouse()
            if self.mundo.tipo_chao(tx, ty) in CHAO_AGUA:
                pygame.draw.rect(cena, (140, 200, 255), (tx * TILE - cx, ty * TILE - cy, TILE, TILE), 1)
                return
        obj, alcanca = self.alvo_mouse()
        if obj is None:
            return
        r = obj.retangulo_desenho().move(-cx, -cy).inflate(2, 2)
        cor = ((255, 236, 110) if int(self.tempo_total * 4) % 2 else (255, 255, 200)) if alcanca else (150, 150, 160)
        for (x, y, dx, dy) in ((r.left, r.top, 1, 1), (r.right - 1, r.top, -1, 1),
                               (r.left, r.bottom - 1, 1, -1), (r.right - 1, r.bottom - 1, -1, -1)):
            pygame.draw.line(cena, cor, (x, y), (x + dx * 3, y))
            pygame.draw.line(cena, cor, (x, y), (x, y + dy * 3))

    def desenhar_luz(self, cena, cx, cy):
        """Escuridão da noite/chuva: máscara multiplicada; fogueiras somam luz."""
        if self.camadas.z < 0 and self.estado != "menu_inicial":     # [v0.5] caverna: escuro total
            m = self.mascara_luz
            self.camadas.desenhar_luzes(m, cx, cy)
            jx, jy = int(self.jogador.x - cx), int(self.jogador.y - 6 - cy)
            if personagem.icone_na_mao(self.jogador.inventario, None) == "tocha":
                r = RAIO_LUZ_TOCHA_MAO + (1 if int(self.tempo_total * 7) % 2 else 0)
                m.blit(gradiente_luz(r), (jx - r, jy - r), special_flags=pygame.BLEND_RGB_ADD)
            for f, raio in self.mundo.lista_luzes():
                fx, fy = int(f.centro[0] - cx), int(f.centro[1] - cy)
                if -100 < fx < LARGURA_INTERNA + 100 and -100 < fy < ALTURA_INTERNA + 100:
                    raio = raio + (2 if int(self.tempo_total * 6 + f.tx) % 2 else 0)
                    cor = (255, 240, 200) if f.tipo == "lampada" else (255, 200, 140)
                    m.blit(gradiente_luz(raio, cor), (fx - raio, fy - raio), special_flags=pygame.BLEND_RGB_ADD)
            cena.blit(m, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            return
        n = self.nivel_escuridao()
        chuva = self.clima.chuva
        n = min(ESCURIDAO_MAXIMA, n + 0.28 * chuva * (1 - n))
        if n <= 0.01:
            return
        ambiente = (int(255 - n * 235), int(255 - n * 225), int(255 - n * (190 - 60 * chuva)))
        m = self.mascara_luz
        m.fill(ambiente)
        if self.estado != "menu_inicial":
            jx, jy = int(self.jogador.x - cx), int(self.jogador.y - 6 - cy)
            m.blit(gradiente_luz(30, (90, 90, 110)), (jx - 30, jy - 30), special_flags=pygame.BLEND_RGB_ADD)
            if personagem.icone_na_mao(self.jogador.inventario, None) == "tocha":
                r = RAIO_LUZ_TOCHA_MAO + (1 if int(self.tempo_total * 7) % 2 else 0)
                m.blit(gradiente_luz(r), (jx - r, jy - r), special_flags=pygame.BLEND_RGB_ADD)
        for f, raio in self.mundo.lista_luzes():
            fx, fy = int(f.centro[0] - cx), int(f.centro[1] - cy)
            if -100 < fx < LARGURA_INTERNA + 100 and -100 < fy < ALTURA_INTERNA + 100:
                raio = raio + (2 if int(self.tempo_total * 6 + f.tx) % 2 else 0)
                m.blit(gradiente_luz(raio), (fx - raio, fy - raio), special_flags=pygame.BLEND_RGB_ADD)
        self.estruturas.desenhar_luzes(m, cx, cy)           # [ESTRUTURAS] tochas / masmorra
        cena.blit(m, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


# ===============================================================
# Loop principal
# ===============================================================
DEPURAR_WEB = False
SALVAR_AUTOMATICO = 30.0    # versão web: salva sozinho (o navegador pode fechar a qualquer hora)


def salvar_quieto(jogo):
    try:
        salvar_jogo(jogo)
        jogo.tem_save = True
    except Exception as erro:          # noqa: BLE001
        print("salvar automático falhou:", erro)


async def main():
    pygame.init()
    pygame.display.set_caption(TITULO)
    try:
        from icone import imagem16
        pygame.display.set_icon(pygame.transform.scale(imagem16(), (32, 32)))
    except Exception:
        pass
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.mouse.set_visible(False)
    if WEB:                            # mostra algo enquanto o mundo é gerado
        tela.fill((24, 22, 34))
        f = pygame.font.Font(None, 48)
        img = f.render("Carregando o mundo...", True, (245, 240, 225))
        tela.blit(img, img.get_rect(center=(LARGURA_TELA // 2, ALTURA_TELA // 2)))
        pygame.display.flip()
        await asyncio.sleep(0)
    relogio = pygame.time.Clock()
    jogo = Jogo(tela)
    from toque import Toque
    toque = Toque(jogo)
    jogo.toque = toque
    proximo_save = SALVAR_AUTOMATICO
    estado_antes = jogo.estado
    quadros, relogio_fps = 0, 0.0
    estado_dbg = jogo.estado
    while jogo.rodando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                jogo.rodando = False
            elif not toque.tratar(ev):
                if DEPURAR_WEB:
                    print("[ev]", pygame.event.event_name(ev.type), ev.dict)
                jogo.tratar_evento(ev)
            if DEPURAR_WEB and jogo.estado != estado_dbg:
                print("[estado]", estado_dbg, "->", jogo.estado, pygame.event.event_name(ev.type), ev.dict)
                estado_dbg = jogo.estado
        jogo.atualizar(dt, pygame.key.get_pressed(), toque.entrada())
        jogo.desenhar()
        toque.desenhar(tela)
        pygame.display.flip()
        if WEB:
            quadros += 1
            relogio_fps += dt
            if relogio_fps >= 10.0:                  # aparece no console do navegador (diagnóstico)
                print(f"[fps] {quadros / relogio_fps:.1f} estado={jogo.estado} chunks={len(jogo.mundo.chunks)}")
                quadros, relogio_fps = 0, 0.0
            if jogo.estado == "jogando":
                proximo_save -= dt
            if proximo_save <= 0 or (jogo.estado == "pausa" and estado_antes != "pausa"):
                proximo_save = SALVAR_AUTOMATICO
                if jogo.estado != "menu_inicial":
                    salvar_quieto(jogo)
            estado_antes = jogo.estado
        await asyncio.sleep(0)
    pygame.quit()
    if not WEB:
        sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
