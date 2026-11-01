# curva-pre

Trabalho com pricing num banco e uso a curva de juros pré quase todo dia, mas sempre
pronta, vinda de algum sistema. Quis montar uma do zero para entender cada passo: de onde
vêm os vértices, como contar os dias úteis, por que a interpolação é flat-forward e não
linear.

O resultado é um pacote Python pequeno, sem dependências, que monta a curva pré de
qualquer dia útil desde 2005 usando só dados públicos. A versão visual, com gráfico e
comparação entre datas, fica no meu site.

> É um projeto de estudo. Não usa dado nem metodologia de nenhuma instituição.

## De onde vêm os dados

Na mesa, a referência é o DI futuro da B3. Só que os termos de uso da B3 proíbem coleta
automatizada, então fui atrás de fontes abertas:

- **Ponta curta (1 dia útil):** o CDI, pela [API do Banco Central](https://dadosabertos.bcb.gov.br/) (série 12 do SGS).
- **Resto da curva:** as LTNs (o "Tesouro Prefixado"), pelos [dados abertos do Tesouro Transparente](https://www.tesourotransparente.gov.br/ckan/dataset/taxas-dos-titulos-ofertados-pelo-tesouro-direto) (licença ODbL).

A LTN paga R$ 1.000 no vencimento, então a taxa sai direto do preço:

```
taxa = (1000 / PU)^(252 / du) − 1
```

O módulo `di1.py` continua aqui porque a conta do DI futuro é a mesma (só muda o
nocional para 100.000), e serve se alguém tiver o arquivo da B3 baixado na mão.

## Coisas que aprendi no caminho

**Conferir contra a taxa publicada pega quase tudo.** O Tesouro publica o PU e a taxa
de cada título. Eu recalculo a taxa a partir do PU com o meu calendário e comparo. Se
um feriado estiver errado, a conta não fecha. Foi assim que achei os dois problemas
abaixo.

**O calendário muda com o tempo.** O 20 de novembro virou feriado nacional por lei em
dezembro de 2023. Antes disso, quem contava dias úteis até 2025 contava os 20/11 como
dia normal. Com o calendário de hoje, as curvas de 2020 a 2023 saíam com até 4 dias
úteis a menos nos vencimentos longos. Agora a contagem usa o calendário que valia na
data-base. Pelos dados, o Tesouro passou a considerar o feriado novo no pregão de
26/12/2023.

**A base tem erros.** Em umas 28 mil linhas de LTN, 56 têm um PU que não bate com a
taxa publicada, quase todas entre julho e setembro de 2005, com diferenças de até 4
pontos percentuais. Esses vértices são descartados e o programa avisa quais foram.

**LTN perto do vencimento atrapalha.** Com poucos dias até o vencimento, um centavo de
arredondamento no PU mexe muito na taxa. Ignoro LTNs a menos de 21 dias úteis do
vencimento e deixo o CDI cobrir essa ponta.

## Como a curva é montada

1. O CDI do dia vira o vértice de 1 dia útil.
2. Cada LTN vira um vértice (dias úteis até o vencimento, taxa).
3. Entre dois vértices, a taxa a termo é constante (flat-forward). Na prática a
   interpolação é feita nos fatores, não nas taxas:

```
F(t) = F₁ · (F₂ / F₁)^((t − t₁) / (t₂ − t₁)),   com F = (1 + taxa)^(du / 252)
```

## Organização

```
src/curva_pre/
  calendario.py      feriados ANBIMA (com a Páscoa calculada) e contagem de dias úteis
  juros.py           taxa, fator e PU em base 252
  curva.py           a curva em si: taxa spot, fator e forward em qualquer prazo
  di1.py             vencimento e taxa de contratos de DI futuro
  montagem.py        junta CDI e LTNs nos vértices do dia
  historico.py       gera o histórico compacto, um arquivo por ano
  fontes/            download dos dados do Tesouro e do Banco Central
historico/           as curvas de 2005 até hoje
vetores/             casos de teste para conferir outras implementações da interpolação
```

## Usando

Requer Python 3.11 ou mais novo.

```bash
pip install -e ".[dev]"
pytest

python -m curva_pre dia                         # curva do último dia disponível
python -m curva_pre dia --data 2026-10-30       # de um dia específico
python -m curva_pre historico --desde 2005      # refaz o histórico todo
```

Na primeira vez ele baixa o CSV do Tesouro (uns 15 MB) para `dados/`. Use `--atualizar`
para baixar de novo.

Na biblioteca:

```python
from curva_pre import CurvaPre

curva = CurvaPre([(252, 0.10), (504, 0.11)])
curva.taxa(378)          # 0.1067, ou 10,67% a.a.
curva.forward(252, 504)  # 0.1201, a taxa implícita entre 1 e 2 anos
```

## O histórico

`historico/2025.json` tem todos os dias de 2025, mas só com os vértices, para ficar
leve (uns 45 KB por ano). Quem lê refaz a interpolação. Cada dia fica assim:

```json
"2026-10-30": {"cdi": "2026-10-29", "v": [[1, 13.65, null], [42, 13.6012, "2027-01-01"], ...]}
```

Cada vértice é `[dias úteis, taxa em % a.a., vencimento]`, e o vencimento é `null` no
CDI. O campo `cdi` diz de que dia é o CDI usado: o Banco Central só publica o CDI no dia
útil seguinte, então a curva mais recente usa o da véspera.

Um GitHub Action roda todo dia útil de manhã, refaz o ano atual e faz commit se algo
mudou.
