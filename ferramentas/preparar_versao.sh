#!/usr/bin/env bash
# preparar_versao.sh - (no box) muda a versão, faz commit + tag e gera o .zip do código
# para levar ao PC do Rafael e compilar lá.
#   uso: ferramentas/preparar_versao.sh 0.4.1
set -euo pipefail
cd "$(dirname "$0")/.."
V="${1:?uso: preparar_versao.sh X.Y.Z}"
[[ "$V" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "versão inválida: $V (use X.Y.Z)"; exit 1; }
git diff --quiet && git diff --cached --quiet || { echo "há mudanças sem commit; faça commit antes"; exit 1; }
if git rev-parse "v$V" >/dev/null 2>&1; then echo "a tag v$V já existe"; exit 1; fi
sed -i -E "s/^VERSAO = \"[^\"]+\"/VERSAO = \"$V\"/" versao.py
git add versao.py
git -c user.name="Grok Bot" -c user.email="grokbot@local" commit -qm "versão $V"
git tag -a "v$V" -m "Sobrevivência Pixel v$V"
mkdir -p /workspace/releases
git archive --format=zip -o "/workspace/releases/fonte-v$V.zip" HEAD
echo "OK: versão $V, tag v$V, código em /workspace/releases/fonte-v$V.zip"
