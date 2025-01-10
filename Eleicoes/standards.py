import polars as pl
import altair as alt
import numpy as np

# define as cores padrões para usar nos plots para os anos de 2018 e 2022
year_range_colors:list[str] = ['#F3AD58','#9489BB']
ideol_range_colors:list[str] = ["#BC3439", "#347DB6"]

def get_min_domain(a:float)->float:
  match a:
    case _ if -.2 <= a <= 0:
        return -.2
    case _ if -.4 <= a < -.2:
        return -.4
    case _ if -.6 <= a < -.4:
        return -.6
    case _ if -.8 <= a < -.6:
        return -.8        
    case _ if -1 <= a < -.8:
        return -1

'''
  Função para carregar arquivos parquet
  path:str -> caminho do arquivo parquet
'''
def load_parquet(path:str)-> pl.DataFrame:
    return pl.read_parquet(source=path) 

''' 
    Define uma função associa uma cor para cada um dos espectos ideológicos do partidos políticos brasileiros
'''  
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

'''
    Filtra os dada de uma eleição pelo cargo político:
    df:pl.DataFrame -> dataframe da eleição
    posit_code:int -> código do cargo eleitoral
        1 - Presidente
        3 - Governador
        5 - Senador
        6 - Deputado Federal
        7 - Deputado Estadual
        8 - Deputado Distrital
'''
def filter_by_position(df_poll:pl.DataFrame, posit_codes:list[int])->pl.DataFrame:
    return (df_poll
        .filter(pl.col("CD_CARGO").is_in(posit_codes))
    )

'''
   Apresenta um grouped bar chart para um cargo político comparando os 15 partidos que mais
   conseguiram votos em 2022 com 2018.
   df_2018:pl.DataFrame -> dados da eleição de 2018
   df_2022:pl.DataFrame -> dados da eleição de 2022
   position:int -> código do cargo eleitoral (1 Presidente, 3 Governador, 5 Senador, 6 Deputado Federal, 7 Deputado Estadual e 8 Deputado Distrital)
   chart_title:str -> título do chart

   Retorna um chart vega-altair   
'''

'''
    Plota, na reta numérica, os partidos conforme suas ideologias políticas.
    Baseado no trabalho de Bolognesi(2018)

    df_partidos:pl.DataFrame -> Dataframe com os partidos políticos e sua classificação ideológica
    
'''
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
                orient='bottom', 
                labelBaseline="middle",
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
            alt.expr.if_(alt.datum.SG_PARTIDO == "NOVO", text_dx, 30))))))
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
    
    return (points + text) \
    .properties(
        width=1000,
        height=45
    ).configure_view(
        strokeWidth=0
    ).configure_title(
        fontSize=14
    )

'''
   Gera uma comparação da votação dos partido para um cargo entre 2018 e 2022
'''
def general_votting_line_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,  
                      position:list[int], chart_title:str, total_parties:int=10,
                      range:list[str]=['#F58518','#4C78A8'])->alt.vegalite.v5.api.Chart:

  # soma todos os votos por partidos de 2018
  df_tmp_18:pl.DataFrame = filter_by_position(df_2018, position)

  df_tmp_18 = (df_tmp_18
      .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )
      .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )

  # soma todos os votos por partidos de 2022
  df_tmp_22:pl.DataFrame = filter_by_position(df_2022, position)

  df_tmp_22 = (df_tmp_22
      .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )    
      .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )
  # concatena as votações de 22 e 18 para os cargos em position
  df_tmp = pl.concat([df_tmp_22, df_tmp_18])

  # os registros dos K partidos mais votados em 2022
  df_partidos = pl.concat(
      [df_tmp_18.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SG_PARTIDO")),
       df_tmp_22.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SG_PARTIDO"))
      ]
  ).unique().to_list()

  # faz join entre com os 15 partidos mais votados em 22 usando o campo QT_ORDER
  # para ordenar o chart
  df_tmp = (df_tmp
      .join(top_k_22, on="SG_PARTIDO", how="inner")
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
    x=alt.X('SG_PARTIDO:N', title="", sort=alt.SortField(field="QT_ORDER")),
    y=alt.Y('PCT:Q', title="", axis=alt.Axis(format="%")),
    color=alt.Color(
        shorthand='ANO_ELEICAO:N', title="Eleição",
        scale = alt.Scale(
            domain=[2018,2022],
            range=range,
        )
    ),
    tooltip=[
        alt.Tooltip('SG_PARTIDO:N', title="Partido"),
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
        alt.X("SG_PARTIDO:O", sort=alt.SortField(field="QT_ORDER")),
        alt.Y("min(PCT):Q"),
        alt.Y2("max(PCT):Q"),
    )
  )
  return alt.layer(lines, dotted_lines)


'''
   Gera uma comparação da votação dos partido para um cargo entre 2018 e 2022 em forma de pirâmide
'''
def pyramid_votting_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,
                      position:list[int], chart_title:str, total_parties:int=10)->alt.vegalite.v5.api.Chart:


  # soma todos os votos por partidos de 2018
  df_tmp_18:pl.DataFrame = filter_by_position(df_2018, position)

  df_tmp_18 = (df_tmp_18
      .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )
      .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )

  # soma todos os votos por partidos de 2022
  df_tmp_22:pl.DataFrame = filter_by_position(df_2022, position)

  df_tmp_22 = (df_tmp_22
      .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
      .group_by(["ANO_ELEICAO", "SG_PARTIDO","POSIC_IDEOLOGICO"], maintain_order=True)
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
          (pl.col("QT_VOTOS_VALIDOS")/pl.col("QT_VOTOS_VALIDOS").sum()).alias("PCT"),
          pl.col("QT_VOTOS_VALIDOS").sum().alias("QT_VOTOS_BR")
      )
      .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
      .drop(["SG_POSIC_IDEOLOGICO","MEDIA_IDEOL"])
  )

  # os registros dos K partidos mais votados em 2018
  top_k_22=df_tmp_22.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SG_PARTIDO","QT_VOTOS_VALIDOS"))

  df_tmp_22 = (
      df_tmp_22.join(top_k_22, on="SG_PARTIDO", how="right")
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
      df_tmp_18.join(top_k_22, on="SG_PARTIDO", how="right")
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
      alt.Y('SG_PARTIDO:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Color('POSIC_IDEOLOGICO:O')
          .scale(color_scale)
          .legend(None),
      tooltip=[
          alt.Tooltip("SG_PARTIDO:N", title="Partido"),
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
      alt.Y('SG_PARTIDO:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Text('SG_PARTIDO:O'),
  ).mark_text(fontSize=8.5).properties(width=30)

  right_base = base.transform_filter(
      alt.datum.ANO_ELEICAO == 2022
  ).encode(
      alt.Y('SG_PARTIDO:O', sort=alt.SortField(field="QT_ORDER", order="descending")).axis(None),
      alt.Color('POSIC_IDEOLOGICO:O').scale(color_scale),
      tooltip=[
          alt.Tooltip("SG_PARTIDO:N", title="Partido"),
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

'''

'''
def grouped_bar_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,  
                      position:list[int], chart_title:str, total_parties:int=5)->alt.vegalite.v5.api.Chart:
    # soma todos os votos por partidos de 2018
    df_tmp_18 = filter_by_position(df_2018, position)
    
    df_tmp_18 = (df_tmp_18
        .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","SG_POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
        .group_by(["ANO_ELEICAO", "SG_PARTIDO","SG_POSIC_IDEOLOGICO"], maintain_order=True)
        .agg(pl.col("QT_VOTOS_VALIDOS").sum())
        .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
    )
    
    # soma todos os votos por partidos de 2022
    df_tmp_22 = filter_by_position(df_2022, position)
    
    df_tmp_22 = (df_tmp_22
        .select(pl.col("ANO_ELEICAO", "SG_PARTIDO","SG_POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
        .group_by(["ANO_ELEICAO", "SG_PARTIDO","SG_POSIC_IDEOLOGICO"], maintain_order=True)
        .agg(pl.col("QT_VOTOS_VALIDOS").sum())
        .join(df_colors, left_on="SG_PARTIDO", right_on="SG_PARTIDO", how="inner")
    )
    
    # concatena as votações de 22 e 18 para os cargos em position
    df_tmp = pl.concat([df_tmp_22, df_tmp_18])
    
    # os registros dos K partidos mais votados em 2018
    top_k_22=df_tmp_22.top_k(total_parties, by="QT_VOTOS_VALIDOS").select(pl.col("SG_PARTIDO","QT_VOTOS_VALIDOS"))    
    
    # faz join entre com os 15 partidos mais votados em 22 usando o campo QT_ORDER 
    # para ordenar o chart
    df_tmp = (df_tmp
        .join(top_k_22, on="SG_PARTIDO", how="inner")
        .with_columns(
            QT_ORDER = pl.col("QT_VOTOS_VALIDOS_right")
        )
        .drop(pl.col("SG_POSIC_IDEOLOGICO_right","QT_VOTOS_VALIDOS_right"))              
    ) 

    return alt.Chart(df_tmp).mark_bar().encode(
        y = alt.Y('ANO_ELEICAO:O', 
            title="",
        ),
        x = alt.X('QT_VOTOS_VALIDOS:Q', title="Votação", axis=alt.Axis( labelAngle=-90 )),
        color = alt.Color('ANO_ELEICAO:O',
            scale = alt.Scale(
               domain=[2018,2022], 
               range=['#F58518','#4C78A8'],
            ),
            legend=None
        ),
        row = alt.Row('SG_PARTIDO:N',
            title="",
            spacing = 5,
            header=alt.Header(labelAngle=0, labelAlign='left', title=f'{chart_title}', titleFontSize=12),
            sort=alt.SortField("QT_ORDER", order="descending"),                      
        ),
        opacity=alt.OpacityValue(0.75),
        tooltip=[
            alt.Tooltip('SG_PARTIDO:N', title="Partido"),
            alt.Tooltip('ANO_ELEICAO:O', title="Ano Eleição"),
            alt.Tooltip('QT_VOTOS_VALIDOS:Q', format=",d",  title="Votos"),
        ]        
    ).properties(
        width=300,
        #height=150,
    ) 

'''
    Desenha o mapa do Brasil por cidade comparando a votação de um partido entre duas eleições
'''
def choropleth_votting(df:pl.DataFrame, df_capitais:pl.DataFrame,
                      facet_column:str="ANO_ELEICAO",
                      legend_sort:list[str]=[],
                      facet_sort:list=[],
                      chart_title:str="", 
                      scaleDomain:list[str]=["<=1%", ">1%,<=5%", ">5%,<=10%",">10%"], 
                      scheme="inferno",
                      opacity=.6,
                      rev_Schmeme:bool=False)->alt.vegalite.v5.api.Chart:
  # define choropleth scale
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
          strokeWidth=.3
      )
  )

  cities = alt.Data(
      url="https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/geojs-100-mun_minifier.json",
      format=alt.DataFormat(property='features')
  )

  cities_map = alt.Chart() \
    .mark_geoshape(
        stroke="#000", strokeWidth=0, fillOpacity=opacity
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
            symbolOpacity=.7,
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
    ).properties(width=300)

  return alt.layer(background_states, cities_map).facet(
      data=df,
      row=alt.Row(sort=facet_sort,
        shorthand=f'{facet_column}:N',
        header=alt.Header(title=None, labelFontSize=12),
      )
  )

'''
Plota as diferenças de votos percentuais entre dois anos
'''
def choropleth_diff_votting(df_poll_diff:pl.DataFrame, df_capitais:pl.DataFrame, 
  chart_title:str, scaleDomain:list[str]=[-.01, .01, .05], 
  legend_sort:list[str]=[],
  scheme="inferno", rev_Schmeme:bool=False,
  opacity=.6,
  tooltip_title_22:list[str]=["Total Votos Munic. 2022","Total Votos Part. 2022", "Perc. Votos Part. 2022"], 
  tooltip_title_18:list[str]=["Total Votos Munic. 2018","Total Votos Part. 2018", "Perc. Votos Part. 2018"])->alt.vegalite.v5.api.Chart:

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
          strokeWidth=.3
      )
  )

  cities = alt.Data(
      url="https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/geojs-100-mun_minifier.json",
      format=alt.DataFormat(property='features')
  )

  cities_map =(alt.Chart(df_poll_diff)
    .mark_geoshape(
        stroke="#000", strokeWidth=0, fillOpacity=opacity
    ).project(
        type="equirectangular"
    ).encode(
      shape='geo:G',
      color=alt.Color("PCT_VOTOS_LIMIT:N",
          scale=scale,
          legend=alt.Legend(
            #orient="bottom",
            titleAnchor='middle',
            title="Diferença Perc. de Votos [2022-2018]",
            #direction="horizontal"
            type="symbol",
            symbolSize=400,
            symbolOpacity=.8,
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
    ).properties(width=400)
  ) 
  '''
  text_munic = (alt.Chart(df_capitais) 
      .mark_text(dx=-6, dy=8, fontSize=8) 
      .encode(
          latitude="latitude:Q",
          longitude="longitude:Q",
          text="nome:N",
          color=alt.value("#0000ff")
    )
  )

  point = (alt.Chart(df_capitais)
    .mark_circle(dx=-5, size=25)
    .encode(        
        latitude="latitude:Q",
        longitude="longitude:Q",
        color=alt.value("orange")
    )
  )
  '''
  return (
    alt.layer(background_states, cities_map)
    .properties(title=f"{chart_title}")
    .configure_title(anchor="middle")
  )

'''
    Filtra os votos de duas eleições com o percentual de votos do partido em relação ao município
    Agrupa os votos por cada município brasileiro e compara a votação do partido com o restante dos votos do município
'''
def filter_choropleth_votting(
  df_2018:pl.DataFrame,df_2022:pl.DataFrame, df_municipios:pl.DataFrame, 
  cargo:list[int], partidos:list[str])->alt.vegalite.v5.api.Chart:
    df_poll_18_tmp=(df_2018
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by("ANO_ELEICAO", "SG_PARTIDO", "NM_REGIAO", "CD_MUNICIPIO")
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            .filter((pl.col("SG_PARTIDO").is_in(partidos)))
        )   
    
    df_poll_22_tmp=(df_2022
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by("ANO_ELEICAO", "SG_PARTIDO", "NM_REGIAO", "CD_MUNICIPIO")
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            .filter((pl.col("SG_PARTIDO").is_in(partidos)))
        )  
    return df_poll_18_tmp, df_poll_22_tmp

'''
   Box plot com percentual de votos por partido em relação ao somatório dos demais partidos
   
'''
'''
  Box plox dos estados por uf
'''
def box_plots_votting_by_uf(df:pl.DataFrame, 
                            scheme="blues",
                            color_column:str="ANO_ELEICAO",
                            color_range:list[str]=[],
                            legend_title="Eleição",
                            parties_order:list[str]=[],
                            region:str="",
                            chart_title:str="", 
                            set_y_title=True,
                            group_ideolog:bool=False)->alt.vegalite.v5.api.Chart:
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
          y=alt.Y("PCT_VOTOS_MUNIC:Q", title=f"{y_title}",
                  axis=alt.Axis(format='%') ),
          x=alt.X(f"{color_column}:N", title="", sort=parties_order),
          color=alt.Color(f"{color_column}:N", scale=scale).legend(title=legend_title),        
      )
  )

  boxes = (
      base
      .mark_boxplot()
      .encode(
          tooltip=[
              alt.Tooltip("uf:N", title="Estado"),
              alt.Tooltip("nome:N", title="Município"),
              alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Geral de Votos"),
              alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Total Votos Partido"),
              alt.Tooltip("PCT_VOTOS_MUNIC:Q", format=".2%", title="% Votos"),
          ]
      )
  )

  groupby = ["ANO_ELEICAO", "NM_REGIAO", "uf", "SG_PARTIDO"]
  if group_ideolog:
    groupby.append("NOME_RES_IDEOLOGICO")

  bars = (
      base
      .transform_aggregate(
          PCT_VOTOS_UF="sum(PCT_VOTOS_MUNIC):Q",
          total="sum(TOTAL_VOTOS_MUNIC):Q",
          total_partido="sum(QT_VOTOS_VALIDOS):Q",
          max="max(PCT_VOTOS_MUNIC):Q",
          mean="mean(PCT_VOTOS_MUNIC):Q",
          median="median(PCT_VOTOS_MUNIC):Q",
          min="min(PCT_VOTOS_MUNIC):Q",
          q1="q1(PCT_VOTOS_MUNIC):Q",
          q3="q3(PCT_VOTOS_MUNIC):Q",
          count="count()",
          groupby=groupby
      ).mark_bar(opacity=0, yOffset=3, y2Offset=-3)
      .encode(
          y=alt.Y('q1:Q').scale(zero=False, nice=True),
          y2='q3:Q',
          #color=alt.Color(f"{color_column}:N", scale=scale).legend(None),
          tooltip=[
              alt.Tooltip("uf:N", title="Estado"),
              alt.Tooltip("total:Q",format=",d", title="Total Votos"),
              alt.Tooltip("total_partido:Q",format=",d", title="Total Votos Partido"),
              alt.Tooltip('mean:Q', title="Média", format=".2%"),
              alt.Tooltip('median:Q', title="Mediana", format=".2%"),
              alt.Tooltip('max:Q', title="Máximo", format=".2%"),
              alt.Tooltip('min:Q', title="Mínimo", format=".2%"),
              alt.Tooltip('q3:Q', title="3o Quartil", format=".2%"),
              alt.Tooltip('q1:Q', title="1o Quartil", format=".2%"),
          ]
      ).properties(height=250)
  )

  return (
      alt.layer(boxes, bars)
      .facet(facet=alt.Facet("uf:N", title=f"{region}"))
      .properties(title=f"{chart_title}")
      .configure_title(anchor="middle")
  )

'''
   Box plot com percentual de votos por partido em relação ao somatório dos demais partidos
   
'''
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
          groupby=["ANO_ELEICAO", "SG_PARTIDO",f"{color_column}"]
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
    .facet(facet=alt.Facet('NM_REGIAO:N'))
    .configure_headerFacet(
      title = None    
    ).resolve_scale(y='shared')
    .properties(title=f"{chart_title}")
    .configure_title(anchor="middle")
  )
'''

'''
def scatter_votting_by_regions(
  df_tmp:pl.DataFrame, chart_title:str,
    scheme:str="blues",
    color_range=[],
    opacity=.5,
    axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
    axis_col_titles:list[str]=["Perc. Votos em 2018","Perc. Votos em 2022"],
    axis_titles:list[str]=["2018","2022"]
  )->alt.vegalite.v5.api.Chart:

  if color_range:
    color = alt.condition(
        alt.datum.PCT_VOTOS_18 >= alt.datum.PCT_VOTOS_22,
          alt.value(color_range[0]),
          alt.value(color_range[1])
    )
  else:
    color = alt.Color("SG_PARTIDO:N", legend=None, scale=alt.Scale(scheme=scheme))

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

'''
'''
def scatter_facet_votting_by_regions(df:pl.DataFrame, chart_title:str, region:str="",
                              scheme:str="blues", 
                              axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
                              axis_titles:list[str]=["2018","2022"],
                              color_range:list[str]=[],
                              opacity:float=1.,
                              box_opacity:float=.4, 
                              num_cols:int=int(3))->alt.vegalite.v5.api.Chart:
  if color_range:
    color = alt.condition( 
        alt.datum.PCT_VOTOS_18 >= alt.datum.PCT_VOTOS_22, 
          alt.value(color_range[0]), 
          alt.value(color_range[1])
    )
  else:
    scale = alt.Scale(scheme=scheme)
    color = alt.Color("NM_REGIAO:N", title="Região", scale=scale, sort=alt.SortField("NM_REGIAO:N")).legend()

  line_plot =(
      alt.Chart(pl.DataFrame({"x":[0,1], "y":[0,1]}))
      .mark_line(fillOpacity=0, color="#9ECAE9", opacity=.8)
      .encode(
          x=alt.X("x:Q"),
          y=alt.Y("y:Q")
      )
  )

  scatter_plot= alt.Chart().mark_point(opacity=opacity).encode(
      x=alt.X(f'{axis_cols[0]}:Q', title=f"{axis_titles[0]}", axis=alt.Axis(labelAngle=-90)),
      y=alt.Y(f'{axis_cols[1]}:Q', title=f"{axis_titles[1]}"),
      color=color,
      tooltip=[
          alt.Tooltip("NM_REGIAO:N", title="Região"),
          alt.Tooltip("uf:N", title="Estado"),
          alt.Tooltip("nome:N", title="Município"),
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
          Maior_22 = alt.datum.PCT_VOTOS_22 > alt.datum.PCT_VOTOS_18
      )
  )

  base_count = (
      base
      .transform_aggregate(
          groupby=["NM_REGIAO","Maior_22"],
          QT = "count(Maior_22)",
      ).transform_pivot(
        'Maior_22',
        groupby=['NM_REGIAO', "uf"],
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

  y_text_value+=10
  median_pct_22 = (
      base.transform_aggregate(
          groupby=["NM_REGIAO", "uf"],
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
          groupby=["NM_REGIAO", "uf"],
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
      base.transform_calculate(
          Diff = alt.datum.PCT_VOTOS_22 - alt.datum.PCT_VOTOS_18
      ).transform_aggregate(
          groupby=["NM_REGIAO", "uf"],
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
      .mark_rect(stroke='black', strokeWidth=1, opacity=box_opacity, cornerRadius=1.5, color=year_range_colors[0])
      .encode(
        x=alt.value(100),
        x2=alt.value(168),
        y=alt.value(113),
        y2=alt.value(168)
    )
  )

  return (
      alt.layer(scatter_plot, box,
          line_plot, won_22, won_18, 
          median_pct_22, median_pct_18,median_diff, 
          data=df
      )
      .facet(alt.Facet('uf:N', title=f"{region}"))
      .configure_axisX(
          orient="bottom",
      ).configure_facet(
          columns=num_cols, spacing=10
      ).configure_headerFacet(
          labelOrient="top"
      ).properties(title=f"{chart_title}")
      .configure_title(anchor="middle")
  )
  
'''

'''
def bar_plot_capitals(
    df:pl.DataFrame, chart_title:str,
    color_range:list[str]=["#B3B2D6","#1A67AC"],
    y_domain:list[int]=[0, 1.],
    region:str="",
    color_column:str="ANO_ELEICAO",
    legend_title="Eleição",
    y_title="Percentual de votos",
    filter_col:str="ANO_ELEICAO",
    filter_values=[2018,2022])->alt.vegalite.v5.api.Chart:

  scale=alt.Scale(range=color_range)

  base = alt.Chart(df).encode(
    x=alt.X("nome:N", title=""),
    y=alt.Y("PCT_VOTOS_MUNIC:Q", title=f"{y_title}", scale=alt.Scale(domain=y_domain), axis=alt.Axis(format=".0%"))
  )

  lines = base.mark_line(
      opacity=.6,
      point=alt.OverlayMarkDef(filled=True, opacity=.9, size=140)
  ).encode(
    color=alt.Color(f"{color_column}:N", title=f"{legend_title}", scale=scale),
    tooltip=[
        alt.Tooltip('ANO_ELEICAO:N', title='Ano da Eleição'),
        alt.Tooltip('uf:N', title='Estado'),
        alt.Tooltip('nome:N', title='Capital'),
        alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Geral de Votos"),
        alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Total Votos Partido"),
        alt.Tooltip('PCT_VOTOS_MUNIC:Q', format=".2%", title='Perc. Votos')
    ]
  ).properties(
      title=f"{region}"
  )

  dotted_lines = base.mark_line(opacity=.4, strokeDash=[12,8], color="#5EAFC0").encode(
        alt.Y("min(PCT_VOTOS_MUNIC):Q"),
        alt.Y2("max(PCT_VOTOS_MUNIC):Q")
    )

   #   text=alt.expr.if_((alt.datum.Mdna_22-alt.datum.Mdna_18)>0, "+", "") +
   #                     alt.expr.format((alt.datum.Mdna_22-alt.datum.Mdna_18), ".2%"),

  df_diff = df.filter(
      pl.col(f"{filter_col}")==filter_values[0]
  ).join(
      (df.filter(pl.col(f"{filter_col}")==filter_values[1])),
      on="nome"
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

  return alt.layer(lines, dotted_lines, diff_text)

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
      y=alt.Y('density:Q', title="").stack(None),
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

def perc_votting_by_city(
  df_18:pl.DataFrame, 
  df_22:pl.DataFrame, 
  df_municipios:pl.DataFrame,
  breaks=list[float], 
  domain=list[str], cargo:list[str]=[],
  group_by_cols:list[str]=["ANO_ELEICAO", "SG_PARTIDO", "NM_REGIAO", "CD_MUNICIPIO"])->pl.DataFrame:
    df_poll_18_tmp=(df_18
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by(group_by_cols)
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC"),
                pl.lit("A").alias("TIPO")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            #.filter((pl.col("SG_PARTIDO").is_in(partidos)))
        )   

    df_poll_22_tmp=(df_22
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by(group_by_cols)
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC"),
                pl.lit("A").alias("TIPO")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            #.filter((pl.col("SG_PARTIDO").is_in(partidos)))
        )  

    df_poll_18_tmp = df_poll_18_tmp.with_columns(
        pl.col("PCT_VOTOS_MUNIC").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )

    df_poll_22_tmp = df_poll_22_tmp.with_columns(
        pl.col("PCT_VOTOS_MUNIC").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )

    return pl.concat([df_poll_18_tmp, df_poll_22_tmp])

def set_region_agg_for_choro(df:pl.DataFrame, partidos:list[str]=[], eleicoes:list[int]=[],
                             tipo:str="B", breaks=list[float], domain=list[str]):
  df_tmp = df
  if partidos:
    df_tmp = df_tmp.filter(pl.col("SG_PARTIDO").is_in(partidos))
  if eleicoes:
    df_tmp = df_tmp.filter(pl.col("ANO_ELEICAO").is_in(eleicoes))

  return (
      df_tmp.group_by(["ANO_ELEICAO","NM_REGIAO"])
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
        pl.lit(tipo).alias("TIPO"),
        pl.lit(partidos[0]).alias("SG_PARTIDO"), pl.lit(0).cast(pl.Int64).alias("CD_MUNICIPIO"),
        pl.lit(0).cast(pl.Float64).alias("PCT_VOTOS_MUNIC"), pl.lit(0).cast(pl.Int64).alias("TOTAL_VOTOS_MUNIC"),
        pl.lit(0).cast(pl.Int64).alias("codigo_ibge"), pl.lit("").alias("nome"), pl.lit("").alias("uf"),
        pl.lit(0).cast(pl.Float64).alias("latitude"),pl.lit(0).cast(pl.Float64).alias("longitude"),
        pl.lit("<=5%").cast(pl.Categorical(ordering='physical')).alias("PCT_VOTOS_LIMIT")
    )
    .select(df.columns)
    .with_columns(
        pl.col("PCT_VOTOS_MUNIC").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )   
  )

'''
  Resumo dos mapas 

  df_totais:pl.DataFrame -> votos totais por região
  df_perc:pl.DataFrame -> votos percentuais por região
  year:int -> ano da eleição
'''
def map_resume(
  df_totais:pl.DataFrame, df_perc:pl.DataFrame, year:int, color:str=""
)->alt.vegalite.v5.api.Chart:
  if color:
    color = alt.value(color)
  else:
    color = alt.condition(
        alt.datum.ANO_ELEICAO == 2018,
          alt.value(year_range_colors[0]),
          alt.value(year_range_colors[1])
    )
  ##########################
  ## Barras valore totais ##
  ##########################
  base = (
      alt.Chart(df_totais.filter( (pl.col("ANO_ELEICAO")==year) & (pl.col("TIPO")!="A" )))
      .mark_bar(strokeWidth=.5, stroke="#fff", cornerRadius=4, size=8)
      .encode(
        x=alt.X('NM_REGIAO:N', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('QT_VOTOS_VALIDOS:Q', title="Votação", axis=alt.Axis(format="s")),
        xOffset="TIPO:N",
        color=color,
        opacity=alt.condition(
            alt.datum.TIPO == "C",
            alt.value(1),
            alt.value(.8)
        ),
        tooltip=[
            alt.Tooltip('NM_REGIAO:N', title="Região"),
            alt.Tooltip('QT_VOTOS_VALIDOS:Q', format=",d", title="Votação"),
        ],
        text=alt.Text('sum(QT_VOTOS_VALIDOS):Q', format=",d"),
      )
  )

  regions = alt.layer(base,
      (
          base
          .mark_text(fontSize=10, yOffset=-25, angle=270)
          .encode(color=alt.value("#000"))
      )
  ).properties(width=200, height=120)

  axis_labels =(
      "datum.label == 'B' ? 'Brasil' : 'Partido'"
  )

  base = (
      alt.Chart(df_totais.filter( (pl.col("ANO_ELEICAO")==year) & (pl.col("TIPO")!="A" )))    
      .transform_aggregate(
          groupby=["ANO_ELEICAO", "TIPO"],
          QT_VOTOS_VALIDOS = "sum(QT_VOTOS_VALIDOS)"
      ).mark_bar(
          strokeWidth=.5, stroke="#fff", cornerRadius=4, size=8
      ).encode(
          y=alt.Y('QT_VOTOS_VALIDOS:Q', title="", axis=None),
          x=alt.X('TIPO:N', title="", axis=alt.Axis(labelAngle=-45, labelExpr=axis_labels)),
          color=color,
          text=alt.Text('QT_VOTOS_VALIDOS:Q', format=",d"),
          tooltip=[
              alt.Tooltip('ANO_ELEICAO:N', title="Eleição"),
              alt.Tooltip('QT_VOTOS_VALIDOS:Q', format=",d", title="Votação"),
          ]
      )
  )

  brasil = alt.layer(base,
      (
          base
          .mark_text(fontSize=8.2, yOffset=-5)
          .encode(color=alt.value("#000"))
      )
  )

  ###############################
  ## Barras valore Percentuais ##
  ###############################
  base = (
      alt.Chart(df_perc.filter( pl.col("ANO_ELEICAO")==year))
      .mark_bar(strokeWidth=.5, stroke="#fff", cornerRadius=4, size=8)
      .encode(
        x=alt.X('NM_REGIAO:N', title="", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(
            'PERC:Q', title="Votação", 
            axis=alt.Axis(
              format=".0%"
            ),
            #scale=alt.Scale(domain=[0, .4]),
        ),
        color=color,
        tooltip=[
            alt.Tooltip('NM_REGIAO:N', title="Região"),
            alt.Tooltip('PERC:Q', format=".2%", title="Percentual"),
        ],
        text=alt.Text('PERC:Q', format=".2%"),
      )
  )

  regions_perc = alt.layer(base,
      (
          base
          .mark_text(fontSize=10, yOffset=-8)
          .encode(color=alt.value("#000"))
      )
  ).properties(width=200, height=80)

  base = (
      alt.Chart(df_perc.filter(pl.col("ANO_ELEICAO")==year))    
      .transform_aggregate(
          groupby=["ANO_ELEICAO"],
          QT_VOTOS_TOTAIS = "sum(QT_TOTAL_REG)",
          QT_VOTOS_PART = "sum(QT_TOTAL_PART)"
      ).transform_calculate(
          PERC = alt.datum.QT_VOTOS_PART/alt.datum.QT_VOTOS_TOTAIS
      )
      .mark_bar(
          strokeWidth=.5, stroke="#fff", cornerRadius=4, size=8
      ).encode(
          y=alt.Y('PERC:Q', title="", axis=None),
          x=alt.X("ANO_ELEICAO:N", title="", axis=alt.Axis(labelAngle=-45)),
          color=color,
          text=alt.Text('PERC:Q', format=".2%"),
          tooltip=[
            alt.Tooltip('ANO_ELEICAO:N', title="Eleição"),
            alt.Tooltip('PERC:Q', format=".2%", title="Percentual"),
        ]
      )
  )

  brasil_perc = alt.layer(base,
      (
          base
          .mark_text(fontSize=8.2, yOffset=-5, angle=0)
          .encode(color=alt.value("#000"))
      )
  )

  return (
      alt.concat(regions, brasil).resolve_scale(y="shared") &
      alt.concat(regions_perc, brasil_perc).resolve_scale(y="shared")
  )

def votes_by_region(df:pl.DataFrame, partido:str="", eleicao:int=2018,
                        tipo:str="B", res_ideologico:str="",
                        breaks=list[float], domain=list[str]):
  df_tmp = df
  if partido:
    df_tmp = df_tmp.filter(pl.col("SG_PARTIDO")==partido)
  if eleicao:
    df_tmp = df_tmp.filter(pl.col("ANO_ELEICAO").is_in(eleicao))
  if res_ideologico:
    df_tmp = df_tmp.filter(pl.col("NOME_RES_IDEOLOGICO")==res_ideologico)

  return (
      df_tmp.group_by(["ANO_ELEICAO","NM_REGIAO"])
      .agg(pl.col("QT_VOTOS_VALIDOS").sum())
      .with_columns(
        pl.lit(tipo).alias("TIPO"),
        pl.lit(partido).alias("SG_PARTIDO"), pl.lit(0).cast(pl.Int64).alias("CD_MUNICIPIO"),
        pl.lit(res_ideologico).alias("NOME_RES_IDEOLOGICO"),
        pl.lit(0).cast(pl.Float64).alias("PCT_VOTOS_MUNIC"), pl.lit(0).cast(pl.Int64).alias("TOTAL_VOTOS_MUNIC"),
        pl.lit(0).cast(pl.Int64).alias("codigo_ibge"), pl.lit("").alias("nome"), pl.lit("").alias("uf"),
        pl.lit(0).cast(pl.Float64).alias("latitude"),pl.lit(0).cast(pl.Float64).alias("longitude"),
        pl.lit("<=5%").cast(pl.Categorical(ordering='physical')).alias("PCT_VOTOS_LIMIT")
    )
    .select(df.columns)
    .with_columns(
        pl.col("PCT_VOTOS_MUNIC").cut(breaks, labels=domain).alias("PCT_VOTOS_LIMIT")
    )   
  )

def resumo_eleicao(
    summary:pl.DataFrame, ano_eleicao:str='2018',
    color_range:list[str]=["#C54B53", "#D68186"],
    text_color:str="#000",
    y_domain:list[int]=[0, 50_000_000]
    )->alt.vegalite.v5.api.Chart:

  dy:float=6.
  font_size:float=10.

  scale = alt.Scale(
      domain=["Partido","Região"],
      range=color_range
  )

  base = (
    alt.Chart(summary)
  )

  bar1 = base.transform_calculate(
    VOTACAO="'Partido'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="",
              sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom", values=[])),
      y=alt.Y('Votos_'+ ano_eleicao[-2:] + ':Q', scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s")),
      color=alt.Color("VOTACAO:N", title="", scale=scale),
      text=alt.Text('Votos_'+ ano_eleicao[-2:] + ':Q', format='.4s'),
  )

  bar2 = base.transform_calculate(
    VOTACAO="'Região'"
  ).mark_bar(opacity=.7).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Votos_'+ ano_eleicao[-2:] + ':Q', title=""),
      y2=alt.Y2('Total_'+ ano_eleicao[-2:] + ':Q'),
      color=alt.Color("VOTACAO:N", title="Votos", scale=scale,
                  legend=alt.Legend(direction="horizontal",
                                    orient="none", legendX=55, legendY=320,
                                    titleAnchor="middle")),
      text=alt.Text('Total_'+ ano_eleicao[-2:] + ':Q', format='.4s'),
  )

  bar1_text = bar1.mark_text(dy=dy, fontSize=font_size).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('Votos_'+ ano_eleicao[-2:] + ':Q', title=""),
      color=alt.value(f"{text_color}")
  )

  bar2_text = bar2.mark_text(dy=dy, fontSize=font_size).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('Total_'+ ano_eleicao[-2:] + ':Q', title=""),
      color=alt.value(f"{text_color}")
  )

  text = base.transform_calculate(
      text_position='datum.Total_'+ ano_eleicao[-2:]
  ).mark_text(dy=-10, fontSize=font_size).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('text_position:Q', title=""),
      text=alt.Text('text_position:Q', format='.4s'),
      color=alt.value(f"{text_color}")
  )

  return (
      alt.layer(bar1, bar2, bar1_text, bar2_text)
      .resolve_scale(x="independent")
  )

def resumo_votacao_partido(
    summary:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 50_000_000]
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
              sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom", values=[])),
      y=alt.Y('Votos_18:Q', scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s")),
      color=alt.Color("ANO:N", scale=scale),
      text=alt.Text('Votos_18:Q', format='.4s'),
  )

  bar2 = base.transform_calculate(
    ANO="'2022'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Votos_18:Q', title=""),
      y2=alt.Y2('Votos_22:Q'),
      color=alt.Color("ANO:N", title="Eleiçao", scale=scale,
                      legend=alt.Legend(direction="horizontal",
                                        orient="none", legendX=55, legendY=320,
                                        titleAnchor="middle")),
      text=alt.Text('Votos_22:Q', format='.4s'),
  )

  bar1_text = bar1.mark_text(
        dy=dy, fontSize=font_size
      ).encode(
        x=alt.X("NM_REGIAO:N", title="", 
                sort=alt.EncodingSortField("Crescimento"),
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
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('y:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar2, bar1_text, diff_text)
      .resolve_scale(x="independent")
  )


def resumo_perc_votacao_partido(
    summary:pl.DataFrame,
    color_range:list[str]=year_range_colors,
    y_domain:list[int]=[0, 1.]
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
              sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom", values=[])),
      y=alt.Y('Mdna_18:Q', scale=alt.Scale(domain=y_domain), axis=alt.Axis(format="s")),
      color=alt.Color("ANO:N", scale=scale),
      text=alt.Text('Mdna_18:Q', format='.2%'),
  )

  bar2 = base.transform_calculate(
    ANO="'2022'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Mdna_18:Q', title=""),
      y2=alt.Y2('Mdna_22:Q'),
      color=alt.Color("ANO:N", title="Eleiçao", scale=scale,
                      legend=alt.Legend(direction="horizontal",
                                        orient="none", legendX=55, legendY=320,
                                        titleAnchor="middle")),
      text=alt.Text('Mdna_22:Q', format='.2%'),
  )

  bar1_text = bar1.mark_text(dy=dy, fontSize=font_size).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('Mdna_18:Q', title=""),
      color=alt.value("#000")
  )

  diff_text = base.transform_calculate(
      #text="+" + alt.expr.format((alt.datum.Mdna_22-alt.datum.Mdna_18), ".2%"),
      text=alt.expr.if_((alt.datum.Mdna_22-alt.datum.Mdna_18)>0, "+", "") + 
                        alt.expr.format((alt.datum.Mdna_22-alt.datum.Mdna_18), ".2%"),      
      #y=(alt.datum.Mdna_18 +  (alt.datum.Mdna_22-alt.datum.Mdna_18)/2)
      y=alt.expr.if_((alt.datum.Mdna_22-alt.datum.Mdna_18)<0,
        (alt.datum.Mdna_18-.07),
        alt.expr.if_((alt.datum.Mdna_22-alt.datum.Mdna_18) < .02,
                        (alt.datum.Mdna_18+.04),
                        (alt.datum.Mdna_18 + (alt.datum.Mdna_22-alt.datum.Mdna_18)/2)                       
        )
      )
      #y=alt.expr.if_(
      #    (alt.datum.Mdna_22-alt.datum.Mdna_18)<0, 
      #    (alt.datum.Votos_18-.1), 
      #    alt.expr.if_((alt.datum.Mdna_22-alt.datum.Mdna_18) < 0.05,
      #                 (alt.datum.Votos_18+.05),
      #                 (alt.datum.Mdna_18 +(alt.datum.Mdna_22-alt.datum.Mdna_18)/2)
      #    )
      #)      
  ).mark_text(dy=0, fontSize=font_size-1).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(labels=False, ticks=False)),
      y=alt.Y('y:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar2, bar1_text, diff_text)
      .resolve_scale(x="independent")
  )

def resumo_cresc_perc_votacao_partido(
    summary:pl.DataFrame,
    color_range:list[str]=["#C54B53", "#D68186"],
    y_domain:list[int]=[0, 1.]
    )->alt.vegalite.v5.api.Chart:

  dy:float=6.
  font_size:float=10.

  scale = alt.Scale(
      domain=["Geral","Partido"],
      range=color_range
  )

  y_domain = [
      get_min_domain( summary.get_column("Crescimento").min() ), 
      1, 
  ]

  base = (
    alt.Chart(summary)
  )

  bar1 = base.transform_calculate(
    tp_cresc="'Partido'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="", axis=None, sort=alt.EncodingSortField("Crescimento")),
      y=alt.Y('Crescimento:Q', title="", scale=alt.Scale(domain=y_domain)),
      color=alt.Color("tp_cresc:N", scale=scale,
                      title="Crescimento",
                      legend=None),
      text=alt.Text('Crescimento:Q', format=".2%"),
  )

  bar1_text = bar1.mark_text(dy=dy, fontSize=9).encode(
      x=alt.X("NM_REGIAO:N", title="", axis=None, sort=alt.EncodingSortField("Crescimento")),
      y=alt.Y('Crescimento', title="", scale=alt.Scale(domain=y_domain)),
      color=alt.value("#000")
  )

  diff_text = base.transform_calculate(
      #text="+" + alt.expr.format((alt.datum.Votos_22-alt.datum.Votos_18), ".3s"),
      text=alt.expr.if_((alt.datum.Votos_22-alt.datum.Votos_18)>0, "+", "") + 
                        alt.expr.format((alt.datum.Votos_22-alt.datum.Votos_18), ".3s"),         
  ).mark_text(dy=-10, fontSize=font_size-1).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento")),
      y=alt.Y('Crescimento:Q', title=""),
      text=alt.Text('text:N'),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar1_text, diff_text)
      .resolve_scale(x="independent")
  )

def resumo_perc_votacao_diff(
    summary:pl.DataFrame,
    color_range:list[str]=["#C54B53", "#D68186"],
    y_domain:list[int]=[0, 1.]
    )->alt.vegalite.v5.api.Chart:

  dy:float=6.
  font_size:float=10.

  scale = alt.Scale(
      domain=["Geral","Partido"],
      range=color_range
  )

  base = (
    alt.Chart(summary)
  )

  y_domain = [
      get_min_domain( summary.get_column("Mdna Diff").min() ), 
      1, 
  ]

  bar1 = base.transform_calculate(
    tp_cresc="'Partido'"
  ).mark_bar().encode(
      x=alt.X("NM_REGIAO:N", title="",
              sort=alt.EncodingSortField("Crescimento"),
              axis=alt.Axis(orient="bottom")),
      y=alt.Y('Mdna Diff:Q', title="", scale=alt.Scale(domain=y_domain)),
      color=alt.Color("tp_cresc:N", scale=scale, legend=None),
      text=alt.Text('Mdna Diff:Q', format=".2%"),
  )

  bar1_text = bar1.mark_text(dy=dy, fontSize=10).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=None),
      y=alt.Y('Mdna Diff', axis=None, title="", scale=alt.Scale(domain=y_domain)),
      color=alt.value("#000")
  )


  line = base.transform_calculate(
      tp_cresc="'Partido'"
    ).mark_line(
      opacity=.8,
      point=alt.OverlayMarkDef(opacity=.4, filled=True, size=40)
    ).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=None),      
      y=alt.Y('Mdna Diff Abs:Q', title=""),
      text=alt.Text('Mdna Diff Abs:Q', format=",d"),
      color=alt.Color("tp_cresc:N", scale=scale, legend=None),      
  )

  line_text = line.mark_text(dy=-10, fontSize=10).encode(
      x=alt.X("NM_REGIAO:N", title="", sort=alt.EncodingSortField("Crescimento"),
              axis=None),
      #y=alt.Y('Mdna Diff Abs:Q', axis=None, title="", scale=alt.Scale(domain=y_domain)),
      color=alt.value("#000")
  )

  return (
      alt.layer(bar1,bar1_text,line,line_text)
      .resolve_scale(x="independent", y="independent")
  )

def summary_by_region(df_tmp:pl.DataFrame, df_cresc_perc_regiao:pl.DataFrame, region:str="")->pl.DataFrame:
  return (
    (
    df_tmp.filter(
          (pl.col("ANO_ELEICAO")==2018) &
          (pl.col("NM_REGIAO")==f"{region}")
      ).select(
          ["NM_REGIAO","nome", "PCT_VOTOS_MUNIC"]
      ).rename({"PCT_VOTOS_MUNIC":"PCT_VOTOS_18"})
    ).join(
      (
        df_tmp.filter(
            (pl.col("ANO_ELEICAO")==2022) &
            (pl.col("NM_REGIAO")==f"{region}")
        ).select(
            ["NM_REGIAO","nome", "PCT_VOTOS_MUNIC"]
        ).rename({"PCT_VOTOS_MUNIC":"PCT_VOTOS_22"})
      ), on=["NM_REGIAO","nome"]
    ).with_columns(
        ( (pl.col("PCT_VOTOS_22")-pl.col("PCT_VOTOS_18"))/(pl.col("PCT_VOTOS_18"))).alias("Crescimento")
    ).join(
        df_cresc_perc_regiao, on="NM_REGIAO"
    ).rename({"Crescimento_right":"Crescimento_Regiao"})
  )

def bar_plot_cidades(
    summary:pl.DataFrame,
    color_range:list[str]=["#C54B53", "#D68186"],
    y_domain:list[int]=[0, 1.],
    y_rule:float=.5
    )->alt.vegalite.v5.api.Chart:

  font_size:float=10.

  scale = alt.Scale(
      domain=["Geral","Partido"],
      range=color_range
  )

  base = (
    alt.Chart(summary)
  )

  bar1 = base.transform_calculate(
    tp_cresc="'Partido'"
  ).mark_bar().encode(
      x=alt.X("nome:N", title="", #sort=alt.EncodingSortField("Crescimento")
      ),
      y=alt.Y('Crescimento:Q', title="", scale=alt.Scale(domain=y_domain)),
      color=alt.Color("tp_cresc:N", scale=scale,
                      title="Crescimento",
                      legend=None),
      text=alt.Text('Crescimento:Q', format=".2%"),
  )

  bar1_text = bar1.mark_text(fontSize=9, dx=-20, baseline='middle', angle=270).encode(
      x=alt.X("nome:N", title="", #sort=alt.EncodingSortField("Crescimento")
      ),
      y=alt.Y('Crescimento', title="", scale=alt.Scale(domain=y_domain)),
      color=alt.value("#000")
  )

  line = base.transform_calculate(
      text="Crescimento Regional: " +
        alt.expr.format(alt.expr.max(alt.datum.Crescimento_Regiao), ".2%"),
  ).mark_rule(color='steelblue', opacity=.7, strokeWidth=1, strokeDash=[8,4] ).encode(
      y='mean(Crescimento_Regiao):Q',
      #text=alt.Text('mean(Crescimento_Regiao):Q', format=".2%"),
      text='text:N'
  )

  line_text = line.mark_text(fontSize=8, align='left', dy=9, dx=-71).encode(
      x=alt.X("max(nome):N")
  )

  circle = line_text.mark_circle(size=50, dx=100).encode(
      x=alt.X("max(nome):N"),
      y='mean(Crescimento_Regiao):Q',
  )

  return (
      alt.layer(bar1,bar1_text, line, line_text)
      .resolve_scale(x="shared")
  )