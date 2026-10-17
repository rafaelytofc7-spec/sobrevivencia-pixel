# -*- coding: utf-8 -*-
"""
estacoes.py - As quatro estações do ano.

Primavera -> Verão -> Outono -> Inverno, cada uma dura DIAS_POR_ESTACAO dias.
Elas mudam:
  - as cores do mundo (folhas laranjas no outono, neve cobrindo tudo no inverno)
  - a temperatura (frio dá mais fome; calor dá mais sede)
  - o crescimento de frutas e plantações
  - a chance de chuva e de seca
  - os bichos (filhotes na primavera, mais lobos no inverno)
"""
from config import DIAS_POR_ESTACAO

ORDEM = ["primavera", "verao", "outono", "inverno"]
NOMES = {"primavera": "Primavera", "verao": "Verão", "outono": "Outono", "inverno": "Inverno"}

# quanto as frutas/plantações crescem (1 = normal, 0 = não crescem)
CRESCIMENTO = {"primavera": 1.6, "verao": 1.0, "outono": 0.7, "inverno": 0.0}
# pesos para sortear o próximo clima: (chuva, seca)
PESOS_CLIMA = {"primavera": (3.0, 0.4), "verao": (1.0, 2.0), "outono": (2.2, 0.8), "inverno": (2.0, 0.2)}
# temperatura: base por bioma + ajuste da estação
TEMP_BIOMA = {"neve": -6, "montanha": 3, "floresta": 14, "planicie": 17, "pantano": 19, "deserto": 31}
TEMP_ESTACAO = {"primavera": 0, "verao": 8, "outono": -3, "inverno": -13}
# bichos
FILHOTES = {"primavera": 0.5, "verao": 1.0, "outono": 1.2, "inverno": 3.0}      # multiplica o tempo de espera
PASSIVOS = {"primavera": 1.0, "verao": 1.0, "outono": 0.9, "inverno": 0.6}      # multiplica o limite
PREDADORES_EXTRA = {"primavera": 0, "verao": 0, "outono": 1, "inverno": 3}
FOME_LOBO = {"primavera": 1.0, "verao": 1.0, "outono": 1.1, "inverno": 1.35}    # alcance de caça


def estacao_do_dia(dia):
    return ORDEM[((dia - 1) // DIAS_POR_ESTACAO) % 4]


def dia_na_estacao(dia):
    return (dia - 1) % DIAS_POR_ESTACAO + 1


def temperatura(bioma, estacao, escuridao=0.0, chuva=0.0, perto_do_fogo=False, na_agua=False):
    """Temperatura em °C sentida pelo jogador."""
    t = TEMP_BIOMA.get(bioma, 15) + TEMP_ESTACAO[estacao]
    t -= 7 * escuridao                # noite esfria
    t -= 4 * chuva
    if na_agua:
        t -= 4
    if perto_do_fogo:
        t += 16
    return t


def efeito_temperatura(t):
    """Retorna (nome, multiplicador de fome, multiplicador de sede, dano por segundo sem roupa)."""
    if t < -5:
        return "Congelando", 1.8, 1.0, 0.5
    if t < 3:
        return "Frio", 1.5, 1.0, 0.0
    if t > 33:
        return "Muito quente", 1.0, 1.7, 0.0
    if t > 27:
        return "Quente", 1.0, 1.35, 0.0
    return "Agradável", 1.0, 1.0, 0.0
