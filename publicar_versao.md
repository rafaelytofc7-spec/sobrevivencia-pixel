# Como publicar uma versão nova (para o bot)

O Rafael abre o jogo pelo atalho **Sobrevivência Pixel** na área de trabalho,
que aponta para `C:\Users\RAFAEL\Jogos\SobrevivenciaPixel\Atualizar.exe`.
O Atualizar.exe pergunta para a API do GitHub
(`https://api.github.com/repos/rafaelytofc7-spec/sobrevivencia-pixel/releases/latest`,
sem login), compara com `version.txt` e, se houver versão nova, baixa o `.zip`
da release, troca a pasta `jogo\` e abre o jogo. **Publicar uma release = atualizar
o jogo do Rafael.** Sem internet ele só abre o jogo.

Saves e controles: `%APPDATA%\SobrevivenciaPixel\` (save.json, controles.json).
Rodando pelo código (`python main.py`) eles continuam na pasta do código.

## Pasta instalada
```
C:\Users\RAFAEL\Jogos\SobrevivenciaPixel\
  Atualizar.exe        lançador/atualizador (tkinter, onefile)
  version.txt          versão instalada (ex.: 0.4.0)
  LEIA-ME.txt
  jogo\SobrevivenciaPixel.exe  (+ _internal\)   o jogo (PyInstaller, uma pasta)
  atualizador.log      registro do que o atualizador fez
```

## Passo a passo (versão X.Y.Z)

Máquina do Rafael: machineId `6776422c-60c0-4e07-9ca1-b3623714e027` (PowerShell).

1. **No box**, com tudo commitado em `/workspace/jogo-sobrevivencia` (master):
   ```
   ferramentas/preparar_versao.sh X.Y.Z
   ```
   Isso muda `versao.py`, faz commit, cria a tag `vX.Y.Z` e gera
   `/workspace/releases/fonte-vX.Y.Z.zip`. (Atualize também o README/ajuda se quiser.)
   Testes headless: `/workspace/jogo-testes/` (func5.py, soak5.py, shots5.py, smoke5.py...).

2. **Levar ao PC e compilar** (CopyFromBox + Shell com o machineId):
   - CopyFromBox `/workspace/releases/fonte-vX.Y.Z.zip` →
     `C:\Users\RAFAEL\Jogos\_build\fonte-vX.Y.Z.zip`
   - PowerShell (não use `$ErrorActionPreference='Stop'`; o PyInstaller escreve no stderr):
     ```
     $b="C:\Users\RAFAEL\Jogos\_build\sobrevivencia-pixel"
     Remove-Item -Recurse -Force $b -ErrorAction SilentlyContinue
     Expand-Archive "C:\Users\RAFAEL\Jogos\_build\fonte-vX.Y.Z.zip" -DestinationPath $b -Force
     powershell -ExecutionPolicy Bypass -File "$b\ferramentas\build_windows.ps1" 2>&1 | Select-String "PRONTO|ERRO"
     ```
     Gera `$b\dist_pacote\SobrevivenciaPixel-vX.Y.Z-windows.zip` (~24 MB):
     `Atualizar.exe`, `version.txt`, `LEIA-ME.txt`, `jogo\...`.
   - Teste rápido: `Start-Process "$b\dist_pacote\SobrevivenciaPixel\jogo\SobrevivenciaPixel.exe"`
     e veja `(Get-Process SobrevivenciaPixel).MainWindowTitle`; feche depois.

3. **Trazer o zip para o box**: CopyToBox
   `C:\Users\RAFAEL\Jogos\_build\sobrevivencia-pixel\dist_pacote\SobrevivenciaPixel-vX.Y.Z-windows.zip`
   → `/workspace/releases/SobrevivenciaPixel-vX.Y.Z-windows.zip`

4. **Publicar** (no box; precisa da aprovação do Rafael, é público):
   ```
   ferramentas/criar_release.sh X.Y.Z "o que mudou"
   ```
   (faz `git push` do master e da tag e `gh release create ... --latest` com o zip).

5. Pronto: na próxima vez que o Rafael abrir pelo atalho, o Atualizar.exe baixa e
   instala. Para conferir na hora: rode o Atualizar.exe e leia `atualizador.log`.

## Primeira publicação (uma vez só)
```
cd /workspace/jogo-sobrevivencia
gh repo create rafaelytofc7-spec/sobrevivencia-pixel --public --source . --remote origin \
   --description "Sobrevivência Pixel - jogo de sobrevivência 2D em pixel art (Python + pygame)"
git push -u origin master --tags
ferramentas/criar_release.sh 0.4.0 "Primeira versão com .exe e atualização automática"
```
(o zip `/workspace/releases/SobrevivenciaPixel-v0.4.0-windows.zip` já está no box;
a tag `v0.4.0` é criada pelo próprio criar_release.sh se não existir — veja abaixo.)

## Testar o atualizador sem publicar
No PC, copie uma instalação para uma pasta de teste, ponha `0.0.1` no `version.txt`,
sirva um `latest.json` falso com `python -m http.server 8799` e rode
`Atualizar.exe --api http://127.0.0.1:8799/latest.json --nao-abrir`.
Formato do latest.json (igual ao do GitHub):
`{"tag_name":"vX.Y.Z","assets":[{"name":"SobrevivenciaPixel-vX.Y.Z-windows.zip","size":N,"browser_download_url":"http://127.0.0.1:8799/pacote.zip"}]}`
Já existe um servidor de teste em `C:\Users\RAFAEL\Jogos\_build\servidor_teste\`.

## Detalhes do atualizador (`atualizador.py`)
- Compara versões como números (0.10.0 > 0.9.0). Tag pode ter "v".
- Pega o asset `.zip` (prefere nome com "windows").
- Baixa para `_atualizacao\`, testa o zip, bloqueia caminhos fora da pasta,
  renomeia `jogo\` → `_atualizacao\jogo_antigo`, coloca o novo; se falhar, volta o antigo.
  `version.txt` é copiado por último.
- O próprio `Atualizar.exe` novo vira `Atualizar.exe.novo` e um `cmd` escondido troca
  depois que ele fecha (tenta por ~60 s; se ficar pendente, a próxima abertura agenda de novo).
- GitHub 404 (sem release) / 403 (limite da API: 60 pedidos/hora por IP) / sem internet:
  abre o jogo instalado.
