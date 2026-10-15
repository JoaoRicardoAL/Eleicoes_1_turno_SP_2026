# Análise eleitoral por bairro — São Paulo

Análise descritiva dos votos nominais para Presidente, no primeiro turno, comparando as candidaturas de números **13 e 22** no município de São Paulo. O projeto associa as seções eleitorais aos bairros dos locais de votação, calcula votos e percentuais por bairro e gera um mapa interativo.

O ano de **2026** é o indicado pelos arquivos utilizados. Os resultados descrevem as bases locais do projeto e não constituem uma conferência independente da apuração publicada pelo TSE.

## O que o projeto produz

- Tabela com votos e percentuais de cada candidatura por bairro.
- Mapa interativo com um ponto por bairro e cores conforme a participação do candidato 13 no total dos dois candidatos.
- Tabela com as coordenadas aproximadas dos bairros exibidos.
- Relatório de cobertura geográfica e bairros sem coordenadas válidas.

Os resultados disponíveis abrangem **899 nomes de bairro** na tabela eleitoral e **898 bairros** no mapa. O bairro `CONJUNTO HABITACIONAL TURISTICA` permanece na tabela, mas não possui posição válida para exibição.

## Estrutura do projeto

```text
.
├── README.md
├── .gitignore
├── dados/
│   ├── locais/                         # Dados brutos locais, ignorados pelo Git
│   │   └── eleitorado_local_votacao_2026_SP.csv
│   ├── votos/                          # Dados brutos locais, ignorados pelo Git
│   │   └── bweb_1t_SP_051020261403.csv
│   └── resultados/
│       ├── votos_por_bairro_SP.csv
│       ├── pontos_por_bairro_13_22.csv
│       ├── mapa_pontos_por_bairro_13_22.html
│       └── mapa_pontos_por_bairro_relatorio.json
├── docs/
│   └── DADOS_TSE_2026.md
└── notebooks/
    ├── main.ipynb
    └── gerar_mapa_bairros.py
```

## Consultar os resultados

Os arquivos em [`dados/resultados/`](dados/resultados/) permitem consultar a análise sem processar novamente os dados brutos.

Para visualizar o mapa, baixe ou clone o repositório e abra [`mapa_pontos_por_bairro_13_22.html`](dados/resultados/mapa_pontos_por_bairro_13_22.html) em um navegador. A visualização completa requer internet para carregar o mapa-base e os recursos externos.

O CSV [`votos_por_bairro_SP.csv`](dados/resultados/votos_por_bairro_SP.csv) usa separador `;`, codificação UTF-8 e as seguintes colunas:

| Coluna | Descrição |
| --- | --- |
| `Bairro` | Nome do bairro conforme o cadastro dos locais de votação. |
| `Candidato` | Número da candidatura: 13 ou 22. |
| `Votos` | Soma dos votos nas seções associadas ao bairro. |
| `Percentual` | Participação nos votos dos dois candidatos naquele bairro, de 0 a 100. |

## Preparar o ambiente

É necessário ter Python 3, `pip` e um ambiente para executar notebooks Jupyter. A partir da raiz do projeto, instale as dependências:

```bash
python -m pip install pandas numpy matplotlib seaborn folium branca notebook
```

## Obter os dados brutos

As fontes de referência são o [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/), a base de [Boletim de Urna 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna) e o cadastro de [Eleitorado 2026](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026).

Os dados brutos não são versionados devido ao tamanho. Para reproduzir a análise completa, obtenha os arquivos de São Paulo, extraia os CSVs e organize-os nestes caminhos:

```text
dados/votos/bweb_1t_SP_051020261403.csv
dados/locais/eleitorado_local_votacao_2026_SP.csv
```

O boletim utilizado ocupa aproximadamente **8,32 GB**, e o cadastro dos locais, **83,84 MB**. Reserve espaço para os downloads, a extração e os resultados. As entradas são lidas com separador `;` e codificação `latin-1`.

Caso utilize outra versão dos arquivos, ajuste os caminhos no notebook e no script do mapa e confira a compatibilidade das colunas. O projeto não possui download automático dos dados.

## Executar a análise completa

Inicie o Jupyter com o diretório de trabalho em `notebooks/`, pois o notebook usa caminhos relativos iniciados por `../dados/`:

```bash
cd notebooks
python -m notebook main.ipynb
```

Execute as células em ordem. O notebook:

1. Seleciona as seções principais de São Paulo, no primeiro turno.
2. Lê o boletim de urna em blocos de 100.000 linhas.
3. Filtra os votos nominais para Presidente nas candidaturas 13 e 22.
4. Soma os votos por seção e candidato e associa cada seção ao bairro.
5. Calcula os totais e percentuais por bairro e salva o CSV eleitoral.
6. Executa o script que gera o mapa, a tabela de pontos e o relatório.

A leitura integral do boletim pode demorar. Os arquivos de resultados existentes são sobrescritos durante a execução.

## Gerar somente o mapa

Se o CSV eleitoral já estiver disponível, execute a partir da raiz do projeto:

```bash
python notebooks/gerar_mapa_bairros.py
```

Essa etapa exige o CSV de resultados e o cadastro bruto dos locais de votação. Ela preserva os votos e percentuais já calculados e atualiza o HTML, o CSV de pontos e o relatório JSON.

## Metodologia e interpretação

A análise usa o código municipal do TSE `71072`. Os votos são somados pela coluna `QT_VOTOS`, associados ao cadastro pela combinação de UF, município, zona e seção, e agrupados pelo nome do bairro.

O percentual de cada candidato considera exclusivamente os votos em 13 e 22:

```text
Percentual do candidato = 100 × votos do candidato / (votos do 13 + votos do 22)
```

No mapa, cada bairro recebe um ponto de tamanho fixo. Sua posição corresponde à mediana das latitudes e longitudes dos locais de votação únicos com coordenadas válidas. A escala vai de azul, com 0% para o 13, a vermelho, com 100% para o 13, passando por uma cor neutra em 50%.

### Limitações

- O bairro corresponde ao local de votação e não necessariamente à residência dos eleitores.
- Os nomes são preservados como aparecem no cadastro, sem unificação manual de grafias.
- Os percentuais excluem outras candidaturas, votos brancos e nulos.
- Os pontos representam posições aproximadas, sem delimitar os bairros; seu tamanho não indica quantidade de votos.
- A consistência dos resultados agregados não substitui a conferência da cobertura da junção com a base bruta. O agrupamento pode descartar registros sem bairro associado.
- Não foram realizados cruzamentos com renda, escolaridade ou outros dados socioeconômicos.

Consulte [`docs/DADOS_TSE_2026.md`](docs/DADOS_TSE_2026.md) para detalhes sobre campos, filtros, resultados, cobertura geográfica e verificações realizadas.
