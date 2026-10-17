# -*- coding: utf-8 -*-
"""
atualizador.py - Lançador do Sobrevivência Pixel (vira o Atualizar.exe).

Ao abrir:
  1. pergunta ao GitHub qual é a última versão publicada (Releases "latest");
  2. se for mais nova que a do arquivo version.txt, baixa o .zip da versão,
     troca a pasta "jogo" com segurança (a antiga só é apagada depois que a
     nova está no lugar; se der erro, volta a antiga);
  3. abre o jogo.
Sem internet (ou se o GitHub não responder) ele só abre o jogo.
Os saves e os controles ficam em %APPDATA%\\SobrevivenciaPixel, longe daqui,
então a atualização nunca mexe neles.

Pasta instalada:
  Atualizar.exe      <- este programa (o atalho da área de trabalho aponta para ele)
  version.txt        <- versão instalada, ex.: 0.4.0
  jogo\\SobrevivenciaPixel.exe (+ _internal\\)

Opções (para testes):  --nao-abrir   não abre o jogo no final
                        --api URL     usa outra URL no lugar da API do GitHub
Um arquivo atualizador.json na pasta também pode trocar "api" (testes).
"""
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile

REPO = "rafaelytofc7-spec/sobrevivencia-pixel"
API_PADRAO = f"https://api.github.com/repos/{REPO}/releases/latest"
NOME_EXE = "SobrevivenciaPixel.exe"
TITULO = "Sobrevivência Pixel"

if getattr(sys, "frozen", False):
    PASTA = os.path.dirname(os.path.abspath(sys.executable))
    RECURSOS = getattr(sys, "_MEIPASS", PASTA)
else:
    PASTA = os.path.dirname(os.path.abspath(__file__))
    RECURSOS = PASTA
PASTA_JOGO = os.path.join(PASTA, "jogo")
TEMP = os.path.join(PASTA, "_atualizacao")
LOG = os.path.join(PASTA, "atualizador.log")


def log(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def versao_tupla(texto):
    texto = (texto or "").strip().lstrip("vV")
    partes = []
    for p in texto.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        partes.append(int(num) if num else 0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def versao_local():
    try:
        with open(os.path.join(PASTA, "version.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"


def url_api():
    if "--api" in sys.argv:
        i = sys.argv.index("--api")
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    try:
        with open(os.path.join(PASTA, "atualizador.json"), encoding="utf-8") as f:
            return json.load(f).get("api", API_PADRAO)
    except (OSError, ValueError):
        return API_PADRAO


def pedir(url, timeout=6):
    req = urllib.request.Request(url, headers={"User-Agent": "SobrevivenciaPixel-Atualizador",
                                               "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout)


# ----------------------------------------------------------------------
# trabalho (roda numa thread; fala com a janela pela fila)
# ----------------------------------------------------------------------
def trabalhar(fila):
    def status(texto, prog=None):
        fila.put(("status", texto, prog))

    local = versao_local()
    status(f"Versão instalada: {local}\nProcurando atualização...")
    try:
        with pedir(url_api()) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except Exception as e:               # sem internet, GitHub fora, limite da API...
        log(f"sem verificar atualização: {e!r}")
        fila.put(("jogar", "Sem conexão com o GitHub. Abrindo o jogo..."))
        return
    remota = dados.get("tag_name", "")
    if versao_tupla(remota) <= versao_tupla(local):
        log(f"atualizado (local {local}, GitHub {remota})")
        fila.put(("jogar", f"Você já tem a versão mais nova ({local}). Abrindo o jogo..."))
        return
    assets = [a for a in dados.get("assets", []) if a.get("name", "").lower().endswith(".zip")]
    assets.sort(key=lambda a: "windows" not in a["name"].lower())
    if not assets:
        log(f"versão {remota} sem .zip")
        fila.put(("jogar", "A nova versão ainda não tem arquivo para baixar. Abrindo o jogo..."))
        return
    asset = assets[0]
    try:
        instalar(asset, remota, status)
    except Exception as e:
        log(f"falha ao atualizar: {e!r}")
        fila.put(("erro", f"Não deu para atualizar ({e}).\nAbrindo a versão instalada..."))
        return
    log(f"atualizado de {local} para {remota}")
    fila.put(("jogar", f"Atualizado para a versão {remota.lstrip('vV')}! Abrindo o jogo..."))


def instalar(asset, remota, status):
    shutil.rmtree(TEMP, ignore_errors=True)
    os.makedirs(TEMP, exist_ok=True)
    pacote = os.path.join(TEMP, "pacote.zip")
    total = asset.get("size") or 0
    status(f"Baixando a versão {remota.lstrip('vV')}...", 0.0)
    with pedir(asset["browser_download_url"], timeout=30) as r, open(pacote, "wb") as f:
        total = int(r.headers.get("Content-Length") or total or 0)
        baixado = 0
        while True:
            bloco = r.read(256 * 1024)
            if not bloco:
                break
            f.write(bloco)
            baixado += len(bloco)
            if total:
                mb = baixado / 1048576
                status(f"Baixando a versão {remota.lstrip('vV')}...  {mb:.1f} / {total / 1048576:.1f} MB",
                       baixado / total)
    if total and baixado < total:
        raise IOError("download incompleto")
    status("Conferindo o arquivo...", 1.0)
    novo = os.path.join(TEMP, "novo")
    with zipfile.ZipFile(pacote) as z:
        ruim = z.testzip()
        if ruim:
            raise IOError(f"arquivo estragado no zip: {ruim}")
        for nome in z.namelist():         # proteção contra caminhos fora da pasta
            destino = os.path.abspath(os.path.join(novo, nome))
            if not destino.startswith(os.path.abspath(novo) + os.sep) and destino != os.path.abspath(novo):
                raise IOError(f"caminho inválido no zip: {nome}")
        z.extractall(novo)
    # o zip pode ter uma pasta-raiz (ex.: SobrevivenciaPixel\...)
    raiz = novo
    if not os.path.isdir(os.path.join(raiz, "jogo")):
        subs = [os.path.join(novo, d) for d in os.listdir(novo) if os.path.isdir(os.path.join(novo, d))]
        if len(subs) == 1:
            raiz = subs[0]
    if not os.path.isfile(os.path.join(raiz, "jogo", NOME_EXE)):
        raise IOError("o zip não tem jogo\\" + NOME_EXE)

    status("Instalando...", 1.0)
    antigo = os.path.join(TEMP, "jogo_antigo")
    tinha = os.path.isdir(PASTA_JOGO)
    if tinha:
        for tentativa in range(10):       # se o jogo ainda estiver fechando, espera um pouco
            try:
                os.rename(PASTA_JOGO, antigo)
                break
            except OSError:
                if tentativa == 9:
                    raise IOError("feche o jogo antes de atualizar")
                time.sleep(0.5)
    try:
        shutil.move(os.path.join(raiz, "jogo"), PASTA_JOGO)
    except Exception:
        shutil.rmtree(PASTA_JOGO, ignore_errors=True)
        if tinha:
            os.rename(antigo, PASTA_JOGO)  # volta a versão antiga
        raise
    # arquivos soltos da raiz (version.txt, LEIA-ME...). O próprio Atualizar.exe
    # não pode ser sobrescrito enquanto roda: fica como .novo e é trocado ao sair.
    eu = os.path.basename(sys.executable).lower() if getattr(sys, "frozen", False) else ""
    for nome in os.listdir(raiz):
        origem = os.path.join(raiz, nome)
        if not os.path.isfile(origem) or nome.lower() == "version.txt":
            continue
        if nome.lower() == eu:
            shutil.copy2(origem, os.path.join(PASTA, nome + ".novo"))
            trocar_depois(nome)
        else:
            shutil.copy2(origem, os.path.join(PASTA, nome))
    shutil.copy2(os.path.join(raiz, "version.txt"), os.path.join(PASTA, "version.txt"))  # por último
    shutil.rmtree(TEMP, ignore_errors=True)


def trocar_depois(nome):
    """Troca o Atualizar.exe depois que este processo fechar."""
    if os.name != "nt":
        return
    cmd = (f'ping -n 4 127.0.0.1 >nul & move /y "{nome}.novo" "{nome}" >nul')
    subprocess.Popen(["cmd", "/c", cmd], cwd=PASTA, creationflags=0x08000000)   # sem janela


def abrir_jogo():
    exe = os.path.join(PASTA_JOGO, NOME_EXE)
    if not os.path.isfile(exe):
        return False
    if "--nao-abrir" in sys.argv:
        log("teste: jogo não aberto (--nao-abrir)")
        return True
    subprocess.Popen([exe], cwd=PASTA_JOGO)
    return True


# ----------------------------------------------------------------------
# janela
# ----------------------------------------------------------------------
def main():
    import tkinter as tk
    from tkinter import ttk

    raiz = tk.Tk()
    raiz.title(TITULO)
    raiz.resizable(False, False)
    raiz.configure(bg="#1e1c2a")
    try:
        raiz.iconbitmap(os.path.join(RECURSOS, "icone.ico"))
    except Exception:
        pass
    larg, alt = 440, 170
    raiz.geometry(f"{larg}x{alt}+{(raiz.winfo_screenwidth() - larg) // 2}+{(raiz.winfo_screenheight() - alt) // 2}")
    tk.Label(raiz, text=TITULO, font=("Segoe UI", 16, "bold"), fg="#ffe08a", bg="#1e1c2a").pack(pady=(14, 4))
    texto = tk.StringVar(value="Iniciando...")
    tk.Label(raiz, textvariable=texto, font=("Segoe UI", 10), fg="#f5f0e1", bg="#1e1c2a",
             justify="center").pack(pady=4)
    estilo = ttk.Style(raiz)
    try:
        estilo.theme_use("clam")
    except tk.TclError:
        pass
    estilo.configure("V.Horizontal.TProgressbar", troughcolor="#2e2b40", background="#78d250")
    barra = ttk.Progressbar(raiz, length=380, mode="indeterminate", style="V.Horizontal.TProgressbar")
    barra.pack(pady=10)
    barra.start(12)

    fila = queue.Queue()
    threading.Thread(target=trabalhar, args=(fila,), daemon=True).start()

    def terminar(msg, espera):
        texto.set(msg)
        barra.stop()
        barra.configure(mode="determinate", value=100)

        def abrir():
            if not abrir_jogo():
                texto.set("Não achei o jogo (jogo\\" + NOME_EXE + ").\nConecte-se à internet e abra de novo.")
                raiz.after(6000, raiz.destroy)
                return
            raiz.after(600, raiz.destroy)
        raiz.after(espera, abrir)

    def olhar():
        try:
            while True:
                item = fila.get_nowait()
                if item[0] == "status":
                    texto.set(item[1])
                    if item[2] is not None:
                        if str(barra.cget("mode")) != "determinate":
                            barra.stop()
                            barra.configure(mode="determinate", maximum=100)
                        barra.configure(value=item[2] * 100)
                elif item[0] == "jogar":
                    terminar(item[1], 700)
                    return
                elif item[0] == "erro":
                    terminar(item[1], 3500)
                    return
        except queue.Empty:
            pass
        raiz.after(80, olhar)

    raiz.after(80, olhar)
    raiz.mainloop()


if __name__ == "__main__":
    main()
