import basedosdados as bd
import pandas as pd
import json
import matplotlib.pyplot as plt
import urllib.request
import plotly as plt
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from ibge.localidades import Estados
import os

dir = os.path.dirname(__file__)
out_dir = os.path.abspath(os.path.join(dir, '..', 'out'))
data_file_path = os.path.join(out_dir, 'data.json')
f = open(data_file_path)
base = pd.read_json(f, orient='split')

dados_estados = Estados()
Estados = dados_estados.getNome()
Siglas = dados_estados.getSigla()  # Estados e Siglas IBGE
loc = Nominatim(user_agent="GetLoc")  # Funcao de georreferenciamento

estados_lat_lon = pd.DataFrame(Siglas, Estados)
estados_lat_lon = estados_lat_lon.reset_index()
estados_lat_lon = estados_lat_lon.rename(
    columns={'index': 'Estado', 0: 'Sigla'}, index={})


def long(estado):
    geoloc = loc.geocode(estado)
    return geoloc.longitude


def lat(estado):
    geoloc = loc.geocode(estado)
    return geoloc.latitude


estados_lat_lon['latitude'] = estados_lat_lon['Estado'].apply(lambda x: lat(x))
estados_lat_lon['longitude'] = estados_lat_lon['Estado'].apply(
    lambda x: long(x))

base_total = pd.merge(base, estados_lat_lon, how='inner', on='Sigla')

despesa_uf_media = base_total.groupby(["Estado", "Sigla", "latitude", "longitude"]).agg(
    {"valor_despesa": "mean"}).sort_values('valor_despesa', ascending=True).reset_index()
despesa_uf_media['valor_despesa'] = despesa_uf_media['valor_despesa'].round(
    decimals=2)
despesa_uf_media = despesa_uf_media.rename(
    columns={"valor_despesa": "despesa_uf_media"})

base_eleitos = base_total[(base_total.resultado == 'eleito por qp') | (
    base_total.resultado == 'eleito por media')]

despesa_uf_eleito = base_eleitos.groupby(["Estado", "Sigla", "latitude", "longitude"]).agg(
    {"valor_despesa": "mean"}).sort_values('valor_despesa', ascending=True).reset_index()
despesa_uf_eleito['valor_despesa'] = despesa_uf_eleito['valor_despesa'].round(
    decimals=2)
despesa_uf_eleito = despesa_uf_eleito.rename(
    columns={"valor_despesa": "despesa_uf_eleito"})

despesa_uf = pd.merge(despesa_uf_media, despesa_uf_eleito, how='inner', on=[
                      "Estado", "Sigla", "longitude", "latitude"])

despesa_partido_media = base_total.groupby(["Partido"]).agg(
    {"valor_despesa": "mean"}).sort_values('valor_despesa', ascending=True).reset_index()
despesa_partido_media['valor_despesa'] = despesa_partido_media['valor_despesa'].round(
    decimals=2)
despesa_partido_media = despesa_partido_media.rename(
    columns={"valor_despesa": "despesa_partido_media"})

despesa_partido_eleito = base_eleitos.groupby(["Partido"]).agg(
    {"valor_despesa": "mean"}).sort_values('valor_despesa', ascending=True).reset_index()
despesa_partido_eleito['valor_despesa'] = despesa_partido_eleito['valor_despesa'].round(
    decimals=2)
despesa_partido_eleito = despesa_partido_eleito.rename(
    columns={"valor_despesa": "despesa_partido_eleito"})

despesa_partido = pd.merge(despesa_partido_media,
                           despesa_partido_eleito, how='inner', on="Partido")

# 1) Mapa com as despesas médias dos deputados federais, por Estado (2018)
br_shape_url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
with urllib.request.urlopen(br_shape_url) as response:
    # Polígonos correspondentes aos estados do Brasil
    Brazil = json.load(response)

state_id_map = {}
for feature in Brazil['features']:
    feature['id'] = feature['properties']['name']
    state_id_map[feature['properties']['sigla']] = feature['id']

map_uf = px.choropleth(
    despesa_uf,
    locations="Estado",
    geojson=Brazil,
    color="despesa_uf_media",
    labels={'despesa_uf_media': 'Despesa média em R$'},
    color_continuous_scale="Emrld",
    hover_name="Estado",
    hover_data=["despesa_uf_media", "longitude", "latitude"],
    title="Quanto, em média, é o valor das despesas eleitorais de um candidato " +
    "a deputado federal? (2018)",
)
map_uf.update_geos(fitbounds="locations", visible=False)

plt.offline.plot(map_uf, filename=os.path.join(out_dir, 'map_uf.html'))

# 2) Gráfico: Mostrando a despesa média eleitoral dos candidatos a deputado federal,
# por partido (2018)

graf_partido = px.bar(despesa_partido, x="despesa_partido_media", y="Partido",
                      color="despesa_partido_media",
                      color_continuous_scale="deep", orientation='h',
                      height=1000, labels={'despesa_partido_media': 'Despesa média em R$'},
                      title='Despesa eleitoral média dos candidatos a deputado federal,' +
                      ' por partido (2018)',
                      text_auto='.2s')

plt.offline.plot(graf_partido, filename=os.path.join(
    out_dir, 'graf_partido.html'))

# 3) Gráficos: Comparação entre a média das despesas eleitorais dos candidatos a deputado
# federal com a média das despesas eleitorais dos candidatos ELEITOS a deputado federal (2018)

graf_comp_uf = go.Figure(data=[
    go.Bar(name='Despesa eleitoral média dos candidatos (todos)', x=despesa_uf["despesa_uf_media"],
           y=despesa_uf["Estado"], orientation='h', marker_color='slateblue'),
    go.Bar(name='Despesa eleitoral média dos candidatos eleitos', x=despesa_uf["despesa_uf_eleito"],
           y=despesa_uf["Estado"], orientation='h', marker_color='turquoise')
])
graf_comp_uf.update_layout(title=go.layout.Title(
    text="Despesa eleitoral média: Todos os candidatos X Candidatos eleitos <br>" +
    "<sup>Candidatos a deputado federal</sup>",
    xref="paper",
    x=0
),
    xaxis=go.layout.XAxis(
    title=go.layout.xaxis.Title(
        text="2018<br><sup>Despesa média dos candidatos por Estado</sup>"
    )
), barmode='group', height=1000, width=1000) 

plt.offline.plot(graf_comp_uf, filename=os.path.join(
    out_dir, 'graf_comp_uf.html'))

graf_comp_partido = go.Figure(data=[
    go.Bar(name='Despesa eleitoral média dos candidatos (todos)', x=despesa_partido["despesa_partido_media"],
           y=despesa_partido["Partido"], orientation='h', marker_color='slateblue'),
    go.Bar(name='Despesa eleitoral média dos candidatos eleitos', x=despesa_partido["despesa_partido_eleito"],
           y=despesa_partido["Partido"], orientation='h', marker_color='turquoise')
])
graf_comp_partido.update_layout(title=go.layout.Title(
    text="Despesa eleitoral média: Todos os candidatos X Candidatos eleitos " +
    "<br><sup>Candidatos a deputado federal</sup>",
    xref="paper",
    x=0
),
    xaxis=go.layout.XAxis(
    title=go.layout.xaxis.Title(
        text="2018<br><sup>Despesa média dos candidatos por Partido</sup>"
    )
), barmode='group', height=1000, width=1000)

plt.offline.plot(graf_comp_partido, filename=os.path.join(
    out_dir, 'graf_comp_partido.html'))
