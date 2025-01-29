#######################
# Import libraries
import streamlit as st
import altair as alt
import polars as pl
import numpy as np

##########################################################################################
##                                       Layout                                         ##
##########################################################################################
st.set_page_config(
    page_title="Dashboard Eleições",
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
#partidos_18:list[str] = ["PT","PSL"]
#partidos_22:list[str] = ["PT","PL"]

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
def mapas_votacao(partido:str, eleicao:int, df:pl.DataFrame, df_municipios:pl.DataFrame, 
                     df_capitais:pl.DataFrame)->alt.vegalite.v5.api.Chart:
    breaks:list[int] = list([.25, .4, .55])
    domain:list[str] = list(["<=25%", ">25%,<=40%", ">40%,<=55%",">55%"])
    
    df_tmp = sdt_f.perc_votting_by_partie(
        df, df_municipios=df_municipios, cargo=list([1]),
        breaks=breaks, domain=domain
    )    
    df_tmp = df_tmp.filter( pl.col("SG_PARTIDO").is_in([partido]) & (pl.col("ANO_ELEICAO")==eleicao))

    return sdt_f.choropleth_votting(df_tmp, df_capitais=df_capitais,
                             chart_title="", scaleDomain=domain,
                              legend_sort=domain[::-1],
                              facet_column="ANO_ELEICAO"
        ).configure_legend(
            orient="left",
            titleColor="#000",
            labelColor="#000",
            titleFontSize=12,
            labelFontSize=10,
            offset=-150,
        ).properties(
            title=f"{partido} {eleicao}"
        ).configure_title(
            anchor="middle"
        )

def mapas_diferancas(df_poll_a:pl.DataFrame,
                     df_poll_b:pl.DataFrame,
                     df_municipios:pl.DataFrame, 
                     df_capitais:pl.DataFrame, 
                     cargo:list[int], titulo:str='', 
                     partido_a:str='', 
                     partido_b:str='',
                     eleicao_a:int=2018,
                     eleicao_b:int=2022,
                     regioes:list[str]=[])->alt.vegalite.v5.api.Chart:    
    breaks = [-.1, -.01, .01, .1]
    domain=["<-10%", ">-10% e <=-1%", ">-1%,<=1%",">1% e <=10%", ">10%"]

    if regioes:
        df_poll_a = df_poll_a.filter(pl.col("NM_REGIAO").is_in(regioes))
        df_poll_b = df_poll_b.filter(pl.col("NM_REGIAO").is_in(regioes))
    
    #todos os votos para os cargos específicos
    df_tmp = sdt_f.perc_votting_by_city(
        df_poll_a, df_poll_b, df_municipios=df_municipios, cargo=cargo,
        breaks=breaks, domain=domain
    )
    
    #votos por municípios para cada partido para o choropleth
    df_tmp_choroplet = pl.concat(
        [df_tmp.filter( pl.col("SG_PARTIDO").is_in([f"{partido_a}"]) & (pl.col("ANO_ELEICAO")==eleicao_a)),
         df_tmp.filter( pl.col("SG_PARTIDO").is_in([f"{partido_b}"]) & (pl.col("ANO_ELEICAO")==eleicao_b))
        ]
    )    
    
    df_poll_pta_tmp = df_tmp_choroplet.filter( (pl.col("ANO_ELEICAO")==eleicao_a) & (pl.col("SG_PARTIDO")==f"{partido_a}" ) )
    df_poll_ptb_tmp = df_tmp_choroplet.filter( (pl.col("ANO_ELEICAO")==eleicao_b) & (pl.col("SG_PARTIDO")==f"{partido_b}" ) )
    
    df_poll_pta_diff = df_poll_pta_tmp.select([
        "CD_MUNICIPIO",
        "QT_VOTOS_VALIDOS",
        "TOTAL_VOTOS_MUNIC",
        "PCT_VOTOS_MUNIC"]
    ).rename({
        "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_18",
        "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_18",
        "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_18"
    })
    
    df_poll_ptb_diff = df_poll_ptb_tmp.select(
        ["uf", "codigo_ibge", "nome", "CD_MUNICIPIO","QT_VOTOS_VALIDOS", "TOTAL_VOTOS_MUNIC","PCT_VOTOS_MUNIC"]
    ).rename({
        "TOTAL_VOTOS_MUNIC":"TOTAL_VOTOS_MUNIC_22",
        "QT_VOTOS_VALIDOS":"QT_VOTOS_VALIDOS_22",
        "PCT_VOTOS_MUNIC":"PCT_VOTOS_MUNIC_22"
    })
    
    #Diferença percentual de votos entre os dois anos
    df_poll_diff = (
      df_poll_pta_diff
      .join(df_poll_ptb_diff, on="CD_MUNICIPIO", how="inner")
      .with_columns(
          (pl.col("PCT_VOTOS_MUNIC_22")-pl.col("PCT_VOTOS_MUNIC_18")).alias("PCT_DIFF"),
          (pl.col("QT_VOTOS_VALIDOS_22")-pl.col("QT_VOTOS_VALIDOS_18")).alias("QT_DIFF")
      )
    )
    
    df_poll_diff = df_poll_diff.with_columns(
        pl.col("PCT_DIFF").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )
    
    scheme = "inferno"
    rev_Schmeme = False
    if (partido_a in ["PT"] and partido_b in ["PSL","PL"]):
        scheme = "redyellowblue"

    if (partido_b in ["PT"] and partido_a in ["PSL","PL"]):
        scheme = "redyellowblue"
        rev_Schmeme = True

    return sdt_f.choropleth_diff_votting(
        df_poll_diff, df_capitais,
        scaleDomain=domain,
        chart_title=titulo,
        legend_sort=domain[::-1],
        opacity=.8,
        scheme=scheme,
        rev_Schmeme=rev_Schmeme,
        tooltip_title_22=[f"Total Votos Munic. {eleicao_b}",f"Tot Votos {partido_b} {eleicao_b}", f"Perc. Votos {partido_b} {eleicao_b}"],
        tooltip_title_18=[f"Total Votos Munic. {eleicao_a}",f"Tot Votos {partido_a} {eleicao_a}", f"Perc. Votos {partido_a} {eleicao_a}"],
        legend_title=f'{partido_b} {eleicao_b} - {partido_a} {eleicao_a}'
    ).configure_legend(
        orient="left",
        titleColor="#000",
        labelColor="#000",
        titleFontSize=12,
        labelFontSize=10,
        offset=-150,
    )    

##########################################################################################
##                                     Apresentação                                     ##
##########################################################################################
cruzamentos:list[str] = ["PT 2022 x PL 2022", "PT 2022 x PSL 2018", "PT 2022 x PT 2018", 
                        "PL 2022 x PSL 2018", "PL 2022 x PT 2018", "PT 2018 x PSL 2018"]

with st.sidebar:
    st.markdown("# Selecione os Filtros da Aplicação ✔️")    
    regioes = st.multiselect('Regiões', regions_list, default=regions_list)
    disputa = st.radio("Escolha o Cruzamento", cruzamentos, horizontal=False)
    #divide os dados relativos à escolha do cruzamento
    disputa_arr = disputa.split(" ")
    partido_b = disputa_arr[0]
    eleicao_b = np.int16( disputa_arr[1] )
    partido_a = disputa_arr[3]
    eleicao_a =np.int16( disputa_arr[4] )

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
            sdt_f.class_ideologica_chart(df_partidos, df_colors).properties(height=220, title=""), 
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
    df_poll_a:pl.DataFrame=df_poll_18 if eleicao_a==2018 else df_poll_22
    df_poll_b:pl.DataFrame=df_poll_18 if eleicao_b==2018 else df_poll_22        
    
    linha = st.columns([2,1,2])
    with linha[0]:
        st.altair_chart(
            mapas_votacao(partido=partido_b, 
                          eleicao=eleicao_b, 
                          df=df_poll_b,
                          df_municipios = df_municipios, 
                          df_capitais = df_capitais,)
        )
    with linha[2]:
        st.altair_chart(
            mapas_diferancas(df_poll_a=df_poll_a,
                     df_poll_b=df_poll_b,
                     df_municipios = df_municipios, 
                     df_capitais = df_capitais, 
                     cargo=list([1]), titulo=f'{disputa}',
                     partido_a=partido_a, 
                     partido_b=partido_b,
                     eleicao_a=eleicao_a,
                     eleicao_b=eleicao_b,
                     regioes=regioes)
        )
