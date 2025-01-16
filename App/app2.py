#######################
# Import libraries
import streamlit as st
#import pandas as pd
import altair as alt
import plotly.express as px
import polars as pl
import numpy as np

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


##  Resumo dos mapas 

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
          .mark_text(fontSize=10, yOffset=-25, angle=270)
          .encode(color=alt.value("#000"))
      )
  )

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
    
    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)
    
    #divide os dados relativos à escolha do cruzamento
    disputa_arr:list[str] = disputa.split(" ")
    partido_b:str = disputa_arr[0]
    eleicao_b:int = np.int16( disputa_arr[1] )
    partido_a:str = disputa_arr[3]
    eleicao_a:int = np.int16( disputa_arr[4] )

    df_poll_a:pl.DataFrame=df_poll_18 if eleicao_a==2018 else df_poll_22
    df_poll_b:pl.DataFrame=df_poll_18 if eleicao_b==2018 else df_poll_22   
#######################
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')


with col[0]:
    st.markdown('#### Resumo')
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

    total_votos_b:np.int32 = (
        df_poll_b.filter(pl.col("SG_PARTIDO")==partido_b)
        .get_column("QT_VOTOS_VALIDOS").sum()        
    )
    total_votos_a:np.int32 = (
        df_poll_a.filter(pl.col("SG_PARTIDO")==partido_a)
        .get_column("QT_VOTOS_VALIDOS").sum()        
    )    
    st.metric(label=f"Total Votos {partido_b} {eleicao_b}", value=format_number(total_votos_b).replace(".",","),
             delta=format_number(total_votos_b-total_votos_a).replace(".",","))    

    st.metric(label=f"Total Votos {partido_a} {eleicao_a}", value=format_number(total_votos_a).replace(".",","),
             delta=format_number(total_votos_a-total_votos_b).replace(".",","))
    
with col[1]:
    st.markdown('#### Mapas')

with col[2]:
    st.markdown(f'##### Votação {partido_b} {eleicao_b}')
    #
    df_res_part_reg = votting_by_region(
        df=df_poll_b, 
        df_municipios=df_municipios,
        cargo=list([1]),
        partidos=[partido_b]
    )    
    df_res_reg = votting_by_region(
        df=df_poll_b, 
        df_municipios=df_municipios,
        cargo=list([1]),
        partidos=[]
    )
    df_resume = pl.concat([df_res_reg, df_res_part_reg])
    color = "#C54B53" if partido_b=="PT" else "#347DB6"
    st.altair_chart(
        map_resume(df_totais=df_resume, color=color).configure_title(
            anchor="middle"
        ).configure_axis(
            grid=False
        ).configure_view(
            strokeWidth=0
        ).properties(height=250),use_container_width=True
    )    

    st.markdown(f'##### Votação {partido_a} {eleicao_a}')
    #
    df_res_part_reg = votting_by_region(
        df=df_poll_a, 
        df_municipios=df_municipios,
        cargo=list([1]),
        partidos=[partido_a]
    ) 
    df_res_reg = votting_by_region(
        df=df_poll_a, 
        df_municipios=df_municipios,
        cargo=list([1]),
        partidos=[]
    )
    df_resume = pl.concat([df_res_reg, df_res_part_reg])
    color = "#C54B53" if partido_a=="PT" else "#347DB6"
    st.altair_chart(
        map_resume(df_totais=df_resume, color=color).configure_title(
            anchor="middle"
        ).configure_axis(
            grid=False
        ).configure_view(
            strokeWidth=0
        ).properties(height=250),use_container_width=True
    )      