# -*- coding: utf-8 -*-
"""
armazenamento.py - Guarda o save no navegador (versão web).

No navegador os arquivos somem quando a página fecha. Por isso, na versão
web, cada arquivo salvo (save.json, controles.json) também é copiado para o
localStorage do navegador (comprimido) e volta de lá quando o jogo abre.
No Windows estas funções não fazem nada.
"""
import base64
import os
import sys
import zlib

WEB = sys.platform == "emscripten"
PREFIXO = "sobrevivencia_pixel_"


def _local():
    import platform            # no pygbag, platform.window é o "window" do JavaScript
    return platform.window.localStorage


def gravar(chave, texto):
    if not WEB:
        return False
    try:
        z = base64.b64encode(zlib.compress(texto.encode("utf-8"), 6)).decode("ascii")
        _local().setItem(PREFIXO + chave, "z:" + z)
        return True
    except Exception as erro:                       # noqa: BLE001
        print("localStorage: não deu para gravar", chave, erro)
        return False


def ler(chave):
    if not WEB:
        return None
    try:
        v = _local().getItem(PREFIXO + chave)
    except Exception:                               # noqa: BLE001
        return None
    if v is None:
        return None
    v = str(v)
    if v in ("", "null", "undefined", "None"):
        return None
    try:
        if v.startswith("z:"):
            return zlib.decompress(base64.b64decode(v[2:])).decode("utf-8")
        return v
    except Exception:                               # noqa: BLE001
        return None


def existe(chave):
    return ler(chave) is not None


def espelhar(chave, caminho):
    """Arquivo -> navegador."""
    if not WEB:
        return
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            gravar(chave, f.read())
    except OSError:
        pass


def restaurar(chave, caminho):
    """Navegador -> arquivo (se o arquivo ainda não existe)."""
    if not WEB or os.path.exists(caminho):
        return
    texto = ler(chave)
    if texto is None:
        return
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
    except OSError:
        pass
