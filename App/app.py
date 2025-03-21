## https://blog.streamlit.io/crafting-a-dashboard-app-in-python-using-streamlit/
#######################
# Import libraries
import streamlit as st
import altair as alt
import polars as pl
import numpy as np
import pandas as pd
from polars import selectors as cs

#disabilita o limite de 5.000 para processamento imposto pelo altair
alt.data_transformers.disable_max_rows()

year_range_colors:list[str] = ['#F3AD58','#9489BB']
ideol_range_colors:list[str] = ["#BC3439", "#347DB6"]

#######################
# Page configuration
st.set_page_config(
    page_title="Dashboard Eleições",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon = "🗳️"
)

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    #background-color: #393939;
    border:1px solid #393939;
    text-align: center;
    padding: 2px 0;
}

[data-testid="stMetricValue"] {
    font-size: 18px;
    font-weight: 700;
}

[data-testid="stMetricDelta"] {
    font-size: 15px;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDelta"] {
    color: #000 !important;
}
</style>
""", unsafe_allow_html=True)

##########################################################################################
##                                Definição das Funções                                 ##
##########################################################################################
### Busca os datasets no google drive
def get_df(url):
    #url='https://drive.google.com/uc?id=' + url.split('/')[-2]
    return pl.read_parquet(source=url)
    

### Funções para melhorar a performance
@st.cache_data
def get_regioes():
    df_regioes = get_df("https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/regioes.parquet")     
    return df_regioes

### Carrega as regiões do google drive
@st.cache_data
def get_regioes():
    return get_df("https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/regioes.parquet")     

### Carrega dados da eleição de 2018
@st.cache_data
def get_eleicao_18():
    return get_df(f"https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/eleicao18_turno_01.parquet")     

### Carrega dados da eleição de 2022
@st.cache_data
def get_eleicao_22():
    return get_df(f"https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/eleicao22_turno_01.parquet")     

@st.cache_data 
def get_partidos():
    return get_df(f"https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/partidos_br.parquet")     

@st.cache_data 
def get_municipios():
    return get_df(f"https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/municipios.parquet")     

@st.cache_data 
def get_capitais():
    return get_df(f"https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/main/Dados/Eleicoes/capitais.parquet")     

# Funções gerais
# Convert population to text 
def format_number(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
        #num = round(num,2)
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Partido": ['', input_text],
      "% Votação": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Partido": ['', input_text],
      "% Votação": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% Votação",
      color= alt.Color("Partido:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=25, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% Votação",
      color= alt.Color("Partido:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text
    
##
##    Plota, na reta numérica, os partidos conforme suas ideologias políticas.
##    Baseado no trabalho de Bolognesi(2018)

##    df_partidos:pl.DataFrame -> Dataframe com os partidos políticos e sua classificação ideológica
##
def class_ideologica_chart(df_partidos:pl.DataFrame, df_colors:pl.DataFrame)->alt.vegalite.v5.api.Chart:
    df_colors_tmp = df_colors.sort(by="MEDIA_IDEOL") 
    
    _domains = ["EE","E","CE","C","CD","D","ED"]
    _range = ["#7F0000","#FF0000","#C54B53","#FFD966","#97A3FF","#262DDA","#030886"]
    color_scale = alt.Scale(
        domain=_domains,
        range=_range
    )   

    #svg que renderiza uma pessoinha
    person = (
        "M1.7 -1.7h-0.8c0.3 -0.2 0.6 -0.5 0.6 -0.9c0 -0.6 "
        "-0.4 -1 -1 -1c-0.6 0 -1 0.4 -1 1c0 0.4 0.2 0.7 0.6 "
        "0.9h-0.8c-0.4 0 -0.7 0.3 -0.7 0.6v1.9c0 0.3 0.3 0.6 "
        "0.6 0.6h0.2c0 0 0 0.1 0 0.1v1.9c0 0.3 0.2 0.6 0.3 "
        "0.6h1.3c0.2 0 0.3 -0.3 0.3 -0.6v-1.8c0 0 0 -0.1 0 "
        "-0.1h0.2c0.3 0 0.6 -0.3 0.6 -0.6v-2c0.2 -0.3 -0.1 "
        "-0.6 -0.4 -0.6z"
    )
    
    points = alt.Chart(
        df_colors        
    ).mark_point(
        filled=True,
        size=100,
        opacity=.9
    ).encode(
        x=alt.X("MEDIA_IDEOL:Q", 
                title="Média Ideológica",
                scale=alt.Scale(nice=True)
        ),
        shape=alt.ShapeValue(person),
        color=alt.Color('SG_POSIC_IDEOLOGICO:O',
            title="Ideologia", legend=alt.Legend(
                #orient='bottom', 
                #labelBaseline="middle",
                symbolType="square",                
                 #["Extrema Esquerda","Esquerda","Centro Esquerda","Centro","Centro Direita","Direita","Extrema Direita"],
            ),
            scale=color_scale,
        ),
        tooltip=[
            alt.Tooltip("SG_PARTIDO:O", title="Partido"),
            alt.Tooltip("MEDIA_IDEOL:Q", title="Média Ideológica", format=".2f",)
        ]        
    )

    text_dx:int=-70
    text = points.mark_text(
        align="left",
        baseline="top",
        dy=0,
        #dx=30,
        dx=alt.expr(
            alt.expr.if_(alt.datum.SG_PARTIDO == "PMB", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "PSD", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "PRD", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "PODE", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "AGIR", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "NOVO", text_dx, 
            alt.expr.if_(alt.datum.SG_PARTIDO == "PL", text_dx, 30)))))))
        ),
        fontSize=8.5,
        angle=270,
        fontWeight="bold",
        opacity=1
    ).encode(
        text=alt.Text("SG_PARTIDO:O"),
        color=alt.value("#000"),
        tooltip=[
            alt.Tooltip("SG_PARTIDO:O", title="Partido"),
            alt.Tooltip("MEDIA_IDEOL:Q", title="Média Ideológica", format=".2f",)
        ] 
    )
    
    return (points + text) #\
    #.properties(
    #    width=1000,
    #    height=45
    #).configure_view(
    #    #strokeWidth=0
    #).configure_title(
    #    fontSize=14
    #)
## Define uma função associa uma cor para cada um dos espectos ideológicos do partidos políticos brasileiros
def parties_colors(df:pl.DataFrame)->pl.DataFrame:
    return (df
    .select(pl.col("SG_PARTIDO", "SG_POSIC_IDEOLOGICO", "MEDIA_IDEOL"))
    .unique() 
    .with_columns(
        pl.col("MEDIA_IDEOL").str.replace(",","."),
        cor = pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="EE").then(pl.lit("#7F0000")).otherwise(
                pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="E").then(pl.lit("#FF0000")).otherwise(
                    pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="CE").then(pl.lit("#C54B53")).otherwise(
                        pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="C").then(pl.lit("#FFD966")).otherwise(
                            pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="CD").then(pl.lit("#97A3FF")).otherwise(
                                pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="D").then(pl.lit("#262DDA")).otherwise(
                                    pl.when(pl.col("SG_POSIC_IDEOLOGICO")=="ED").then(pl.lit("#030886"))
                                )
                            )
                        )
                    )
                )
            )
    ).with_columns(
        pl.col("MEDIA_IDEOL").cast(pl.Float32)
    )
)
    
##
###   Gera uma comparação da votação dos partido para um cargo entre 2018 e 2022 em forma de pirâmide
def pyramid_votting_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,
                      position:list[int], chart_title:str, total_parties:int=10)->alt.vegalite.v5.api.Chart:

  df_tmp_18 = (df_2018.filter(pl.col("CD_CARGO").is_in(position))
      .select(pl.col("ANO_ELEICAO", "SIGLA_2022","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SIGLA_2022","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )
      .join(df_colors, left_on="SIGLA_2022", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )

  df_tmp_22 = (df_2022.filter(pl.col("CD_CARGO").is_in(position))
      .select(pl.col("ANO_ELEICAO", "SIGLA_2022","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SIGLA_2022","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )
      .join(df_colors, left_on="SIGLA_2022", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )

  # os registros dos K partidos mais votados em 2018
  top_k_22=df_tmp_22.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SIGLA_2022","QT_VOTOS_VALIDOS"))

  df_tmp_22 = (
      df_tmp_22.join(top_k_22, on="SIGLA_2022", how="right")
      .with_columns(
          QT_ORDER = pl.col("QT_VOTOS_VALIDOS_right")
      )
      .drop(pl.col("QT_VOTOS_VALIDOS_right"))
      .with_columns(
          pl.col(["QT_VOTOS_VALIDOS","QT_VOTOS_BR","PCT"]).fill_null(strategy="zero"),
          pl.col("ANO_ELEICAO").fill_null(2022)
      )
  )
  df_tmp_18 = (
      df_tmp_18.join(top_k_22, on="SIGLA_2022", how="right")
      .with_columns(
          QT_ORDER = pl.col("QT_VOTOS_VALIDOS_right")
      )
      .drop(pl.col("QT_VOTOS_VALIDOS_right"))
      .with_columns(
          pl.col(["QT_VOTOS_VALIDOS","QT_VOTOS_BR","PCT"]).fill_null(strategy="zero"),
          pl.col("ANO_ELEICAO").fill_null(2018)
      )

  )

  # concatena as votações de 22 e 18 para os cargos em position
  df_tmp = pl.concat([df_tmp_22, df_tmp_18])

  base = alt.Chart(df_tmp).properties(
      width=350
  )

  _domains = ["Extrema Esquerda","Esquerda","Centro Esquerda","Centro","Centro Direita","Direita","Extrema Direita"]
  _range = ["#7F0000","#FF0000","#C54B53","#FFD966","#97A3FF","#262DDA","#030886"]
  color_scale = alt.Scale(
      domain=_domains,
      range=_range
  )

  left_base = base.transform_filter(
      alt.datum.ANO_ELEICAO == 2018
  ).encode(
      alt.Y('SIGLA_2022:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Color('POSIC_IDEOLOGICO:O')
          .scale(color_scale)
          .legend(None),
      tooltip=[
          alt.Tooltip("SIGLA_2022:N", title="Partido"),
          alt.Tooltip("POSIC_IDEOLOGICO:N", title="Ideologia"),
          alt.Tooltip("ANO_ELEICAO:N", title="Eleição"),
          alt.Tooltip("QT_VOTOS_BR:Q", format=",d", title="Total Geral"),
          alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Votos Partido"),
          alt.Tooltip("PCT:Q", format=".2%", title="Percentual"),
      ]
  ).mark_bar(opacity=.8).properties(title='2018')

  max_abs = df_tmp_18.get_column("QT_VOTOS_BR").max()/2

  left_pct = left_base.encode(
      alt.X('PCT:Q',
          title='',
          axis=alt.Axis(values=np.arange(0,.55, .05), format="%", labelAngle=-90),
          sort="descending",
          scale=alt.Scale(domain=[0, .5])
      )
  )  

  left_abs = left_base.encode(
      alt.X('QT_VOTOS_VALIDOS:Q',
          title='',
          axis=alt.Axis(format="s", orient="top", labelAngle=-90),
          sort="descending",
          scale=alt.Scale(domain=[0, max_abs]),
      ),
      opacity=alt.value(0)
  )

  middle = base.encode(
      alt.Y('SIGLA_2022:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Text('SIGLA_2022:O'),
  ).mark_text(fontSize=8.5).properties(width=30)

  right_base = base.transform_filter(
      alt.datum.ANO_ELEICAO == 2022
  ).encode(
      alt.Y('SIGLA_2022:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Color('POSIC_IDEOLOGICO:O').scale(color_scale),
      tooltip=[
          alt.Tooltip("SIGLA_2022:N", title="Partido"),
          alt.Tooltip("POSIC_IDEOLOGICO:N", title="Ideologia"),
          alt.Tooltip("ANO_ELEICAO:N", title="Eleição"),
          alt.Tooltip("QT_VOTOS_BR:Q", format=",d", title="Total Geral"),
          alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Votos Partido"),
          alt.Tooltip("PCT:Q", format=".2%", title="Percentual"),
      ]
  ).mark_bar(opacity=0.8).properties(title='2022')

  right_pct = right_base.encode(
      alt.X('PCT:Q',
            title="",
            axis=alt.Axis(values=np.arange(0, 1.1, .05), format="%", labelAngle=-90),
            scale=alt.Scale(domain=[0, 0.5])
      ),
  )
  max_abs = df_tmp_22.get_column("QT_VOTOS_BR").max()/2
  right_abs = right_base.encode(
      alt.X('QT_VOTOS_VALIDOS:Q',
          title='',
          axis=alt.Axis(format="s", orient="top", labelAngle=-90),
          sort="ascending",
          scale=alt.Scale(domain=[0, max_abs]),
      ),
      opacity=alt.value(0)
  )

  return (
    alt.hconcat(
      alt.layer(left_pct,left_abs).resolve_scale(x='independent'),
      middle,
      alt.layer(right_pct,right_abs).resolve_scale(x='independent'),
      spacing=2, title = alt.TitleParams(f"{chart_title}", anchor="middle")
    )
  )

## renderiza uma mapa com a votação do partido
def mapa_eleitoral(df_eleicao:pl.DataFrame, 
                   df_municipios:pl.DataFrame,
                   df_capitais:pl.DataFrame,
                   partido:str="", 
                   breaks=list[float], 
                   domain=list[str],
                   scheme:str="inferno",
                   legend_sort:list[str]=[],
                   opacity=1.,
                   rev_Schmeme:bool=False)->alt.vegalite.v5.api.Chart:

    df_choropleth = (
        df_eleicao
        .filter(pl.col("SG_PARTIDO")==f"{partido}")
        .select(["CD_MUNICIPIO","TOTAL_VOTOS_MUNIC","QT_VOTOS_VALIDOS","PCT_VOTOS_MUNIC"])        
    )
    df_choropleth = (
        df_choropleth
        .with_columns(
            pl.col("PCT_VOTOS_MUNIC").cut(breaks=[.25, .4, .55], labels=["<=25%", ">25%,<=40%", ">40%,<=55%",">55%"]).alias("PCT_VOTOS_LIMIT")
        )
    )
    df_choropleth = (
        df_choropleth
        .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
        .drop(pl.col(["capital","ddd"])) 
    )    
    scale = alt.Scale(type="threshold", reverse=rev_Schmeme, domain=domain, scheme=scheme)    

    states = alt.Data(
      url='https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/br_states.json',
      format=alt.DataFormat(property='features')
    )
    background_states:alt.vegalite.v5.api.Chart = (
      alt.Chart(alt.Data(states))
      .mark_geoshape(
          stroke='#000',
          fillOpacity = 0,
          strokeWidth=.6
      )
    )
    
    cities = alt.Data(
      url="https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/geojs-100-mun_minifier.json",
      format=alt.DataFormat(property='features')
    )
    
    cities_map = alt.Chart(df_choropleth) \
    .mark_geoshape(
        stroke="#000", strokeWidth=.03, fillOpacity=opacity
    ).project(
        type="equirectangular"
    ).encode(
      shape='geo:G',
      color=alt.Color("PCT_VOTOS_LIMIT:N",
          scale=scale,
          legend=alt.Legend(
            #orient="bottom",
            titleAnchor='middle',
            title="Percentual de Votos",
            #direction="horizontal"
            type="symbol",
            symbolSize=400,
            #symbolOpacity=.7,
            symbolStrokeWidth=0,
            symbolType="square",
            values=legend_sort
          )
      ),
      tooltip=[
          alt.Tooltip('uf:N', title='Estado'),
          alt.Tooltip('nome:N', title="Município"),
          alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Votos Totais Município"),
          alt.Tooltip("QT_VOTOS_VALIDOS:Q",format=",d", title="Votos no Partido"),
          alt.Tooltip("PCT_VOTOS_MUNIC:Q", format=".2%", title="% Votos"),
      ]
    ).transform_lookup(
      lookup='codigo_ibge',
      from_=alt.LookupData(cities, key="properties.id"),
      as_='geo'
    ).properties(width=600)
    
    return alt.layer(background_states, cities_map), df_choropleth

## Plota as diferenças de votos percentuais entre dois anos
def prepara_mapa_diferenca(
        df_choropleth_a:pl.DataFrame, 
        df_choropleth_b:pl.DataFrame, 
        df_capitais:pl.DataFrame, 
        breaks = [],
        domain=[], 
        chart_title:str="", 
        legend_sort:list[str]=[],
        scheme="inferno", 
        rev_Schmeme:bool=False,
        opacity=1., 
        tooltip_title_22:list[str]=[], 
        tooltip_title_18:list[str]=[],
        legend_title:str='')->alt.vegalite.v5.api.Chart:

    df_choropleth_diff_a = (
        df_choropleth_a.rename({
            "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_18",
            "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_18",
            "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_18"
        }).drop(["codigo_ibge", "nome",	"uf", "latitude","longitude"])
    )
    
    df_choropleth_diff_b=df_choropleth_b.rename({
        "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_22",
        "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_22",
        "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_22"
    })  

    df_choropleth_diff = (
      df_choropleth_diff_a
      .join(df_choropleth_diff_b, on="CD_MUNICIPIO", how="inner")
      .with_columns(
          (pl.col("PCT_VOTOS_MUNIC_22")-pl.col("PCT_VOTOS_MUNIC_18")).alias("PCT_DIFF"),
          (pl.col("QT_VOTOS_VALIDOS_22")-pl.col("QT_VOTOS_VALIDOS_18")).alias("QT_DIFF")
      ).with_columns(
        pl.col("PCT_DIFF").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
      )
    )

    return mapa_diferenca(
        df_poll_diff=df_choropleth_diff, 
        df_capitais=df_capitais,
        scaleDomain=domain,
        legend_sort=legend_sort,
        rev_Schmeme=rev_Schmeme,
        legend_title=legend_title,
        opacity=opacity,
        tooltip_title_22=tooltip_title_22,
        tooltip_title_18=tooltip_title_18
    )
    
def mapa_diferenca(
    df_poll_diff:pl.DataFrame, 
    df_capitais:pl.DataFrame, 
    chart_title:str="", 
    scaleDomain:list[str]=[], 
    legend_sort:list[str]=[],
    scheme="inferno", 
    rev_Schmeme:bool=False,
    opacity=1., 
    tooltip_title_22:list[str]=[], 
    tooltip_title_18:list[str]=[],
    legend_title:str='')->alt.vegalite.v5.api.Chart:

  scale = alt.Scale(type="threshold", reverse=rev_Schmeme, domain=scaleDomain, scheme=scheme)

  states = alt.Data(
      url='https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/br_states.json',
      format=alt.DataFormat(property='features')
  )
  background_states:alt.vegalite.v5.api.Chart = (
      alt.Chart(alt.Data(states))
      .mark_geoshape(
          stroke='#000',
          fillOpacity=0,
          strokeWidth=.6
      )
  )

  cities = alt.Data(
      url="https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/geojs-100-mun_minifier.json",
      format=alt.DataFormat(property='features')
  )

  cities_map =(alt.Chart(df_poll_diff)
    .mark_geoshape(
        stroke="#000", strokeWidth=.03, fillOpacity=opacity
    ).project(
        #type="equirectangular",
        type='identity',
        reflectY=True 
    ).encode(
      shape='geo:G',
      color=alt.Color("PCT_VOTOS_LIMIT:N",
          scale=scale,
          legend=alt.Legend(
            titleAnchor='middle',
            title=f"{legend_title}",
            type="symbol",
            symbolSize=400,
            #symbolOpacity=.8,
            symbolStrokeWidth=0,
            symbolType="square",
            values=legend_sort
          )
      ),
      tooltip=[
          alt.Tooltip('uf:N', title='Estado'),
          alt.Tooltip('nome:N', title="Município"),
          alt.Tooltip("TOTAL_VOTOS_MUNIC_22:Q", format=",d", title=f"{tooltip_title_22[0]}"),
          alt.Tooltip("TOTAL_VOTOS_MUNIC_18:Q", format=",d", title=f"{tooltip_title_18[0]}"),
          alt.Tooltip("QT_VOTOS_VALIDOS_22:Q", format=",d", title=f"{tooltip_title_22[1]}"),
          alt.Tooltip("QT_VOTOS_VALIDOS_18:Q", format=",d", title=f"{tooltip_title_18[1]}"),
          alt.Tooltip("PCT_VOTOS_MUNIC_22:Q", format=".2%", title=f"{tooltip_title_22[2]}"),
          alt.Tooltip("PCT_VOTOS_MUNIC_18:Q",format=".2%", title=f"{tooltip_title_18[2]}"),
          alt.Tooltip("QT_DIFF:Q", format=",d", title="Diff. Votos"),
          alt.Tooltip("PCT_DIFF:Q", format=".2%", title="Diff. % Votos")      
    ]
    ).transform_lookup(
      lookup='codigo_ibge',
      from_=alt.LookupData(cities, key="properties.id"),
      as_='geo'
    ).properties(width=600)
  ) 

  return (
    alt.layer(background_states, cities_map)
    .properties(title=f"{chart_title}")
    .configure_title(anchor="middle")
  )

def crescimento(
    summary:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 30_000_000],
    y_axis=alt.Axis(format="s"),
    x_column="NM_REGIAO",
    legend=[],
    )->alt.vegalite.v5.api.Chart:

  dy:float=6.
  font_size:float=10.

  scale = alt.Scale(
      domain=legend,
      range=color_range
  )

  base = (
    alt.Chart(summary)
  )

  bar1 = base.transform_calculate(
    ANO=f"'{legend[0]}'"
  ).mark_bar().encode(
      x=alt.X(f"{x_column}:N", title="",
              axis=alt.Axis(orient="bottom", values=[])),
      y=alt.Y('Votos_18:Q', scale=alt.Scale(domain=y_domain), axis=y_axis),
      color=alt.Color("ANO:N", scale=scale, legend=alt.Legend(symbolSize=150)),
      text=alt.Text('Votos_18:Q', format='.3s'),
  )

  bar2 = base.transform_calculate(
    ANO=f"'{legend[1]}'"
  ).mark_bar().encode(
      x=alt.X(f"{x_column}:N", title="",
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Votos_18:Q', title=""),
      y2=alt.Y2('Votos_22:Q'),
      color=alt.Color("ANO:N", title="Eleiçao", scale=scale,
                      #legend=alt.Legend(direction="horizontal",
                      #                  orient="none", legendX=55, legendY=320,
                      #                  titleAnchor="middle")
                      ),
      text=alt.Text('Votos_22:Q', format='.3s'),
  )

  bar1_text = bar1.mark_text(
        dy=dy, fontSize=font_size
      ).encode(
        x=alt.X(f"{x_column}:N", title="",
                axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y('Votos_18:Q', title=""),
        color=alt.value("#000")
  )

  diff_text = base.transform_calculate(
      text=alt.expr.if_((alt.datum.Votos_22-alt.datum.Votos_18)>0, "+", "") + alt.expr.format((alt.datum.Votos_22-alt.datum.Votos_18), ".3s"),
      y=alt.expr.if_(
          (alt.datum.Votos_22-alt.datum.Votos_18)<0,
          (alt.datum.Votos_18-3_200_000),
          alt.expr.if_((alt.datum.Votos_22-alt.datum.Votos_18) < 1_300_000,
                       (alt.datum.Votos_18+1_200_000),
                       (alt.datum.Votos_18 +  (alt.datum.Votos_22-alt.datum.Votos_18)/2))
      )
  ).mark_text(dy=0, fontSize=font_size-1).encode(
      x=alt.X(f"{x_column}:N", title="",
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('y:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar2, bar1_text, diff_text)
      .resolve_scale(x="independent")
  )

def votacao_regiao(
    df_resumos:pl.DataFrame,
    x_order=None,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 60_000_000]
    )->alt.vegalite.v5.api.Chart:
    
    base = alt.Chart(df_resumos).encode(
        x=alt.X("NM_REGIAO:N", title=""),
        y=alt.Y("Voto:Q", title="", scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s")),
        xOffset=alt.XOffset("LEGEND:N", sort=x_order, scale=alt.Scale(paddingOuter=0.0))
    )
    
    return alt.layer(
        base.mark_bar(size=20, stroke="white").encode(
            fill=alt.Fill("LEGEND:N", sort=x_order, title="", scale=alt.Scale(range=color_range))
        ),
        base.mark_text(
            dx=20,
            angle=270,        
            fontSize=10).encode(text=alt.Text("Voto:Q", format=".4s"))
    )

def total_brasil(
    df_total:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 60_000_000]
)->alt.vegalite.v5.api.Chart:
    base_partidos = (
      alt.Chart(df_total).encode(
        x=alt.X("LEGEND:N", title=""),
      )
      .encode(
            y=alt.Y("Voto:Q", title="", scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s", ticks=False, labels=False)),
      )
    )
    
    return alt.layer(  
        base_partidos
        .mark_bar(size=20, stroke="white")
        .encode(
            fill=alt.Fill("LEGEND:N", legend=alt.Legend(title="Legenda", rowPadding=-10, symbolSize=250), scale=alt.Scale(range=color_range))
        ),
        base_partidos.mark_text(color="#000", dx=-20, angle=270, fontSize=10).encode(text=alt.Text("Voto:Q", format=".4s"))
    ).properties(height=200, title="")

def percentual_regiao(
    df_resumos:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    x_order=None,
    x_column="NM_REGIAO",
    y_domain:list[int]=[.2, .7],
    y_axis=alt.Axis(format=".0%")
)->alt.vegalite.v5.api.Chart:
    base = alt.Chart(df_resumos).encode(
        x=alt.X(f"{x_column}:N", title=""),
        y=alt.Y("PERCENTUAL:Q", title="", scale=alt.Scale(domain=y_domain), axis=y_axis)        
    )        
    return alt.layer(
        base.mark_line(point=alt.OverlayMarkDef(filled=True, size=100)).encode(
            color=alt.Color("LEGEND:N", sort=x_order, legend=alt.Legend(title="Legenda"),
                          scale=alt.Scale(range=color_range)
            )
        ),
        base.mark_text(
            fontSize=10,
            dy=-10,
        ).encode(text=alt.Text("PERCENTUAL:Q", format=".2%")),
    )

def box_plots_votting_by_region(
    df:pl.DataFrame,
    chart_title:str,
    scheme="blues",    
    color_column:str="ANO_ELEICAO",
    color_range:list[str]=[],
    parties_order=[],
    legend_title="Eleição",
    y_axis=True,
    x_sort=None,
    y_title="")->alt.vegalite.v5.api.Chart:

    if color_range:
        scale=alt.Scale(range=color_range)
    else:
        scale=alt.Scale(scheme=scheme)   

    yaxis= (alt.Axis(format='.1f', grid=True) if y_axis else None)
    
    base = (
      alt.Chart(df)
      .encode(
          x=alt.X(
            shorthand=f"{color_column}:N",
            sort=x_sort,
            axis=alt.Axis(
              title="", grid=True
            ),              
          ),
          color=alt.Color(
              f"{color_column}:N", 
              scale=scale
          ).legend(title=legend_title),        
      )
    )
    
    boxes = (
      base
      .mark_boxplot()
      .encode(
          y=alt.Y(
              "PCT_VOTOS_MUNIC:Q", 
              title=f"{y_title}", 
              axis=yaxis
          ).scale(domain=[0.,1.], zero=True, nice=True),
          tooltip=[
              alt.Tooltip("NM_REGIAO:N", title="Região"),
              alt.Tooltip("uf:N", title="Estado"),
              alt.Tooltip("nome:N", title="Município"),
              alt.Tooltip("PCT_VOTOS_MUNIC:Q", title="Votação", format=".2%"),
              alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Geral de Votos"),
              alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Total Votos Partido"),
              alt.Tooltip("PCT_VOTOS_MUNIC:Q", format=".2%", title="% Votos"),                
          ]
      )
    )
    
    bars = (
      base
      .transform_aggregate(
          PCT_VOTOS_UF="sum(PCT_VOTOS_MUNIC):Q",
          max="max(PCT_VOTOS_MUNIC):Q",
          mean="mean(PCT_VOTOS_MUNIC):Q",
          median="median(PCT_VOTOS_MUNIC):Q",
          min="min(PCT_VOTOS_MUNIC):Q",
          q1="q1(PCT_VOTOS_MUNIC):Q",
          q3="q3(PCT_VOTOS_MUNIC):Q",
          count="count()",
          groupby=["ANO_ELEICAO", "SG_PARTIDO", f"{color_column}"]
      ).mark_bar(opacity=.0, yOffset=3, y2Offset=-3)
      .encode(        
          y=alt.Y('q1:Q').scale(zero=False, nice=True),
          y2=alt.Y2('q3:Q'),
          tooltip=[
              alt.Tooltip('max:Q', title="Máximo", format=".2%"),
              alt.Tooltip('q3:Q', title="3o Quartil", format=".2%"),
              alt.Tooltip('median:Q', title="Mediana", format=".2%"),
              alt.Tooltip('q1:Q', title="1o Quartil", format=".2%"),
              alt.Tooltip('min:Q', title="Mínimo", format=".2%"),
          ]
      ).properties(height=250)
    )
    
    return alt.layer(boxes, bars).properties(title=f"{chart_title}")

##
###
def kde_plot(df:pl.DataFrame, 
             groupby:list[str]=['ANO_ELEICAO', 'NM_REGIAO'], 
             color_range:list[str]=year_range_colors, 
             color_column:str="ANO_ELEICAO", 
             legend_title:str="Eleição",
             titulo:str="", 
             num_cols:int=3)->alt.vegalite.v5.api.Chart:
  
  scale=alt.Scale(range=color_range)

  return (
    alt.Chart(
        df,
        width=180,
        height=180
    ).transform_density(
      'PCT_VOTOS_MUNIC',
      as_=['PCT_VOTOS_MUNIC', 'density'],
      groupby=groupby,
      #groupby=['NM_REGIAO','SG_PARTIDO'],
      #extent=[-.001, .3]
    ).mark_area(opacity=.6).encode(
      x=alt.X(
          "PCT_VOTOS_MUNIC:Q",
          title="",
          axis=alt.Axis(
            labelAngle=-90
          ), scale=alt.Scale(domain=[0., 1.])
      ),
      y=alt.Y('density:Q', axis=alt.Axis(labels=False), title="").stack(None),
      color=alt.Color(f"{color_column}:N", scale=scale, title=f"{legend_title}")
    ).add_params (
        alt.selection_interval(bind='scales')
    ).properties(height=250, width=250)
  )   

def scatter_votting_by_regions(
  df_tmp:pl.DataFrame, chart_title:str,
    scheme:str="blues",
    color_range=[],
    opacity=.8,
    x_sort=None,
    axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
    axis_col_titles:list[str]=["Perc. Votos em 2018","Perc. Votos em 2022"],
    axis_titles:list[str]=["2018","2022"],
    color_column:str="LEGEND",
    group_by="NM_REGIAO"
  )->alt.vegalite.v5.api.Chart:

  color = alt.condition(
        alt.datum.PCT_VOTOS_18 >= alt.datum.PCT_VOTOS_22,alt.value(color_range[0]),alt.value(color_range[1]) 
  )
  #color = alt.when(alt.datum.PCT_VOTOS_18 >= alt.datum.PCT_VOTOS_22).then("Legend:N").otherwise(alt.value("lightgray"))

  scatter_plot = (
      alt.Chart()
      .mark_point(opacity=opacity)
      .encode(
        x=alt.X(f'{axis_cols[0]}:Q', title=f"{axis_titles[0]}", axis=alt.Axis(labelAngle=-90)),
        #x=alt.X(f'{axis_cols[0]}:Q', title="", sort=x_sort, axis=alt.Axis(labelAngle=-90)),
        y=alt.Y(f'{axis_cols[1]}:Q', title=f"{axis_titles[1]}"),
        #y=alt.Y(f'{axis_cols[1]}:Q', title=f"", axis=alt.Axis(ticks=False, labels=False)),
        color=color,
        tooltip=[
          alt.Tooltip("NM_REGIAO:N", title="Região"),
          alt.Tooltip("uf:N", title="Estado"),
          alt.Tooltip("nome:N", title="Município"),
          #alt.Tooltip(f'{axis_cols[0]}:Q', format=".2%", title=f"{axis_col_titles[0]}"),
          #alt.Tooltip(f'{axis_cols[1]}:Q', format=".2%", title=f"{axis_col_titles[1]}"),

          alt.Tooltip("TOTAL_VOTOS_22:Q", format=",d", title=f"Total Votos Munic. {axis_titles[1]}"),
          alt.Tooltip("QT_VOTOS_VALIDOS_22:Q", format=",d", title=f"Votos {axis_titles[1]}"),
          alt.Tooltip(f'{axis_cols[1]}:Q', format=".2%", title=f"Perc. Votos {axis_titles[1]}"),

          alt.Tooltip("TOTAL_VOTOS_18:Q", format=",d", title=f"Total Votos Munic. {axis_titles[0]}"),
          alt.Tooltip("QT_VOTOS_VALIDOS_18:Q", format=",d", title=f"Votos {axis_titles[0]}"),
          alt.Tooltip(f'{axis_cols[0]}:Q', format=".2%", title=f"Perc. Votos {axis_titles[0]}"),

        ],
    ).add_params (
        alt.selection_interval(bind='scales')
    ).properties(
      width=170,
      height=170
    )
  )

  line_plot =(
      alt.Chart(pl.DataFrame({"x":[0,1], "y":[0,1]}))
      .mark_line(color="#9ECAE9")
      .encode(
          x=alt.X("x:Q"),
          y=alt.Y("y:Q")
      )
  )

  #posição do texto na caixa de resumo
  x_text_value=155
  y_text_value=190
  base = (
      alt.Chart()
      .mark_text(
        fontSize=10,
        align="left"
        #, baseline="bottom"
      ).encode(
          text="text:N"
      ).transform_calculate(
          Maior_22 = alt.datum.PCT_VOTOS_22 > alt.datum.PCT_VOTOS_18,
          Diff = alt.datum.PCT_VOTOS_22 - alt.datum.PCT_VOTOS_18
      )
  )

  base_count = (
      base
      .transform_aggregate(
          groupby=[f"{group_by}","Maior_22"],
          QT = "count(Maior_22)",
      ).transform_pivot(
        'Maior_22',
        groupby=[f"{group_by}"],
        value='QT'
      )
  )

  y_text_value+=10
  won_22 = (
    base_count.transform_calculate(
      text=f"{axis_titles[1]}: " + alt.datum.true
    ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top
    )
  )

  y_text_value+=10
  won_18 = (
      base_count.transform_calculate(
          text=f"{axis_titles[0]}: " + alt.datum.false
      ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top
    )
  )

#PCT_VOTOS_18
  y_text_value+=10
  median_pct_22 = (
      base.transform_aggregate(
          groupby=[f"{group_by}"],
          median_22 = "median(PCT_VOTOS_22)",
      ).transform_calculate(
        text=f"Mna. {axis_titles[1]}: " + alt.expr.format(alt.datum.median_22, ".2%")
      ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top,
    )
  )

  y_text_value+=10
  median_pct_18 = (
      base.transform_aggregate(
          groupby=[f"{group_by}"],
          median_18 = "median(PCT_VOTOS_18)",
      ).transform_calculate(
        text=f"Mna. {axis_titles[0]}: " + alt.expr.format(alt.datum.median_18, ".2%")
      ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top,
    )
  )

  y_text_value+=10
  median_diff = (
      base.transform_aggregate(
          groupby=[f"{group_by}"],
          median_diff = "median(Diff)",
      ).transform_calculate(
        text="Diff: " + alt.expr.format(alt.datum.median_diff, ".2%")
      ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top,
      )
  )

  box = (
    alt.Chart({'values':[{}]})
      .mark_rect(stroke='black', strokeWidth=1, opacity=1, cornerRadius=1.5, color="#000")
      .encode(
        x=alt.value(160),
        x2=alt.value(200),
        y=alt.value(180),
        y2=alt.value(240)
    )
  )

  return (
      alt.layer(scatter_plot, line_plot, won_22, won_18, median_pct_22, median_pct_18, median_diff, box, data=df_tmp)
  ).properties(
      title=f'{chart_title}', height=250, width=250
  )

def line_plot_capitals(
    df_poll_capitais:pl.DataFrame, 
    df_poll:pl.DataFrame,
    X_ORDER=[],
    color_range:list[str]=["#B3B2D6","#1A67AC"],
    y_domain:list[int]=[0, 1.]
)->alt.vegalite.v5.api.Chart:

    scale=alt.Scale(range=color_range)

    df_medians = (
        df_poll
        .group_by("LEGEND")
        .agg( pl.col("PCT_VOTOS_MUNIC").median() )
    )
   
    median_b:float = (
        df_medians
        .filter( (pl.col("LEGEND")==X_ORDER[0]) )
        .get_column("PCT_VOTOS_MUNIC").item()
    )
    
    median_a:float = (
        df_medians
        .filter( (pl.col("LEGEND")==X_ORDER[1]) )
        .get_column("PCT_VOTOS_MUNIC").item()
    )

    base = alt.Chart(df_poll_capitais).encode(
        x=alt.X("nome:N", title="", axis=alt.Axis(grid=True)),
        y=alt.Y(
            "PCT_VOTOS_MUNIC:Q", 
            title="", 
            scale=alt.Scale(domain=y_domain), 
            axis=alt.Axis(format=".1"))
    ).add_params(
        alt.selection_interval(bind='scales')
    )

    lines = base.mark_line(
      opacity=.9,
      point=alt.OverlayMarkDef(filled=True, opacity=.9, size=140)
    ).encode(
        color=alt.Color("LEGEND:N", title="Legenda", scale=alt.Scale(range=color_range)),
    tooltip=[
        alt.Tooltip('ANO_ELEICAO:N', title='Ano da Eleição'),
        alt.Tooltip('uf:N', title='Estado'),
        alt.Tooltip('nome:N', title='Capital'),
        alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Geral de Votos"),
        alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Total Votos Partido"),
        alt.Tooltip('PCT_VOTOS_MUNIC:Q', format=".2%", title='Perc. Votos')
    ]
    ).properties(height=250, width=400)
    
    dotted_lines = base.mark_line(opacity=.4, strokeDash=[12,8], color="#5EAFC0").encode(
        alt.Y("min(PCT_VOTOS_MUNIC):Q"),
        alt.Y2("max(PCT_VOTOS_MUNIC):Q")
    )
    
    df_diff = df_poll_capitais.filter(
      pl.col("LEGEND")==X_ORDER[0]
    ).join(
      (df_poll_capitais.filter(pl.col("LEGEND")==X_ORDER[1])), on="nome"
    ).select(
      ["nome","QT_VOTOS_VALIDOS","QT_VOTOS_VALIDOS_right","PCT_VOTOS_MUNIC","PCT_VOTOS_MUNIC_right"]
    ).rename({"QT_VOTOS_VALIDOS":"QT_VOTOS_18",
            "QT_VOTOS_VALIDOS_right":"QT_VOTOS_22",
            "PCT_VOTOS_MUNIC":"PCT_VOTOS_18",
            "PCT_VOTOS_MUNIC_right":"PCT_VOTOS_22"})
    
    diff_text = alt.Chart(df_diff).transform_calculate(
      text=alt.expr.if_((alt.datum.QT_VOTOS_22-alt.datum.QT_VOTOS_18)>0, "+", "") +
        alt.expr.format((alt.datum.QT_VOTOS_22-alt.datum.QT_VOTOS_18), ".3s"),
      y=(alt.datum.PCT_VOTOS_18 +  (alt.datum.PCT_VOTOS_22-alt.datum.PCT_VOTOS_18)/2)
    ).mark_text(angle=270, fontSize=10, fontWeight=500).encode(
      x=alt.X("nome:N", title=""),
      y=alt.Y('y:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
    )

    off_set = -10 if median_b > median_a else 10

    rule_xpos = df_poll_capitais.filter((pl.col("NM_REGIAO")==f"{region}") & (pl.col("LEGEND")==X_ORDER[0])).select(pl.col("nome").min()).item()

    base = alt.Chart(
        pl.DataFrame({'x':[rule_xpos], 'y': [median_b], 'text': [f'Mna. {X_ORDER[0]} {round(median_b*100,2)}%']})
    ).encode(y='y')
    
    rule_b=base.mark_rule(strokeDash=(1,3), color=COLOR_RANGE[0])
    
    annotate_b = base.mark_text(fontSize=10,dx=40, dy=(median_b+off_set)).encode(
        x='x',
        text='text'
    )

    rule_xpos = df_poll_capitais.filter((pl.col("NM_REGIAO")==f"{region}") & (pl.col("LEGEND")==X_ORDER[1])).select(pl.col("nome").min()).item()
    base = alt.Chart(
        pl.DataFrame({'x':[rule_xpos], 'y': [median_a], 'text': [f'Mna. {X_ORDER[1]} {round(median_a*100,2)}%']})
    ).encode(y='y')
    
    rule_a=base.mark_rule(strokeDash=(1,3), color=COLOR_RANGE[1])
    
    annotate_a = base.mark_text(fontSize=10, dx=40, dy=(median_a-off_set)).encode(
        x='x',
        text='text'
    )                
    
    rule_a = alt.Chart(
        pl.DataFrame({'y': [median_a]})
    ).mark_rule(strokeDash=(1,3), color=COLOR_RANGE[1]).encode(y='y')   
    
    return alt.layer(lines, dotted_lines, diff_text, rule_b,annotate_b, rule_a,annotate_a)
    
def bar_plot_capitals(
    df_diff_capitais:pl.DataFrame,
    COLOR_RANGE=[],
    region_median:float=0                
)->alt.vegalite.v5.api.Chart:
    predicate = alt.datum.Diff > 0
    color = alt.when(predicate).then(alt.value(COLOR_RANGE[1])).otherwise(alt.value(COLOR_RANGE[0]))
    dx=alt.expr(
        alt.expr.if_(predicate > 0, 18, -20)
    )     
    base = alt.Chart(df_diff_capitais).mark_bar(opacity=.9).encode(
        x=alt.X("nome:N", axis=alt.Axis(grid=True), title=""),
        y=alt.Y("Diff:Q", title="",
                scale=alt.Scale(domain=[-1,1])
               ),
        color=color,
    ).add_params (
        alt.selection_interval(bind='scales')
    )

    #rule_ypos:float = df_diff.filter(pl.col("NM_REGIAO")==region).get_column("Mna. Diff").item()                
    text_pos = df_diff_capitais.select(pl.col("nome").min()).get_column("nome").item()
    
    rule_base = alt.Chart(
        pl.DataFrame({'x':[text_pos], 'y': [region_median], 'text': [f'Mna. Dif. {round(region_median*100,2)}%']})
    ).encode(y='y')                
    rule=rule_base.mark_rule(strokeDash=(1,3), color="#000")

    annotate= rule_base.mark_text(fontSize=10,dx=25, dy=-10).encode(
        x='x',
        text=alt.Text('text')
    )
    
    return alt.layer(
        base,
        base.mark_text(
            dx=dx,
            fontSize=9,
            angle=270
        ).encode(
            text=alt.Text("Diff:Q", format=".2%"),
            color=alt.value("#000")
        ),rule,annotate
    )     
##################################################################################
### Carga dos dados
#lista das regiões brasileiras
df_regioes = get_regioes()
regions_list = list(df_regioes.get_column("NM_REGIAO").unique().sort().to_list()) #apenas as grandes regiões brasileiras

#dados das eleições
df_poll_18:pl.DataFrame = get_eleicao_18()
df_poll_18 = df_poll_18.filter( (pl.col("CD_CARGO")==1) & (pl.col("SG_REGIAO")!="ZZ") )#apenas presidente 
df_poll_18 = df_poll_18.drop("NR_ZONA") #remove a zona

df_poll_22:pl.DataFrame = get_eleicao_22()
#apenas presidente 
df_poll_22 = df_poll_22.filter( (pl.col("CD_CARGO")==1) & (pl.col("SG_REGIAO")!="ZZ") )
df_poll_22 = df_poll_22.drop("NR_ZONA")

cols_list:list[str] = df_poll_18.columns
cols_list.remove("QT_VOTOS_VALIDOS")

df_poll_18 = df_poll_18.group_by(cols_list).sum()
df_poll_22 = df_poll_22.group_by(cols_list).sum()

df_poll_18 = df_poll_18.with_columns(
    pl.col("QT_VOTOS_VALIDOS").sum().over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC"),
    (pl.col("QT_VOTOS_VALIDOS")/ pl.col("QT_VOTOS_VALIDOS").sum().over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
)
df_poll_22 = df_poll_22.with_columns(
    pl.col("QT_VOTOS_VALIDOS").sum().over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC"),
    (pl.col("QT_VOTOS_VALIDOS")/ pl.col("QT_VOTOS_VALIDOS").sum().over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
)


#plot da classificação ideológica dos partidos políticos brasileiros segundo Bolognesi
df_partidos = get_partidos()
df_colors = parties_colors(df_partidos) #define uma cor para cada partido político baseado na sua ideologia

# Carga munícipios
df_municipios = get_municipios()
df_capitais = get_capitais()

# Título da Ferramenta
st.title("Eleições Presidenciais 1o Turno 🗳️")

## Cria as abas
tabResumos, tabInter = st.tabs(["Geral", "Interatividade"]) 

with tabResumos:
    row = st.columns(1, gap='small', border=True)
    with row[0]:
        st.markdown("###### Classificação Ideológica dos Partidos Políticos Brasileiros", unsafe_allow_html=True)
        st.altair_chart(
            class_ideologica_chart(
                df_partidos, df_colors
            ).properties(
                height=330, title=""
            ).configure_axis(
                grid=True,
                labelColor='#000',
                titleColor='#000'
            ).configure_legend(
                fillColor='#EEEEEE',
                padding=10,
                cornerRadius=4,
                orient='bottom'
            ), 
            use_container_width=True
        )

    row = st.columns(1, gap='small', border=True)
    with row[0]:
        st.markdown("###### Votação por Partidos", unsafe_allow_html=True)
        pres_piramide = pyramid_votting_chart(df_poll_18, df_poll_22, df_colors, list([1]), '')
        st.altair_chart(
            pres_piramide.configure_axis(
                grid=True,
                labelColor='#000',
                titleColor='#000'
            ).configure_title(
                anchor="middle", orient="bottom"
            ), 
            use_container_width=True
        ) 

with tabInter:
    st.write(":mega: **Todos os gráficos e métricas foram construídos baseados nos votos válidos dos partidos em cada município brasileiro nas eleições presidenciais de 2018 e 2022.**")
   
    row = st.columns(1, gap='small', border=True)
    cruzamentos:list[str] = ["PT 2022 x PL 2022", "PT 2022 x PSL 2018", "PT 2022 x PT 2018", 
                        "PL 2022 x PSL 2018", "PL 2022 x PT 2018", "PT 2018 x PSL 2018"]
    # Linha com os filtros
    with row[0]:
        st.markdown("###### Selecione os Filtros:", unsafe_allow_html=True)
        cells = st.columns((1,1), gap='small')
        with cells[0]:
            regioes = st.multiselect('Regiões', regions_list, default=regions_list)
        with cells[1]:
            disputa = st.radio("Cruzamentos", cruzamentos, horizontal=True)

    #divide os dados relativos à escolha do cruzamento
    disputa_arr:list[str] = disputa.split(" ")
    partido_b:str = disputa_arr[0]
    eleicao_b:int = np.int16( disputa_arr[1] )
    partido_a:str = disputa_arr[3]
    eleicao_a:int = np.int16( disputa_arr[4] )

    if regioes:
        df_poll_a:pl.DataFrame=df_poll_18.filter(pl.col("NM_REGIAO").is_in(regioes)) if eleicao_a==2018 else df_poll_22.filter(pl.col("NM_REGIAO").is_in(regioes))
        df_poll_b:pl.DataFrame=df_poll_18.filter(pl.col("NM_REGIAO").is_in(regioes)) if eleicao_b==2018 else df_poll_22.filter(pl.col("NM_REGIAO").is_in(regioes))
    else:
        df_poll_a:pl.DataFrame=df_poll_18 if eleicao_a==2018 else df_poll_22
        df_poll_b:pl.DataFrame=df_poll_18 if eleicao_b==2018 else df_poll_22  

    ## datasets para plotar os gráficos
    df_poll_partido_a = (
        df_poll_a
            .filter(pl.col("SG_PARTIDO")==partido_a)
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))
            .select(["ANO_ELEICAO","NM_REGIAO","uf","CD_MUNICIPIO","nome","SG_PARTIDO",
                     "PCT_VOTOS_MUNIC","TOTAL_VOTOS_MUNIC","QT_VOTOS_VALIDOS"])
            .with_columns(
                pl.lit(f"{partido_a} {eleicao_a}").alias("LEGEND")
            ) 
    )
    
    df_poll_partido_b = (
        df_poll_b
            .filter(pl.col("SG_PARTIDO")==partido_b)
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))
            .select(["ANO_ELEICAO","NM_REGIAO","uf","CD_MUNICIPIO","nome","SG_PARTIDO","PCT_VOTOS_MUNIC","TOTAL_VOTOS_MUNIC","QT_VOTOS_VALIDOS"])
            .with_columns(
                pl.lit(f"{partido_b} {eleicao_b}").alias("LEGEND")
            )    
    )

    #dataset para plotar os boxplot
    df_poll_box = pl.concat([df_poll_partido_b,df_poll_partido_a])
    #st.write(df_poll_box)
    df_tmp = df_poll_partido_b.join(df_poll_partido_a, on="CD_MUNICIPIO")
    df_tmp = df_tmp.rename(
        {"QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_22",
         "QT_VOTOS_VALIDOS_right":"QT_VOTOS_VALIDOS_18",
         "PCT_VOTOS_MUNIC":"PCT_VOTOS_22",
         "PCT_VOTOS_MUNIC_right": "PCT_VOTOS_18",
         "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_22",
         "TOTAL_VOTOS_MUNIC_right": "TOTAL_VOTOS_18"})
    
    df_resumos = (pl.concat([
          (df_poll_partido_b
               .group_by(["SG_PARTIDO","NM_REGIAO"])
                .agg(
                    pl.col("QT_VOTOS_VALIDOS").sum().alias("Voto")
                ).join((
                        df_poll_partido_b
                            .select(["NM_REGIAO","TOTAL_VOTOS_MUNIC"])
                            .group_by("NM_REGIAO")
                            .agg(pl.col("TOTAL_VOTOS_MUNIC").sum().alias("TOTAL_REGIAO"))
                ), on="NM_REGIAO").with_columns(
                    pl.lit(f"{partido_b} {eleicao_b}").alias("LEGEND"),
                    pl.lit(f"{eleicao_b}").alias("ANO_ELEICAO")
                )               
          ),
          (df_poll_partido_a
               .group_by(["SG_PARTIDO","NM_REGIAO"])
                .agg(
                    pl.col("QT_VOTOS_VALIDOS").sum().alias("Voto")
                ).join((
                        df_poll_partido_a
                            .select(["NM_REGIAO","TOTAL_VOTOS_MUNIC"])
                            .group_by("NM_REGIAO")
                            .agg(pl.col("TOTAL_VOTOS_MUNIC").sum().alias("TOTAL_REGIAO"))
                ), on="NM_REGIAO").with_columns(
                    pl.lit(f"{partido_a} {eleicao_a}").alias("LEGEND"),
                    pl.lit(f"{eleicao_a}").alias("ANO_ELEICAO")
                )
          )]).with_columns(
              (pl.col("Voto")/pl.col("TOTAL_REGIAO")).alias("PERCENTUAL")
          )
    )    

    #st.write(df_tmp)
    #st.write(df_capitais)
    df_poll_capitais = (df_poll_box
        .select(["LEGEND","ANO_ELEICAO","NM_REGIAO","uf","CD_MUNICIPIO","nome","TOTAL_VOTOS_MUNIC","QT_VOTOS_VALIDOS","PCT_VOTOS_MUNIC"])
        .join(df_capitais, left_on="CD_MUNICIPIO", right_on="codigo_tse")
    ).select(~cs.ends_with("_right"))
    
    if eleicao_a<eleicao_b:
        X_ORDER = [f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
    elif eleicao_b<eleicao_a:
        X_ORDER = [f"{partido_b} {eleicao_b}", f"{partido_a} {eleicao_a}"]
    else:
        X_ORDER = [f"{partido_b} {eleicao_b}", f"{partido_a} {eleicao_a}"] if partido_a=="PT" else [f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
        

    if eleicao_a==eleicao_b:
        COLOR_RANGE = ["#BC3439","#347DB6"] if partido_a=="PT" else ["#347DB6", "#BC3439"]
    elif partido_a==partido_b:#só pode ser o PT
        COLOR_RANGE = ["#D68186","#BC3439"]
    elif partido_a=="PT":
        COLOR_RANGE = ["#347DB6", "#BC3439"]
    elif partido_b=="PT":
        COLOR_RANGE = ["#347DB6", "#BC3439"]
    else:
       COLOR_RANGE= ["#7e81e9","#bfc1f4"]
            
    tabMapas, tabGrafs, tabCapitais = st.tabs([":earth_americas: Mapas e Indicadores", ":chart_with_upwards_trend: Regiões e UFs", ":cityscape: Capitais"]) 

    #mapas do brasil e resumos
    with tabMapas:
        breaks = [.25, .4, .55],
        domain = ["<=25%", ">25%,<=40%", ">40%,<=55%",">55%"]

        row = st.columns((3.5, 3.5, 3.5), gap='small', border=False)
        with row[0]:
            #cria o mapa
            st.markdown(f'#### {partido_b} {eleicao_b}')
            mapa, df_choropleth_b = mapa_eleitoral(df_eleicao=df_poll_b, 
                   df_municipios=df_municipios,
                   df_capitais=df_capitais,
                   partido=partido_b, 
                   breaks = breaks,
                   domain = domain, 
                   opacity=.8,
                   legend_sort=domain[::-1],
                   rev_Schmeme=False)
            
            mapa = mapa.configure_legend(
                    titleColor="#000",
                    labelColor="#000",            
                      offset=-20,
                      titleFontSize=12,
                      labelFontSize=10            
                    )            
            st.altair_chart(mapa, use_container_width=True)                

        with row[1]:
            #cria o mapa 
            st.markdown(f'#### {partido_a} {eleicao_a}')             
            mapa, df_choropleth_a = mapa_eleitoral(df_eleicao=df_poll_a, 
                   df_municipios=df_municipios,
                   df_capitais=df_capitais,
                   partido=partido_a, 
                   breaks = breaks,
                   domain = domain,
                   opacity=.8,
                   legend_sort=domain[::-1],
                   rev_Schmeme=False)
            mapa=mapa.configure_legend(
                    titleColor="#000",
                    labelColor="#000",            
                      offset=-20,
                      titleFontSize=12,
                      labelFontSize=10
                    )
            st.altair_chart(mapa, use_container_width=True)  
            
        with row[2]: 
            st.markdown(f'#### Diferença {partido_b} {eleicao_b} - {partido_a} {eleicao_a}')
            breaks = [-.1, -.01, .01, .1]
            domain=["<-10%", ">-10% e <=-1%", ">-1%,<=1%",">1% e <=10%", ">10%"]   
            legend_title = f"Dif. {partido_b} {eleicao_b} - {partido_a} {eleicao_a}"
            mapa = prepara_mapa_diferenca(        
                df_choropleth_a = df_choropleth_a, 
                df_choropleth_b = df_choropleth_b, 
                df_capitais=df_capitais,
                breaks = breaks,
                domain=domain,
                chart_title="", 
                rev_Schmeme=False,
                opacity=.8,
                legend_sort=domain[::-1],
                tooltip_title_22=[f"Total Votos Munic. {eleicao_b}", f"Tot Votos {partido_b} {eleicao_b}", f"Perc. Votos {partido_b} {eleicao_b}"],
                tooltip_title_18=[f"Total Votos Munic. {eleicao_a}", f"Tot Votos {partido_a} {eleicao_a}", f"Perc. Votos {partido_a} {eleicao_a}"],
                legend_title=legend_title
            )
            mapa=mapa.configure_legend(
                titleColor="#000",
                labelColor="#000",
                offset=-20,
                titleFontSize=12,
                labelFontSize=10,              
            )            
            st.altair_chart(mapa, use_container_width=False)        

        #indicadores
        total_votos_18:np.int32 = (
            df_poll_18
            .get_column("QT_VOTOS_VALIDOS").sum()
        )        

        total_votos_22:np.int32 = (
            df_poll_22
            .get_column("QT_VOTOS_VALIDOS").sum()
        )

        total_votos_part_b:np.int32 = (
            df_poll_b.filter(pl.col("SG_PARTIDO")==partido_b)
            .get_column("QT_VOTOS_VALIDOS").sum()        
        )
        total_votos_part_a:np.int32 = (
            df_poll_a.filter(pl.col("SG_PARTIDO")==partido_a)
            .get_column("QT_VOTOS_VALIDOS").sum()        
        )        

        #Rosquinhas
        total_votos_a:np.int32 = (
            df_poll_a
            .get_column("QT_VOTOS_VALIDOS").sum()
        )
        
        total_votos_b:np.int32 = (
            df_poll_b
            .get_column("QT_VOTOS_VALIDOS").sum()
        )
        
        color:str = "red" if partido_b=="PT" else "blue"
        perc_part_b = round(100 * total_votos_part_b/total_votos_b,2)
        donut_part_b = make_donut(perc_part_b, partido_b, color)
        
        color:str = "red" if partido_a=="PT" else "blue"
        perc_part_a = round(100 * total_votos_part_a/total_votos_a,2)
        donut_part_a = make_donut(perc_part_a, partido_a, color)

        #Linha dos indicadores
        st.markdown(f'#### Indicadores')
        row = st.columns((2, 1), gap='small', border=False)        
        with row[0]:
            cells = st.columns((1,1,1), gap='small', border=False, vertical_alignment="center")
            with cells[0]:
                if not (eleicao_b==eleicao_a and eleicao_a==2018):
                    st.metric(label=f'Votos Válidos em {eleicao_b}', value=format_number(total_votos_22).replace(".",","), 
                          #delta=format_number(total_votos_22-total_votos_18).replace(".",",")
                             )
            with cells[1]:
                st.metric(label=f"Votos {partido_b} {eleicao_b}", value=format_number(total_votos_part_b).replace(".",","),
                 #delta=format_number(total_votos_part_b-total_votos_part_a).replace(".",",")
                )
            with cells[2]:
                st.altair_chart(donut_part_b, use_container_width=True) 
                
        row = st.columns((2, 1), gap='small', border=False)
        with row[0]:
            cells = st.columns((1,1,1), gap='small', border=False, vertical_alignment="center")
            with cells[0]:
                if not (eleicao_b==eleicao_a and eleicao_a==2022):                
                    st.metric(label=f'Votos Válidos em {eleicao_a}', value=format_number(total_votos_18).replace(".",","),
                        #delta=format_number(total_votos_18-total_votos_22).replace(".",",")
                    )
            with cells[1]:
                st.metric(label=f"Votos {partido_a} {eleicao_a}", value=format_number(total_votos_part_a).replace(".",","),
                 #delta=format_number(total_votos_part_a-total_votos_part_b).replace(".",",")
            ) 
            with cells[2]:
                st.altair_chart(donut_part_a, use_container_width=True) 
            
        row = st.columns((2, 1), gap='large', border=False) 

        with row[0]:
            #st.write(X_ORDER)
            st.markdown(f'#### Resumos Votos Válidos')
            partb_parta_abs = votacao_regiao(df_resumos, x_order=X_ORDER, color_range=COLOR_RANGE).properties(width=300, height=200, title="")            
            #
            df_total = df_resumos.group_by(["SG_PARTIDO","ANO_ELEICAO","LEGEND"]).agg(pl.col("Voto").sum())
            total_partidos = total_brasil(df_total, color_range=COLOR_RANGE)
            partb_parta_abs = alt.hconcat(partb_parta_abs, total_partidos)
            #Votação absoluta
            st.altair_chart(partb_parta_abs
                    .resolve_scale(y='shared',color="independent")
                    .configure(
                        concat=alt.CompositionConfig(spacing=2)
                    ), use_container_width=False)
            
            #Crescimento do partido
            if (partido_b == "PT" and partido_a=="PT" ) or (partido_b=="PL" and partido_a=="PSL"):
                df_crescimento = df_tmp.group_by("NM_REGIAO").agg(
                    pl.col("QT_VOTOS_VALIDOS_22").sum().alias("Votos_22"),
                    pl.col("QT_VOTOS_VALIDOS_18").sum().alias("Votos_18"))             
                if (partido_b=="PL"):
                    color_range = COLOR_RANGE
    
                cresc_br=(df_crescimento.with_columns(
                            pl.lit("Brasil").alias("BR")
                        ).group_by("BR").agg(pl.col("Votos_22").sum(), pl.col("Votos_18").sum())
                    )
                cresc_br = crescimento(cresc_br, x_column="BR", legend=X_ORDER,  
                                    y_domain=[0,70_000_000], color_range=COLOR_RANGE,
                                    y_axis=alt.Axis(ticks=False, labels=False)).properties(width=60, height=200, title="") 
                cresc = crescimento(df_crescimento, legend=X_ORDER,  y_domain=[0,70_000_000], color_range=COLOR_RANGE).properties(width=270, height=200, title="Crescimento") 
    
                st.altair_chart(alt.hconcat(cresc, cresc_br), use_container_width=False) 

            df_resumo_br = (df_resumos.group_by("LEGEND").agg(
                (pl.col("Voto").sum()/pl.col("TOTAL_REGIAO").sum()).alias("PERCENTUAL")                
            ))
            line_perc_br = percentual_regiao(df_resumo_br, x_column="LEGEND", x_order=X_ORDER, 
                                             color_range=COLOR_RANGE, y_axis=alt.Axis(ticks=False, labels=False)
                                            ).properties(width=60, height=200, title="")
            
            line_perc = percentual_regiao(df_resumos, x_order=X_ORDER, color_range=COLOR_RANGE).properties(width=270, height=200)
            st.altair_chart(
                alt.hconcat(
                    line_perc,line_perc_br
                ).resolve_scale(
                    y='shared'
                ).configure(
                    concat=alt.CompositionConfig(spacing=2)
                ), 
                use_container_width=False
            )
            
    with tabGrafs:
        tabRegioes, tabBoxplotUfs, tabScatterUfs = st.tabs([":flag-br: Brasil e Regiões", "Boxplots por UFs","Dispersões por UFs"])         
        with tabRegioes:
            stat_regions = (np.sort( regioes ) if regioes else regions_list)
    
            #Resumo das regiões filtradas
            region_boxes = box_plots_votting_by_region(
                df_poll_box,
                chart_title=f"",
                x_sort = X_ORDER,
                color_range=COLOR_RANGE,
                color_column="LEGEND",
                legend_title="Legenda"
            )
    
            kde = kde_plot(
                df_poll_box.select(["ANO_ELEICAO","SG_PARTIDO","LEGEND", "NM_REGIAO","PCT_VOTOS_MUNIC"]),
                groupby=["ANO_ELEICAO","LEGEND"],
                color_column="LEGEND",
                color_range=COLOR_RANGE,
                legend_title="Legenda", titulo="", num_cols=5)#.configure_axis(grid=True).configure_view(strokeWidth=1)
            
            _color_range = COLOR_RANGE
            if (partido_b=="PL" and partido_a=="PSL") or (partido_b=="PL" and partido_a=="PT"):
               _color_range = COLOR_RANGE[::-1]
            scatter = scatter_votting_by_regions(
                df_tmp,
                group_by="LEGEND",
                chart_title="",
                opacity=.3,
                color_range=_color_range,
                axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
                axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
            )
            resumo = "Brasil" if len(stat_regions)==5 else ", ".join(stat_regions)
            st.markdown(f'#### Resumo: {resumo}')
            st.altair_chart(
                (kde | region_boxes | scatter),
                use_container_width=False
            )
            
            for region in stat_regions:
                st.markdown(f'#### {region}')
                region_boxes = box_plots_votting_by_region(
                    df_poll_box.filter(pl.col("NM_REGIAO")==region),
                    chart_title=f"",
                    x_sort = X_ORDER,
                    color_range=COLOR_RANGE,
                    color_column="LEGEND",
                    legend_title="Legenda"
                )
        
                kde = kde_plot(
                    df_poll_box.filter(pl.col("NM_REGIAO")==region).select(["ANO_ELEICAO","SG_PARTIDO","LEGEND", "NM_REGIAO","PCT_VOTOS_MUNIC"]),
                    groupby=['NM_REGIAO','SG_PARTIDO',"LEGEND"],
                    color_column="LEGEND",
                    color_range=COLOR_RANGE,
                    legend_title="Legenda", titulo="", num_cols=5)#.configure_axis(grid=True).configure_view(strokeWidth=1)

                _color_range = COLOR_RANGE
                if (partido_b=="PL" and partido_a=="PSL") or (partido_b=="PL" and partido_a=="PT"):
                   _color_range = COLOR_RANGE[::-1]                
                scatter = scatter_votting_by_regions(
                    df_tmp.filter(pl.col("NM_REGIAO")==region),
                    chart_title="",
                    opacity=.3,
                    x_sort = X_ORDER,
                    color_range=_color_range,
                    axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
                    axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
                )
            
                st.altair_chart(
                    (kde | region_boxes | scatter),
                    use_container_width=False
                )
        with tabBoxplotUfs:
            for region in stat_regions:
                st.markdown(f'#### {region}')
                columns = 9 
                region_boxes = box_plots_votting_by_region(
                    df_poll_box.filter(pl.col("NM_REGIAO")==region),
                    chart_title=f"",
                    x_sort = X_ORDER,
                    color_range=COLOR_RANGE,
                    color_column="LEGEND",
                    legend_title="Legenda"
                )
                st.altair_chart(
                    (
                        region_boxes
                        .facet(columns=columns, facet=alt.Facet("uf:N", title=""))
                        .configure_axis(grid=True)
                        .configure_view(continuousHeight=1, continuousWidth=1, strokeWidth=1, stroke='#cecece')
                    ),
                    use_container_width=False
                )                
        with tabScatterUfs:
            for region in stat_regions:
                columns = 3 if region=="Nordeste" else 4
                st.markdown(f'#### {region}')        
                _color_range = COLOR_RANGE
                if (partido_b=="PL" and partido_a=="PSL") or (partido_b=="PL" and partido_a=="PT"):
                   _color_range = COLOR_RANGE[::-1]
                
                scatter = scatter_votting_by_regions(
                    df_tmp.filter(pl.col("NM_REGIAO")==region),
                    chart_title="",
                    opacity=.3,
                    x_sort = X_ORDER,
                    color_range=_color_range,
                    axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
                    axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
                )                
                st.altair_chart(
                    (
                        scatter
                        .facet(columns=columns, facet=alt.Facet("uf:N", title=""))
                        .configure_axis(grid=True)
                        .configure_view(continuousHeight=1, continuousWidth=1, strokeWidth=1, stroke='#cecece')
                    ),
                    use_container_width=False
                )
    with tabCapitais:        
        df_diff = (
            df_poll_box.filter(pl.col("LEGEND")==X_ORDER[0])
            .with_columns(
                pl.col("PCT_VOTOS_MUNIC").alias("PCT_VOTOS_18")
            ).select(["NM_REGIAO","CD_MUNICIPIO","PCT_VOTOS_18"])
        ).join(
            (
                df_poll_box.filter(pl.col("LEGEND")==X_ORDER[1])
                .with_columns(
                    pl.col("PCT_VOTOS_MUNIC").alias("PCT_VOTOS_22")
                ).select(["NM_REGIAO","CD_MUNICIPIO","PCT_VOTOS_22"])
            ), on="CD_MUNICIPIO"
        ).with_columns(
            (pl.col("PCT_VOTOS_22")-pl.col("PCT_VOTOS_18")).alias("Diff")
        ).group_by("NM_REGIAO").agg(pl.col("Diff").median().alias("Mna. Diff"))
        
        df_diff_capitais = (
            df_poll_capitais
            .filter(pl.col("LEGEND")==X_ORDER[0])
            .join((df_poll_capitais.filter(pl.col("LEGEND")==X_ORDER[1])), on="nome")
            .select(["nome","NM_REGIAO", "QT_VOTOS_VALIDOS","QT_VOTOS_VALIDOS_right","PCT_VOTOS_MUNIC","PCT_VOTOS_MUNIC_right"])
            .rename({"QT_VOTOS_VALIDOS":"QT_VOTOS_18",
                "QT_VOTOS_VALIDOS_right":"QT_VOTOS_22",
                "PCT_VOTOS_MUNIC":"PCT_VOTOS_18",
                "PCT_VOTOS_MUNIC_right":"PCT_VOTOS_22"})
            .with_columns(
                (pl.col("PCT_VOTOS_22")-pl.col("PCT_VOTOS_18")).alias("Diff")
            )
        )            

        max_domain = df_poll_capitais.select(pl.col("PCT_VOTOS_MUNIC").max()).item()+.1
        min_domain = df_poll_capitais.select(pl.col("PCT_VOTOS_MUNIC").min()).item()-.1                
        y_domain= [min_domain, max_domain]

        st.markdown('#### Resumo Capitais')
        line_plot = line_plot_capitals(
            df_poll_capitais,
            df_poll=df_poll_box,
            X_ORDER=X_ORDER,
            color_range=COLOR_RANGE,
            y_domain=y_domain,
        )  
        
        st.altair_chart(
            (line_plot).properties(height=300, width=800),
            use_container_width=False
        )
        
        for region in stat_regions:
            st.markdown(f'#### {region}')    

            region_median = df_diff.filter(pl.col("NM_REGIAO")==region).get_column("Mna. Diff").item()
            
            bar_plot = bar_plot_capitals(
                df_diff_capitais.filter(pl.col("NM_REGIAO")==region),
                COLOR_RANGE = COLOR_RANGE,
                region_median = region_median
            )
            
            line_plot = line_plot_capitals(
                df_poll_capitais.filter(pl.col("NM_REGIAO")==region),
                df_poll=df_poll_box.filter(pl.col("NM_REGIAO")==region),
                X_ORDER=X_ORDER,
                color_range=COLOR_RANGE,
                y_domain=y_domain,
            )
            st.altair_chart(
                
                alt.hconcat(
                    line_plot.properties(height=250, width=450),
                    bar_plot.properties(height=250)
                ).configure_view(continuousHeight=1, continuousWidth=1, strokeWidth=2, stroke='#cecece'),
                use_container_width=False
            )            

rodape = st.columns(1)
with rodape[0]:
    with st.expander('Sobre', expanded=True):
        st.write('''
            - S. de Oliveira, Antonio Fagner
            - :orange[**Análise da Migração dos Votos Regionais entre as Eleições Presidenciais Brasileiras de 2018 e 2022**]
            - Monografia (especialização) – Universidade Federal do Rio Grande do Sul. Curso de Especialização em Ciência de Dados, Porto Alegre, BR–RS, 2025
            - Orientadora: Profa. Dra. Lisiane Selau
            - Co-orientador: Profa. Dra. Viviane P. Moreira
            - Ciência de Dados. Eleições Brasileiras. Visualização de Dados.
            ''')