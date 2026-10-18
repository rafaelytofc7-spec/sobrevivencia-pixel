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


# ---------------------------------------------------------------
# Ruído 3D (v0.5): usado nas cavernas. O "z" é a camada (profundidade),
# então as cavernas de camadas vizinhas se parecem (túneis que continuam).
# ---------------------------------------------------------------
def _hash3(ix, iy, iz, semente):
    v = (ix * 374761393 + iy * 668265263 + iz * 1440670441 + semente * 982451653) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    v ^= v >> 16
    return (v & 0xFFFF) / 65535.0


def ruido3(x, y, z, semente):
    """Value noise 3D: interpola os 8 cantos do cubo."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    fz = fz * fz * (3 - 2 * fz)
    h = _hash3
    a = h(ix, iy, iz, semente)
    b = h(ix + 1, iy, iz, semente)
    c = h(ix, iy + 1, iz, semente)
    d = h(ix + 1, iy + 1, iz, semente)
    e = h(ix, iy, iz + 1, semente)
    f = h(ix + 1, iy, iz + 1, semente)
    g = h(ix, iy + 1, iz + 1, semente)
    k = h(ix + 1, iy + 1, iz + 1, semente)
    ab = a + (b - a) * fx
    cd = c + (d - c) * fx
    ef = e + (f - e) * fx
    gk = g + (k - g) * fx
    baixo = ab + (cd - ab) * fy
    cima = ef + (gk - ef) * fy
    return baixo + (cima - baixo) * fz


def fractal3(x, y, z, semente, oitavas=2):
    total = soma = 0.0
    amp = freq = 1.0
    for i in range(oitavas):
        total += ruido3(x * freq + i * 17.3, y * freq - i * 9.1, z * freq + i * 5.7, semente + i * 31) * amp
        soma += amp
        amp *= 0.5
        freq *= 2.0
    return total / soma


# ---------------------------------------------------------------
# Ruído em grade (versão web): calcula o MESMO fractal() para uma grade
# inteira de blocos de uma vez, reaproveitando os cantos (hash) entre
# blocos vizinhos. Dá exatamente os mesmos números que fractal(x/div, y/div),
# só que bem mais rápido (importante no navegador do celular).
# ---------------------------------------------------------------
def fractal_grade(xs, ys, div, semente, oitavas=3):
    """Lista de linhas: resultado[j][i] == fractal(xs[i] / div, ys[j] / div, semente, oitavas)."""
    floor = math.floor
    h = _hash
    total = [[0.0] * len(xs) for _ in ys]
    amp = 1.0
    freq = 1.0
    soma = 0.0
    for o in range(oitavas):
        s = semente + o * 31
        dx = o * 17.3
        dy = o * 9.1
        colunas = []
        for x in xs:
            px = (x / div) * freq + dx
            ix = floor(px)
            fx = px - ix
            colunas.append((ix, fx * fx * (3 - 2 * fx)))
        cantos = {}
        for j, y in enumerate(ys):
            py = (y / div) * freq - dy
            iy = floor(py)
            fy = py - iy
            fy = fy * fy * (3 - 2 * fy)
            linha = total[j]
            for i, (ix, fx) in enumerate(colunas):
                c4 = cantos.get((ix, iy))
                if c4 is None:
                    c4 = cantos[(ix, iy)] = (h(ix, iy, s), h(ix + 1, iy, s), h(ix, iy + 1, s), h(ix + 1, iy + 1, s))
                a, b, c, d = c4
                cima = a + (b - a) * fx
                linha[i] += (cima + ((c + (d - c) * fx) - cima) * fy) * amp
        soma += amp
        amp *= 0.5
        freq *= 2.0
    return [[t / soma for t in linha] for linha in total]
