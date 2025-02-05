## https://blog.streamlit.io/crafting-a-dashboard-app-in-python-using-streamlit/
#######################
# Import libraries
import streamlit as st
#import pandas as pd
import altair as alt
#import plotly.express as px
import polars as pl
import numpy as np
import pandas as pd


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

alt.themes.enable("dark")

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

##
##   Gera uma comparação da votação dos partido para um cargo entre 2018 e 2022
def general_votting_line_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,  
                      position:list[int], chart_title:str, total_parties:int=10,
                      range:list[str]=['#F58518','#4C78A8'])->alt.vegalite.v5.api.Chart:
  df_tmp_18 = (df_2018
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

  df_tmp_22 = (df_2022
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
  # concatena as votações de 22 e 18 para os cargos em position
  df_tmp = pl.concat([df_tmp_22, df_tmp_18])

  # os registros dos K partidos mais votados em 2018
  top_k_22=df_tmp_22.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SIGLA_2022","QT_VOTOS_VALIDOS"))

  # faz join entre com os 15 partidos mais votados em 22 usando o campo QT_ORDER
  # para ordenar o chart
  df_tmp = (df_tmp
      .join(top_k_22, on="SIGLA_2022", how="inner")
      .with_columns(
          QT_ORDER = pl.col("QT_VOTOS_VALIDOS_right")
      )
      .drop(pl.col("QT_VOTOS_VALIDOS_right"))
  )

  base = (
    alt.Chart(df_tmp, title=f"{chart_title}")
    .mark_line(
        point=alt.OverlayMarkDef(filled=True, size=100),
        opacity=.7
    )
  )

  lines=base.encode(
    x=alt.X('SIGLA_2022:N', title="", sort=alt.SortField(field="QT_ORDER")),
    y=alt.Y('PCT:Q', title="", axis=alt.Axis(format="%")),
    color=alt.Color(
        shorthand='ANO_ELEICAO:N', title="Eleição",
        scale = alt.Scale(
            domain=[2018,2022],
            range=range,
        )
    ),
    tooltip=[
        alt.Tooltip('SIGLA_2022:N', title="Partido"),
        alt.Tooltip('ANO_ELEICAO:O', title="Ano Eleição"),
        alt.Tooltip('QT_VOTOS_VALIDOS:Q', format=",d", title="Total Votos Partido"),
        alt.Tooltip('QT_VOTOS_BR:Q', format=",d",  title="Total de Votos"),
        alt.Tooltip('PCT:Q', format=".2%",  title="% Votos"),
    ]
  ).properties(
          #width=300,
          height=250,
  )
  dotted_lines = (
    base.mark_line(opacity=0.8, strokeDash=[2,2], color="#F58518").encode(
        alt.X("SIGLA_2022:O", sort=alt.SortField(field="QT_ORDER")),
        alt.Y("min(PCT):Q"),
        alt.Y2("max(PCT):Q"),
    )
  )
  return alt.layer(lines, dotted_lines)


##
###   Gera uma comparação da votação dos partido para um cargo entre 2018 e 2022 em forma de pirâmide
def pyramid_votting_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,
                      position:list[int], chart_title:str, total_parties:int=10)->alt.vegalite.v5.api.Chart:

  df_tmp_18 = (df_2018
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

  df_tmp_22 = (df_2022
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
      width=220
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

  max_pct = max(df_tmp_18.get_column("PCT").max()+.05, df_tmp_22.get_column("PCT").max()+.05)
  #max_abs = np.ceil(df_tmp_18.get_column("QT_VOTOS_BR").max()/2)
  #max_abs = np.ceil(df_tmp_22.get_column("QT_VOTOS_BR").max()/2)
  max_abs = max(df_tmp_18.get_column("QT_VOTOS_BR").max(), df_tmp_22.get_column("QT_VOTOS_BR").max())

  left_pct = left_base.encode(
      alt.X('PCT:Q',
          title='',
          axis=alt.Axis(values=np.arange(0, 1.1, .1), format="%", labelAngle=-90),
          sort="descending",
          scale=alt.Scale(domain=[0, max_pct])
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
            axis=alt.Axis(values=np.arange(0, 1.1, .1), format="%", labelAngle=-90),
            scale=alt.Scale(domain=[0, max_pct])
      ),
  )

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

# agrupa os votos por partido por região
def votting_by_region(
  df:pl.DataFrame, 
  df_municipios:pl.DataFrame,
  cargo:list[str]=[],
  partidos:list[str]=[],
  group_by_cols:list[str]=["ANO_ELEICAO", "NM_REGIAO"])->pl.DataFrame:
    
    if partidos:
        df = df.filter((pl.col("SG_PARTIDO").is_in(partidos)))
        
    df = (df
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by(group_by_cols)
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())           
        )
    df = df.with_columns(pl.lit("B").alias("TIPO")) if partidos else df.with_columns(pl.lit("A").alias("TIPO"))
        
    return df

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

## Mapas

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

##  Mapas resumo
##  df_totais:pl.DataFrame -> votos totais por região
##  year:int -> ano da eleição
def map_resume(
  df_totais:pl.DataFrame, 
  color:str=""
)->alt.vegalite.v5.api.Chart:
  color = alt.condition(
    alt.datum.TIPO == 'A',
      alt.value('#000'),
      alt.value(color)
  )
  ##########################
  ## Barras valore totais ##
  ##########################
  base = (
      alt.Chart(df_totais)
      .mark_bar(strokeWidth=.5, stroke="#fff", cornerRadius=4, size=8)
      .encode(
        x=alt.X('NM_REGIAO:N', title="", ),
        y=alt.Y('QT_VOTOS_VALIDOS:Q', title="Votação", axis=alt.Axis(format="s")),
        xOffset="TIPO:N",
        color=color,
        tooltip=[
            alt.Tooltip('NM_REGIAO:N', title="Região"),
            alt.Tooltip('QT_VOTOS_VALIDOS:Q', format=",d", title="Votação"),
        ],
        text=alt.Text('sum(QT_VOTOS_VALIDOS):Q', format=",d"),
      )
  )

  return alt.layer(
      base,
      (
          base
          .mark_text(fontSize=8, yOffset=-25, angle=270)
          .encode(color=alt.value("#000"))
      )
  )

# Donut chart
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
###   Box plot com percentual de votos por partido em relação ao somatório dos demais partidos
def box_plots_votting_by_region(
    df:pl.DataFrame,chart_title:str,
    scheme="blues",    
    color_column:str="ANO_ELEICAO",
    color_range:list[str]=[],
    parties_order=[],
    legend_title="Eleição",
    set_y_title=True)->alt.vegalite.v5.api.Chart:

  if color_range:
    scale=alt.Scale(range=color_range)
  else:
    scale=alt.Scale(scheme=scheme)

  if set_y_title:
    y_title = "Votação por Município"
  else:
    y_title = ""

  base = (
      alt.Chart(df)
      .encode(
          x=alt.X(
            shorthand=f"{color_column}:N",
            sort=alt.SortField("MEDIAN:Q)"),
            axis=alt.Axis(
              title="" 
            )
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
              axis=alt.Axis(format='%')
          ).scale(zero=True, nice=True),
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

  return (
    alt.layer(boxes, bars)
    .facet(facet='NM_REGIAO:N', columns=5)
    .configure_headerFacet(
      title = None    
    ).resolve_scale(y='shared')
    .properties(title=f"{chart_title}")
    .configure_title(anchor="middle")
  )

##
###
def scatter_votting_by_regions(
  df_tmp:pl.DataFrame, chart_title:str,
    scheme:str="blues",
    color_range=[],
    opacity=.5,
    axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
    axis_col_titles:list[str]=["Perc. Votos em 2018","Perc. Votos em 2022"],
    axis_titles:list[str]=["2018","2022"],
    color_column:str="LEGEND"
  )->alt.vegalite.v5.api.Chart:

  color = alt.condition(
        alt.datum.PCT_VOTOS_18 >= alt.datum.PCT_VOTOS_22,
          alt.value(color_range[0]),
          alt.value(color_range[1])
  )

  scatter_plot = (
      alt.Chart()
      .mark_point(opacity=opacity)
      .encode(
        x=alt.X(f'{axis_cols[0]}:Q', title=f"{axis_titles[0]}", axis=alt.Axis(labelAngle=-90)),
        y=alt.Y(f'{axis_cols[1]}:Q', title=f"{axis_titles[1]}"),
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
  x_text_value=102
  y_text_value=112
  base = (
      alt.Chart()
      .mark_text(
        fontSize=8,
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
          groupby=["NM_REGIAO","Maior_22"],
          QT = "count(Maior_22)",
      ).transform_pivot(
        'Maior_22',
        groupby=['NM_REGIAO'],
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
          groupby=["NM_REGIAO"],
          median_22 = "median(PCT_VOTOS_22)",
      ).transform_calculate(
        text=f"Mda. {axis_titles[1]}: " + alt.expr.format(alt.datum.median_22, ".2%")
      ).encode(
        x=alt.value(x_text_value),  # pixels from left
        y=alt.value(y_text_value),  # pixels from top,
    )
  )

  y_text_value+=10
  median_pct_18 = (
      base.transform_aggregate(
          groupby=["NM_REGIAO"],
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
          groupby=["NM_REGIAO"],
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
      .mark_rect(stroke='black', strokeWidth=1, opacity=.2, cornerRadius=1.5, color=year_range_colors[0])
      .encode(
        x=alt.value(100),
        x2=alt.value(168),
        y=alt.value(113),
        y2=alt.value(168)
    )
  )

  return (
  alt.layer(scatter_plot, line_plot, won_22, won_18, median_pct_22, median_pct_18, median_diff, box, data=df_tmp)
      .facet(
          column = alt.Column("NM_REGIAO:N", title="", sort=alt.SortField("NM_REGIAO")),
          row=alt.Row(shorthand='SG_PARTIDO:N', header=None, title=""),
          center=True
      )
  ).properties(
      title=f'{chart_title}'
  )

##
###
def kde_plot(df:pl.DataFrame, groupby:list[str]=['ANO_ELEICAO', 'NM_REGIAO'], 
             color_range:list[str]=year_range_colors, 
             color_column:str="ANO_ELEICAO", legend_title:str="Eleição",
             titulo:str="", num_cols:int=3)->alt.vegalite.v5.api.Chart:
  
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
          )
      ),
      y=alt.Y('density:Q', axis=alt.Axis(labels=False), title="").stack(None),
      color=alt.Color(f"{color_column}:N", scale=scale, title=f"{legend_title}")
      #color=alt.Color("SG_PARTIDO:N", scale=scale, title='Partido')
    ).facet(
      alt.Column("NM_REGIAO:N", title=""), columns=num_cols
    ).configure_axisX(
      orient="bottom",
    ).configure_headerFacet(
          labelOrient="top",
          title = None
    ).properties(title=f"{titulo}").configure_title(anchor="middle")
  )

##
###
def bar_plot(df:pl.DataFrame, metric_col:str="Voto", 
             scale=alt.Scale(domain=[0,25_000_000]),
             axis_format="s", text_format=",",
             color_range=[],
             legend=True
              )->alt.vegalite.v5.api.Chart:

    if legend:
        legend=alt.Legend(symbolSize=300)
    else:
        legend=None
        
    base = alt.Chart(df, width=alt.Step(12)).encode(
        x=alt.X(f"NM_REGIAO:N", title=""),
        y=alt.Y(f"{metric_col}:Q", title="", scale=scale, axis=alt.Axis(format=f"{axis_format}")),
        xOffset=alt.XOffset(
            "LEGEND:N", 
            scale=alt.Scale(paddingOuter=0.2),            
        ),
    )            
    return alt.layer(
        base.mark_bar(size=20, stroke="white", fillOpacity=0.7).encode(
            fill=alt.Fill(
                "LEGEND:N", 
                title="Partido", 
                scale=alt.Scale(range=color_range),
                legend=legend
            )
        ),
        base.mark_text(
            dx=25, angle=270, fontSize=12
        ).encode(
            text=alt.Text(f"{metric_col}:Q", format=f"{text_format}")
        )
    )

def crescimento(
    summary:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 60_000_000]
    )->alt.vegalite.v5.api.Chart:

  dy:float=6.
  font_size:float=10.

  scale = alt.Scale(
      domain=["2018", "2022"],
      range=color_range
  )

  base = (
    alt.Chart(summary)
  )

  bar1 = base.transform_calculate(
    ANO="'2018'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="",
              #sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom", values=[])),
      y=alt.Y('Votos_18:Q', scale=alt.Scale(domain=y_domain), axis=alt.Axis(labels=False, ticks=False)),
      color=alt.Color("ANO:N", scale=scale),
      text=alt.Text('Votos_18:Q', format='.3s'),
  )

  bar2 = base.transform_calculate(
    ANO="'2022'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="", #sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Votos_18:Q', title=""),
      y2=alt.Y2('Votos_22:Q'),
      color=alt.Color("ANO:N", title="Eleiçao", scale=scale,legend=None,
                      #legend=alt.Legend(direction="horizontal",
                      #                  orient="none", legendX=55, legendY=320,
                      #                  titleAnchor="middle")
                      ),
      text=alt.Text('Votos_22:Q', format='.3s'),
  )

  bar1_text = bar1.mark_text(
        dy=dy, fontSize=font_size
      ).encode(
        x=alt.X("NM_REGIAO:N", title="",
                #sort=alt.EncodingSortField("Crescimento"),
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
      x=alt.X("NM_REGIAO:N", title="", #sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('y:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar2, bar1_text, diff_text)
      .properties(width=180, height=250, title="Votação Absoluta")
      .resolve_scale(x="independent")
  )

def votacao_regiao(
    df_resumos:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 60_000_000]
    )->alt.vegalite.v5.api.Chart:
    
    base = alt.Chart(df_resumos).encode(
        x=alt.X("NM_REGIAO:N", title=""),
        y=alt.Y("Voto:Q", title="", scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s")),
        xOffset=alt.XOffset("LEGEND:N", scale=alt.Scale(paddingOuter=0.0))
    )
    
    return alt.layer(
        base.mark_bar(size=20, stroke="white").encode(
            fill=alt.Fill("LEGEND:N", title="", scale=alt.Scale(range=color_range))
        ),
        base.mark_text(
            dx=20,
            angle=270,        
            fontSize=10).encode(text=alt.Text("Voto:Q", format=".4s"))
    ).properties(width=180, height=250, title="Votação Absoluta")

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
    ).properties(height=250, title="")

def percentual_regiao(
    df_resumos:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[.2, .7]
)->alt.vegalite.v5.api.Chart:
    base = alt.Chart(df_resumos).encode(
        x=alt.X("NM_REGIAO:N", title=""),
        y=alt.Y("PERCENTUAL:Q", title="", scale=alt.Scale(domain=y_domain), axis=alt.Axis(format=".0%")),
    )        
    return alt.layer(
        base.mark_line(point=True).encode(
            color=alt.Color("LEGEND:N", legend=alt.Legend(title="Partido"),
                          scale=alt.Scale(range=color_range)
            )
        ),
        base.mark_text(
            fontSize=10,
            dy=-10,
        ).encode(text=alt.Text("PERCENTUAL:Q", format=".2%")),
    ).properties(width=400, height=300, title="Votação Percentual")

#######################
# Load data
#lista das regiões brasileiras
df_regioes = get_regioes()
regions_list = list(df_regioes.get_column("NM_REGIAO").unique().sort().to_list()) #apenas as grandes regiões brasileiras

########################################################
# Tratar dados das eleições

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
########################################################

##################################################################################################################################################
with st.sidebar:
    st.title("Eleições Presidenciais 1o Turno 🗳️")
    cruzamentos:list[str] = ["PT 2022 x PL 2022", "PT 2022 x PSL 2018", "PT 2022 x PT 2018", 
                        "PL 2022 x PSL 2018", "PL 2022 x PT 2018", "PT 2018 x PSL 2018"]    
    regioes = st.multiselect('Regiões', regions_list, default=regions_list)
    disputa = st.radio("Escolha o Cruzamento", cruzamentos, horizontal=False)
    
    #color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    #selected_color_theme = st.selectbox('Select a color theme', color_theme_list)
    
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

## Cria as abas
tabResumos, tabMapas, tabGrafs, tabCapitais = st.tabs(["Geral", "Mapas e Resumos", "Gráficos Gerais", "Capitais"]) 

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

df_poll_box = pl.concat([df_poll_partido_b,df_poll_partido_a])

suffix:str="_right"        
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

#Ajusta as cores do gráfico de barras
if partido_b == "PT" and partido_a != "PT":
    color_range = ["#347DB6", "#BC3439"] #vermelho, azul
elif partido_a == "PT" and partido_b=="PT":
    color_range = ["#D68186","#BC3439"]
elif partido_a != "PT" and partido_b!="PT":
    color_range = ["#7e81e9","#bfc1f4"]
else:
    color_range = ["#347DB6", "#BC3439"] 
#df_resumos = (
#    df_poll_partido_a
#        .select(["NM_REGIAO","TOTAL_VOTOS_MUNIC"])
#        .group_by("NM_REGIAO")
#        .agg(pl.col("TOTAL_VOTOS_MUNIC").sum().alias("TOTAL_REGIAO"))
#)
with tabResumos:
#############################################################
    # Dashboard Main Panel
    row = st.columns(1, gap='small', border=True)
    with row[0]:
        st.markdown("###### Classificação Ideológica dos Partidos Políticos Brasileiros", unsafe_allow_html=True)
        st.altair_chart(
            class_ideologica_chart(
                df_partidos, df_colors
            ).properties(
                height=220, title=""
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
        
    row = st.columns((3.5, 7), gap='small', border=True)
    with row[0]:
        st.markdown("###### Votação para Presidente por Partidos", unsafe_allow_html=True)
        # Gráfico votação percentual por partidos
        pres_linhas = general_votting_line_chart(df_poll_18, df_poll_22, df_colors, list([1]), '', range=year_range_colors)
        st.altair_chart(
            pres_linhas.properties(
                height=320
            ).configure_axis(
                grid=True,
                labelColor='#000',
                titleColor='#000'
            ), 
            use_container_width=True
        )  
    with row[1]:
        pres_piramide = pyramid_votting_chart(df_poll_18, df_poll_22, df_colors, list([1]), '')
        st.markdown("###### Pirâmide da Votação para Presidente por Partidos - Brasil", unsafe_allow_html=True)
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
    # Dashboard Main Panel
    row = st.columns((1,1), gap='small', border=True)
    #if eleicao_b==eleicao_a:
    #    df_total = df_resumos.filter(pl.col("SG_PARTIDO")==partido_b).group_by("SG_PARTIDO").agg(pl.col("TOTAL_REGIAO").sum())
    #    df_total = df_total.with_columns(
    #        pl.lit(f"{eleicao_b}").alias("ANO_ELEICAO"),
    #        pl.lit(f"{eleicao_b}").alias("LEGEND")
    #    ).rename({"TOTAL_REGIAO":"Voto"})
    #    total_colors = year_range_colors if eleicao_b==2018 else year_range_colors[::-1]
    #else:
    #    df_total = df_resumos.group_by(["SG_PARTIDO","ANO_ELEICAO","LEGEND"]).agg(pl.col("TOTAL_REGIAO").sum())
    #    df_total = df_total.rename({"TOTAL_REGIAO":"Voto"})        
    #    total_colors = year_range_colors    
    
    #with row[0]:
    #    st.write(df_resumos)
    #with row[1]:
        #st.write(df_resumos.group_by("LEGEND").agg(
        #    pl.col("Voto").sum()/pl.col("TOTAL_REGIAO").sum()
        #))
with tabMapas:
    row = st.columns((3.5, 3.5, 3.5), gap='small', border=True)
    with row[0]:
        st.markdown(f'###### Votação {partido_b} {eleicao_b}')
        breaks = [.25, .4, .55],
        domain = ["<=25%", ">25%,<=40%", ">40%,<=55%",">55%"]
    
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
        
        #st.altair_chart(mapa, use_container_width=True)

    with row[1]:
        st.markdown(f'###### Votação {partido_a} {eleicao_a}')
    
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
        #st.altair_chart(mapa, use_container_width=True)   
        
    #############################################################
    with row[2]:
        st.markdown(f'###### Diferença Perc. {partido_b} {eleicao_b} - {partido_a} {eleicao_a}')    
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
        
        #st.altair_chart(mapa, use_container_width=True)
        
    #############################################################        
    row = st.columns((1.5, 3, 3.5), gap='small', border=True)
    with row[0]:
        st.markdown('#### Indicadores')
        #st.subheader("Resumos")
        total_votos_18:np.int32 = (
            df_poll_18
            .get_column("QT_VOTOS_VALIDOS").sum()
        )
        
        total_votos_22:np.int32 = (
            df_poll_22
            .get_column("QT_VOTOS_VALIDOS").sum()
        )  

        st.metric(label='Total de Votos em 2022', value=format_number(total_votos_22).replace(".",","), 
                      delta=format_number(total_votos_22-total_votos_18).replace(".",","))
        st.metric(label='Total de Votos em 2018', value=format_number(total_votos_18).replace(".",","),
                 delta=format_number(total_votos_18-total_votos_22).replace(".",","))
    
        total_votos_part_b:np.int32 = (
            df_poll_b.filter(pl.col("SG_PARTIDO")==partido_b)
            .get_column("QT_VOTOS_VALIDOS").sum()        
        )
        total_votos_part_a:np.int32 = (
            df_poll_a.filter(pl.col("SG_PARTIDO")==partido_a)
            .get_column("QT_VOTOS_VALIDOS").sum()        
        )    
        
        st.metric(label=f"Total Votos {partido_b} {eleicao_b}", value=format_number(total_votos_part_b).replace(".",","),
                 delta=format_number(total_votos_part_b-total_votos_part_a).replace(".",","))    
    
        st.metric(label=f"Total Votos {partido_a} {eleicao_a}", value=format_number(total_votos_part_a).replace(".",","),
                 delta=format_number(total_votos_part_a-total_votos_part_b).replace(".",","))    

    #with row[1]:

    with row[2]:
        st.markdown('#### Votos Válidos', unsafe_allow_html=True)        
        #st.write(df_resumos)
        
        col_1, col_2 = st.columns([1,1])
        #######################################################################
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
        with col_1:
            st.markdown(f'###### Votação {partido_b} {eleicao_b}')
            st.altair_chart(donut_part_b, use_container_width=True)
        with col_2:
            st.markdown(f'###### Votação {partido_a} {eleicao_a}')            
            st.altair_chart(donut_part_a, use_container_width=True)        
        #abs_plot = bar_plot(df_resumos, text_format=".3s", 
        #                    color_range=color_range, legend=False
        #                   )

        #scale=alt.Scale(domain=[0,1.])
        #axis_format="%"
        #text_format=".2%"
        
        #perc_plot = bar_plot(df_resumos, 
        #                     metric_col="PERCENTUAL", 
        #                     scale=scale, 
        #                     axis_format=axis_format,
        #                     text_format=text_format,
        #                     color_range=color_range)

        #st.markdown(f"#### Votação por Região {partido_b} {eleicao_b} x {partido_a} {eleicao_a}", unsafe_allow_html=True)

        partb_parta_abs = votacao_regiao(df_resumos, color_range=color_range)
        #
        df_total = df_resumos.group_by(["SG_PARTIDO","ANO_ELEICAO","LEGEND"]).agg(pl.col("Voto").sum())
        total_partidos = total_brasil(df_total, color_range=color_range)

        resume_plots = alt.hconcat(partb_parta_abs, total_partidos)        
        if (partido_b == "PT" and partido_a=="PT" ) or (partido_b=="PL" and partido_a=="PSL"):
            df_crescimento = df_tmp.group_by("NM_REGIAO").agg(
                pl.col("QT_VOTOS_VALIDOS_22").sum().alias("Votos_22"),
                pl.col("QT_VOTOS_VALIDOS_18").sum().alias("Votos_18"))             
            if (partido_b=="PL"):
                color_range = color_range[::-1]
                
            c = crescimento(df_crescimento, y_domain=[0,60_000_000], color_range=color_range).properties(width=220, height=250, title="Crescimento")        
            resume_plots = alt.hconcat(resume_plots, c)
        #col_1, col_2 = st.columns((1,1), gap='small')        
        #with col_1:
        st.altair_chart(resume_plots
        .resolve_scale(y='shared',color="independent")
        .configure(
            concat=alt.CompositionConfig(spacing=2)
        ), use_container_width=False)
        #with col_2:
        #    st.markdown('###### Perc. Votos Válidos')            
        #    st.altair_chart(perc_plot, use_container_width=True)        

        line_perc = percentual_regiao(df_resumos, color_range=color_range)
        st.altair_chart(
            line_perc, 
            use_container_width=False
        )


with tabGrafs:
    row = st.columns((1, 1), gap='small', border=True)
    with row[0]:
        #st.write(df_poll_box)
        st.markdown(f'#### Boxplot Votação {partido_b} {eleicao_b} x {partido_a} {eleicao_a}')

        #color_column = ("ANO_ELEICAO" if eleicao_a != eleicao_b else "SG_PARTIDO")
        
        mapa = box_plots_votting_by_region(
            df_poll_box,
            chart_title=f"",
            color_range=color_range,
            color_column="LEGEND",
            legend_title="Legenda"
        ).configure_axis(
            grid=True
        ).configure_view(
            strokeWidth=1
        ).configure_legend(
            titleColor="#000",
            labelColor="#000"
        )
        
        st.altair_chart(mapa, use_container_width=True)

        mapa = kde_plot(
            df_poll_box.select(["ANO_ELEICAO","SG_PARTIDO","LEGEND", "NM_REGIAO","PCT_VOTOS_MUNIC"]),
            groupby=['NM_REGIAO','SG_PARTIDO',"LEGEND"],
            color_column="LEGEND",
            color_range=color_range,
            legend_title="Legenda", titulo="", num_cols=2).configure_axis(grid=True).configure_view(strokeWidth=1)

        st.markdown(f'###### KDE Votação {partido_b} {eleicao_b} x {partido_a} {eleicao_a}')        
        st.altair_chart(mapa, use_container_width=True)        

    with row[1]:        
        st.markdown(f'#### Dispersão Votação {partido_b} {eleicao_b} x {partido_a} {eleicao_a}')
        _color_range = color_range
        if partido_b=="PL" and partido_a=="PT":
            _color_range = color_range[::-1]
        mapa = scatter_votting_by_regions(
            df_tmp.filter(pl.col("NM_REGIAO").is_in(["Centro-Oeste","Nordeste"])),
            chart_title="",
            opacity=.3,
            color_range=_color_range,
            axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
            axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
        )
        st.altair_chart(mapa, use_container_width=True)        
        
        mapa = scatter_votting_by_regions(
            df_tmp.filter(pl.col("NM_REGIAO").is_in(["Norte","Sudeste"])),
            chart_title="",
            opacity=.3,
            color_range=_color_range,
            axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
            axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
        )
        st.altair_chart(mapa, use_container_width=True)

        mapa = scatter_votting_by_regions(
            df_tmp.filter(pl.col("NM_REGIAO").is_in(["Sul"])),
            chart_title="",
            opacity=.3,
            color_range=_color_range,
            axis_col_titles=[f"Perc. Votos {partido_a}",f"Perc. Votos {partido_b}"],
            axis_titles=[f"{partido_a} {eleicao_a}", f"{partido_b} {eleicao_b}"]
        )
        st.altair_chart(mapa, use_container_width=True)
    #with row[2]:

rodape = st.columns(1)
with rodape[0]:
    with st.expander('Sobre', expanded=True):
        st.write('''
            - S. de Oliveira, Antonio Fagner
            - :orange[**Desmistificando 2022: Quem Definiu a Eleição Mais Importante do Século?**]
            - Monografia (especialização) – Universidade Federal do Rio Grande do Sul. Curso de Especialização em Ciência de Dados, Porto Alegre, BR–RS, 2025
            - Orientadora: Profa. Dra. Lisiane Selau
            - Co-orientador: Profa. Dra. Viviane P. Moreira
            - Ciência de Dados, Eleições Brasileiras, Estatística, Narrativa, Nordeste, Sudeste, Visualização de Dados.
            ''')