# build_windows.ps1 - Gera o pacote Windows do Sobrevivência Pixel.
#
# Uso (PowerShell, dentro da pasta do código):
#   powershell -ExecutionPolicy Bypass -File ferramentas\build_windows.ps1
# Resultado: dist_pacote\SobrevivenciaPixel-v<versão>-windows.zip
#   (Atualizar.exe + version.txt + LEIA-ME.txt + jogo\SobrevivenciaPixel.exe)
param(
    [string]$Python = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# versão (de versao.py)
$linha = Select-String -Path "versao.py" -Pattern 'VERSAO\s*=\s*"([^"]+)"' | Select-Object -First 1
if (-not $linha) { Write-Output "ERRO: não achei VERSAO em versao.py"; exit 1 }
$versao = $linha.Matches[0].Groups[1].Value
Write-Output "Versão: $versao"

& $Python -m pip install --quiet --disable-pip-version-check --upgrade pyinstaller pygame 2>&1 | Out-Null
& $Python ferramentas\gerar_icone.py

Remove-Item -Recurse -Force build, dist, dist_pacote -ErrorAction SilentlyContinue
# o jogo: uma pasta (abre rápido)
& $Python -m PyInstaller --noconfirm --clean --windowed --name SobrevivenciaPixel --icon icone.ico `
    --add-data "icone.ico;." --distpath dist --workpath build main.py 2>&1 | Select-Object -Last 3
if (-not (Test-Path "dist\SobrevivenciaPixel\SobrevivenciaPixel.exe")) { Write-Output "ERRO: build do jogo falhou"; exit 1 }
# o lançador/atualizador: um arquivo só
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --name Atualizar --icon icone.ico `
    --add-data "icone.ico;." --distpath dist --workpath build atualizador.py 2>&1 | Select-Object -Last 3
if (-not (Test-Path "dist\Atualizar.exe")) { Write-Output "ERRO: build do atualizador falhou"; exit 1 }

$pacote = "dist_pacote\SobrevivenciaPixel"
New-Item -ItemType Directory -Force -Path $pacote | Out-Null
Copy-Item -Recurse "dist\SobrevivenciaPixel" "$pacote\jogo"
Copy-Item "dist\Atualizar.exe" "$pacote\Atualizar.exe"
[System.IO.File]::WriteAllText("$raiz\$pacote\version.txt", $versao)
$leia = @"
Sobrevivência Pixel v$versao

Abra o jogo pelo Atualizar.exe (ou pelo atalho da área de trabalho):
ele procura uma versão nova no GitHub, atualiza sozinho e abre o jogo.
Sem internet ele só abre o jogo.

Os saves e os controles ficam em %APPDATA%\SobrevivenciaPixel
(não somem quando o jogo atualiza).
"@
[System.IO.File]::WriteAllText("$raiz\$pacote\LEIA-ME.txt", $leia, [System.Text.Encoding]::UTF8)
$zip = "dist_pacote\SobrevivenciaPixel-v$versao-windows.zip"
# zip com barras "/" (padrão), feito pelo Python
& $Python -c "import os,sys,zipfile; r=sys.argv[1]; z=zipfile.ZipFile(sys.argv[2],'w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(d,f), os.path.relpath(os.path.join(d,f), r).replace(os.sep,'/')) for d,_,fs in os.walk(r) for f in fs]; z.close()" "$raiz\$pacote" "$raiz\$zip"
$tam = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Output "PRONTO: $raiz\$zip ($tam MB)"
