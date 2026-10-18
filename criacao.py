# -*- coding: utf-8 -*-
"""
criacao.py - Grade de criação (2x2 no inventário, 3x3 na bancada) e o forno.

Grade: lista de lado*lado espaços (None ou [item, qtd]). A receita é achada
pela FORMA (cortando as bordas vazias, então dá para montar em qualquer canto
da grade, e também espelhada). Receitas "sem_forma" só olham os itens.
"""
from dados import ITENS, RECEITAS
from blocos import CHAVES, FUNDICAO, COMBUSTIVEL, TEMPO_FUNDIR, durabilidade_max


def _recortar(grade, lado):
    """Matriz (linhas) com só a parte usada da grade. [] se vazia."""
    linhas = [[(grade[j * lado + i][0] if grade[j * lado + i] else None) for i in range(lado)]
              for j in range(lado)]
    usadas_y = [j for j in range(lado) if any(linhas[j])]
    usadas_x = [i for i in range(lado) if any(linhas[j][i] for j in range(lado))]
    if not usadas_y:
        return []
    return [linhas[j][usadas_x[0]:usadas_x[-1] + 1] for j in range(usadas_y[0], usadas_y[-1] + 1)]


def _matriz_forma(forma):
    larg = max(len(l) for l in forma)
    return [[(CHAVES[c] if c != " " else None) for c in l.ljust(larg)] for l in forma]


_CACHE_FORMAS = {}


def _formas(rc):
    chave = id(rc)
    if chave not in _CACHE_FORMAS:
        m = _matriz_forma(rc["forma"])
        _CACHE_FORMAS[chave] = (m, [list(reversed(l)) for l in m])
    return _CACHE_FORMAS[chave]


def casar(grade, lado):
    """Receita que a grade forma (ou None)."""
    m = _recortar(grade, lado)
    if not m:
        return None
    itens = sorted(x for l in m for x in l if x)
    for rc in RECEITAS:
        if "forma" in rc:
            if rc["altura"] != len(m) or rc["largura"] != len(m[0]) or rc["altura"] > lado or rc["largura"] > lado:
                continue
            normal, espelho = _formas(rc)
            if m == normal or m == espelho:
                return rc
        elif "sem_forma" in rc and len(rc["sem_forma"]) <= lado * lado:
            if sorted(rc["sem_forma"]) == itens:
                return rc
    return None


def resultado(grade, lado):
    """[item, qtd(, usos)] que sai da grade (ou None)."""
    rc = casar(grade, lado)
    if rc is None:
        return None
    return nova_pilha(rc["item"], rc.get("qtd", 1))


def nova_pilha(item, qtd=1):
    usos = durabilidade_max(item)
    return [item, qtd, usos] if usos else [item, qtd]


def consumir(grade):
    """Tira 1 de cada espaço usado (depois de criar)."""
    for i, e in enumerate(grade):
        if e:
            e[1] -= 1
            if e[1] <= 0:
                grade[i] = None


def maximo_criavel(grade):
    """Quantas vezes dá para criar com o que está na grade (Shift+clique)."""
    usados = [e[1] for e in grade if e]
    return min(usados) if usados else 0


# ===============================================================
# Forno: conteudo = [entrada, combustível, saída]
# ===============================================================
def fundivel(item):
    return item in FUNDICAO


def combustivel(item):
    return item in COMBUSTIVEL


def atualizar_forno(obj, dt):
    """Queima combustível e derrete a entrada. Retorna True se produziu algo."""
    c = obj.conteudo
    entrada, comb, saida = c
    alvo = FUNDICAO.get(entrada[0]) if entrada else None
    pode = alvo is not None and (saida is None or (saida[0] == alvo and saida[1] < ITENS[alvo]["pilha"]))
    if obj.queima <= 0 and pode and comb and comb[0] in COMBUSTIVEL:
        obj.queima = obj.queima_max = COMBUSTIVEL[comb[0]]
        comb[1] -= 1
        if comb[1] <= 0:
            c[1] = None
    produziu = False
    if obj.queima > 0:
        obj.queima = max(0.0, obj.queima - dt)
        if pode:
            obj.progresso += dt
            if obj.progresso >= TEMPO_FUNDIR:
                obj.progresso = 0.0
                entrada[1] -= 1
                if entrada[1] <= 0:
                    c[0] = None
                if saida is None:
                    c[2] = [alvo, 1]
                else:
                    saida[1] += 1
                produziu = True
        else:
            obj.progresso = 0.0
    else:
        obj.progresso = max(0.0, obj.progresso - dt * 2)
    return produziu
