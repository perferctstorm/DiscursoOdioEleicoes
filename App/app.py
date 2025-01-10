import streamlit as st
import altair as alt
import polars as pl
import numpy as np
import sys
# adding Folder_2 to the system path
sys.path.insert(0, '../Eleicoes/')

import standards as sdt_f

##########################################################################################
##                               Lista de variáveis a usar                              ##
##########################################################################################

##########################################################################################
##                                       Layout                                         ##
##########################################################################################
st.set_page_config(
    page_title="Desmistificando 2022",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon = "🗳️"
)

##########################################################################################
##                                Definição das Funções                                 ##
##########################################################################################
### Busca os datasets no google drive
def get_df(url):
    #url='https://drive.google.com/uc?id=' + url.split('/')[-2]
    return pl.read_parquet(source=url)
    

### Carrega as regiões do google drive
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


##########################################################################################
##                                Carregando os dados                                   ##
##########################################################################################
#lista das regiões brasileiras
regions_list = list(get_regioes().get_column("NM_REGIAO").unique().sort().to_list()) #apenas as grandes regiões brasileiras

#lista dos partidos que chegram ao 2o turno em 2018 e 2022
partidos_18:list[str] = ["PT","PSL"]
partidos_22:list[str] = ["PT","PL"]

#dados das eleições
df_poll_18:pl.DataFrame = get_eleicao_18()
df_poll_22:pl.DataFrame = get_eleicao_22()
total_votos_pres_18:np.int32 = (
    df_poll_18
    .filter(pl.col("CD_CARGO")==1)
    .get_column("QT_VOTOS_VALIDOS").sum()
)

total_votos_pres_22:np.int32 = (
    df_poll_22
    .filter(pl.col("CD_CARGO")==1)
    .get_column("QT_VOTOS_VALIDOS").sum()
)

#plot da classificação ideológica dos partidos políticos brasileiros segundo Bolognesi
df_partidos = get_partidos()
df_colors = sdt_f.parties_colors(df_partidos) #define uma cor para cada partido político baseado na sua ideologia

# Carga munícipios
df_municipios = get_municipios()
df_capitais = get_capitais()

# Gráfico votação percentual por partidos
pres_linhas = sdt_f.general_votting_line_chart(df_poll_18, df_poll_22, df_colors, list([1]), '', range=sdt_f.year_range_colors)

# Pimâmide votação absoluta presidente 
pres_piramide = sdt_f.pyramid_votting_chart(df_poll_18, df_poll_22, df_colors, list([1]), '')
regioes:str = ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]
region_plot = []
for regiao in regioes:
  region_plot.append(
      sdt_f.pyramid_votting_chart(
          df_poll_18.filter(pl.col("NM_REGIAO")==regiao), 
          df_poll_22.filter(pl.col("NM_REGIAO")==regiao), 
          df_colors, list([1]), f'{regiao}'
    )
  )

##########################################################################################
##                                       Funções                                        ##
##########################################################################################

def mapas_diferancas(df_poll_18:pl.DataFrame,
                     df_poll_22:pl.DataFrame,
                     df_municipios:pl.DataFrame, 
                     df_capitais:pl.DataFrame, 
                     cargo:list[int], titulo:str='', 
                     partido_18:str='', 
                     partido_22:str='',
                     regioes:list[str]=[])->alt.vegalite.v5.api.Chart:    
    breaks = [-.1, -.01, .01, .1]
    domain=["<-10%", ">-10% e <=-1%", ">-1%,<=1%",">1% e <=10%", ">10%"]

    if regioes:
        df_poll_18 = df_poll_18.filter(pl.col("NM_REGIAO").is_in(regioes))
        df_poll_22 = df_poll_22.filter(pl.col("NM_REGIAO").is_in(regioes))
    
    #todos os votos para os cargos específicos
    df_tmp = sdt_f.perc_votting_by_city(
        df_poll_18, df_poll_22, df_municipios=df_municipios, cargo=cargo,
        breaks=breaks, domain=domain
    )
    
    #votos por municípios para cada partido para o choropleth
    df_tmp_choroplet = pl.concat(
        [df_tmp.filter( pl.col("SG_PARTIDO").is_in([f"{partido_18}"]) & (pl.col("ANO_ELEICAO")==2018)),
         df_tmp.filter( pl.col("SG_PARTIDO").is_in([f"{partido_22}"]) & (pl.col("ANO_ELEICAO")==2022))
        ]
    )    
    
    df_poll_pt18_tmp = df_tmp_choroplet.filter( (pl.col("ANO_ELEICAO")==2018) & (pl.col("SG_PARTIDO")==f"{partido_18}" ) )
    df_poll_pt22_tmp = df_tmp_choroplet.filter( (pl.col("ANO_ELEICAO")==2022) & (pl.col("SG_PARTIDO")==f"{partido_22}" ) )
    
    df_poll_pt18_diff = df_poll_pt18_tmp.select([
        "CD_MUNICIPIO",
        "QT_VOTOS_VALIDOS",
        "TOTAL_VOTOS_MUNIC",
        "PCT_VOTOS_MUNIC"]
    ).rename({
        "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_18",
        "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_18",
        "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_18"
    })
    
    df_poll_pt22_diff = df_poll_pt22_tmp.select(
        ["uf", "codigo_ibge", "nome", "CD_MUNICIPIO","QT_VOTOS_VALIDOS", "TOTAL_VOTOS_MUNIC","PCT_VOTOS_MUNIC"]
    ).rename({
        "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_22",
        "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_22",
        "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_22"
    })
    
    #Diferença percentual de votos entre os dois anos
    df_poll_diff = (
      df_poll_pt18_diff
      .join(df_poll_pt22_diff, on="CD_MUNICIPIO", how="inner")
      .with_columns(
          (pl.col("PCT_VOTOS_MUNIC_22")-pl.col("PCT_VOTOS_MUNIC_18")).alias("PCT_DIFF"),
          (pl.col("QT_VOTOS_VALIDOS_22")-pl.col("QT_VOTOS_VALIDOS_18")).alias("QT_DIFF")
      )
    )
    
    df_poll_diff = df_poll_diff.with_columns(
        pl.col("PCT_DIFF").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )
    
    return sdt_f.choropleth_diff_votting(
        df_poll_diff, df_capitais,
        scaleDomain=domain,
        chart_title=titulo,
        legend_sort=domain[::-1],
        tooltip_title_22=["Total Votos Munic. 2022",f"Tot Votos {partido_22} 2022", f"Perc. Votos {partido_22} 2022"],
        tooltip_title_18=["Total Votos Munic. 2018",f"Tot Votos {partido_18} 2018", f"Perc. Votos {partido_18} 2018"]
    ).configure_legend(
        orient="top",
        titleColor="#000",
        labelColor="#000",
        titleFontSize=12,
        labelFontSize=10,
        offset=-10,
    )    

##########################################################################################
##                                     Apresentação                                     ##
##########################################################################################
with st.sidebar:
    st.markdown("# Selecione os Filtros da Aplicação ✔️")    
    regioes = st.multiselect('Regiões', regions_list, default=regions_list)
    partido_18 = st.radio("Escolha o Partido de 2018", partidos_18, horizontal=True)
    partido_22 = st.radio('Escolha o Partido de 2022', partidos_22, horizontal=True)

st.title("Desmistificando 2022") 

tabGeral, tabMapas= st.tabs(["Geral", "Mapas"]) 

with tabGeral:   
    linha = st.columns([1,1])    
    with linha[0]:       
        st.metric(label="Total de Votos Presidente em 2018", value="{:,}".format(total_votos_pres_18).replace(",","."))
    with linha[1]:
        st.metric(label="Total de Votos Presidente em 2022", value="{:,}".format(total_votos_pres_22).replace(",","."))

    linha = st.columns(1) 
    with linha[0]:
        st.markdown("Classificação Ideológica dos Partidos Políticos Brasileiros", unsafe_allow_html=True)
        st.altair_chart(
            sdt_f.class_ideologica_chart(df_partidos, df_colors).properties(height=200, title=""), 
            use_container_width=True
        )
        
    linha = st.columns([2,3])   
    with linha[0]:
        st.markdown("Votação para Presidente por Partidos", unsafe_allow_html=True)
        st.altair_chart(
            pres_linhas.properties(height=320), 
            use_container_width=True
        )

    with linha[1]: 
        st.markdown("Pirâmide da Votação para Presidente por Partidos - Brasil", unsafe_allow_html=True)
        st.altair_chart(
            pres_piramide.configure_title(anchor="middle", orient="bottom"), 
            use_container_width=True
        )
    linha = st.columns(1) 
    with linha[0]:
        st.markdown("Pirâmide da Votação para Presidente por Partidos/Regiões", unsafe_allow_html=True)

    linha = st.columns([1,1])
    with linha[0]:
        st.altair_chart(
            region_plot[0].configure_title(anchor="middle"), 
            use_container_width=True
        )
        st.altair_chart(
            region_plot[2].configure_title(anchor="middle"), 
            use_container_width=True
        )
        st.altair_chart(
            region_plot[4].configure_title(anchor="middle"), 
            use_container_width=True
        )    
    with linha[1]:
        st.altair_chart(
            region_plot[1].configure_title(anchor="middle"), 
            use_container_width=True
        )
        st.altair_chart(
            region_plot[3].configure_title(anchor="middle"), 
            use_container_width=True
        )
        
with tabMapas:
    linha = st.columns(1)
    with linha[0]:
        st.altair_chart(
            mapas_diferancas(df_poll_18 = df_poll_18, 
                               df_poll_22 = df_poll_22, 
                               df_municipios = df_municipios, 
                               df_capitais = df_capitais, 
                               cargo=list([1]), titulo='', 
                               partido_18 = partido_18, 
                               partido_22 = partido_22,
                               regioes=regioes)
        )
