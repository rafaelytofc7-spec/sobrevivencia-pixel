# Estruturas (v0.4 - ramo `estruturas`)

Vilas, cidadelas, castelos, masmorras, ruínas e baús de tesouro gerados pela
**semente**, em regiões de 96x96 blocos (cada região tem no máximo uma estrutura,
que cabe inteira nela). A planta é montada uma vez e "carimbada" em cada chunk
quando ele é gerado, então estruturas que ocupam vários chunks saem certinhas.

| Estrutura | O que tem |
|---|---|
| **Vila** | casas (paredes, porta, piso, cama, às vezes baú/bancada), caminhos, praça com poço e tochas, plantações cercadas (trigo/abóbora), **aldeões** que fazem trocas. Deserto = arenito, neve = madeira escura. Nunca na montanha nem em cima de lago. |
| **Cidadela** | muralha de pedra com torres, 4 portões com **guardas** (atacam monstros e lobos), vila de pedra dentro com comerciantes melhores. |
| **Castelo** | muralha com torres, pátio, salão do trono com tapete e estandartes, baús de ouro, **cavaleiros** e o chefe **Cavaleiro Negro**. Não aparece no pântano. |
| **Masmorra** | entrada com escada (E para descer). Lá embaixo: salas e corredores escuros (só sua luz e as tochas), esqueletos, aranhas, slimes, baús e o chefe **Rei Esqueleto** (chama reforços). Escada de volta na sala inicial. |
| **Ruínas** | paredes com musgo caídas, piso rachado, um baú e às vezes um esqueleto. |
| **Tesouro** | baú perdido com uma tocha. |

Controles novos: **E** ou **botão direito** perto de aldeão = trocas (clique ou 1-4,
Esc sai); guarda = conversa; baú = abrir (o clique esquerdo também abre); poço = beber;
escada = descer/subir. Itens novos: moeda de ouro, trigo, pão, poção de vida,
tocha (constrói e ilumina) e espada de rubi.

O save guarda os baús abertos, os chefes derrotados, as estruturas descobertas
e se você está numa masmorra.

## Arquivos
- `estruturas.py` - planejador por região + plantas + carimbo nos chunks
- `dungeon.py` - masmorra (planta, MundoMasmorra, EcossistemaMasmorra)
- `npcs.py` - aldeões, guardas, inimigos, chefes e a janela de trocas
- `baus.py` - conteúdo dos baús por bioma e nível
- `dados_estruturas.py` - itens/objetos/criaturas/receitas novos (acrescentados em dados.py)
- `arte_estruturas.py` - pixel art nova (acrescentada no objeto Sprites)
- `sistema_estruturas.py` - liga tudo ao jogo (ganchos marcados `# [ESTRUTURAS]` em main.py, mundo.py e salvar.py)

## Compatibilidade com a v0.4 (visual/controles/estações)
- Objetos com nome próprio para não colidir: `bau_tesouro`/`bau_tesouro_aberto`
  (o `bau` de guardar itens continua sendo o do dados.py), `plantacao_trigo`/`plantacao_abobora`.
- `tocha`, `cama`, `trigo`, `pao`: se já existirem em dados.py/sprites.py, valem os de lá
  (este ramo só cria se faltar). Se `Mundo.lista_luzes()` existir, as tochas da superfície
  são iluminadas pelo main.py; na masmorra o sistema usa `lista_luzes()` para redesenhar as luzes.
