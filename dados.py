# -*- coding: utf-8 -*-
"""
dados.py - TABELAS do jogo: itens, receitas, objetos do mundo, biomas e criaturas.

O jogo é "orientado a dados": para criar um item ou receita novos, quase
sempre basta acrescentar uma linha aqui (e um ícone em sprites.py).
"""

# ===============================================================
# ITENS
# ---------------------------------------------------------------
# tipo: material, comida, bebida, ferramenta, arma, armadura, construcao, utilidade
# pilha: quantos cabem num espaço
# fome/sede/vida: o que muda ao consumir
# slot: onde equipa ("cabeca", "corpo", "arma", "ferramenta")
# ferramenta: (tipo, poder) -> poder 2 = madeira, 3 = pedra, 5 = ferro
# ===============================================================
ITENS = {
    # --- materiais ---
    "madeira":       {"nome": "Madeira", "tipo": "material", "pilha": 99},
    "pedra":         {"nome": "Pedra", "tipo": "material", "pilha": 99},
    "fibra":         {"nome": "Fibra", "tipo": "material", "pilha": 99,
                      "desc": "Vem de capim, junco e cactos"},
    "couro":         {"nome": "Couro", "tipo": "material", "pilha": 99},
    "minerio_ferro": {"nome": "Minério de ferro", "tipo": "material", "pilha": 99,
                      "desc": "Achado nas montanhas. Derreta na fogueira"},
    "ferro":         {"nome": "Barra de ferro", "tipo": "material", "pilha": 99,
                      "desc": "Feita no forno (minério + carvão)"},
    "carvao":        {"nome": "Carvão", "tipo": "material", "pilha": 99,
                      "desc": "Madeira queimada no forno"},
    "trigo":         {"nome": "Trigo", "tipo": "material", "pilha": 99,
                      "desc": "Faça pão no forno"},
    "sementes_trigo": {"nome": "Sementes de trigo", "tipo": "construcao", "pilha": 99,
                       "objeto": "plantacao",
                       "desc": "Plante na grama (botão direito). Cresce mais rápido na primavera"},
    "flecha":        {"nome": "Flecha", "tipo": "municao", "pilha": 99,
                      "desc": "Munição do arco"},
    # --- comida e bebida ---
    "frutas":        {"nome": "Frutas", "tipo": "comida", "pilha": 99, "fome": 15},
    "carne_crua":    {"nome": "Carne crua", "tipo": "comida", "pilha": 99, "fome": 10, "vida": -5,
                      "desc": "Asse na fogueira (E perto dela)"},
    "carne_assada":  {"nome": "Carne assada", "tipo": "comida", "pilha": 99, "fome": 35, "vida": 5},
    "peixe":         {"nome": "Peixe cru", "tipo": "comida", "pilha": 99, "fome": 8,
                      "desc": "Asse na fogueira (E perto dela)"},
    "peixe_assado":  {"nome": "Peixe assado", "tipo": "comida", "pilha": 99, "fome": 30, "vida": 4},
    "pao":           {"nome": "Pão", "tipo": "comida", "pilha": 99, "fome": 30, "vida": 3},
    "sopa":          {"nome": "Sopa", "tipo": "comida", "pilha": 10, "fome": 40, "sede": 15, "vida": 8,
                      "desc": "Esquenta no frio"},
    "cantil":        {"nome": "Cantil (vazio)", "tipo": "utilidade", "pilha": 1,
                      "desc": "Encha com E perto da água"},
    "cantil_cheio":  {"nome": "Cantil cheio", "tipo": "bebida", "pilha": 1, "sede": 45,
                      "devolve": "cantil"},
    # --- ferramentas ---
    "machado_madeira":  {"nome": "Machado de madeira", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("machado", 2)},
    "machado_pedra":    {"nome": "Machado de pedra", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("machado", 3)},
    "machado_ferro":    {"nome": "Machado de ferro", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("machado", 5)},
    "picareta_madeira": {"nome": "Picareta de madeira", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("picareta", 2)},
    "picareta_pedra":   {"nome": "Picareta de pedra", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("picareta", 3),
                         "desc": "Consegue quebrar minério de ferro"},
    "picareta_ferro":   {"nome": "Picareta de ferro", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("picareta", 5)},
    "vara_pesca":       {"nome": "Vara de pesca", "tipo": "ferramenta", "pilha": 1,
                         "slot": "ferramenta", "ferramenta": ("pesca", 1),
                         "desc": "Escolha na barra e clique com o botão direito na água"},
    # --- armas ---
    "espada_madeira": {"nome": "Espada de madeira", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 2},
    "espada_pedra":   {"nome": "Espada de pedra", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 4},
    "espada_ferro":   {"nome": "Espada de ferro", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 7},
    "lanca":          {"nome": "Lança", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 5, "alcance": 20,
                       "desc": "Alcança mais longe que a espada"},
    "arco":           {"nome": "Arco", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 1, "disparo": 5,
                       "desc": "Na mão: clique para atirar flechas na direção do mouse"},
    # --- armaduras ---
    "capuz_couro":     {"nome": "Capuz de couro", "tipo": "armadura", "pilha": 1, "slot": "cabeca", "defesa": 1},
    "roupa_couro":     {"nome": "Roupa de couro", "tipo": "armadura", "pilha": 1, "slot": "corpo", "defesa": 2},
    "capacete_ferro":  {"nome": "Capacete de ferro", "tipo": "armadura", "pilha": 1, "slot": "cabeca", "defesa": 3},
    "armadura_ferro":  {"nome": "Armadura de ferro", "tipo": "armadura", "pilha": 1, "slot": "corpo", "defesa": 5},
    # --- construções (botão direito para colocar) ---
    "bancada":        {"nome": "Bancada", "tipo": "construcao", "pilha": 10,
                       "desc": "Necessária para itens avançados"},
    "fogueira":       {"nome": "Fogueira", "tipo": "construcao", "pilha": 10,
                       "desc": "Luz, assa comida e derrete ferro"},
    "parede_madeira": {"nome": "Parede de madeira", "tipo": "construcao", "pilha": 99},
    "parede_pedra":   {"nome": "Parede de pedra", "tipo": "construcao", "pilha": 99},
    "piso":           {"nome": "Piso", "tipo": "construcao", "pilha": 99},
    "tocha":          {"nome": "Tocha", "tipo": "construcao", "pilha": 99,
                       "desc": "Ilumina. Na mão também ilumina em volta de você"},
    "forno":          {"nome": "Forno", "tipo": "construcao", "pilha": 10,
                       "desc": "Faz carvão, barras de ferro e pão"},
    "bau":            {"nome": "Baú", "tipo": "construcao", "pilha": 10,
                       "desc": "Guarda 18 pilhas de itens (E ou botão direito para abrir)"},
    "cama":           {"nome": "Cama", "tipo": "construcao", "pilha": 10,
                       "desc": "Marca onde você renasce. À noite: dormir pula para a manhã"},
}

NOMES_SLOTS = {"cabeca": "Cabeça", "corpo": "Corpo", "arma": "Arma", "ferramenta": "Ferramenta"}
ORDEM_SLOTS = ["cabeca", "corpo", "arma", "ferramenta"]


def nome_item(item):
    return ITENS[item]["nome"]


# ===============================================================
# RECEITAS (menu C)
# estacao: None = em qualquer lugar, "bancada" ou "fogueira" = precisa estar perto
# ===============================================================
CATEGORIAS = ["Ferramentas", "Armas", "Armaduras", "Construção", "Móveis", "Comida", "Materiais"]

RECEITAS = [
    # Ferramentas
    {"item": "machado_madeira", "custo": {"madeira": 3}, "categoria": "Ferramentas"},
    {"item": "picareta_madeira", "custo": {"madeira": 3}, "categoria": "Ferramentas"},
    {"item": "machado_pedra", "custo": {"madeira": 2, "pedra": 3}, "categoria": "Ferramentas", "estacao": "bancada"},
    {"item": "picareta_pedra", "custo": {"madeira": 2, "pedra": 3}, "categoria": "Ferramentas", "estacao": "bancada"},
    {"item": "machado_ferro", "custo": {"madeira": 2, "ferro": 3}, "categoria": "Ferramentas", "estacao": "bancada"},
    {"item": "picareta_ferro", "custo": {"madeira": 2, "ferro": 3}, "categoria": "Ferramentas", "estacao": "bancada"},
    {"item": "vara_pesca", "custo": {"madeira": 2, "fibra": 3}, "categoria": "Ferramentas"},
    {"item": "cantil", "custo": {"couro": 2, "fibra": 1}, "categoria": "Ferramentas"},
    # Armas
    {"item": "espada_madeira", "custo": {"madeira": 4}, "categoria": "Armas"},
    {"item": "espada_pedra", "custo": {"madeira": 1, "pedra": 4}, "categoria": "Armas", "estacao": "bancada"},
    {"item": "espada_ferro", "custo": {"madeira": 1, "ferro": 4}, "categoria": "Armas", "estacao": "bancada"},
    {"item": "lanca", "custo": {"madeira": 3, "pedra": 2, "fibra": 1}, "categoria": "Armas", "estacao": "bancada"},
    {"item": "arco", "custo": {"madeira": 3, "fibra": 3}, "categoria": "Armas", "estacao": "bancada"},
    {"item": "flecha", "custo": {"madeira": 1, "pedra": 1, "fibra": 1}, "qtd": 4, "categoria": "Armas",
     "estacao": "bancada"},
    # Armaduras
    {"item": "capuz_couro", "custo": {"couro": 3, "fibra": 1}, "categoria": "Armaduras", "estacao": "bancada"},
    {"item": "roupa_couro", "custo": {"couro": 5, "fibra": 2}, "categoria": "Armaduras", "estacao": "bancada"},
    {"item": "capacete_ferro", "custo": {"ferro": 4}, "categoria": "Armaduras", "estacao": "bancada"},
    {"item": "armadura_ferro", "custo": {"ferro": 7}, "categoria": "Armaduras", "estacao": "bancada"},
    # Construção
    {"item": "fogueira", "custo": {"madeira": 4, "pedra": 3}, "categoria": "Construção"},
    {"item": "parede_madeira", "custo": {"madeira": 2}, "categoria": "Construção"},
    {"item": "parede_pedra", "custo": {"pedra": 2}, "categoria": "Construção"},
    {"item": "piso", "custo": {"madeira": 1}, "categoria": "Construção"},
    {"item": "tocha", "custo": {"madeira": 1, "fibra": 1}, "qtd": 2, "categoria": "Construção"},
    # Móveis
    {"item": "bancada", "custo": {"madeira": 6, "pedra": 2}, "categoria": "Móveis"},
    {"item": "forno", "custo": {"pedra": 8, "madeira": 2}, "categoria": "Móveis", "estacao": "bancada"},
    {"item": "bau", "custo": {"madeira": 8}, "categoria": "Móveis", "estacao": "bancada"},
    {"item": "cama", "custo": {"madeira": 6, "couro": 2, "fibra": 4}, "categoria": "Móveis", "estacao": "bancada"},
    # Comida
    {"item": "carne_assada", "custo": {"carne_crua": 1}, "categoria": "Comida", "estacao": "fogueira"},
    {"item": "peixe_assado", "custo": {"peixe": 1}, "categoria": "Comida", "estacao": "fogueira"},
    {"item": "sopa", "custo": {"carne_crua": 1, "frutas": 2}, "categoria": "Comida", "estacao": "fogueira"},
    {"item": "pao", "custo": {"trigo": 3}, "categoria": "Comida", "estacao": "forno"},
    # Materiais
    {"item": "carvao", "custo": {"madeira": 2}, "categoria": "Materiais", "estacao": "forno"},
    {"item": "ferro", "custo": {"minerio_ferro": 2, "carvao": 1}, "categoria": "Materiais", "estacao": "forno"},
]

NOMES_ESTACOES = {"bancada": "Bancada", "fogueira": "Fogueira acesa", "forno": "Forno"}


# ===============================================================
# OBJETOS DO MUNDO (recursos e construções)
# ferramenta: qual ferramenta acelera; poder_min: poder mínimo para conseguir quebrar
# drops: lista de (item, quantidade)
# ===============================================================
OBJETOS = {
    "arvore":         {"vida": 6, "ferramenta": "machado", "drops": [("madeira", 4)], "solido": True, "altura": 8},
    "arvore_pantano": {"vida": 6, "ferramenta": "machado", "drops": [("madeira", 3), ("fibra", 1)], "solido": True, "altura": 8},
    "pinheiro":       {"vida": 6, "ferramenta": "machado", "drops": [("madeira", 4)], "solido": True, "altura": 10},
    "cacto":          {"vida": 3, "ferramenta": "machado", "drops": [("frutas", 1), ("fibra", 2)], "solido": True, "altura": 4},
    "pedra":          {"vida": 6, "ferramenta": "picareta", "drops": [("pedra", 3)], "solido": True},
    "minerio_ferro":  {"vida": 9, "ferramenta": "picareta", "poder_min": 3,
                       "drops": [("minerio_ferro", 2), ("pedra", 1)], "solido": True},
    "arbusto":        {"vida": 2, "drops": [("frutas", 2)], "drops_vazio": [("madeira", 1), ("fibra", 1)], "solido": True},
    "capim":          {"vida": 1, "drops": [("fibra", 1)], "solido": False},
    "junco":          {"vida": 1, "drops": [("fibra", 2)], "solido": False, "altura": 4},
    "trigo":          {"vida": 1, "drops": [("trigo", 1), ("sementes_trigo", 1)], "solido": False, "altura": 3},
    "plantacao":      {"vida": 1, "drops": [("sementes_trigo", 1)], "drops_maduro": [("trigo", 2), ("sementes_trigo", 2)],
                       "solido": False, "altura": 3, "construcao": True},
    # construções
    "bancada":        {"vida": 4, "ferramenta": "machado", "drops": [("bancada", 1)], "solido": True, "construcao": True},
    "fogueira":       {"vida": 2, "drops": [("fogueira", 1)], "solido": False, "construcao": True},
    "parede_madeira": {"vida": 4, "ferramenta": "machado", "drops": [("madeira", 2)], "solido": True,
                       "construcao": True, "altura": 4},
    "parede_pedra":   {"vida": 6, "ferramenta": "picareta", "drops": [("pedra", 2)], "solido": True,
                       "construcao": True, "altura": 4},
    "piso":           {"vida": 2, "ferramenta": "machado", "drops": [("madeira", 1)], "solido": False,
                       "construcao": True},
    "tocha":          {"vida": 1, "drops": [("tocha", 1)], "solido": False, "construcao": True, "altura": 2},
    "forno":          {"vida": 6, "ferramenta": "picareta", "drops": [("forno", 1)], "solido": True,
                       "construcao": True, "altura": 6},
    "bau":            {"vida": 4, "ferramenta": "machado", "drops": [("bau", 1)], "solido": True, "construcao": True},
    "cama":           {"vida": 4, "ferramenta": "machado", "drops": [("cama", 1)], "solido": True, "construcao": True},
}

NOMES_OBJETOS = {
    "arvore": "Árvore", "arvore_pantano": "Árvore do pântano", "pinheiro": "Pinheiro",
    "cacto": "Cacto", "pedra": "Pedra", "minerio_ferro": "Minério de ferro",
    "arbusto": "Arbusto", "capim": "Capim", "junco": "Junco", "bancada": "Bancada",
    "fogueira": "Fogueira", "parede_madeira": "Parede de madeira",
    "parede_pedra": "Parede de pedra", "piso": "Piso", "trigo": "Trigo selvagem",
    "plantacao": "Plantação de trigo", "tocha": "Tocha", "forno": "Forno", "bau": "Baú", "cama": "Cama",
}


# ===============================================================
# BIOMAS
# agua: muda o nível de água da região (pântano tem mais lagos, deserto menos)
# recursos: (objeto, chance por bloco)
# ===============================================================
BIOMAS = {
    "planicie": {"nome": "Planície", "agua": 0.0,
                 "recursos": [("arvore", 0.02), ("arbusto", 0.03), ("pedra", 0.012), ("capim", 0.07),
                               ("trigo", 0.012)],
                 "animais": ["coelho", "galinha", "cervo"], "predadores": ["lobo"],
                 "noturnos": ["slime"]},
    "floresta": {"nome": "Floresta", "agua": 0.0,
                 "recursos": [("arvore", 0.20), ("arbusto", 0.04), ("pedra", 0.01), ("capim", 0.03)],
                 "animais": ["cervo", "coelho"], "predadores": ["lobo"],
                 "noturnos": ["aranha", "slime"]},
    "deserto":  {"nome": "Deserto", "agua": -0.07,
                 "recursos": [("cacto", 0.03), ("pedra", 0.015)],
                 "animais": ["coelho"], "predadores": ["escorpiao"],
                 "noturnos": ["escorpiao"]},
    "pantano":  {"nome": "Pântano", "agua": 0.07,
                 "recursos": [("arvore_pantano", 0.06), ("junco", 0.10), ("arbusto", 0.02)],
                 "animais": ["galinha"], "predadores": ["lobo"],
                 "noturnos": ["slime", "aranha"]},
    "neve":     {"nome": "Neve", "agua": -0.02,
                 "recursos": [("pinheiro", 0.10), ("pedra", 0.02)],
                 "animais": ["coelho", "cervo"], "predadores": ["lobo"],
                 "noturnos": ["slime"]},
    "montanha": {"nome": "Montanha", "agua": -0.09,
                 "recursos": [("pedra", 0.12), ("minerio_ferro", 0.04), ("pinheiro", 0.015)],
                 "animais": [], "predadores": ["lobo"],
                 "noturnos": ["aranha"]},
}


# ===============================================================
# CRIATURAS
# comportamento: "passivo" (foge), "predador" (caça animais e você), "monstro" (caça você)
# ===============================================================
CRIATURAS = {
    "coelho":    {"nome": "Coelho", "vida": 2, "velocidade": 30, "comportamento": "passivo",
                  "drops": [("carne_crua", 1), ("couro", 1)]},
    "galinha":   {"nome": "Galinha", "vida": 2, "velocidade": 22, "comportamento": "passivo",
                  "drops": [("carne_crua", 1), ("fibra", 1)]},
    "cervo":     {"nome": "Cervo", "vida": 5, "velocidade": 34, "comportamento": "passivo",
                  "drops": [("carne_crua", 3), ("couro", 2)]},
    "lobo":      {"nome": "Lobo", "vida": 7, "velocidade": 44, "comportamento": "predador",
                  "dano": 9, "alcance": 110, "drops": [("carne_crua", 1), ("couro", 2)]},
    "slime":     {"nome": "Slime", "vida": 4, "velocidade": 32, "comportamento": "monstro",
                  "dano": 7, "alcance": 160, "noturno": True, "drops": [("fibra", 1)]},
    "aranha":    {"nome": "Aranha", "vida": 5, "velocidade": 42, "comportamento": "monstro",
                  "dano": 8, "alcance": 140, "noturno": True, "drops": [("fibra", 3)]},
    "escorpiao": {"nome": "Escorpião", "vida": 6, "velocidade": 30, "comportamento": "monstro",
                  "dano": 10, "alcance": 100, "drops": [("carne_crua", 1)]},
}
