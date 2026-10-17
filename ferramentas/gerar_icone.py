# -*- coding: utf-8 -*-
"""Gera o ícone do jogo (icone.ico e icone.png) por código, em pixel art 16x16.

Uso:  python ferramentas/gerar_icone.py
O .ico tem as imagens 16, 24, 32, 48, 64, 128 e 256 (PNG dentro do ICO,
formato aceito pelo Windows Vista em diante). Só precisa do pygame.
"""
import io
import os
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, PASTA)
from icone import imagem16  # noqa: E402


def png_bytes(sup):
    buf = io.BytesIO()
    pygame.image.save(sup, buf, "png")
    return buf.getvalue()


def salvar_ico(caminho, base):
    tamanhos = [16, 24, 32, 48, 64, 128, 256]
    pngs = [png_bytes(pygame.transform.scale(base, (t, t))) for t in tamanhos]
    cab = struct.pack("<HHH", 0, 1, len(pngs))
    desloc = 6 + 16 * len(pngs)
    entradas = b""
    for t, dados in zip(tamanhos, pngs):
        entradas += struct.pack("<BBBBHHII", t % 256, t % 256, 0, 0, 1, 32, len(dados), desloc)
        desloc += len(dados)
    with open(caminho, "wb") as f:
        f.write(cab + entradas + b"".join(pngs))


def main():
    pygame.display.init()
    base = imagem16()
    saida = sys.argv[1] if len(sys.argv) > 1 else PASTA
    salvar_ico(os.path.join(saida, "icone.ico"), base)
    pygame.image.save(pygame.transform.scale(base, (256, 256)), os.path.join(saida, "icone.png"))
    print("icone.ico e icone.png gerados em", saida)


if __name__ == "__main__":
    main()
