# -*- coding: utf-8 -*-
"""icone.py - Ícone do jogo em pixel art 16x16 (usado na janela e no .exe)."""
import pygame

# 16x16: céu ao entardecer, grama, uma árvore e uma fogueira
MAPA = [
    "KKKKKKKKKKKKKKKK",
    "KSSSSSSSSSSSSSSK",
    "KSSSSSSSSSSyySSK",
    "KSSSSSSSSSSyySSK",
    "KSSSGGGSSSSSSSSK",
    "KSSGGgGGSSSSSSSK",
    "KSGGgGGGGSSSSSSK",
    "KSGGGGGgGSSSSSSK",
    "KSSGGGGGSSSoSSSK",
    "KSSSSTTSSSSoOSSK",
    "KSSSSTTSSSoOYoSK",
    "KvvvvTTvvvoYYovK",
    "KvVvvTTvvvMMMMvK",
    "KvvvVvvvvVvvvVvK",
    "KVvvvvVvvvvVvvvK",
    "KKKKKKKKKKKKKKKK",
]
CORES = {
    "K": (24, 20, 34), "S": (112, 168, 222), "y": (255, 236, 140),
    "G": (58, 140, 66), "g": (110, 190, 90), "T": (110, 72, 40),
    "v": (86, 166, 70), "V": (64, 132, 56),
    "o": (240, 120, 40), "O": (255, 170, 60), "Y": (255, 236, 120), "M": (120, 82, 48),
}


def imagem16():
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, linha in enumerate(MAPA):
        for x, c in enumerate(linha):
            s.set_at((x, y), CORES[c])
    # cantos arredondados (transparentes)
    for (x, y) in ((0, 0), (15, 0), (0, 15), (15, 15)):
        s.set_at((x, y), (0, 0, 0, 0))
    return s
