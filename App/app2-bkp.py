## https://blog.streamlit.io/crafting-a-dashboard-app-in-python-using-streamlit/
#######################
# Import libraries
import streamlit as st
#import pandas as pd
import altair as alt
import plotly.express as px
import polars as pl
import numpy as np
import pandas as pd

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

tabMapas, tabResumos, tabCapitais = st.tabs(["Mapas", "Resumos", "Capitais"]) 

with tabMapas:
#######################
    # Dashboard Main Panel
    col = st.columns((2, 3.5, 3.5), gap='small', border=True)
    
    with col[0]:
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

    with col[1]:
        st.markdown(f'#### Mapa de Votação {partido_b} {eleicao_b}')
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
                  offset=-20,
                  titleFontSize=12,
                  labelFontSize=10            
                )
        
        #st.altair_chart(mapa, use_container_width=True)
    
        st.markdown(f'#### Mapa de Votação {partido_a} {eleicao_a}')
    
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
                  offset=-20,
                  titleFontSize=12,
                  labelFontSize=10
                )
        #st.altair_chart(mapa, use_container_width=True)
    with col[2]:
        st.markdown(f'#### Mapa Dif. Perc. {partido_b} {eleicao_b} {partido_a} {eleicao_a}')    
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
            tooltip_title_22=["Total Votos Munic. 2022","Tot Votos PT 2022", "Perc. Votos PT 2022"],
            tooltip_title_18=["Total Votos Munic. 2018","Tot Votos PT 2018", "Perc. Votos PT 2018"],
            legend_title=legend_title
        )
        mapa=mapa.configure_legend(
              offset=-20,
              titleFontSize=12,
              labelFontSize=10
            )
        
        #st.altair_chart(mapa, use_container_width=True)
        
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
            st.write(f'Votação {partido_b} {eleicao_b}')
            st.altair_chart(donut_part_b)
        with col_2:
            st.write(f'Votação {partido_a} {eleicao_a}')
            st.altair_chart(donut_part_a)
        #
        #df_res_part_reg = votting_by_region(
        #    df=df_poll_b, 
        #    df_municipios=df_municipios,
        #    cargo=list([1]),
        #    partidos=[partido_b]
        #)    
        #df_res_reg = votting_by_region(
        #    df=df_poll_b, 
        #    df_municipios=df_municipios,
        #    cargo=list([1]),
        #    partidos=[]
        #)
        #df_resume = pl.concat([df_res_reg, df_res_part_reg])
        #color = "#C54B53" if partido_b=="PT" else "#347DB6"
        #st.altair_chart(
        #    map_resume(df_totais=df_resume, color=color).configure_title(
        #        anchor="middle"
        #    ).configure_axis(
        #        grid=True
        #    ).configure_view(
        #        strokeWidth=.5
        #    ).properties(height=250),use_container_width=True
        #)    
    
        #st.markdown(f'#### Votação {partido_a} {eleicao_a}')
        #
        #df_res_part_reg = votting_by_region(
        #    df=df_poll_a, 
        #   df_municipios=df_municipios,
        #    cargo=list([1]),
        #    partidos=[partido_a]
        #) 
        #df_res_reg = votting_by_region(
        #    df=df_poll_a, 
        #    df_municipios=df_municipios,
        #    cargo=list([1]),
        #    partidos=[]
        #)
        #df_resume = pl.concat([df_res_reg, df_res_part_reg])
        #color = "#C54B53" if partido_a=="PT" else "#347DB6"
        #st.altair_chart(
        #    map_resume(df_totais=df_resume, color=color).configure_title(
        #        anchor="middle"
        #    ).configure_axis(
        #        grid=True
        #    ).configure_view(
        #        stroke='#E3E3E3',
        #        strokeWidth=.5
        #    ).properties(height=250),use_container_width=True
        #)      
rodape = st.columns(1)
with rodape[0]:
    with st.expander('Sobre', expanded=True):
        st.write('''
            - S. de Oliveira, Antonio Fagner
            - :orange[**Desmistificando 2022: Quem Definiu aEleição Mais Importante do Século?**]
            - Monografia (especialização) – Universidade Federal do Rio Grande do Sul. Curso de Especialização em Ciência de Dados, Porto Alegre, BR–RS, 2025
            - Orientadora: Profa. Dra. Lisiane Selau
            - Co-orientador: Profa. Dra. Viviane P. Moreira
            - Ciência de Dados, Eleições Brasileiras, Estatística, Narrativa, Nordeste, Sudeste, Visualização de Dados.
            ''')