# -*- coding: utf-8 -*-
"""
dados_estruturas.py - Tabelas das ESTRUTURAS (vilas, cidadelas, castelos,
masmorras, ruínas e baús). Tudo é ACRESCENTADO às tabelas de dados.py quando
este arquivo é importado, para não precisar mexer em dados.py.

- Itens novos: moeda de ouro, trigo, pão, poção de vida, tocha, espada de rubi.
- Objetos novos: baú, porta, poço, plantação, cerca, tocha, cama, trono,
  estandarte, escadas, ossos e os pisos das construções (caminho, piso de
  pedra, arenito, tapete, terra arada).
- Criaturas novas: aldeão, guarda, cavaleiro, esqueleto e os chefes.
"""
from dados import ITENS, OBJETOS, NOMES_OBJETOS, CRIATURAS, RECEITAS

# Chão novo (só dentro das masmorras)
PISO_MASMORRA = 20
VAZIO = 21

ITENS_NOVOS = {
    "moeda_ouro":  {"nome": "Moeda de ouro", "tipo": "material", "pilha": 99,
                    "desc": "Achada em baús. Os aldeões aceitam em trocas"},
    "trigo":       {"nome": "Trigo", "tipo": "material", "pilha": 99,
                    "desc": "Colhido nas plantações das vilas"},
    "pao":         {"nome": "Pão", "tipo": "comida", "pilha": 99, "fome": 28, "vida": 2},
    "pocao_vida":  {"nome": "Poção de vida", "tipo": "bebida", "pilha": 10, "vida": 40, "sede": 5},
    "tocha":       {"nome": "Tocha", "tipo": "construcao", "pilha": 99,
                    "desc": "Ilumina à noite e nas masmorras"},
    "espada_rubi": {"nome": "Espada de rubi", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 11,
                    "desc": "Tesouro do Rei Esqueleto"},
}

# "piso": True = vai para a camada de pisos do chunk (desenhado no chão)
OBJETOS_NOVOS = {
    "bau_tesouro":   {"vida": 4, "drops": [], "solido": True, "construcao": True},
    "bau_tesouro_aberto": {"vida": 4, "ferramenta": "machado", "drops": [("madeira", 2)], "solido": True,
                           "construcao": True},
    "porta":         {"vida": 4, "ferramenta": "machado", "drops": [("madeira", 2)], "solido": False,
                      "construcao": True, "altura": 4},
    "poco":          {"vida": 99, "drops": [], "solido": True, "construcao": True, "altura": 6},
    "plantacao_trigo":   {"vida": 1, "drops": [("trigo", 2)], "solido": False, "construcao": True},
    "plantacao_abobora": {"vida": 1, "drops": [("frutas", 2)], "solido": False, "construcao": True},
    "cerca":         {"vida": 3, "ferramenta": "machado", "drops": [("madeira", 1)], "solido": True,
                      "construcao": True},
    "tocha":         {"vida": 1, "drops": [("tocha", 1)], "solido": False, "construcao": True, "altura": 2},
    "cama":          {"vida": 3, "ferramenta": "machado", "drops": [("madeira", 2), ("fibra", 2)],
                      "solido": True, "construcao": True},
    "trono":         {"vida": 99, "drops": [], "solido": True, "construcao": True, "altura": 8},
    "estandarte":    {"vida": 2, "drops": [("fibra", 2)], "solido": False, "construcao": True, "altura": 8},
    "escada_descer": {"vida": 99, "drops": [], "solido": False, "construcao": True},
    "escada_subir":  {"vida": 99, "drops": [], "solido": False, "construcao": True},
    "ossos":         {"vida": 1, "drops": [], "solido": False, "construcao": True},
    # pisos (camada do chão)
    "caminho":       {"vida": 3, "ferramenta": "picareta", "drops": [("pedra", 1)], "solido": False,
                      "construcao": True, "piso": True},
    "piso_pedra":    {"vida": 4, "ferramenta": "picareta", "drops": [("pedra", 1)], "solido": False,
                      "construcao": True, "piso": True},
    "piso_arenito":  {"vida": 3, "ferramenta": "picareta", "drops": [("pedra", 1)], "solido": False,
                      "construcao": True, "piso": True},
    "tapete":        {"vida": 2, "drops": [("fibra", 2)], "solido": False, "construcao": True, "piso": True},
    "terra_arada":   {"vida": 1, "drops": [], "solido": False, "construcao": True, "piso": True},
}
TIPOS_PISO = {"piso"} | {t for t, d in OBJETOS_NOVOS.items() if d.get("piso")}
# objetos que não quebram (o clique faz outra coisa: abrir, descer...)
INQUEBRAVEIS = {"bau_tesouro", "poco", "trono", "escada_descer", "escada_subir"}

NOMES_NOVOS = {
    "bau_tesouro": "Baú de tesouro", "bau_tesouro_aberto": "Baú vazio", "porta": "Porta", "poco": "Poço",
    "plantacao_trigo": "Plantação de trigo", "plantacao_abobora": "Plantação de abóbora", "cerca": "Cerca", "tocha": "Tocha", "cama": "Cama",
    "trono": "Trono", "estandarte": "Estandarte", "escada_descer": "Escada para a masmorra",
    "escada_subir": "Escada para a superfície", "ossos": "Ossos", "caminho": "Caminho",
    "piso_pedra": "Piso de pedra", "piso_arenito": "Piso de arenito", "tapete": "Tapete",
    "terra_arada": "Terra arada",
}

# comportamento "npc" = amigável (não é contado pelo ecossistema)
# comportamento "inimigo" = defende uma estrutura (não some de dia)
CRIATURAS_NOVAS = {
    "aldeao":    {"nome": "Aldeão", "vida": 10, "velocidade": 18, "comportamento": "npc"},
    "guarda":    {"nome": "Guarda", "vida": 30, "velocidade": 40, "comportamento": "npc", "dano": 6},
    "cavaleiro": {"nome": "Cavaleiro", "vida": 14, "velocidade": 34, "comportamento": "inimigo",
                  "dano": 11, "alcance": 110, "drops": [("ferro", 1), ("moeda_ouro", 2)]},
    "esqueleto": {"nome": "Esqueleto", "vida": 7, "velocidade": 36, "comportamento": "inimigo",
                  "dano": 8, "alcance": 120, "drops": [("moeda_ouro", 1)]},
    "senhor_castelo": {"nome": "Cavaleiro Negro", "vida": 45, "velocidade": 32, "comportamento": "inimigo",
                       "dano": 14, "alcance": 130, "chefe": True,
                       "drops": [("armadura_ferro", 1), ("moeda_ouro", 8)]},
    "rei_esqueleto": {"nome": "Rei Esqueleto", "vida": 60, "velocidade": 28, "comportamento": "inimigo",
                      "dano": 15, "alcance": 150, "chefe": True,
                      "drops": [("espada_rubi", 1), ("moeda_ouro", 12), ("pocao_vida", 2)]},
}

RECEITAS_NOVAS = [
    {"item": "tocha", "custo": {"madeira": 1, "fibra": 1}, "qtd": 2, "categoria": "Construção"},
    {"item": "pao", "custo": {"trigo": 3}, "categoria": "Comida", "estacao": "fogueira"},
]


# Nomes que talvez já existam em dados.py (tocha, cama, trigo, pão...): se existirem,
# a versão de dados.py VALE e a daqui é ignorada. Os que eu acrescentei ficam aqui:
REGISTRADOS = set()


def registrar():
    """Acrescenta nas tabelas de dados.py só o que ainda não existe lá."""
    for nome, d in ITENS_NOVOS.items():
        if nome not in ITENS:
            ITENS[nome] = d
            REGISTRADOS.add(nome)
    for nome, d in OBJETOS_NOVOS.items():
        OBJETOS.setdefault(nome, d)
    for nome, d in NOMES_NOVOS.items():
        NOMES_OBJETOS.setdefault(nome, d)
    CRIATURAS.update(CRIATURAS_NOVAS)
    for rc in RECEITAS_NOVAS:
        if not any(r["item"] == rc["item"] for r in RECEITAS):
            RECEITAS.append(rc)


def e_piso(tipo):
    return tipo in TIPOS_PISO


registrar()
