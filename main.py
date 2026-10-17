# -*- coding: utf-8 -*-
"""
main.py - Arquivo principal. Rode com:  python main.py

A classe Jogo junta tudo: tela inicial (semente), mundo infinito em chunks,
clima, ecossistema, jogador, inventário, criação, construção, pesca,
desenho (com cache das imagens dos chunks) e o loop principal.
"""
import math
import random
import sys

import pygame

from config import *          # noqa: F401,F403  (constantes)
from dados import ITENS, OBJETOS, RECEITAS, CATEGORIAS, CRIATURAS, NOMES_OBJETOS
from sprites import Sprites, gradiente_luz
from mundo import Mundo, Objeto
from clima import Clima
from entidades import Jogador, ItemChao
from ecossistema import Ecossistema
from interface import Interface
from ruido import semente_de_texto
from salvar import salvar_jogo, carregar_jogo, existe_save

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
}
COMIDA_CRUA = {"carne_crua": "carne_assada", "peixe": "peixe_assado"}


class Jogo:
    def __init__(self, tela):
        self.tela = tela
        self.cena = pygame.Surface((LARGURA_INTERNA, ALTURA_INTERNA))
        self.mascara_luz = pygame.Surface((LARGURA_INTERNA, ALTURA_INTERNA))
        self.sprites = Sprites()
        self.interface = Interface(self.sprites)
        self.pos_mouse = (LARGURA_TELA // 2, ALTURA_TELA // 2)
        self.botoes_mouse = (False, False, False)
        self.tempo_total = 0.0
        self.mensagens = []
        self.texto_semente = ""
        self.arrastando = None          # pilha [item, qtd] presa no mouse (inventário)
        self.origem_arrasto = None
        self.categoria = CATEGORIAS[0]
        self.selecao_criacao = None
        self.estado_anterior = "jogando"
        self.tem_save = existe_save()
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
        self.clima = Clima(semente)
        self.popups = []
        self.particulas = []
        self.gotas = []
        self.pesca = None
        self.derrotados = 0
        self.mensagens = []

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
        self.mundo.atualizar_chunks(self.jogador.x, self.jogador.y, limite=99)
        self.estado = "jogando"
        self.centralizar_camera()
        self.avisar("Jogo carregado!")

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
        if ev.type == pygame.MOUSEMOTION:
            self.pos_mouse = ev.pos
            return
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.pos_mouse = ev.pos
            self.clique(ev.button, ev.pos)
            return
        if ev.type == pygame.MOUSEBUTTONUP:
            self.pos_mouse = ev.pos
            if self.estado == "inventario":
                self.soltar_arrasto(ev.pos)
            return
        if ev.type == pygame.MOUSEWHEEL and self.estado == "jogando":
            inv = self.jogador.inventario
            inv.selecionado = (inv.selecionado - ev.y) % TAMANHO_BARRA
            return
        if ev.type != pygame.KEYDOWN:
            return

        tecla = ev.key
        if self.estado == "menu_inicial":
            self.tecla_menu(ev)
            return
        if tecla == pygame.K_F5 and self.estado in ("jogando", "inventario", "criando"):
            self.salvar()
            return
        if tecla == pygame.K_F9:
            self.carregar()
            return
        if self.estado == "ajuda":
            self.estado = self.estado_anterior
        elif self.estado == "morto":
            if tecla == pygame.K_r:
                self.novo_jogo(self.mundo.semente)
        elif self.estado == "criando":
            if tecla in (pygame.K_c, pygame.K_ESCAPE):
                self.estado = "jogando"
        elif self.estado == "inventario":
            if tecla in (pygame.K_i, pygame.K_TAB, pygame.K_ESCAPE):
                self.fechar_inventario()
        elif self.estado == "jogando":
            self.tecla_jogando(tecla)

    def tecla_menu(self, ev):
        if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.iniciar_pelo_menu()
        elif ev.key == pygame.K_BACKSPACE:
            self.texto_semente = self.texto_semente[:-1]
        elif ev.key == pygame.K_F9:
            self.carregar()
        elif ev.unicode and ev.unicode.isprintable() and len(self.texto_semente) < 24:
            self.texto_semente += ev.unicode

    def tecla_jogando(self, tecla):
        inv = self.jogador.inventario
        if tecla == pygame.K_e:
            self.interagir()
        elif tecla == pygame.K_f:
            self.comer()
        elif tecla == pygame.K_SPACE:
            self.atacar()
        elif tecla == pygame.K_c:
            self.estado = "criando"
        elif tecla in (pygame.K_i, pygame.K_TAB):
            self.estado = "inventario"
        elif tecla == pygame.K_h:
            self.estado_anterior = "jogando"
            self.estado = "ajuda"
        elif pygame.K_1 <= tecla <= pygame.K_9:
            inv.selecionado = tecla - pygame.K_1

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
        elif self.estado == "ajuda":
            self.estado = self.estado_anterior
        elif self.estado == "morto":
            if botoes.get("mesma") and botoes["mesma"].collidepoint(pos):
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
        elif self.estado == "inventario":
            self.pegar_arrasto(botao, pos)
        elif self.estado == "jogando":
            espaco = self.interface.espaco_barra_no_ponto(pos)
            if espaco is not None:
                self.jogador.inventario.selecionado = espaco
            elif self.pesca:
                self.fisgar()
            elif botao == 3:
                self.clique_direito()

    # ===========================================================
    # Inventário: arrastar e soltar
    # ===========================================================
    def pegar_arrasto(self, botao, pos):
        inv = self.jogador.inventario
        ref = self.interface.no_ponto(self.interface.slots_inventario, pos)
        if ref is None or self.arrastando:
            return
        pilha = inv.pegar(ref)
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
                return
        self.arrastando = pilha
        self.origem_arrasto = ref
        inv.por(ref, None)

    def soltar_arrasto(self, pos):
        if not self.arrastando:
            return
        inv = self.jogador.inventario
        mao = self.arrastando
        ref = self.interface.no_ponto(self.interface.slots_inventario, pos)
        if ref is None:
            if not self.interface.ret_painel.collidepoint(pos):
                self.jogar_no_chao(mao)           # soltou fora: joga no chão
                self.arrastando = None
            else:
                self.devolver_arrasto()
            return
        if not inv.cabe_no(ref, mao):
            self.avisar("Esse item não vai nesse espaço")
            self.devolver_arrasto()
            return
        alvo = inv.pegar(ref)
        if alvo is None:
            inv.por(ref, mao)
        elif alvo[0] == mao[0] and ITENS[mao[0]]["pilha"] > 1:
            cabe = min(ITENS[mao[0]]["pilha"] - alvo[1], mao[1])
            alvo[1] += cabe
            mao[1] -= cabe
            if mao[1] > 0:
                self.devolver_arrasto()
                return
        else:
            # troca de lugar (se o que estava lá couber na origem)
            if inv.pegar(self.origem_arrasto) is None and inv.cabe_no(self.origem_arrasto, alvo):
                inv.por(ref, mao)
                inv.por(self.origem_arrasto, alvo)
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
        o = inv.pegar(self.origem_arrasto)
        if o is None:
            inv.por(self.origem_arrasto, mao)
        elif o[0] == mao[0]:
            o[1] += mao[1]
        else:
            sobra = inv.adicionar(mao[0], mao[1])
            if sobra:
                self.jogar_no_chao([mao[0], sobra])

    def fechar_inventario(self):
        self.devolver_arrasto()
        self.estado = "jogando"

    def jogar_no_chao(self, pilha):
        j = self.jogador
        fx, fy = j.ponto_frente(14)
        it = ItemChao(pilha[0], fx, fy + 4, pilha[1])
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
        if est and not self.estacao_perto(est):
            return False, f"Precisa de {('uma bancada' if est == 'bancada' else 'uma fogueira acesa')} por perto"
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
        return True

    # ===========================================================
    # Quebrar, drops e coleta
    # ===========================================================
    def golpear(self, obj):
        j = self.jogador
        info = OBJETOS[obj.tipo]
        ferramenta = info.get("ferramenta")
        poder = j.inventario.poder_ferramenta(ferramenta) if ferramenta else 1
        obj.tremor = 0.2
        j.tempo_golpe = 0.15
        if poder < info.get("poder_min", 0):
            self.avisar("Precisa de uma picareta de pedra (ou melhor)", 1.5)
            return
        obj.vida -= poder
        obj.tempo_sem_golpe = 0.0
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
            self.mundo.remover(obj)
        self.soltar_lascas(obj.centro, obj.tipo, 10)
        self.soltar_itens(drops, *obj.centro)

    def soltar_itens(self, drops, x, y):
        for item, qtd in drops:
            for _ in range(qtd):
                self.mundo.itens.append(ItemChao(item, x + random.uniform(-3, 3), y + random.uniform(-2, 4)))

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
                sobra = j.inventario.adicionar(it.item, it.quantidade)
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
        if m.tipo_chao(tx, ty) in CHAO_AGUA:
            return False, "Não dá para construir na água"
        if not self.no_alcance(tx * TILE + 8, ty * TILE + 8, folga=6):
            return False, "Longe demais"
        obj = m.objeto(tx, ty)
        if item == "piso":
            if m.piso(tx, ty):
                return False, "Já tem piso aqui"
            if obj and not obj.construcao:
                return False, "Tem algo no caminho"
            return True, ""
        if obj:
            return False, "Tem algo no caminho"
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
        inv.remover(item, 1)
        novo = Objeto(item, tx, ty)
        self.mundo.colocar(novo)
        self.soltar_lascas(novo.centro, item, 5)
        self.jogador.olhar_para(*novo.centro)
        if item == "fogueira":
            self.avisar("Fogueira acesa!")
        return True

    def clique_direito(self):
        """Botão direito: construir, consumir, pescar ou usar a fogueira."""
        inv = self.jogador.inventario
        item = inv.item_selecionado()
        tx, ty = self.bloco_mouse()
        tipo = ITENS[item]["tipo"] if item else None
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
        if j.espera_coleta > 0:
            return
        j.espera_coleta = TEMPO_ENTRE_GOLPES
        cx, cy = j.centro
        inv = j.inventario
        fogueira = self.mundo.objeto_mais_proximo(cx, cy, 36, tipos=("fogueira",))
        if fogueira and fogueira.acesa and any(inv.tem(c) for c in COMIDA_CRUA):
            self.usar_fogueira(fogueira)
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
            return f"[Segure o clique] Quebrar {nome.lower()}"
        j = self.jogador
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
        return ""

    # ===========================================================
    # Combate
    # ===========================================================
    def atacar(self, mira=None):
        j = self.jogador
        if j.espera_ataque > 0:
            return
        j.espera_ataque = TEMPO_ENTRE_ATAQUES
        j.tempo_golpe = 0.15
        cx, cy = j.centro
        if mira:
            j.olhar_para(*mira)
            dx, dy = mira[0] - cx, mira[1] - cy
            d = math.hypot(dx, dy) or 1.0
            fx, fy = cx + dx / d * 10, cy + dy / d * 10
        else:
            fx, fy = j.ponto_frente(10)
        dano = j.inventario.dano()
        for c in self.criaturas:
            sx, sy = c.centro
            perto = math.hypot(sx - fx, sy - fy) < 14
            no_mouse = mira is not None and math.hypot(sx - mira[0], sy - mira[1]) < 9 and self.no_alcance(sx, sy)
            if perto or no_mouse:
                c.levar_golpe(dano, j.x, j.y)

    def jogador_atacado(self, criatura):
        real = self.jogador.levar_dano(criatura.info.get("dano", 5))
        if real:
            self.avisar(f"{criatura.info['nome']} te atacou! (-{real})", 1.5)

    def criatura_morreu(self, c):
        self.derrotados += 1
        self.soltar_lascas(c.centro, "", 8)
        if c.tipo == "slime" and self.nivel_escuridao() < 0.2:
            return                       # derreteu no sol: não solta nada
        self.soltar_itens(CRIATURAS[c.tipo].get("drops", []), *c.centro)

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

        if self.estado == "menu_inicial":
            # a câmera passeia devagar pelo mundo do fundo
            self.jogador.x += 14 * dt
            self.jogador.y += 6 * dt
            self.mundo.atualizar_chunks(self.jogador.x, self.jogador.y, limite=1)
            self.centralizar_camera()
            return
        if self.estado != "jogando":
            return

        self.tempo += dt
        if self.tempo >= DURACAO_DIA:
            self.tempo -= DURACAO_DIA
            self.dia += 1
            self.avisar(f"Começou o dia {self.dia}!", 4)

        # clima e nível da água
        estado_antes = self.clima.estado
        self.clima.atualizar(dt)
        if self.clima.estado != estado_antes:
            self.avisar({"chuva": "Começou a chover!", "seca": "Uma seca começou... os lagos vão secar",
                         "normal": "O tempo melhorou"}[self.clima.estado], 4)
        self.mundo.definir_nivel_agua(self.clima.nivel)

        j = self.jogador
        j.atualizar(dt, teclas, self.mundo)
        self.acoes_mouse()
        self.atualizar_pesca(dt)
        self.mundo.atualizar_chunks(j.x, j.y, limite=CHUNKS_POR_QUADRO)
        self.mundo.atualizar(dt)
        self.mundo.itens = [it for it in self.mundo.itens if not it.atualizar(dt, j, self.mundo)]
        self.pegar_itens()
        self.atualizar_status(dt)
        for c in self.criaturas:
            c.atualizar(dt, self)
        self.ecossistema.atualizar(dt)
        self.atualizar_chuva(dt)
        self.centralizar_camera()
        if j.vida <= 0:
            self.estado = "morto"
            self.pesca = None

    def acoes_mouse(self):
        if not self.mouse_no_mundo() or self.pesca:
            return
        j = self.jogador
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
            else:
                self.atacar(mira)
        elif direito and j.espera_construir <= 0:
            item = j.inventario.item_selecionado()
            if item and ITENS[item]["tipo"] == "construcao":
                j.espera_construir = TEMPO_ENTRE_CONSTRUCOES
                self.tentar_colocar(*self.bloco_mouse())

    def atualizar_status(self, dt):
        j = self.jogador
        sede = SEDE_POR_SEGUNDO * (1.3 if self.clima.estado == "seca" else 1.0)
        j.fome = max(0.0, j.fome - FOME_POR_SEGUNDO * dt)
        j.sede = max(0.0, j.sede - sede * dt)
        if j.fome <= 0 or j.sede <= 0:
            j.vida = max(0.0, j.vida - DANO_FOME_SEDE * dt)
        elif j.fome > 60 and j.sede > 60 and j.vida > 0:
            j.vida = min(VIDA_MAX, j.vida + REGENERACAO_VIDA * dt)

    def atualizar_chuva(self, dt):
        alvo = int(110 * self.clima.chuva)
        while len(self.gotas) < alvo:
            self.gotas.append([random.uniform(0, LARGURA_INTERNA + 40), random.uniform(-20, ALTURA_INTERNA)])
        del self.gotas[alvo:]
        for g in self.gotas:
            g[0] -= 60 * dt
            g[1] += 230 * dt
            if g[1] > ALTURA_INTERNA or g[0] < -4:
                g[0] = random.uniform(0, LARGURA_INTERNA + 40)
                g[1] = random.uniform(-20, 0)

    def centralizar_camera(self):
        j = self.jogador
        self.camera_x = int(j.x - LARGURA_INTERNA / 2)
        self.camera_y = int(j.y - 6 - ALTURA_INTERNA / 2)

    # ===========================================================
    # Desenho
    # ===========================================================
    def desenhar_chunk(self, ch):
        """Desenha (uma vez) a imagem do chão de um chunk e guarda em cache."""
        if ch.superficie is None:
            ch.superficie = pygame.Surface((PX_CHUNK, PX_CHUNK))
        sup = ch.superficie
        sp = self.sprites.chao
        m = self.mundo
        x0, y0 = ch.cx * CH, ch.cy * CH
        espuma = (176, 214, 246)
        for j in range(CH):
            for i in range(CH):
                k = j * CH + i
                tipo = ch.chao[k]
                tx, ty = x0 + i, y0 + j
                var = (tx * 7 + ty * 13 + (tx * ty) % 5) % 4
                px, py = i * TILE, j * TILE
                sup.blit(sp[tipo][var], (px, py))
                if tipo in CHAO_AGUA:
                    # espuma na beira (olha os vizinhos, mesmo de outros chunks)
                    def vizinho(di, dj):
                        ii, jj = i + di, j + dj
                        if 0 <= ii < CH and 0 <= jj < CH:
                            return ch.chao[jj * CH + ii]
                        return m.tipo_chao(tx + di, ty + dj)
                    if vizinho(0, -1) not in CHAO_AGUA:
                        pygame.draw.line(sup, espuma, (px, py), (px + 15, py))
                    if vizinho(0, 1) not in CHAO_AGUA:
                        pygame.draw.line(sup, espuma, (px, py + 15), (px + 15, py + 15))
                    if vizinho(-1, 0) not in CHAO_AGUA:
                        pygame.draw.line(sup, espuma, (px, py), (px, py + 15))
                    if vizinho(1, 0) not in CHAO_AGUA:
                        pygame.draw.line(sup, espuma, (px + 15, py), (px + 15, py + 15))
        for (tx, ty) in ch.pisos:
            sup.blit(self.sprites.piso, ((tx - x0) * TILE, (ty - y0) * TILE))
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
                if ch.superficie is None or (ch.sujo and redesenhos < 3):
                    self.desenhar_chunk(ch)
                    redesenhos += 1
                cena.blit(ch.superficie, (ccx * PX_CHUNK - cx, ccy * PX_CHUNK - cy))
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
                    lista.append((obj.base_y, 0, obj))
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
        if self.estado != "menu_inicial":
            lista.append((self.jogador.y, 3, self.jogador))
        lista.sort(key=lambda e: (e[0], e[1]))
        for _, tipo, coisa in lista:
            if tipo == 0:
                self.desenhar_objeto(cena, coisa, cx, cy)
            elif tipo == 1:
                self.desenhar_item_chao(cena, coisa, cx, cy)
            elif tipo == 2:
                self.desenhar_criatura(cena, coisa, cx, cy)
            else:
                self.desenhar_jogador(cena, cx, cy)
        for pt in self.particulas:
            cena.fill(pt[5], (int(pt[0] - cx), int(pt[1] - cy), 1, 1))
        if self.pesca:
            self.desenhar_pesca(cena, cx, cy)

        # 3) luz, chuva e mira
        self.desenhar_luz(cena, cx, cy)
        for g in self.gotas:
            pygame.draw.line(cena, (170, 190, 235), (int(g[0]), int(g[1])), (int(g[0]) - 1, int(g[1]) + 3))
        if self.estado == "jogando":
            self.desenhar_mira(cena, cx, cy)

        # 4) amplia para a tela e desenha a interface
        pygame.transform.scale(cena, (LARGURA_TELA, ALTURA_TELA), self.tela)
        ui = self.interface
        if self.estado == "menu_inicial":
            escuro = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            escuro.fill((10, 10, 20, 120))
            self.tela.blit(escuro, (0, 0))
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
        elif self.estado == "ajuda":
            ui.desenhar_ajuda(self.tela)
        elif self.estado == "morto":
            ui.desenhar_morte(self.tela, self, self.pos_mouse)
        ui.desenhar_cursor(self.tela, self.pos_mouse, self.arrastando)

    def desenhar_objeto(self, cena, obj, cx, cy):
        sp = self.sprites
        px, py = obj.tx * TILE - cx, obj.ty * TILE - cy
        treme = int(math.sin(obj.tremor * 60) * 1.5) if obj.tremor > 0 else 0
        if obj.tipo == "fogueira" and obj.acesa:
            img = sp.fogueira[int(self.tempo_total * 8) % 3]
        else:
            base = sp.sprite_objeto(obj)
            img = sp.rachado((obj.tipo, obj.variante, obj.tem_frutas), base, obj.estagio_dano)
        sobe = img.get_height() - TILE
        if obj.tipo in ("arvore", "arvore_pantano", "pinheiro", "cacto"):
            cena.blit(sp.sombra, (px + 2, py + 13))
        cena.blit(img, (px + treme, py - sobe))

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
        if c.piscar > 0 and c.olhando == "esquerda":
            img = pygame.transform.flip(img, True, False)
        x, y = int(c.x - 8 - cx), int(c.y - 15 - cy)
        cena.blit(self.sprites.sombra, (x + 2, y + 13))
        cena.blit(img, (x, y))

    def desenhar_jogador(self, cena, cx, cy):
        j = self.jogador
        x, y = int(j.x - 8 - cx), int(j.y - 15 - cy)
        if not j.na_agua:
            cena.blit(self.sprites.sombra, (x + 2, y + 12))
        if j.invencivel > 0 and int(j.invencivel * 12) % 2 == 0:
            return
        img = self.sprites.jogador[j.direcao][j.quadro_atual()]
        if j.na_agua:      # na água rasa, os pés ficam escondidos
            cena.blit(img, (x, y + 1), (0, 0, 16, 12))
            pygame.draw.line(cena, (170, 210, 245), (x + 3, y + 13), (x + 12, y + 13))
        else:
            cena.blit(img, (x, y))
        if j.tempo_golpe > 0:
            fx, fy = j.ponto_frente(10)
            ret = pygame.Rect(int(fx - cx) - 6, int(fy - cy) - 6, 12, 12)
            ang = {"direita": 0, "cima": math.pi / 2, "esquerda": math.pi, "baixo": -math.pi / 2}[j.direcao]
            pygame.draw.arc(cena, (255, 255, 240), ret, ang - 1.0, ang + 1.0, 1)

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
        for f in self.mundo.lista_fogueiras():
            fx, fy = int(f.centro[0] - cx), int(f.centro[1] - cy)
            if -100 < fx < LARGURA_INTERNA + 100 and -100 < fy < ALTURA_INTERNA + 100:
                raio = RAIO_LUZ_FOGUEIRA + (2 if int(self.tempo_total * 6) % 2 else 0)
                m.blit(gradiente_luz(raio), (fx - raio, fy - raio), special_flags=pygame.BLEND_RGB_ADD)
        cena.blit(m, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


# ===============================================================
# Loop principal
# ===============================================================
def main():
    pygame.init()
    pygame.display.set_caption(TITULO)
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.mouse.set_visible(False)
    relogio = pygame.time.Clock()
    jogo = Jogo(tela)
    rodando = True
    while rodando:
        dt = min(relogio.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            else:
                jogo.tratar_evento(ev)
        jogo.atualizar(dt, pygame.key.get_pressed())
        jogo.desenhar()
        pygame.display.flip()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
