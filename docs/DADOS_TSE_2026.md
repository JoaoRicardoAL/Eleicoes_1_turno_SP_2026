# Dados e resultados da análise eleitoral por bairro — São Paulo

Documentação revisada em 15/10/2026 com base nos arquivos presentes no projeto.

## 1. Objetivo e recorte

O projeto compara os votos nominais para **Presidente**, no **primeiro turno**, entre as candidaturas **13 e 22**, nos locais de votação do **município de São Paulo**. Os votos são agrupados pelo nome do bairro informado no cadastro dos locais.

O ano de 2026 é o indicado pelos arquivos utilizados. Os resultados abaixo descrevem o conteúdo dos arquivos locais; não constituem uma conferência independente da apuração publicada pelo TSE.

- Código municipal do **TSE: `71072`**, usado nas bases eleitorais.
- Código municipal do **IBGE: `3550308`**, que seria usado em um eventual cruzamento com o Censo; não é a chave eleitoral.

Os percentuais consideram **somente os votos em 13 e 22**. Outras candidaturas, brancos e nulos ficam fora do denominador.

## 2. Dados utilizados

### Boletim de urna

Arquivo: [`dados/votos/bweb_1t_SP_051020261403.csv`](../dados/votos/bweb_1t_SP_051020261403.csv).

Contém registros de opções de voto por seção e cargo no estado de São Paulo. A medida somada é `QT_VOTOS`; contar linhas não equivale a contar votos.

| Campo | Uso no projeto |
| --- | --- |
| `SG_UF` | Unidade da federação e parte da chave da seção. |
| `CD_MUNICIPIO` | Seleciona São Paulo: `71072`. |
| `NR_ZONA`, `NR_SECAO` | Identificam a seção dentro do município. |
| `NR_TURNO` | Seleciona o primeiro turno. |
| `DS_CARGO_PERGUNTA` | Seleciona `Presidente`. |
| `DS_TIPO_VOTAVEL` | Seleciona votos `Nominal`. |
| `NR_VOTAVEL` | Seleciona os números `13` e `22`. |
| `NM_VOTAVEL` | Permite conferir o nome associado ao número da candidatura. |
| `QT_VOTOS` | Quantidade de votos a somar. |

O arquivo tem 45 colunas e aproximadamente **8,32 GB**. Seu cabeçalho informa geração em **05/10/2026, às 14:03:43**. O notebook lê blocos de **100.000 linhas**, selecionando apenas as colunas necessárias e acumulando os votos por seção/candidato.

### Cadastro dos locais de votação

Arquivo: [`dados/locais/eleitorado_local_votacao_2026_SP.csv`](../dados/locais/eleitorado_local_votacao_2026_SP.csv).

Relaciona seções a locais, bairros e coordenadas. Uma escola pode aparecer em várias linhas porque recebe várias seções. O arquivo também contém mais de um turno.

| Campo | Uso no projeto |
| --- | --- |
| `SG_UF`, `CD_MUNICIPIO`, `NR_ZONA`, `NR_SECAO` | Ligam a seção aos seus votos. |
| `NR_TURNO` | Mantém o primeiro turno. |
| `DS_TIPO_SECAO_AGREGADA` | Mantém as seções `Principal` no procedimento atual. |
| `NR_LOCAL_VOTACAO` | Identifica o local em conjunto com município e zona. |
| `NM_BAIRRO` | Define o agrupamento por bairro. |
| `NR_LATITUDE`, `NR_LONGITUDE` | Permitem construir a posição aproximada do ponto de cada bairro. |
| `AA_ELEICAO` | Informa o ano no título do mapa. |

O arquivo tem 41 colunas e aproximadamente **83,84 MB**. Seu cabeçalho informa geração em **07/10/2026, às 06:28:10**.

No recorte de São Paulo, primeiro turno e seções principais, foram encontrados:

- **26.683 seções principais**;
- **2.057 locais**, identificados por município, zona e número do local;
- **899 nomes distintos de bairro**.

### Formatos e origem

As duas entradas são lidas com `sep=';'` e `encoding='latin-1'`. O código municipal é tratado como texto. As coordenadas usam vírgula decimal e são convertidas para números antes do mapa.

Referências de origem: [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/), [Boletim de Urna 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna) e [Eleitorado 2026](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026). Os ZIPs originais e os documentos de leiaute não estão na estrutura atual do projeto.

## 3. Processamento dos votos

Implementação: [`notebooks/main.ipynb`](../notebooks/main.ipynb).

### Etapa A — filtrar

Na base de votos, o notebook aplica:

```python
CD_MUNICIPIO == "71072"
NR_TURNO == 1
DS_CARGO_PERGUNTA == "Presidente"
DS_TIPO_VOTAVEL == "Nominal"
NR_VOTAVEL in [13, 22]
```

No cadastro de locais, seleciona o mesmo município, o primeiro turno e as seções principais.

### Etapa B — somar por seção e candidato

O acumulador `votos_por_candidato` soma `QT_VOTOS` por seção/candidato ao longo dos blocos. A tabela intermediária `votos_secoes_df` contém uma linha para cada combinação encontrada.

### Etapa C — associar o bairro

A chave da junção é:

```python
chave = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
```

O notebook verifica a unicidade dessa chave no cadastro filtrado e usa `merge(..., validate='many_to_one')`. Assim, as linhas de candidatos encontram uma única seção no cadastro. O número do local de votação não faz parte dessa junção.

**Conferência necessária:** `validate` verifica a cardinalidade, mas não garante que toda seção encontrou um bairro. Antes de agrupar, conferir os registros com `NM_BAIRRO` ausente, pois o `groupby` padrão descarta chaves ausentes. No notebook atual, as linhas que imprimem a contagem de votos sem bairro estão comentadas. Esta revisão não executou novamente a leitura integral do boletim bruto para auditar essa cobertura.

### Etapa D — agrupar por bairro e candidato

```python
votos_por_bairro = (
    votos_com_bairro
    .groupby(["NM_BAIRRO", "NR_VOTAVEL"], as_index=False)["QT_VOTOS"]
    .sum()
)
```

Os nomes dos bairros são preservados como aparecem no cadastro. Não houve unificação manual de grafias ou de bairros com nomes semelhantes.

### Etapa E — calcular os percentuais

Para cada bairro:

```text
Total dos dois = votos do 13 + votos do 22
Percentual do 13 = 100 × votos do 13 / total dos dois
Percentual do 22 = 100 × votos do 22 / total dos dois
```

No notebook, `groupby(...).transform('sum')` coloca o total do bairro ao lado de cada linha. Os percentuais são arredondados para duas casas. Denominadores iguais a zero são tratados como ausentes.

As colunas são então renomeadas para `Bairro`, `Candidato`, `Votos` e `Percentual`, e o resultado é salvo em CSV.

## 4. Resultados eleitorais

Arquivo: [`dados/resultados/votos_por_bairro_SP.csv`](../dados/resultados/votos_por_bairro_SP.csv).

São **1.798 linhas**, correspondentes a **899 bairros**, com duas linhas por bairro. O arquivo usa separador `;` e codificação UTF-8.

| Coluna | Significado |
| --- | --- |
| `Bairro` | Nome do bairro no cadastro dos locais de votação. |
| `Candidato` | Número `13` ou `22`. |
| `Votos` | Soma dos votos do candidato nas seções associadas ao bairro. |
| `Percentual` | Participação no total dos dois naquele bairro, em escala de 0 a 100. |

### Totais na tabela de bairros

| Candidato | Votos | Percentual no total dos dois |
| --- | ---: | ---: |
| 13 | 3.052.349 | 52,51% |
| 22 | 2.760.747 | 47,49% |
| **Total** | **5.813.096** | **100,00%** |

O candidato 13 apresenta **291.602 votos** a mais nessa tabela. O percentual municipal é calculado pela soma dos votos, não pela média simples dos percentuais dos bairros.

- **570 bairros** têm mais votos para o 13.
- **329 bairros** têm mais votos para o 22.
- Não há empate em quantidade de votos entre os dois nos bairros da tabela.

A quantidade de bairros com vantagem não representa a proporção de habitantes ou a proporção da área municipal favorável a cada candidatura.

### Cinco bairros com maior volume de votos nos dois candidatos

| Bairro, conforme o cadastro | Votos no 13 | Votos no 22 | Total dos dois |
| --- | ---: | ---: | ---: |
| VILA MARIANA | 30.688 | 26.980 | 57.668 |
| IPIRANGA | 21.125 | 23.730 | 44.855 |
| MOOCA | 17.513 | 23.150 | 40.663 |
| BELA VISTA | 26.752 | 13.683 | 40.435 |
| CIDADE TIRADENTES | 24.478 | 12.905 | 37.383 |

Esse volume expressa votos registrados nos locais associados ao nome de bairro, sem medir diretamente sua população residente.

### Conferências do CSV de resultados

- A combinação bairro/candidato não se repete.
- Todos os 899 bairros têm os dois candidatos.
- Os percentuais dos dois somam 100% por bairro neste arquivo.
- O recálculo a partir dos votos difere dos percentuais salvos em menos de 0,005 ponto percentual, compatível com arredondamento a duas casas.

Essas verificações conferem a consistência interna do CSV. Não substituem uma reconciliação completa com o boletim bruto ou com uma publicação externa.

## 5. Mapa com um ponto por bairro

Código: [`notebooks/gerar_mapa_bairros.py`](../notebooks/gerar_mapa_bairros.py).

Mapa: [`dados/resultados/mapa_pontos_por_bairro_13_22.html`](../dados/resultados/mapa_pontos_por_bairro_13_22.html).

### Como a posição é calculada

1. Selecionar os locais de São Paulo, primeiro turno e seções principais.
2. Converter as coordenadas para números.
3. Verificar se um mesmo local apresenta bairros ou coordenadas divergentes.
4. Manter uma linha por município/zona/local. Isso evita que uma escola com muitas seções tenha mais peso na posição do bairro.
5. Excluir coordenadas ausentes ou fora da triagem regional: latitude de `-24.1` a `-23.3` e longitude de `-47.0` a `-46.3`.
6. Calcular separadamente a mediana das latitudes e das longitudes dos locais válidos de cada bairro.
7. Juntar a posição à tabela eleitoral pelo nome exato do bairro.

A triagem regional é uma caixa ampla de conferência, não o contorno municipal. A mediana gera uma **posição aproximada dos locais de votação**. Ela não define centro geográfico oficial ou limites de bairro e pode não coincidir com uma escola.

As coordenadas inválidas afetam somente a posição. Os votos de um bairro com ao menos um local válido permanecem completos, conforme o CSV eleitoral. O script preserva os percentuais existentes; não os recalcula a partir dos locais com coordenadas válidas.

### Como ler as cores

| Percentual do 13 entre os dois | Cor | Interpretação |
| --- | --- | --- |
| 0% | Azul intenso | Todos os votos considerados para o 22. |
| 50% | Neutra, próxima de branco | Metade dos votos considerados para cada um. |
| 100% | Vermelho intenso | Todos os votos considerados para o 13. |

Valores intermediários recebem cores graduais. A escala é fixa de 0 a 100. Todos os pontos têm tamanho igual; o tamanho não representa quantidade de votos.

Ao passar o cursor ou clicar no ponto, são apresentados bairro, votos, percentuais e quantidade de locais com coordenadas válidas. O mapa usa Folium e mapa-base OpenStreetMap. A visualização completa requer internet para carregar os recursos e o mapa-base.

### Cobertura obtida

- **898 bairros exibidos**, um marcador por bairro.
- **13 locais únicos** descartados do cálculo da posição por coordenadas inválidas ou ausentes.
- **1 bairro sem posição válida:** `CONJUNTO HABITACIONAL TURISTICA`.

O bairro sem ponto continua no CSV eleitoral:

| Candidato | Votos | Percentual entre os dois |
| --- | ---: | ---: |
| 13 | 1.471 | 55,72% |
| 22 | 1.169 | 44,28% |

Os bairros exibidos reúnem **5.810.456 votos**, aproximadamente **99,95%** do total da tabela eleitoral. A ausência do ponto não altera os resultados por bairro.

## 6. Arquivos gerados

Os caminhos abaixo são relativos à raiz do projeto.

| Arquivo | Conteúdo e finalidade |
| --- | --- |
| `dados/resultados/votos_por_bairro_SP.csv` | Duas linhas por bairro, com votos e percentuais. Gerado pelo notebook. |
| `dados/resultados/pontos_por_bairro_13_22.csv` | Uma linha por bairro exibido, incluindo votos, percentuais, posição e número de locais válidos. |
| `dados/resultados/mapa_pontos_por_bairro_13_22.html` | Mapa interativo para navegador ou notebook. |
| `dados/resultados/mapa_pontos_por_bairro_relatorio.json` | Cobertura, bairros sem coordenadas e método de posicionamento. |

O CSV de pontos contém `Bairro`, `votos_13`, `votos_22`, `percentual_13`, `percentual_22`, `latitude`, `longitude` e `locais_com_coordenadas`. Usa `;`, UTF-8 e ponto decimal. Os três últimos arquivos da tabela são gerados pelo script do mapa.

## 7. Como reproduzir

Dependências Python: `pandas`, `numpy`, `matplotlib`, `seaborn`, `folium` e `branca`. As quatro primeiras aparecem nos imports do notebook; o mapa usa `pandas`, `folium` e `branca`.

1. Abrir `notebooks/main.ipynb` com o diretório de trabalho em `notebooks/`, pois os caminhos das células começam por `../dados/`.
2. Executar as células em ordem para ler os locais, processar os votos, calcular os percentuais e salvar o CSV. A leitura do boletim de aproximadamente 8,32 GB pode demorar.
3. Executar a célula de visualização:

```python
%run gerar_mapa_bairros.py
```

Se o CSV eleitoral já estiver atualizado, gerar somente o mapa pelo terminal, a partir da raiz do projeto:

```bash
python notebooks/gerar_mapa_bairros.py
```

O script resolve os caminhos a partir de sua própria localização. Ele lê os percentuais existentes, gera o HTML e atualiza o CSV de pontos e o relatório. Não recalcula os votos a partir do boletim.

## 8. Limites da interpretação e análises ainda não realizadas

- **Bairro do local de votação:** identifica onde os votos foram registrados; não garante que os eleitores residam nesse bairro.
- **Nomes cadastrais:** os 899 agrupamentos são nomes observados na base. Grafias diferentes podem separar um mesmo lugar; nomes iguais podem reunir locais que exigem revisão.
- **Mapa de pontos:** apresenta posições aproximadas, sem delimitar ou preencher o território dos bairros. Pontos próximos ou coincidentes podem se sobrepor.
- **Percentuais condicionados:** excluem demais candidaturas, brancos e nulos. Não representam percentual de todos os votos válidos ou de todos os eleitores.
- **Dados socioeconômicos:** renda, alfabetização e instrução do Censo e da Pesquisa OD não participam dos resultados atuais. Essas bases não estão na estrutura atual de `dados/`; não foram realizados cruzamentos socioeconômicos ou modelos de machine learning.
- **Perfil individual:** esses resultados territoriais não permitem concluir como pessoas de determinada renda ou escolaridade votaram.

O resultado atual é uma comparação descritiva dos dois candidatos por bairro cadastrado, com um mapa de pontos e registros das limitações de cobertura geográfica.
