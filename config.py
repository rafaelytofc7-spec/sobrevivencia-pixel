# -*- coding: utf-8 -*-
"""
config.py - Constantes e números de ajuste do jogo.
Itens, receitas, biomas e criaturas ficam em dados.py.
"""
import os
import sys

# ---------------------------------------------------------------
# Tela e pixel art
# ---------------------------------------------------------------
TILE = 16                 # cada bloco tem 16x16 pixels
ESCALA = 3                # cada pixel vira 3x3 na tela
LARGURA_INTERNA = 320
ALTURA_INTERNA = 200
WEB = sys.platform == "emscripten"      # rodando no navegador (pygbag)


def _largura_celular():
    """Versão web: tela mais larga nos celulares compridos (20:9), sem faixas pretas dos lados."""
    try:
        if os.environ.get("SP_LARGURA"):          # teste no PC
            return int(os.environ["SP_LARGURA"])
        if not WEB:
            return LARGURA_INTERNA
        import platform as _pf
        w, h = float(_pf.window.innerWidth), float(_pf.window.innerHeight)
        if w < h:
            w, h = h, w                           # em pé: conta como se já estivesse deitado
        return max(320, min(448, int(round(ALTURA_INTERNA * w / h / 8.0)) * 8))
    except Exception:                             # noqa: BLE001
        return LARGURA_INTERNA


LARGURA_INTERNA = _largura_celular()
LARGURA_TELA = LARGURA_INTERNA * ESCALA   # 960 no PC
ALTURA_TELA = ALTURA_INTERNA * ESCALA     # 600
FPS = 30 if WEB else 60
from versao import VERSAO
VERSAO_CURTA = VERSAO[:-2] if VERSAO.count(".") == 2 and VERSAO.endswith(".0") else VERSAO   # 0.4.0 -> 0.4
TITULO = "Sobrevivência Pixel - v" + VERSAO_CURTA

# ---------------------------------------------------------------
# Mundo infinito em chunks
# ---------------------------------------------------------------
TAMANHO_CHUNK = 16        # cada chunk tem 16x16 blocos
RAIO_CARREGAR = 2         # chunks carregados em volta do jogador (5x5)
RAIO_DESCARREGAR = 4      # chunks mais longe que isso são guardados e tirados da memória
CHUNKS_POR_QUADRO = 1 if WEB else 2     # quantos chunks novos gerar por quadro (evita travadas)

# Tipos de chão
AGUA_FUNDA = 0
AGUA_RASA = 1
LAMA = 2
AREIA = 3
GRAMA = 4
GRAMA_FLORESTA = 5
GRAMA_PANTANO = 6
NEVE = 7
ROCHA = 8
CHAO_AGUA = (AGUA_FUNDA, AGUA_RASA)
# v0.5: chão das cavernas (20 e 21 são da masmorra)
CAVERNA = 22
LAVA = 23

# Chão principal de cada bioma
CHAO_DO_BIOMA = {
    "planicie": GRAMA, "floresta": GRAMA_FLORESTA, "deserto": AREIA,
    "pantano": GRAMA_PANTANO, "neve": NEVE, "montanha": ROCHA,
}

# Nível da água: um bloco é água quando sua "altura" fica abaixo do nível.
NIVEL_AGUA_BASE = 0.33
PROFUNDIDADE_FUNDA = 0.05     # abaixo de nível - isso = água funda (não dá para andar)

# ---------------------------------------------------------------
# Clima
# ---------------------------------------------------------------
NIVEL_CHUVA = 0.035           # quanto o nível da água sobe na chuva
NIVEL_SECA = -0.045           # quanto desce na seca
VELOCIDADE_NIVEL = 0.0015     # quão rápido o nível muda (por segundo)

# ---------------------------------------------------------------
# Jogador
# ---------------------------------------------------------------
VELOCIDADE_JOGADOR = 62.0
VIDA_MAX = 100.0
FOME_MAX = 100.0
SEDE_MAX = 100.0
FOME_POR_SEGUNDO = 0.40
SEDE_POR_SEGUNDO = 0.55
DANO_FOME_SEDE = 2.0
REGENERACAO_VIDA = 0.6
ALCANCE_INTERACAO = 22        # tecla E
ALCANCE_MOUSE = 40            # ~2,5 blocos
TEMPO_ENTRE_GOLPES = 0.30
TEMPO_ENTRE_ATAQUES = 0.40
TEMPO_ENTRE_CONSTRUCOES = 0.15
RAIO_IMA_ITENS = 22
RAIO_PEGAR_ITENS = 6
RAIO_ESTACAO = 48             # distância para usar bancada/fogueira na criação

# movimento suave, corrida, rolamento e natação
ACELERACAO = 520.0            # pixels/s² para chegar na velocidade
ATRITO = 640.0                # pixels/s² para parar
MULT_CORRIDA = 1.6            # Shift
MULT_AGUA_RASA = 0.6
MULT_NADANDO = 0.45
ENERGIA_MAX = 100.0
GASTO_CORRIDA = 18.0          # energia por segundo correndo
GASTO_ROLAR = 22.0            # energia por rolamento
REGEN_ENERGIA = 16.0          # energia por segundo descansando
ESPERA_REGEN_ENERGIA = 0.8    # segundos sem gastar antes de recuperar
GASTO_NADO = 4.0              # energia por segundo nadando em água funda
DURACAO_ROLAR = 0.32
VELOCIDADE_ROLAR = 165.0
AR_MAX = 100.0
GASTO_AR = 5.0                # ar por segundo em água funda (~20 s)
REGEN_AR = 40.0
DANO_AFOGAR = 6.0             # vida por segundo sem ar
CANTO_DESLIZE = 5             # pixels de "correção de quina" ao bater em algo

# ---------------------------------------------------------------
# Objetos
# ---------------------------------------------------------------
TEMPO_REGENERAR_DANO = 5.0
TEMPO_FRUTAS_VOLTAR = 60.0
TEMPO_SUMIR_ITEM = 300.0
COMBUSTIVEL_INICIAL = 180.0
COMBUSTIVEL_POR_MADEIRA = 60.0
RAIO_LUZ_FOGUEIRA = 64
RAIO_LUZ_TOCHA = 44
RAIO_LUZ_TOCHA_MAO = 52
TAMANHO_BAU = 18

# ---------------------------------------------------------------
# Dia e noite
# ---------------------------------------------------------------
DURACAO_DIA = 240.0
DIAS_POR_ESTACAO = 3          # Primavera -> Verão -> Outono -> Inverno
HORA_INICIAL = 7.0
ESCURIDAO_MAXIMA = 0.85

# ---------------------------------------------------------------
# Ecossistema
# ---------------------------------------------------------------
MAX_PASSIVOS = 24
MAX_PREDADORES = 5
MAX_MONSTROS_BASE = 5         # +1 por dia, até 14
MAX_POR_CHUNK = 4             # animais da mesma espécie por chunk (para reproduzir)
TEMPO_ENTRE_SPAWNS = 2.0

# ---------------------------------------------------------------
# Inventário
# ---------------------------------------------------------------
TAMANHO_BARRA = 9             # barra rápida (teclas 1-9)
TAMANHO_INVENTARIO = 36       # 9 da barra + 27 da mochila

# ---------------------------------------------------------------
# Arquivo de salvamento
# ---------------------------------------------------------------
PASTA_JOGO = os.path.dirname(os.path.abspath(__file__))


def _pasta_dados():
    """Onde ficam save.json e controles.json.
    - Rodando pelo código (python main.py): na pasta do jogo, como antes.
    - Rodando pelo .exe (PyInstaller): em %APPDATA%\\SobrevivenciaPixel, assim as
      atualizações trocam os arquivos do jogo sem apagar o save."""
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        pasta = os.path.join(base, "SobrevivenciaPixel")
        try:
            os.makedirs(pasta, exist_ok=True)
            return pasta
        except OSError:
            return os.path.dirname(sys.executable)
    return PASTA_JOGO


PASTA_DADOS = _pasta_dados()
ARQUIVO_SAVE = os.path.join(PASTA_DADOS, "save.json")
ARQUIVO_CONTROLES = os.path.join(PASTA_DADOS, "controles.json")

# ---------------------------------------------------------------
# Cores da interface
# ---------------------------------------------------------------
COR_TEXTO = (245, 240, 225)
COR_SOMBRA = (20, 18, 28)
COR_PAINEL = (30, 28, 42)
COR_BORDA = (90, 84, 110)
COR_DESTAQUE = (250, 220, 90)
COR_VIDA = (214, 56, 56)
COR_FOME = (230, 150, 50)
COR_SEDE = (60, 140, 230)
COR_ENERGIA = (120, 210, 80)
COR_AR = (150, 220, 250)
