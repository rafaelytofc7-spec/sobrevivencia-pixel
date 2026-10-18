# Sobrevivência Pixel — v0.5

Jogo de sobrevivência 2D top-down em pixel art, feito em Python + pygame.
Toda a arte é gerada por código (tiles 16x16 ampliados 3x, sem serrilhado).

## Como rodar

```
python -m pip install -r requirements.txt
python main.py
```

No VS Code: abra a pasta e aperte **F5** (configuração "Jogar (main.py)").

## Novo jogo e semente

Na tela inicial digite uma **semente** (número ou palavra) ou clique em
**Semente aleatória**. A mesma semente gera sempre o mesmo mundo, com as
mesmas vilas, castelos e masmorras. A semente aparece no menu de pausa (Esc).
**Carregar jogo salvo (F9)** continua o último save. Saves da v0.4 ou anteriores **não** abrem na v0.5
(o mundo virou blocos): comece um mundo novo.

## Controles (teclado e mouse)

Todas as teclas podem ser trocadas em **Controles** (menu inicial ou pausa).
Ficam guardadas em `controles.json`.

| Tecla / mouse | Ação |
|---|---|
| WASD / setas | andar (acelera e freia suave; desliza nas quinas) |
| Shift | correr (gasta energia, barra verde) |
| Espaço | rolar / esquivar (invencível durante a rolada) |
| Botão esquerdo (segurar) | minerar blocos, colher, cavar o chão (com pá/picareta), atacar, atirar com o arco |
| J | atacar com o teclado |
| Botão direito | colocar qualquer bloco/item da mão, comer/beber, pescar, abrir baú/bancada/forno, dormir, falar com NPC |
| E | descer pelo buraco / subir a escada, beber, encher cantil, abrir bancada/forno/baú, dormir, negociar |
| V | (debaixo da terra) ver a camada de cima transparente |
| F | comer o item da mão (ou a melhor comida) |
| I ou Tab | inventário (arrastar e soltar, equipar, grade de criação 2x2) |
| C | livro de receitas (mostra a forma de cada receita; clique para criar) |
| M / N | tamanho do minimapa / mapa completo (arraste, roda = zoom, Espaço centraliza) |
| 1-9 / roda do mouse | barra rápida |
| F5 / F9 | salvar / carregar |
| H / Esc | ajuda / pausa |

**Controle (gamepad, layout Xbox):** analógico esquerdo anda, direito mira,
A interage, B rola, X ataca, Y inventário, LB/RB barra rápida, LT corre,
Back mapa, Start pausa.

**Baú:** Shift+clique manda a pilha direto para o outro lado.

## Novidades da v0.5 — blocos e cavernas (estilo Minecraft, mas 2D visto de cima)

- **Tudo é bloco**: pedra, pedregulho, terra, areia, toras, tábuas, vidro, pedra lisa,
  minérios e lâmpadas. Cada bloco tem dureza e ferramenta certa (mão, machado,
  picareta, pá); rachaduras mostram o progresso. O bloco cai como item e pode ser
  **colocado em qualquer lugar** (até sobre a água/lava, para fazer pontes).
- **Camadas (Z)**: superfície (0) e quatro camadas subterrâneas (-1 a -4).
  Segure o clique no chão com uma **pá ou picareta** para abrir um **buraco**;
  fique em cima e aperte **E** para descer. Lá embaixo aparece uma **escada**
  para subir. Escadas de mão (item) também abrem caminho para cima.
- **Cavernas** geradas por ruído 3D (mesma semente = mesmas cavernas), com lagos
  subterrâneos e **lava** nas camadas -3/-4. É **escuro**: leve tochas e lâmpadas.
  Na camada -1, a luz do dia entra pelos buracos. **V** mostra a camada de cima.
- **Minérios por profundidade**: carvão e ferro (-1), ouro (-2), cristal (-3) e
  diamante (-4). Níveis de ferramenta: madeira → pedra → ferro → diamante; cada
  minério pede uma picareta mínima.
- **Criação em grade**: 2x2 no inventário e 3x3 na **bancada**, com receitas de
  forma (como no Minecraft). Shift+clique no resultado cria o máximo. O livro de
  receitas (C) mostra a forma de cada uma.
- **Forno** com espaços de entrada, combustível e saída e tempo de fundição:
  minério → barra, areia → vidro, pedregulho → pedra lisa, tora → carvão, comida crua → assada.
- **Monstros**: zumbi, esqueleto arqueiro, aranha e o **Explosivo** (chia e explode!)
  à noite e no escuro das cavernas. Zumbis e esqueletos queimam ao sol.
  Animais: vaca, porco, ovelha (lã para a cama), cervo, coelho, galinha...
- **Fome estilo Minecraft** (saturação escondida, correr/minerar/lutar cansam;
  barriga cheia cura), **orbes de XP** (nível acima da barra rápida) e
  **durabilidade** das ferramentas, armas e armaduras.
- Estações, clima, vilas, castelos e masmorras continuam. Minimapa por camada.

## Novidades da v0.4

- **Interface nova:** barras com ícones (vida, fome, sede, energia, ar),
  relógio com o céu, dia, estação, tempo e bioma, temperatura, dicas com
  os atributos dos itens (e comparação com o equipado), menus de pausa,
  morte e controles.
- **Personagem** animado (parado, andando, atacando, nadando, rolando) com
  a armadura e a ferramenta/arma aparecendo no corpo.
- **Texturas** com variações, transições entre biomas e beiras de água,
  água animada, grama/árvores balançando e sombras.
- **Natação:** dá para nadar na água funda (mais devagar, sem ferramentas).
  A barra de **ar** esvazia; sem ar você se afoga.
- **Estações** (3 dias cada): Primavera (plantas crescem rápido, muita chuva
  e filhotes), Verão (quente, secas), Outono (folhas laranja), Inverno
  (neve, frio, nada cresce, mais lobos famintos). Frio aumenta a fome;
  calor aumenta a sede; congelando sem roupa você perde vida. Fogueira
  e forno esquentam.
- **Itens novos:** lança (alcance maior), arco + flechas, tocha (na mão ou
  no chão), forno (carvão, barra de ferro, pão), baú (18 espaços), cama
  (ponto de renascer; à noite pula para a manhã), sopa, pão, trigo e sementes.
- **Morte:** renasça na cama (os itens ficam onde você caiu), recomece o
  mundo ou comece outro.
- **Minimapa e mapa** com névoa (só aparece o que você explorou) e
  marcadores: você, cama, baús e estruturas descobertas.
- **Estruturas** (ver `ESTRUTURAS.md`): vilas com aldeões e trocas,
  cidadelas com guardas, castelos com o Cavaleiro Negro, masmorras com o
  Rei Esqueleto, ruínas e baús de tesouro.

## Mundo

- **Infinito**, em chunks de 16x16 blocos. Chunks modificados vão para o save.
- **Biomas:** floresta, planície, deserto, pântano, neve e montanha
  (minério de ferro: precisa de picareta de pedra ou melhor).
- **Lagos e rios** com nível de água dinâmico. **Chuva** enche os lagos
  (no inverno vira neve); **seca** encolhe a água e deixa lama.

## Ecossistema

- **Passivos** (coelho, galinha, cervo): fogem, bebem água e se reproduzem.
- **Lobo:** caça os animais e você.
- **À noite:** slimes e aranhas; o fogo afasta. **Escorpiões** no deserto.

## Sobrevivência e criação

- Comida: frutas, carne/peixe (asse na fogueira), sopa, pão; cantil enche com E.
- **Criação** em grade (2x2 no inventário, 3x3 na bancada) e livro de receitas por
  categorias: Ferramentas, Armas, Armaduras, Blocos, Móveis, Comida e Materiais.
- Ferro/ouro: minério no forno com combustível (carvão, madeira, tábuas...). Carvão: tora no forno.
- Trigo: plante sementes na grama (botão direito); colha quando dourar.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `main.py` | laço do jogo, estados, entrada, desenho |
| `config.py` | constantes |
| `dados.py` | itens, receitas, objetos, biomas, criaturas |
| `controles.py` | teclas configuráveis e gamepad |
| `estacoes.py` | estações e temperatura |
| `personagem.py` | sprite animado do jogador |
| `texturas.py` | tiles do chão, transições e água animada |
| `minimapa.py` | minimapa e mapa com névoa |
| `ruido.py` | ruído determinístico |
| `mundo.py` | gerador de chunks, mundo infinito |
| `clima.py` | chuva / neve / seca |
| `entidades.py` | jogador, inventário, flechas, itens, criaturas |
| `ecossistema.py` | spawn e reprodução |
| `sprites.py` | pixel art |
| `interface.py` | HUD, janelas e menus |
| `salvar.py` | salvar/carregar (`save.json`) |
| `blocos.py` | (v0.5) blocos, minérios, ferramentas, receitas em grade, forno |
| `criacao.py` | (v0.5) casar a grade com as receitas, forno |
| `camadas.py`, `cavernas.py` | (v0.5) camadas Z, buracos/escadas, gerador de cavernas 3D |
| `mobs.py` | (v0.5) esqueleto arqueiro e Explosivo |
| `arte_blocos.py` | (v0.5) pixel art dos blocos, minérios e mobs novos |
| `estruturas.py`, `dungeon.py`, `npcs.py`, `baus.py`, `dados_estruturas.py`, `arte_estruturas.py`, `sistema_estruturas.py` | estruturas, masmorras e NPCs |
