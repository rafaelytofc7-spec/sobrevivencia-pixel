# -*- coding: utf-8 -*-
"""
ruido.py - Ruído determinístico (value noise) em Python puro.

"Determinístico" quer dizer: a mesma semente SEMPRE gera os mesmos números,
em qualquer computador. É isso que faz a mesma semente gerar o mesmo mundo.
"""
import math
import zlib


def _hash(ix, iy, semente):
    """Transforma uma coordenada inteira em um número 'aleatório' fixo entre 0 e 1."""
    v = (ix * 374761393 + iy * 668265263 + semente * 982451653) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    v ^= v >> 16
    return (v & 0xFFFF) / 65535.0


def ruido(x, y, semente):
    """Ruído suave: interpola os valores dos 4 cantos do quadrado."""
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    fx = fx * fx * (3 - 2 * fx)   # curva suave (smoothstep)
    fy = fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy, semente)
    b = _hash(ix + 1, iy, semente)
    c = _hash(ix, iy + 1, semente)
    d = _hash(ix + 1, iy + 1, semente)
    cima = a + (b - a) * fx
    return cima + ((c + (d - c) * fx) - cima) * fy


def fractal(x, y, semente, oitavas=3):
    """Soma camadas de ruído (formas grandes + detalhes). Resultado ~0..1."""
    total = 0.0
    amp = 1.0
    freq = 1.0
    soma = 0.0
    for i in range(oitavas):
        total += ruido(x * freq + i * 17.3, y * freq - i * 9.1, semente + i * 31) * amp
        soma += amp
        amp *= 0.5
        freq *= 2.0
    return total / soma


def esticar(v, forca=2.0):
    """Aumenta o contraste (o ruído fractal fica muito concentrado perto de 0,5)."""
    v = (v - 0.5) * forca + 0.5
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def semente_de_texto(texto):
    """
    Converte o que o jogador digitou em um número de semente.
    Números viram eles mesmos; palavras viram um número fixo (CRC32).
    """
    texto = texto.strip()
    if not texto:
        return None
    if texto.lstrip("-").isdigit():
        return int(texto) % 2_147_483_647
    return zlib.crc32(texto.encode("utf-8")) % 2_147_483_647


def numero_chunk(semente, cx, cy):
    """Número fixo para cada chunk (usado para sortear árvores, animais...)."""
    return (semente * 73856093 ^ cx * 19349663 ^ cy * 83492791) & 0x7FFFFFFF
