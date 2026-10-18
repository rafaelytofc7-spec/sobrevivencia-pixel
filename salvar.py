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
import armazenamento

VERSAO_SAVE = 5   # v0.5: blocos, camadas (cavernas), forno com espaços, durabilidade
VERSOES_ACEITAS = (5,)


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
        "estruturas": jogo.estruturas.para_dict(),   # [ESTRUTURAS] baús abertos, chefes, masmorra
    }
    if hasattr(jogo, "dados_extras"):
        dados.update(jogo.dados_extras())
    temporario = caminho + ".tmp"
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(temporario, caminho)
    armazenamento.espelhar("save", caminho)      # versão web: guarda no navegador


def carregar_jogo(caminho=ARQUIVO_SAVE):
    """Retorna (dados, erro). dados = None se não der para carregar."""
    armazenamento.restaurar("save", caminho)
    if not os.path.exists(caminho):
        return None, "Nenhum jogo salvo encontrado"
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        return None, "O arquivo de save está estragado"
    if dados.get("versao") not in VERSOES_ACEITAS:
        return None, ("Save de versão antiga (v0.4 ou antes): o mundo virou blocos na v0.5. "
                      "Comece um mundo novo")
    return dados, ""


def existe_save(caminho=ARQUIVO_SAVE):
    return os.path.exists(caminho) or (armazenamento.WEB and armazenamento.existe("save"))
