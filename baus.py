# -*- coding: utf-8 -*-
"""
baus.py - Baús de tesouro: o que tem dentro depende do BIOMA e do NÍVEL
do lugar (1 = ruína/vila/baú perdido, 2 = cidadela/castelo/masmorra,
3 = tesouro do chefe). O conteúdo é sorteado pela semente + posição do baú,
então o mesmo baú sempre tem a mesma coisa. Baús abertos ficam no save.
"""
import random

from dados import ITENS
from estruturas import numero

# (item, mínimo, máximo, peso)
COMUM = [("madeira", 3, 8, 3), ("pedra", 3, 8, 3), ("fibra", 2, 6, 2), ("frutas", 2, 5, 3),
         ("pao", 1, 3, 3), ("moeda_ouro", 1, 3, 4), ("tocha", 2, 5, 2), ("couro", 1, 3, 2)]
MEDIO = [("ferro", 1, 4, 3), ("moeda_ouro", 3, 7, 5), ("pocao_vida", 1, 2, 3), ("carne_assada", 2, 4, 2),
         ("espada_pedra", 1, 1, 1), ("picareta_pedra", 1, 1, 1), ("capuz_couro", 1, 1, 1),
         ("roupa_couro", 1, 1, 1), ("cantil_cheio", 1, 1, 1)]
RARO = [("moeda_ouro", 8, 15, 5), ("ferro", 3, 6, 3), ("pocao_vida", 2, 3, 3), ("espada_ferro", 1, 1, 2),
        ("capacete_ferro", 1, 1, 2), ("armadura_ferro", 1, 1, 1), ("picareta_ferro", 1, 1, 1),
        ("machado_ferro", 1, 1, 1)]
POR_BIOMA = {
    "deserto":  [("cantil_cheio", 1, 1, 3), ("moeda_ouro", 2, 5, 3), ("couro", 2, 4, 2)],
    "neve":     [("carne_assada", 2, 4, 3), ("roupa_couro", 1, 1, 1), ("capuz_couro", 1, 1, 1)],
    "floresta": [("madeira", 6, 12, 3), ("frutas", 3, 6, 2), ("vara_pesca", 1, 1, 1), ("machado_pedra", 1, 1, 1)],
    "pantano":  [("fibra", 5, 10, 3), ("pocao_vida", 1, 2, 2), ("peixe_assado", 2, 4, 2)],
    "montanha": [("minerio_ferro", 3, 6, 3), ("ferro", 1, 3, 2), ("picareta_pedra", 1, 1, 1)],
    "planicie": [("trigo", 3, 8, 3), ("pao", 2, 4, 2), ("carne_assada", 1, 3, 1)],
}
TABELAS = {1: [COMUM], 2: [COMUM, MEDIO], 3: [MEDIO, RARO, RARO]}
QUANTOS = {1: (2, 3), 2: (3, 4), 3: (4, 6)}


def _escolher(rng, lista):
    lista = [e for e in lista if e[0] in ITENS]
    total = sum(e[3] for e in lista)
    r = rng.uniform(0, total)
    for e in lista:
        r -= e[3]
        if r <= 0:
            return e
    return lista[-1]


def conteudo(semente, ident, bioma, nivel):
    """Lista [(item, quantidade)] do baú (sempre a mesma para o mesmo baú)."""
    rng = random.Random(numero(semente, "bau", ident))
    nivel = max(1, min(3, nivel))
    tabelas = TABELAS[nivel] + [POR_BIOMA.get(bioma, COMUM)]
    total = {}
    quantos = rng.randint(*QUANTOS[nivel])
    for _ in range(quantos * 4):              # itens diferentes (tenta algumas vezes)
        if len(total) >= quantos:
            break
        item, a, b, _ = _escolher(rng, rng.choice(tabelas))
        if item not in total:
            total[item] = rng.randint(a, b)
    if nivel == 3 and "moeda_ouro" not in total:
        total["moeda_ouro"] = rng.randint(5, 10)
    return sorted(total.items())
