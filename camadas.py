# -*- coding: utf-8 -*-
"""
camadas.py - Camadas verticais (níveis Z), como andar para baixo no Minecraft.

  z =  0  superfície (o mundo de sempre)
  z = -1 .. -4  cavernas (cada vez mais fundo: ouro, cristal, diamante e lava)

Como mudar de camada:
- Cave o CHÃO com uma pá (terra/areia) ou picareta (pedra): vira um BURACO.
  Em cima do buraco, E desce. Lá embaixo aparece uma ESCADA de mão.
- Em cima da escada, E sobe.
- Escada de mão (item) colocada numa caverna abre um buraco na camada de cima.

Cada camada é um Mundo próprio (chunks, cache das imagens, save), com suas
criaturas, ecossistema e minimapa. As camadas são criadas só quando você
vai até elas.
"""
import math
import random
import pygame

from config import (TILE, TAMANHO_CHUNK, LARGURA_INTERNA, ALTURA_INTERNA, ESCURIDAO_MAXIMA,
                    AGUA_FUNDA, AGUA_RASA, LAMA, AREIA, GRAMA, GRAMA_FLORESTA, GRAMA_PANTANO, NEVE,
                    ROCHA, CAVERNA, LAVA, CHAO_AGUA, TEMPO_ENTRE_GOLPES)
from dados import ITENS, OBJETOS
from mundo import Objeto
from minimapa import Minimapa
from cavernas import MundoCaverna, EcossistemaCaverna, CAMADA_MAIS_FUNDA
from entidades import ItemChao
from sprites import gradiente_luz

CH = TAMANHO_CHUNK

# chão -> (item que sai, dureza, ferramenta certa, poder mínimo)
CHAO_CAVAVEL = {
    GRAMA: ("terra", 3, "pa", 0), GRAMA_FLORESTA: ("terra", 3, "pa", 0), GRAMA_PANTANO: ("terra", 3, "pa", 0),
    NEVE: ("terra", 3, "pa", 0), LAMA: ("terra", 3, "pa", 0), AREIA: ("areia", 3, "pa", 0),
    ROCHA: ("pedra", 8, "picareta", 2), CAVERNA: ("pedra", 8, "picareta", 2),
}
NOMES_CAMADAS = {0: "Superfície", -1: "Cavernas rasas", -2: "Cavernas", -3: "Cavernas fundas",
                 -4: "Abismo (lava)"}


def nome_camada(z):
    return NOMES_CAMADAS.get(z, f"Camada {z}")


class SistemaCamadas:
    def __init__(self, jogo):
        self.jogo = jogo
        self.z = 0
        self.mundos = {0: jogo.mundo}
        self.ecos = {0: jogo.ecossistema}
        self.criaturas = {}
        self.minimapas = {0: jogo.minimapa}
        self.pendentes = {}          # z -> chunks salvos ainda não abertos
        self.explorados = {}         # z -> explorados salvos ainda não abertos
        self.cavando = None          # {"x", "y", "dano", "dureza", "tempo"}
        self.espera = 0.0
        self.espiar = False          # V: mostra a camada de cima por cima (transparente)

    # ===========================================================
    @property
    def superficie(self):
        return self.mundos[0]

    @property
    def subterraneo(self):
        return self.z < 0

    def mundo(self, z):
        m = self.mundos.get(z)
        if m is None:
            m = MundoCaverna(self.superficie, z)
            m.salvos = dict(self.pendentes.pop(z, {}))
            eco = EcossistemaCaverna(self.jogo, z)
            m.ao_carregar = eco.ao_carregar_chunk
            self.mundos[z] = m
            self.ecos[z] = eco
            mm = Minimapa()
            mm.explorados = {tuple(int(v) for v in c.split(",")) for c in self.explorados.pop(z, [])}
            self.minimapas[z] = mm
        return m

    def _garantir_chunk(self, m, tx, ty):
        if m.chunk(tx, ty) is None:
            ao = m.ao_carregar
            if m is not self.jogo.mundo:
                m.ao_carregar = None         # sem bichos nascendo numa camada onde você não está
            m.gerar(tx // CH, ty // CH)
            m.ao_carregar = ao
        return m.chunk(tx, ty)

    # ===========================================================
    # Trocar de camada
    # ===========================================================
    def trocar(self, z, x, y, aviso=True):
        jogo = self.jogo
        self.criaturas[self.z] = jogo.criaturas
        self.minimapas[self.z] = jogo.minimapa
        m = self.mundo(z)
        self.z = z
        jogo.mundo = m
        jogo.ecossistema = self.ecos[z]
        jogo.criaturas = self.criaturas.get(z, [])
        jogo.minimapa = self.minimapas[z]
        jogo.minimapa.tamanho = self.minimapas.get(0, jogo.minimapa).tamanho
        jogo.flechas = []
        jogo.pesca = None
        jogo.gotas = []
        if hasattr(jogo, "orbes"):
            jogo.orbes = []
        j = jogo.jogador
        j.x, j.y = x, y
        j.vx = j.vy = 0.0
        m.atualizar_chunks(x, y, limite=99, raio=1)
        jogo.centralizar_camera()
        self.cavando = None
        self.espera = 0.6
        if aviso:
            if z < 0:
                jogo.avisar(f"Camada {z}: {nome_camada(z)}. Está escuro... use tochas!", 3)
            else:
                jogo.avisar("Você voltou para a superfície", 2.5)

    def descer(self, buraco):
        if self.espera > 0:
            return True
        z = self.z - 1
        if z < CAMADA_MAIS_FUNDA:
            self.jogo.avisar("Não dá para descer mais", 1.5)
            return True
        tx, ty = buraco.tx, buraco.ty
        m = self.mundo(z)
        ch = self._garantir_chunk(m, tx, ty)
        o = m.objeto(tx, ty)
        if o is not None and o.tipo != "escada":
            if o.conteudo:
                for e in o.conteudo:
                    if e:
                        m.itens.append(ItemChao(e[0], tx * TILE + 8, ty * TILE + 10, e[1]))
            m.remover(o)
        k = (ty % CH) * CH + (tx % CH)
        if ch.chao[k] in (LAVA, AGUA_FUNDA):
            ch.mudar_chao(k, CAVERNA)              # a lava esfria / a água escoa onde você chega
        if m.objeto(tx, ty) is None:
            m.colocar(Objeto("escada", tx, ty))
        self.trocar(z, tx * TILE + 8, ty * TILE + 12)
        return True

    def subir(self, escada):
        if self.espera > 0:
            return True
        z = self.z + 1
        tx, ty = escada.tx, escada.ty
        m = self.mundo(z)
        self._garantir_chunk(m, tx, ty)
        o = m.objeto(tx, ty)
        if o is not None and o.tipo != "buraco":
            if o.solido or o.construcao:
                self.jogo.avisar(f"Tem {OBJ_NOME(o)} tampando o buraco lá em cima", 2)
                return True
            m.remover(o)
            o = None
        if o is None:
            m.colocar(Objeto("buraco", tx, ty))
        self.trocar(z, tx * TILE + 8, ty * TILE + 12)
        return True

    # ===========================================================
    # Cavar o chão (abre buraco)
    # ===========================================================
    def pode_cavar(self, tx, ty):
        jogo = self.jogo
        m = jogo.mundo
        if jogo.estruturas.subterraneo:
            return False, "O chão da masmorra é duro demais"
        if self.z <= CAMADA_MAIS_FUNDA:
            return False, "Rocha-mãe: não dá para cavar mais fundo"
        if m.chunk(tx, ty) is None:
            return False, ""
        chao = m.tipo_chao(tx, ty)
        if chao not in CHAO_CAVAVEL:
            return False, "Não dá para cavar aqui"
        if m.objeto(tx, ty) is not None:
            return False, ""
        if m.piso(tx, ty) is not None:
            return False, "Tire o piso antes de cavar"
        return True, ""

    def cavar(self, tx, ty, poder_de):
        """Um golpe no chão. poder_de(tipo_ferramenta) -> poder. Retorna True se golpeou."""
        jogo = self.jogo
        ok, motivo = self.pode_cavar(tx, ty)
        if not ok:
            if motivo:
                jogo.avisar(motivo, 1.5)
            return False
        item, dureza, ferramenta, poder_min = CHAO_CAVAVEL[jogo.mundo.tipo_chao(tx, ty)]
        poder = poder_de(ferramenta)
        if poder < poder_min:
            from blocos import picareta_para
            jogo.avisar(f"Precisa de {picareta_para(poder_min)} para cavar pedra", 1.5)
            return False
        c = self.cavando
        if c is None or (c["x"], c["y"], c["z"]) != (tx, ty, self.z):
            c = self.cavando = {"x": tx, "y": ty, "z": self.z, "dano": 0, "dureza": dureza, "tempo": 0.0}
        c["dano"] += poder
        c["tempo"] = 1.2
        jogo.soltar_lascas((tx * TILE + 8, ty * TILE + 10), "chao_" + item, 4)
        if c["dano"] >= c["dureza"]:
            self.cavando = None
            m = jogo.mundo
            m.colocar(Objeto("buraco", tx, ty))
            jogo.soltar_itens([(item, 1)], tx * TILE + 8, ty * TILE + 8)
            jogo.soltar_lascas((tx * TILE + 8, ty * TILE + 10), "chao_" + item, 10)
            jogo.avisar("Você abriu um buraco. Fique em cima e aperte E para descer", 2.5)
        return True

    def fracao_cavando(self):
        c = self.cavando
        if not c or c["z"] != self.z:
            return None
        return c["x"], c["y"], min(1.0, c["dano"] / c["dureza"])

    # ===========================================================
    # Escada de mão (item)
    # ===========================================================
    def colocar_escada(self, tx, ty):
        """Chamado por main.tentar_colocar. Retorna (ok, motivo)."""
        jogo = self.jogo
        if self.z >= 0:
            return False, "Escada de mão serve nas cavernas. Para descer, cave um buraco com a pá"
        acima = self.mundo(self.z + 1)
        self._garantir_chunk(acima, tx, ty)
        o = acima.objeto(tx, ty)
        if o is not None and o.tipo != "buraco":
            if o.construcao and not o.bloco:
                return False, "Tem uma construção em cima (na camada de cima)"
            if o.bloco:
                for item, qtd in OBJETOS[o.tipo]["drops"]:
                    jogo.soltar_itens([(item, qtd)], tx * TILE + 8, ty * TILE + 8)
            acima.remover(o)
            o = None
        if o is None:
            acima.colocar(Objeto("buraco", tx, ty))
        jogo.mundo.colocar(Objeto("escada", tx, ty))
        jogo.avisar("Escada colocada: suba com E", 2)
        return True, ""

    # ===========================================================
    # Atualização, luz e desenho
    # ===========================================================
    def atualizar(self, dt):
        self.espera = max(0.0, self.espera - dt)
        c = self.cavando
        if c:
            c["tempo"] -= dt
            if c["tempo"] <= 0:
                self.cavando = None              # parou de cavar: perde o progresso

    def objeto_para_usar(self):
        """Buraco ou escada embaixo / bem perto do jogador."""
        j = self.jogo.jogador
        cx, cy = j.x, j.y - 4
        return self.jogo.mundo.objeto_mais_proximo(cx, cy, 14, tipos=("buraco", "escada"))

    def interagir(self):
        o = self.objeto_para_usar()
        if o is None:
            return False
        if o.tipo == "buraco":
            return self.descer(o)
        if o.tipo == "escada" and self.z < 0:
            return self.subir(o)
        return False

    def dica(self):
        o = self.objeto_para_usar()
        if o is None:
            return ""
        if o.tipo == "buraco":
            return "[E] Descer pelo buraco" if self.z > CAMADA_MAIS_FUNDA else ""
        if o.tipo == "escada" and self.z < 0:
            return "[E] Subir a escada"
        return ""

    def escuridao(self):
        return ESCURIDAO_MAXIMA if self.z < 0 else None

    def luz_do_dia(self):
        """0..1: quanta luz do sol entra pelos buracos (só na camada -1)."""
        jogo = self.jogo
        luz = 0.5 - 0.5 * math.cos(2 * math.pi * jogo.hora() / 24.0)
        return max(0.0, min(1.0, luz * 1.6 - 0.2))

    def desenhar_luzes(self, m, cx, cy):
        """Embaixo da terra: escuro total + suas luzes, tochas, lava e sol pelos buracos."""
        jogo = self.jogo
        mundo = jogo.mundo
        m.fill((12, 12, 20))
        pisca = 2 if int(jogo.tempo_total * 6) % 2 else 0
        j = jogo.jogador
        jx, jy = int(j.x - cx), int(j.y - 6 - cy)
        m.blit(gradiente_luz(42, (96, 90, 104)), (jx - 42, jy - 42), special_flags=pygame.BLEND_RGB_ADD)
        tx0, ty0 = cx // TILE - 2, cy // TILE - 2
        tx1, ty1 = (cx + LARGURA_INTERNA) // TILE + 2, (cy + ALTURA_INTERNA) // TILE + 2
        # lava brilha
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if (tx + ty) % 2 == 0 and mundo.tipo_chao(tx, ty) == LAVA:
                    r = 22 + (pisca if (tx * 7 + ty) % 3 == 0 else 0)
                    m.blit(gradiente_luz(r, (240, 120, 50)), (tx * TILE + 8 - cx - r, ty * TILE + 8 - cy - r),
                           special_flags=pygame.BLEND_RGB_ADD)
        # sol pelos buracos da superfície
        if self.z == -1:
            sol = self.luz_do_dia()
            if sol > 0.05:
                cima = self.superficie
                cor = (int(230 * sol), int(225 * sol), int(200 * sol))
                for ty in range(ty0, ty1 + 1):
                    for tx in range(tx0, tx1 + 1):
                        o = cima.objeto(tx, ty)
                        if o is not None and o.tipo == "buraco":
                            m.blit(gradiente_luz(40, cor), (tx * TILE + 8 - cx - 40, ty * TILE + 8 - cy - 40),
                                   special_flags=pygame.BLEND_RGB_ADD)

    def desenhar_espiar(self, cena, cx, cy):
        """V: a camada de cima aparece transparente por cima (para se localizar)."""
        if not self.espiar or self.z >= 0:
            return
        jogo = self.jogo
        acima = self.mundos.get(self.z + 1)
        if acima is None:
            return
        camada = pygame.Surface((LARGURA_INTERNA, ALTURA_INTERNA))
        camada.fill((0, 0, 0))
        px_ch = CH * TILE
        mundo_atual = jogo.mundo
        jogo.mundo = acima
        try:
            for ccy in range(cy // px_ch, (cy + ALTURA_INTERNA) // px_ch + 1):
                for ccx in range(cx // px_ch, (cx + LARGURA_INTERNA) // px_ch + 1):
                    ch = acima.chunks.get((ccx, ccy))
                    if ch is None:
                        ao = acima.ao_carregar
                        acima.ao_carregar = None
                        ch = acima.gerar(ccx, ccy)
                        acima.ao_carregar = ao
                    if ch.superficie is None or ch.sujo:
                        jogo.desenhar_chunk(ch)
                    camada.blit(ch.superficie, (ccx * px_ch - cx, ccy * px_ch - cy))
            sp = jogo.sprites
            for ty in range(cy // TILE - 1, (cy + ALTURA_INTERNA) // TILE + 2):
                for tx in range(cx // TILE - 1, (cx + LARGURA_INTERNA) // TILE + 2):
                    o = acima.objeto(tx, ty)
                    if o is not None:
                        img = sp.sprite_objeto(o, jogo.estacao, 0)
                        camada.blit(img, (tx * TILE - cx + (TILE - img.get_width()) // 2,
                                          ty * TILE - cy - (img.get_height() - TILE)))
        finally:
            jogo.mundo = mundo_atual
        camada.fill((150, 170, 230), special_flags=pygame.BLEND_RGB_MULT)
        camada.set_alpha(120)
        cena.blit(camada, (0, 0))

    # ===========================================================
    # Save
    # ===========================================================
    def para_dict(self):
        camadas = {str(z): ch for z, ch in self.pendentes.items()}
        explorados = {str(z): list(e) for z, e in self.explorados.items()}
        for z, m in self.mundos.items():
            if z == 0:
                continue
            camadas[str(z)] = m.dados_proprios()
            explorados[str(z)] = [f"{cx},{cy}" for cx, cy in self.minimapas[z].explorados]
        return {"z": self.z, "camadas": camadas, "explorados": explorados}

    def carregar_dict(self, d):
        self.pendentes = {int(z): dict(v) for z, v in d.get("camadas", {}).items()}
        self.explorados = {int(z): list(v) for z, v in d.get("explorados", {}).items()}
        z = int(d.get("z", 0))
        if z < 0:
            j = self.jogo.jogador
            self.trocar(z, j.x, j.y, aviso=False)
            self.espera = 0.0


def OBJ_NOME(o):
    from dados import NOMES_OBJETOS
    return NOMES_OBJETOS.get(o.tipo, o.tipo).lower()
