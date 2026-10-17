# Sobrevivência Pixel — v0.3

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
**Semente aleatória**. A mesma semente gera sempre o mesmo mundo. A semente
aparece no canto superior direito durante o jogo. **Carregar jogo salvo (F9)**
continua o último save.

> Saves da v0.2 não são compatíveis com a v0.3 (o mundo agora é infinito).

## Controles

| Tecla / mouse | Ação |
|---|---|
| WASD / setas | andar (água rasa deixa mais lento) |
| Botão esquerdo (segurar) | quebrar recurso/construção, atacar bichos |
| Botão direito | construir item da mão, comer/beber, pescar (vara na água), usar fogueira |
| E | beber água e encher cantis, assar carne/peixe, pôr lenha na fogueira |
| F | comer/beber o item da mão (ou a melhor comida) |
| Espaço | atacar na direção em que você olha |
| I ou Tab | inventário (arrastar e soltar, equipar) |
| C | menu de criação |
| 1-9 / roda do mouse | escolher item da barra rápida |
| F5 / F9 | salvar / carregar |
| H / Esc | ajuda / fechar janelas |

**Inventário:** arraste itens entre a mochila (27 espaços), a barra rápida
(9) e os espaços de equipamento (Cabeça, Corpo, Arma, Ferramenta). Botão
direito equipa/desequipa ou divide uma pilha. Soltar fora da janela joga o
item no chão.

## Mundo

- **Infinito**, dividido em chunks de 16x16 blocos, carregados perto de você
  e descarregados longe. Chunks que você modificou são guardados no save.
- **Biomas** (temperatura + umidade):
  - **Floresta:** muitas árvores, cervos, coelhos, lobos; aranhas à noite.
  - **Planície:** grama, arbustos de frutas, galinhas, coelhos, cervos, lobos.
  - **Deserto:** areia, cactos, coelhos, poucos lagos e escorpiões.
  - **Pântano:** muitos lagos, juncos, árvores do pântano, galinhas; slimes e aranhas à noite.
  - **Neve:** pinheiros, cervos, lobos.
  - **Montanha:** rocha, pedras e **minério de ferro** (precisa de picareta de pedra ou melhor).
- **Lagos e rios** com nível de água dinâmico.
- **Clima:**
  - **Chuva:** gotas, céu mais escuro; lagos e rios enchem e transbordam nas margens.
  - **Seca:** chão amarelado, mais sede; a água encolhe e o fundo vira lama.

## Ecossistema

- **Passivos** (coelho, galinha, cervo): passeiam, fogem de você e dos
  lobos, bebem água e se reproduzem. Soltam carne crua e couro.
- **Lobo:** caça os animais e também você.
- **À noite:** slimes e aranhas. Slimes derretem com o sol; o fogo das
  fogueiras afasta os monstros. **Escorpiões** vivem no deserto.

## Sobrevivência e criação

- Barras de **vida, fome e sede**. Comida:
  - frutas (arbustos);
  - carne crua (faz mal);
  - carne assada;
  - peixe e peixe assado (pesque com a **vara de pesca** clicando com o botão direito na água);
  - **cantil**, que você enche com E perto da água.
- Asse carne e peixe na **fogueira** (E ou botão direito nela).
- **Criação** por categorias: Ferramentas, Armas, Armaduras, Construção,
  Comida e Materiais. Itens avançados exigem uma **Bancada** por perto.
  **Ferro** é fundido na fogueira (minério + madeira).
- **Equipamento** em tiers madeira / pedra / ferro: machados, picaretas,
  espadas, capuz e roupa de couro, capacete e armadura de ferro. Armadura
  reduz o dano recebido; arma aumenta o dano.
- **Construção:** paredes de madeira/pedra, piso, bancada e fogueira.
  Selecione o item na barra e clique com o botão direito. A prévia fica
  verde quando dá para construir e vermelha quando não dá.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `main.py` | laço do jogo, estados, entrada, desenho |
| `config.py` | constantes (tela, chunks, água, status, cores) |
| `dados.py` | tabelas: itens, receitas, objetos, biomas, criaturas |
| `ruido.py` | ruído determinístico em Python puro (sementes) |
| `mundo.py` | gerador de chunks, mundo infinito, nível da água |
| `clima.py` | chuva / seca / tempo bom |
| `entidades.py` | jogador, inventário, itens no chão, criaturas (IA) |
| `ecossistema.py` | spawn, reprodução e despawn de criaturas |
| `sprites.py` | pixel art gerada por código |
| `interface.py` | HUD, inventário, criação, menus |
| `salvar.py` | salvar/carregar (`save.json`) |
