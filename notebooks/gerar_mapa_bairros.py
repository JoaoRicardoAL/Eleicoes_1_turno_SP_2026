"""Um ponto por bairro, usando os percentuais eleitorais já calculados.

No main.ipynb: %run gerar_mapa_bairros.py
Dependências: pandas, folium, branca.
"""
from pathlib import Path
from html import escape
import json
import pandas as pd
import folium
from branca.colormap import LinearColormap

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / 'dados' / 'resultados'


def gerar_mapa():
    votos = pd.read_csv(SAIDA / 'votos_por_bairro_SP.csv', sep=';', encoding='utf-8')
    obrigatorias = {'Bairro', 'Candidato', 'Votos', 'Percentual'}
    if not obrigatorias.issubset(votos.columns):
        raise ValueError(f'O CSV de resultados precisa conter {sorted(obrigatorias)}. Encontradas: {votos.columns.tolist()}')
    votos = votos.loc[votos['Candidato'].isin([13, 22])].copy()
    if votos.duplicated(['Bairro', 'Candidato']).any():
        raise ValueError('Há mais de um registro para o mesmo bairro/candidato.')
    for coluna in ['Votos', 'Percentual']:
        votos[coluna] = pd.to_numeric(votos[coluna].astype(str).str.replace(',', '.', regex=False), errors='raise')
    if not votos['Percentual'].between(0, 100).all():
        raise ValueError('Os percentuais devem estar entre 0 e 100.')
    tabela = votos.pivot(index='Bairro', columns='Candidato', values=['Votos', 'Percentual'])
    for candidato in [13, 22]:
        if ('Percentual', candidato) not in tabela.columns:
            raise ValueError(f'Faltam percentuais para o candidato {candidato}.')
    pontos = pd.DataFrame({
        'Bairro': tabela.index,
        'votos_13': tabela[('Votos', 13)].values,
        'votos_22': tabela[('Votos', 22)].values,
        'percentual_13': tabela[('Percentual', 13)].values,
        'percentual_22': tabela[('Percentual', 22)].values,
    })
    if pontos.drop(columns='Bairro').isna().any().any():
        raise ValueError('Cada bairro precisa ter os votos e percentuais dos dois candidatos.')
    if not (pontos['percentual_13'] + pontos['percentual_22'] - 100).abs().le(0.02).all():
        raise ValueError('Os percentuais de 13 e 22 não somam 100% em todos os bairros.')

    colunas = ['AA_ELEICAO', 'CD_MUNICIPIO', 'NR_TURNO', 'DS_TIPO_SECAO_AGREGADA',
               'NR_ZONA', 'NR_LOCAL_VOTACAO', 'NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE']
    locais = pd.read_csv(RAIZ / 'dados' / 'locais' / 'eleitorado_local_votacao_2026_SP.csv',
                         sep=';', encoding='latin-1', usecols=colunas, dtype={'CD_MUNICIPIO': str})
    locais = locais.loc[locais['CD_MUNICIPIO'].eq('71072') & locais['NR_TURNO'].eq(1)
                        & locais['DS_TIPO_SECAO_AGREGADA'].eq('Principal')].copy()
    anos = locais['AA_ELEICAO'].unique()
    if len(anos) != 1:
        raise ValueError('A base de locais contém mais de um ano de eleição.')
    ano = int(anos[0])
    for coluna in ['NR_LATITUDE', 'NR_LONGITUDE']:
        locais[coluna] = pd.to_numeric(locais[coluna].astype(str).str.replace(',', '.', regex=False), errors='coerce')
    chave_local = ['CD_MUNICIPIO', 'NR_ZONA', 'NR_LOCAL_VOTACAO']
    # Cada local contribui uma vez, independentemente de quantas seções possui.
    divergentes = locais.groupby(chave_local)[['NM_BAIRRO', 'NR_LATITUDE', 'NR_LONGITUDE']].nunique().gt(1)
    if divergentes.any().any():
        raise ValueError('Há locais com bairros ou coordenadas divergentes; revisar antes de posicionar os pontos.')
    locais = locais.drop_duplicates(chave_local)
    # Triagem regional ampla: não representa o limite municipal.
    validos = locais['NR_LATITUDE'].between(-24.1, -23.3) & locais['NR_LONGITUDE'].between(-47.0, -46.3)
    locais_invalidos = int((~validos).sum())
    locais = locais.loc[validos]
    coordenadas = locais.groupby('NM_BAIRRO', as_index=False).agg(
        latitude=('NR_LATITUDE', 'median'), longitude=('NR_LONGITUDE', 'median'),
        locais_com_coordenadas=('NR_LOCAL_VOTACAO', 'size')
    ).rename(columns={'NM_BAIRRO': 'Bairro'})
    pontos = pontos.merge(coordenadas, on='Bairro', how='left', validate='one_to_one')
    sem_coordenadas = pontos.loc[pontos['latitude'].isna(), 'Bairro'].tolist()
    pontos = pontos.dropna(subset=['latitude', 'longitude']).copy()
    if pontos.empty:
        raise ValueError('Nenhum bairro com coordenadas disponíveis.')

    mapa = folium.Map(location=[-23.55, -46.63], zoom_start=11, tiles='OpenStreetMap')
    escala = LinearColormap(["#1775d4", '#f7f7f7', "#ff001e"], index=[0, 50, 100], vmin=0, vmax=100,
                            caption='Percentual do 13 entre os votos em 13 e 22 (0%: azul / 50%: neutro / 100%: vermelho)')
    escala.add_to(mapa)
    for _, bairro in pontos.iterrows():
        descricao = (f'<b>{escape(str(bairro["Bairro"]))}</b><br>'
                     f'13: {bairro["percentual_13"]:.2f}% ({int(bairro["votos_13"]):,} votos)<br>'
                     f'22: {bairro["percentual_22"]:.2f}% ({int(bairro["votos_22"]):,} votos)<br>'
                     f'Locais com coordenadas válidas: {int(bairro["locais_com_coordenadas"])}<br>'
                     'Posição aproximada: mediana das coordenadas dos locais de votação.')
        folium.CircleMarker(location=[bairro['latitude'], bairro['longitude']], radius=6,
                            color='#444444', weight=0.7, fill=True,
                            fill_color=escala(bairro['percentual_13']), fill_opacity=0.95,
                            tooltip=folium.Tooltip(descricao), popup=folium.Popup(descricao, max_width=360)).add_to(mapa)
    titulo = f'Votos em 13 e 22 por bairro — São Paulo — {ano}, 1º turno'
    mapa.get_root().header.add_child(folium.Element(f'<title>{escape(titulo)}</title>'))
    nota = (f'<div style="position:fixed;top:10px;left:55px;z-index:9999;background:white;'
            f'padding:10px;max-width:390px;box-shadow:0 1px 5px #999;font:13px Arial;">'
            f'<b>{escape(titulo)}</b><br>Um ponto por bairro, tamanho fixo. '
            'Percentuais calculados somente entre 13 e 22.<br>'
            'Posições aproximadas dos locais de votação; não representam limites dos bairros '
            'nem a residência dos eleitores.'
            f'<br>{len(pontos)} bairros exibidos; {len(sem_coordenadas)} sem coordenadas válidas.</div>')
    mapa.get_root().html.add_child(folium.Element(nota))
    arquivo = SAIDA / 'mapa_pontos_por_bairro_13_22.html'
    mapa.save(str(arquivo))
    pontos.to_csv(SAIDA / 'pontos_por_bairro_13_22.csv', sep=';', index=False, encoding='utf-8')
    relatorio = {'bairros_exibidos': len(pontos), 'bairros_sem_coordenadas': sem_coordenadas,
                 'locais_com_coordenadas_invalidas': locais_invalidos,
                 'metodo_posicionamento': 'Mediana da latitude e longitude dos locais únicos de cada bairro.',
                 'percentuais': 'Preservados do CSV de resultados; não recalculados.'}
    (SAIDA / 'mapa_pontos_por_bairro_relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    print(f'Mapa salvo em: {arquivo}')
    return mapa


if __name__ == '__main__':
    mapa = gerar_mapa()
    try:
        from IPython import get_ipython
        from IPython.display import display
        if get_ipython() is not None:
            display(mapa)
    except ImportError:
        pass
