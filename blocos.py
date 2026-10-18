# -*- coding: utf-8 -*-
"""
blocos.py - Tabelas da v0.5 ("estilo Minecraft", mas visto de cima).

Tudo aqui é ACRESCENTADO (ou ajustado) nas tabelas de dados.py quando este
arquivo é importado:
- Blocos: terra, areia, pedra, pedregulho, pedra lisa, toras, tábuas, vidro,
  minérios (carvão, ferro, ouro, cristal e diamante), lâmpada de cristal,
  escada de mão e buraco (para descer de camada).
- Ferramentas por nível: madeira -> pedra -> ferro -> diamante (e as pás).
- Receitas com FORMA (grade 2x2 no inventário e 3x3 na bancada).
- Forno: o que derrete em quê e quanto tempo cada combustível queima.
- Criaturas novas: vaca, porco, ovelha, zumbi, esqueleto (arqueiro) e o Explosivo.
- Durabilidade de ferramentas, armas e armaduras.
"""
from dados import ITENS, OBJETOS, NOMES_OBJETOS, RECEITAS, CATEGORIAS, BIOMAS, CRIATURAS
import dados_estruturas  # noqa: F401  (registra antes, para as receitas daqui valerem por último)

# ===============================================================
# Níveis das ferramentas
# ===============================================================
PODER = {"madeira": 2, "pedra": 3, "ferro": 5, "diamante": 8}
MATERIAL_TIER = {"madeira": "tabuas", "pedra": "pedra", "ferro": "ferro", "diamante": "diamante"}
NOME_TIER = {"madeira": "madeira", "pedra": "pedra", "ferro": "ferro", "diamante": "diamante"}
DURABILIDADE_TIER = {"madeira": 60, "pedra": 130, "ferro": 250, "diamante": 1000}
DANO_ESPADA = {"madeira": 2, "pedra": 4, "ferro": 7, "diamante": 10}


def picareta_para(poder):
    """Texto da picareta mínima para um poder ('uma picareta de pedra')."""
    for tier, p in PODER.items():
        if p >= poder:
            return f"uma picareta de {NOME_TIER[tier]}"
    return "uma picareta melhor"


# ===============================================================
# Itens
# ===============================================================
ITENS_V5 = {
    "tabuas":       {"nome": "Tábuas", "tipo": "construcao", "pilha": 99, "objeto": "bloco_tabuas",
                     "desc": "Bloco de construção. 1 tora = 4 tábuas"},
    "graveto":      {"nome": "Graveto", "tipo": "material", "pilha": 99, "desc": "Cabo de ferramentas e tochas"},
    "terra":        {"nome": "Terra", "tipo": "construcao", "pilha": 99, "objeto": "bloco_terra",
                     "desc": "Bloco. Cave o chão com a pá para pegar"},
    "areia":        {"nome": "Areia", "tipo": "construcao", "pilha": 99, "objeto": "bloco_areia",
                     "desc": "Bloco. No forno vira vidro"},
    "vidro":        {"nome": "Vidro", "tipo": "construcao", "pilha": 99, "objeto": "bloco_vidro",
                     "desc": "Bloco transparente"},
    "pedra_lisa":   {"nome": "Pedra lisa", "tipo": "construcao", "pilha": 99, "objeto": "bloco_pedra_lisa",
                     "desc": "Pedregulho derretido no forno"},
    "minerio_ouro": {"nome": "Minério de ouro", "tipo": "material", "pilha": 99,
                     "desc": "Fundo nas cavernas (camada -2 ou mais). Derreta no forno"},
    "ouro":         {"nome": "Barra de ouro", "tipo": "material", "pilha": 99,
                     "desc": "Vira moedas na grade (os aldeões aceitam)"},
    "cristal":      {"nome": "Cristal", "tipo": "material", "pilha": 99,
                     "desc": "Pó brilhante das camadas -3 e -4. Faz lâmpadas"},
    "diamante":     {"nome": "Diamante", "tipo": "material", "pilha": 99,
                     "desc": "Só na camada -4. As melhores ferramentas"},
    "lampada":      {"nome": "Lâmpada de cristal", "tipo": "construcao", "pilha": 99, "objeto": "lampada",
                     "desc": "Bloco que ilumina bastante"},
    "escada":       {"nome": "Escada de mão", "tipo": "construcao", "pilha": 99, "objeto": "escada",
                     "desc": "Debaixo da terra: abre um buraco em cima para subir"},
    "la":           {"nome": "Lã", "tipo": "material", "pilha": 99, "desc": "Das ovelhas. Faz camas"},
    "carne_podre":  {"nome": "Carne podre", "tipo": "comida", "pilha": 99, "fome": 8, "vida": -4,
                     "saturacao": 1, "desc": "Dos zumbis. Só se estiver com muita fome..."},
    "osso":         {"nome": "Osso", "tipo": "material", "pilha": 99, "desc": "Dos esqueletos. Vira gravetos"},
    "polvora":      {"nome": "Pólvora", "tipo": "material", "pilha": 99, "desc": "Do Explosivo"},
    "machado_diamante":  {"nome": "Machado de diamante", "tipo": "ferramenta", "pilha": 1,
                          "slot": "ferramenta", "ferramenta": ("machado", 8)},
    "picareta_diamante": {"nome": "Picareta de diamante", "tipo": "ferramenta", "pilha": 1,
                          "slot": "ferramenta", "ferramenta": ("picareta", 8)},
    "espada_diamante":   {"nome": "Espada de diamante", "tipo": "arma", "pilha": 1, "slot": "arma", "dano": 10},
    "capacete_diamante": {"nome": "Capacete de diamante", "tipo": "armadura", "pilha": 1, "slot": "cabeca",
                          "defesa": 4},
    "armadura_diamante": {"nome": "Armadura de diamante", "tipo": "armadura", "pilha": 1, "slot": "corpo",
                          "defesa": 6},
}
for _tier, _p in PODER.items():
    ITENS_V5[f"pa_{_tier}"] = {"nome": f"Pá de {NOME_TIER[_tier]}", "tipo": "ferramenta", "pilha": 1,
                               "slot": "ferramenta", "ferramenta": ("pa", _p),
                               "desc": "Cava o chão (terra/areia) e abre buracos para descer"}

# ajustes nos itens antigos
AJUSTES = {
    "madeira": {"nome": "Tora de madeira", "tipo": "construcao", "objeto": "bloco_tora",
                "desc": "Bloco. Vira 4 tábuas na grade de criação"},
    "pedra": {"nome": "Pedregulho", "tipo": "construcao", "objeto": "bloco_pedregulho",
              "desc": "Bloco. Sai das pedras. No forno vira pedra lisa"},
    "minerio_ferro": {"desc": "Cavernas e montanhas (picareta de pedra). Derreta no forno"},
    "ferro": {"desc": "Minério de ferro derretido no forno"},
    "carvao": {"desc": "Minério das cavernas (ou madeira no forno). Ótimo combustível"},
    "tocha": {"desc": "Ilumina. Monstros não nascem perto da luz"},
    "forno": {"desc": "Entrada + combustível = saída (minérios, areia, comida...)"},
    "bancada": {"desc": "Grade de criação 3x3 (E ou botão direito)"},
    "picareta_madeira": {"desc": "Quebra pedra e minério de carvão"},
    "picareta_pedra": {"desc": "Quebra minério de ferro"},
    "picareta_ferro": {"desc": "Quebra ouro, cristal e diamante"},
}

# durabilidade (usos)
DURABILIDADE = {"vara_pesca": 65, "lanca": 150, "arco": 190, "espada_rubi": 1500,
                "capuz_couro": 80, "roupa_couro": 90, "capacete_ferro": 220, "armadura_ferro": 260,
                "capacete_diamante": 550, "armadura_diamante": 650}
for _tier, _d in DURABILIDADE_TIER.items():
    for _f in ("machado", "picareta", "pa", "espada"):
        DURABILIDADE[f"{_f}_{_tier}"] = _d


# ===============================================================
# Objetos (blocos)
# "bloco": True = cubo cheio (sprite com face da frente, colisão do tile todo)
# ===============================================================
def _bloco(vida, ferramenta, drops, poder_min=0, **extra):
    d = {"vida": vida, "ferramenta": ferramenta, "drops": drops, "solido": True, "bloco": True, "altura": 4}
    if poder_min:
        d["poder_min"] = poder_min
    d.update(extra)
    return d


OBJETOS_V5 = {
    "bloco_terra":      _bloco(3, "pa", [("terra", 1)]),
    "bloco_areia":      _bloco(3, "pa", [("areia", 1)]),
    "bloco_pedra":      _bloco(8, "picareta", [("pedra", 1)], poder_min=2),
    "bloco_pedregulho": _bloco(8, "picareta", [("pedra", 1)], poder_min=2),
    "bloco_pedra_lisa": _bloco(8, "picareta", [("pedra_lisa", 1)], poder_min=2),
    "bloco_tora":       _bloco(5, "machado", [("madeira", 1)]),
    "bloco_tabuas":     _bloco(4, "machado", [("tabuas", 1)]),
    "bloco_vidro":      _bloco(1, None, [("vidro", 1)]),
    "min_carvao":       _bloco(9, "picareta", [("carvao", 1)], poder_min=2, xp=1),
    "min_ferro":        _bloco(11, "picareta", [("minerio_ferro", 1)], poder_min=3, xp=1),
    "min_ouro":         _bloco(11, "picareta", [("minerio_ouro", 1)], poder_min=5, xp=2),
    "min_cristal":      _bloco(11, "picareta", [("cristal", 4)], poder_min=5, xp=3),
    "min_diamante":     _bloco(14, "picareta", [("diamante", 1)], poder_min=5, xp=6),
    "lampada":          _bloco(2, None, [("lampada", 1)], construcao=True),
    "escada":   {"vida": 3, "ferramenta": "machado", "drops": [("escada", 1)], "solido": False,
                 "construcao": True, "altura": 2},
    "buraco":   {"vida": 99, "drops": [], "solido": False, "construcao": True},
}
NOMES_V5 = {
    "bloco_terra": "Terra", "bloco_areia": "Areia", "bloco_pedra": "Pedra", "bloco_pedregulho": "Pedregulho",
    "bloco_pedra_lisa": "Pedra lisa", "bloco_tora": "Tora", "bloco_tabuas": "Tábuas", "bloco_vidro": "Vidro",
    "min_carvao": "Minério de carvão", "min_ferro": "Minério de ferro", "min_ouro": "Minério de ouro",
    "min_cristal": "Minério de cristal", "min_diamante": "Minério de diamante",
    "lampada": "Lâmpada de cristal", "escada": "Escada de mão", "buraco": "Buraco",
}
TIPOS_BLOCO = set(OBJETOS_V5) - {"escada", "buraco"}
MINERIOS = ("min_carvao", "min_ferro", "min_ouro", "min_cristal", "min_diamante")
RAIO_LUZ_LAMPADA = 60

# o que cavar o CHÃO solta (tipo de chão -> (item, vida, poder_min))
# (preenchido em camadas.py, que conhece os números dos tipos de chão)


# ===============================================================
# Forno
# ===============================================================
FUNDICAO = {"minerio_ferro": "ferro", "minerio_ouro": "ouro", "areia": "vidro", "pedra": "pedra_lisa",
            "madeira": "carvao", "carne_crua": "carne_assada", "peixe": "peixe_assado"}
COMBUSTIVEL = {"carvao": 80.0, "madeira": 15.0, "tabuas": 15.0, "graveto": 5.0, "fibra": 4.0,
               "escada": 8.0, "bancada": 15.0, "bau": 15.0}
TEMPO_FUNDIR = 8.0


# ===============================================================
# Receitas com forma
# Letras: cada letra é um item (CHAVES). Espaço = vazio.
# Formas até 2x2 dão para fazer no inventário; maiores precisam da bancada.
# ===============================================================
CHAVES = {"T": "tabuas", "G": "graveto", "P": "pedra", "F": "ferro", "D": "diamante", "O": "ouro",
          "C": "couro", "B": "fibra", "M": "madeira", "K": "carvao", "A": "areia", "V": "vidro",
          "X": "cristal", "R": "trigo", "L": "la", "S": "osso"}
LETRA_TIER = {"madeira": "T", "pedra": "P", "ferro": "F", "diamante": "D"}


def _rc(item, forma, categoria, qtd=1, **extra):
    d = {"item": item, "forma": forma, "categoria": categoria}
    if qtd != 1:
        d["qtd"] = qtd
    d.update(extra)
    return d


def receitas_v5():
    r = []
    # Ferramentas
    for tier, x in LETRA_TIER.items():
        r.append(_rc(f"picareta_{tier}", [x * 3, " G ", " G "], "Ferramentas"))
        r.append(_rc(f"machado_{tier}", [x * 2, x + "G", " G"], "Ferramentas"))
        r.append(_rc(f"pa_{tier}", [x, "G", "G"], "Ferramentas"))
    r.append(_rc("vara_pesca", ["  G", " GB", "G B"], "Ferramentas"))
    r.append(_rc("cantil", [" B ", "C C", " C "], "Ferramentas"))
    # Armas
    for tier, x in LETRA_TIER.items():
        r.append(_rc(f"espada_{tier}", [x, x, "G"], "Armas"))
    r.append(_rc("lanca", ["  P", " G ", "G  "], "Armas"))
    r.append(_rc("arco", [" GB", "G B", " GB"], "Armas"))
    r.append(_rc("flecha", ["P", "G", "B"], "Armas", qtd=4))
    # Armaduras
    r.append(_rc("capuz_couro", ["CCC", "C C"], "Armaduras"))
    r.append(_rc("roupa_couro", ["C C", "CCC", "CCC"], "Armaduras"))
    r.append(_rc("capacete_ferro", ["FFF", "F F"], "Armaduras"))
    r.append(_rc("armadura_ferro", ["F F", "FFF", "FFF"], "Armaduras"))
    r.append(_rc("capacete_diamante", ["DDD", "D D"], "Armaduras"))
    r.append(_rc("armadura_diamante", ["D D", "DDD", "DDD"], "Armaduras"))
    # Blocos
    r.append(_rc("tabuas", ["M"], "Blocos", qtd=4))
    r.append(_rc("graveto", ["T", "T"], "Blocos", qtd=4))
    r.append(_rc("graveto", ["S"], "Blocos", qtd=2))
    r.append(_rc("tocha", ["K", "G"], "Blocos", qtd=4))
    r.append(_rc("tocha", ["B", "G"], "Blocos", qtd=2))
    r.append(_rc("escada", ["G G", "GGG", "G G"], "Blocos", qtd=3))
    r.append(_rc("piso", ["TTT"], "Blocos", qtd=3))
    r.append(_rc("lampada", [" X ", "XVX", " X "], "Blocos"))
    # Móveis
    r.append(_rc("bancada", ["TT", "TT"], "Móveis"))
    r.append(_rc("fogueira", [" G ", "GMG", "PPP"], "Móveis"))
    r.append(_rc("forno", ["PPP", "P P", "PPP"], "Móveis"))
    r.append(_rc("bau", ["TTT", "T T", "TTT"], "Móveis"))
    r.append(_rc("cama", ["LLL", "TTT"], "Móveis"))
    r.append(_rc("cama", ["CCC", "TTT"], "Móveis"))
    # Comida
    r.append(_rc("pao", ["RRR"], "Comida"))
    r.append({"item": "sopa", "sem_forma": ["carne_crua", "frutas", "frutas"], "categoria": "Comida"})
    r.append({"item": "carne_assada", "custo": {"carne_crua": 1}, "categoria": "Comida", "estacao": "fogueira"})
    r.append({"item": "peixe_assado", "custo": {"peixe": 1}, "categoria": "Comida", "estacao": "fogueira"})
    # Materiais
    r.append(_rc("moeda_ouro", ["O"], "Materiais", qtd=4))
    return r


def preparar_receita(rc):
    """Completa custo, tamanho e estação a partir da forma."""
    if "forma" in rc:
        forma = rc["forma"]
        custo = {}
        for linha in forma:
            for letra in linha:
                if letra != " ":
                    item = CHAVES[letra]
                    custo[item] = custo.get(item, 0) + 1
        rc["custo"] = custo
        rc["largura"] = max(len(l) for l in forma)
        rc["altura"] = len(forma)
        if rc["largura"] > 2 or rc["altura"] > 2:
            rc["estacao"] = "bancada"
    elif "sem_forma" in rc:
        custo = {}
        for item in rc["sem_forma"]:
            custo[item] = custo.get(item, 0) + 1
        rc["custo"] = custo
        if len(rc["sem_forma"]) > 4:
            rc["estacao"] = "bancada"
    return rc


# ===============================================================
# Criaturas novas
# ===============================================================
CRIATURAS_V5 = {
    "vaca":    {"nome": "Vaca", "vida": 6, "velocidade": 20, "comportamento": "passivo",
                "drops": [("carne_crua", 2), ("couro", 1)], "xp": 2},
    "porco":   {"nome": "Porco", "vida": 5, "velocidade": 22, "comportamento": "passivo",
                "drops": [("carne_crua", 2)], "xp": 2},
    "ovelha":  {"nome": "Ovelha", "vida": 5, "velocidade": 21, "comportamento": "passivo",
                "drops": [("carne_crua", 1), ("la", 2)], "xp": 2},
    "zumbi":   {"nome": "Zumbi", "vida": 10, "velocidade": 26, "comportamento": "monstro",
                "dano": 9, "alcance": 150, "noturno": True, "queima_sol": True,
                "drops": [("carne_podre", 1)], "xp": 5},
    "esqueleto_arq": {"nome": "Esqueleto", "vida": 8, "velocidade": 30, "comportamento": "monstro",
                      "dano": 7, "alcance": 170, "noturno": True, "queima_sol": True, "arqueiro": True,
                      "drops": [("flecha", 2), ("osso", 1)], "xp": 5},
    "explosivo": {"nome": "Explosivo", "vida": 8, "velocidade": 28, "comportamento": "monstro",
                  "dano": 0, "alcance": 140, "noturno": True, "explode": True,
                  "drops": [("polvora", 1)], "xp": 5},
}
XP_CRIATURA_PADRAO = {"passivo": 1, "predador": 3, "monstro": 4}

# monstros das cavernas por camada (quanto mais fundo, mais perigoso)
MONSTROS_CAVERNA = {
    -1: ["zumbi", "aranha", "slime", "esqueleto_arq"],
    -2: ["zumbi", "aranha", "esqueleto_arq", "explosivo"],
    -3: ["zumbi", "esqueleto_arq", "explosivo", "aranha"],
    -4: ["esqueleto_arq", "explosivo", "zumbi", "aranha"],
}


def registrar():
    for nome, d in AJUSTES.items():
        if nome in ITENS:
            ITENS[nome].update(d)
    for nome, d in ITENS_V5.items():
        ITENS[nome] = d
    for nome, usos in DURABILIDADE.items():
        if nome in ITENS:
            ITENS[nome]["durabilidade"] = usos
    for tier, dano in DANO_ESPADA.items():
        ITENS[f"espada_{tier}"]["dano"] = dano
    OBJETOS.update(OBJETOS_V5)
    NOMES_OBJETOS.update(NOMES_V5)
    # pedras e minério de ferro da superfície continuam iguais; árvores dão toras
    CRIATURAS.update(CRIATURAS_V5)
    # receitas: as com forma substituem as antigas do mesmo item
    novas = [preparar_receita(rc) for rc in receitas_v5()]
    feitos = {rc["item"] for rc in novas}
    antigas = [rc for rc in RECEITAS if rc["item"] not in feitos and rc["item"] not in
               ("parede_madeira", "parede_pedra", "carvao", "ferro")]
    RECEITAS[:] = novas + antigas
    CATEGORIAS[:] = ["Ferramentas", "Armas", "Armaduras", "Blocos", "Móveis", "Comida", "Materiais"]
    for rc in RECEITAS:
        if rc.get("categoria") not in CATEGORIAS:
            rc["categoria"] = "Materiais"
    # biomas: bichos novos de dia e monstros à noite
    extras_dia = {"planicie": ["vaca", "porco", "ovelha"], "floresta": ["porco"], "pantano": ["porco"],
                  "neve": ["ovelha"], "montanha": ["ovelha"], "deserto": []}
    noturnos = {"planicie": ["zumbi", "esqueleto_arq", "explosivo", "aranha", "slime"],
                "floresta": ["zumbi", "esqueleto_arq", "aranha", "explosivo"],
                "deserto": ["escorpiao", "zumbi", "esqueleto_arq"],
                "pantano": ["slime", "aranha", "zumbi"],
                "neve": ["zumbi", "esqueleto_arq", "slime"],
                "montanha": ["aranha", "esqueleto_arq", "explosivo"]}
    for b, info in BIOMAS.items():
        for a in extras_dia.get(b, []):
            if a not in info["animais"]:
                info["animais"].append(a)
        if b in noturnos:
            info["noturnos"] = noturnos[b]
    mont = BIOMAS["montanha"]["recursos"]
    if not any(t == "min_carvao" for t, _ in mont):
        mont.append(("min_carvao", 0.03))
    BIOMAS["caverna"] = {"nome": "Caverna", "agua": 0.0, "recursos": [], "animais": [], "predadores": [],
                         "noturnos": MONSTROS_CAVERNA[-1]}


def durabilidade_max(item):
    return ITENS.get(item, {}).get("durabilidade")


registrar()
