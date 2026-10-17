#!/usr/bin/env bash
# criar_release.sh - (no box) envia o código ao GitHub e cria a release com o .zip do Windows.
# O Atualizar.exe do Rafael baixa essa release sozinho na próxima vez que ele abrir o jogo.
#   uso: ferramentas/criar_release.sh 0.4.1 "Notas da versão (opcional)"
set -euo pipefail
cd "$(dirname "$0")/.."
V="${1:?uso: criar_release.sh X.Y.Z [notas]}"
NOTAS="${2:-Sobrevivência Pixel v$V}"
REPO="rafaelytofc7-spec/sobrevivencia-pixel"
ZIP="/workspace/releases/SobrevivenciaPixel-v$V-windows.zip"
[ -f "$ZIP" ] || { echo "falta $ZIP (compile no PC e traga com CopyToBox)"; exit 1; }
grep -q "VERSAO = \"$V\"" versao.py || { echo "versao.py não está em $V"; exit 1; }
unzip -l "$ZIP" 2>/dev/null | grep -q "SobrevivenciaPixel.exe" || python3 - "$ZIP" <<'P'
import sys, zipfile
nomes = zipfile.ZipFile(sys.argv[1]).namelist()
assert any(n.replace("\\", "/").endswith("jogo/SobrevivenciaPixel.exe") for n in nomes), "zip sem jogo/SobrevivenciaPixel.exe"
assert any(n.replace("\\", "/").endswith("version.txt") for n in nomes), "zip sem version.txt"
P
if ! git rev-parse "v$V" >/dev/null 2>&1; then
  git tag -a "v$V" -m "Sobrevivência Pixel v$V"
fi
git push origin master
git push origin "v$V"
gh release create "v$V" "$ZIP" --repo "$REPO" --title "Sobrevivência Pixel v$V" --notes "$NOTAS" --latest
echo "OK: https://github.com/$REPO/releases/tag/v$V"
