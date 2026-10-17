# -*- coding: utf-8 -*-
"""
salvar.py - Salva e carrega o jogo em JSON (save.json).

O chão nunca é salvo: ele é gerado de novo pela SEMENTE.
Só vão para o arquivo os chunks que mudaram (recursos quebrados,
construções, itens no chão), o jogador, o relógio e o clima.
"""
import json
import os

from config import ARQUIVO_SAVE

VERSAO_SAVE = 4   # v0.4: estações, baús, cama, minimapa (lê saves da v0.3)
VERSOES_ACEITAS = (3, 4)


def salvar_jogo(jogo, caminho=ARQUIVO_SAVE):
    dados = {
        "versao": VERSAO_SAVE,
        "semente": jogo.mundo.semente,
        "tempo": jogo.tempo,
        "dia": jogo.dia,
        "derrotados": jogo.derrotados,
        "clima": jogo.clima.para_dict(),
        "jogador": jogo.jogador.para_dict(),
        "chunks": jogo.mundo.dados_save(),
    }
    if hasattr(jogo, "dados_extras"):
        dados.update(jogo.dados_extras())
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(temporario, caminho)


def carregar_jogo(caminho=ARQUIVO_SAVE):
    """Retorna (dados, erro). dados = None se não der para carregar."""
    if not os.path.exists(caminho):
        return None, "Nenhum jogo salvo encontrado"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return None, "O arquivo de save está estragado"
    if dados.get("versao") not in VERSOES_ACEITAS:
        return None, "Save de versão antiga (o mundo mudou na v0.3)"
    return dados, ""


def existe_save(caminho=ARQUIVO_SAVE):
    return os.path.exists(caminho)
