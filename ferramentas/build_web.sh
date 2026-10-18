#!/usr/bin/env bash
# build_web.sh - (no box) gera a versão web (celular) com pygbag em /tmp/sp_web/.../build/web
# e, com --publicar, copia para o branch gh-pages (GitHub Pages) e faz push.
#   uso: ferramentas/build_web.sh [--publicar]
# Precisa de: python com pygbag e pygame-ce (ex.: /workspace/.venv-web).
set -euo pipefail
cd "$(dirname "$0")/.."
RAIZ="$(pwd)"
PY="${PY_WEB:-/workspace/.venv-web/bin/python}"
NOME=sobrevivencia-pixel
STAGE=/tmp/sp_web/$NOME
rm -rf "$STAGE" && mkdir -p "$STAGE"
for f in *.py; do [ "$f" = atualizador.py ] || cp "$f" "$STAGE/"; done
cp icone.png "$STAGE/favicon.png"
cd /tmp/sp_web
"$PY" -m pygbag --build --ume_block 0 --width 960 --height 600 --title "Sobrevivência Pixel" "$NOME" >/tmp/sp_web/pygbag.log 2>&1 \
    || { tail -30 /tmp/sp_web/pygbag.log; exit 1; }
OUT="$STAGE/build/web"
cp "$RAIZ/web/manifest.json" "$RAIZ/web/sw.js" "$OUT/"
"$PY" - "$RAIZ" "$OUT" <<'PYEOF'
import sys, os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
raiz, out = sys.argv[1], sys.argv[2]
pygame.init(); pygame.display.set_mode((1, 1))
img = pygame.image.load(os.path.join(raiz, "icone.png"))
for t in (192, 512):
    fundo = pygame.Surface((t, t)); fundo.fill((24, 22, 31))
    m = int(t * 0.8)
    fundo.blit(pygame.transform.scale(img, (m, m)), ((t - m) // 2, (t - m) // 2))
    pygame.image.save(fundo, os.path.join(out, f"icone-{t}.png"))
pygame.image.save(pygame.transform.scale(img, (64, 64)), os.path.join(out, "favicon.png"))
p = os.path.join(out, "index.html")
s = open(p, encoding="utf-8").read()
head = open(os.path.join(raiz, "web", "extra_head.html"), encoding="utf-8").read()
body = open(os.path.join(raiz, "web", "extra_body.html"), encoding="utf-8").read()
s = s.replace('<html lang="en-us">', '<html lang="pt-BR">', 1)
s = s.replace('    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n', '', 1)
s = s.replace('    <meta name="viewport" content="height=device-height, initial-scale=1.0">\n', '', 1)
s = s.replace('sizes="16x16"', 'sizes="64x64"', 1)
s = s.replace("</head>", head + "\n</head>", 1)
s = s.replace("</body>", body + "\n</body>", 1)
s = s.replace("Loading, please wait ...", "Carregando o jogo... (na primeira vez pode levar até 1 minuto)", 1)
s = s.replace(">Downloading...<", ">Baixando...<", 1)
s = s.replace('platform.document.body.style.background = "#7f7f7f"', 'platform.document.body.style.background = "#18161f"', 1)
assert "sp_tela_cheia" in s and "manifest.json" in s
open(p, "w", encoding="utf-8").write(s)
print("index.html ajustado")
PYEOF
touch "$OUT/.nojekyll"
echo "OK: versão web em $OUT"
ls -la "$OUT"

if [ "${1:-}" = "--publicar" ]; then
    cd "$RAIZ"
    WT=/tmp/sp_web/gh-pages
    rm -rf "$WT"; git worktree prune
    if git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
        git fetch -q origin gh-pages
        git worktree add -q -B gh-pages "$WT" origin/gh-pages
    else
        git worktree add -q --detach "$WT"
        (cd "$WT" && git checkout -q --orphan gh-pages && git rm -rqf . )
    fi
    (cd "$WT" && find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} + \
        && cp -r "$OUT"/. . && rm -f "$NOME.apk" \
        && git add -A \
        && git -c user.name="Grok Bot" -c user.email="grokbot@local" commit -qm "versão web: $(git -C "$RAIZ" rev-parse --short HEAD)" \
        && git push -q origin gh-pages)
    git worktree remove --force "$WT"
    echo "Publicado: https://rafaelytofc7-spec.github.io/$NOME/"
fi
