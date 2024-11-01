import polars as pl
import altair as alt

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
        df_colors, 
        title="Classificação ideológica dos partidos políticos brasileiros"
    ).mark_point(
        filled=True,
        size=100,
        opacity=.6
    ).encode(
        x=alt.X("MEDIA_IDEOL:Q", 
                title="Média Ideológica",
                scale=alt.Scale(nice=True)
        ),
        shape=alt.ShapeValue(person),
        color=alt.Color('SG_POSIC_IDEOLOGICO:O',
            scale=color_scale,
            title="Ideologia"
        ),
        tooltip=[
            alt.Tooltip("SG_PARTIDO:O", title="Partido"),
            alt.Tooltip("MEDIA_IDEOL:Q", title="Média Ideológica", format=".2f",)
        ]        
    )
    text = points.mark_text(
        align="left",
        baseline="top",
        dy=-3,
        dx=30,
        fontSize=8,
        angle=270,
        fontWeight="bold",
        opacity=1
    ).encode(
        text=alt.Text("SG_PARTIDO:O"),
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

'''
def grouped_bar_chart(df_2018:pl.DataFrame, df_2022:pl.DataFrame, df_colors:pl.DataFrame,  
                      position:list[int], chart_title:str, total_parties:int=5)->alt.vegalite.v5.api.Chart:
    # soma todos os votos por partidos de 2018
    df_tmp_18 = filter_by_position(df_2018, position)
    
    df_tmp_18 = (df_tmp_18
        .select(pl.col("ANO_ELEICAO", "SIGLA_2022","SG_POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
        .group_by(["ANO_ELEICAO", "SIGLA_2022","SG_POSIC_IDEOLOGICO"], maintain_order=True)
        .agg(pl.col("QT_VOTOS_VALIDOS").sum())
        .join(df_colors, left_on="SIGLA_2022", right_on="SG_PARTIDO", how="inner")
    )
    
    # soma todos os votos por partidos de 2022
    df_tmp_22 = filter_by_position(df_2022, position)
    
    df_tmp_22 = (df_tmp_22
        .select(pl.col("ANO_ELEICAO", "SIGLA_2022","SG_POSIC_IDEOLOGICO","QT_VOTOS_VALIDOS"))
        .group_by(["ANO_ELEICAO", "SIGLA_2022","SG_POSIC_IDEOLOGICO"], maintain_order=True)
        .agg(pl.col("QT_VOTOS_VALIDOS").sum())
        .join(df_colors, left_on="SIGLA_2022", right_on="SG_PARTIDO", how="inner")
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
        row = alt.Row('SIGLA_2022:N',
            title="",
            spacing = 5,
            header=alt.Header(labelAngle=0, labelAlign='left', title=f'{chart_title}', titleFontSize=12),
            sort=alt.SortField("QT_ORDER", order="descending"),                      
        ),
        opacity=alt.OpacityValue(0.75),
        tooltip=[
            alt.Tooltip('SIGLA_2022:N', title="Partido"),
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
def choropleth_votting(df_2018:pl.DataFrame, df_2022:pl.DataFrame, 
                       chart_title:str, parties:list[str], years:list[int]=[2018,2022])->alt.vegalite.v5.api.Chart:
    
    df_facet = pl.concat([df_2018,df_2022])
    
    regions = alt.Data(
        url='https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/br_regions.json',
        format=alt.DataFormat(property='features')
    )
    
    states = alt.Data(
        url='https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/br_states.json',
        format=alt.DataFormat(property='features')
    ) 
    
    cities = alt.Data(
        url="https://raw.githubusercontent.com/perferctstorm/DiscursoOdioEleicoes/refs/heads/main/Dados/Eleicoes/geojs-100-mun_minifier.json",
        format=alt.DataFormat(property='features')
    ) 
    
    background_reg:alt.vegalite.v5.api.Chart = (
        alt.Chart(alt.Data(regions))
        .mark_geoshape(
            stroke='#98CCAA',
            fillOpacity=0,
            strokeWidth=1.5
        )
    )   
    
    background_states:alt.vegalite.v5.api.Chart = (
        alt.Chart(alt.Data(states))
        .mark_geoshape(
            stroke='#98CCAA',
            fillOpacity=.0,
            strokeWidth=.7
        )
    )
    
    return alt.concat(
    *(
        (
            background_reg + background_states +
            alt.Chart(cities) \
            .mark_geoshape(
                stroke="#000", strokeWidth=.035, fillOpacity=.6
            ).project(
                type="equirectangular"  
            ).transform_lookup(
                lookup='properties.id',
                from_=alt.LookupData(df_facet.filter( (pl.col("ANO_ELEICAO")==ano) & (pl.col("SIGLA_2022")==party) ), 
                    'codigo_ibge', 
                    fields=list(["uf", "nome", "QT_VOTOS_VALIDOS", "TOTAL_VOTOS_MUNIC", "PCT_VOTOS_MUNIC"])
                )
            ).encode(
                color=alt.Color("PCT_VOTOS_MUNIC:Q", 
                    legend=alt.Legend(orient="bottom", titleAnchor='middle', title="", direction="horizontal")
                ),
                tooltip=[
                    alt.Tooltip('uf:N', title='Estado'),
                    alt.Tooltip('nome:N', title="Município"),
                    alt.Tooltip("QT_VOTOS_VALIDOS:Q",format=",d", title="Votos"),  
                    alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Votos Município")
                ]
            ).properties(title=f"{party} ({ano})")
        ) for ano in years for party in parties
    ),
        columns=2, title=f"{chart_title}"
    ).resolve_scale(
        color="independent"
    ).configure_title(
        anchor='middle', fontSize=12,
    )

'''
    Filtra os votos de duas eleições com o percentual de votos do partido em relação ao município
    Agrupa os votos por cada município brasileiro e compara a votação do partido com o restante dos votos do município
'''
def filter_choropleth_votting(df_2018:pl.DataFrame,df_2022:pl.DataFrame, df_municipios:pl.DataFrame, cargo:list[int], partido:str):
    df_poll_18_tmp=(df_2018
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by("ANO_ELEICAO", "SIGLA_2022", "NM_REGIAO", "CD_MUNICIPIO")
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            .filter((pl.col("SIGLA_2022")==partido))
        )   
    
    df_poll_22_tmp=(df_2022
            .filter( pl.col("CD_CARGO").is_in( cargo ) )
            .group_by("ANO_ELEICAO", "SIGLA_2022", "NM_REGIAO", "CD_MUNICIPIO")
            .agg(pl.col("QT_VOTOS_VALIDOS").sum())                    
            .with_columns(
                (pl.col("QT_VOTOS_VALIDOS") / pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO")).alias("PCT_VOTOS_MUNIC"),
                pl.sum("QT_VOTOS_VALIDOS").over("CD_MUNICIPIO").alias("TOTAL_VOTOS_MUNIC")
            )
            .join(df_municipios, left_on="CD_MUNICIPIO", right_on="codigo_tse", how="inner")
            .drop(pl.col(["capital","ddd"]))            
            .filter((pl.col("SIGLA_2022")==partido))
        )  
    return df_poll_18_tmp, df_poll_22_tmp

'''
   Box plot com percentual de votos por partido em relação ao somatório dos demais partidos
   
'''
def box_plots_votting_by_uf(df:pl.DataFrame, title:str, facet_column:str="ANO_ELEICAO")->alt.vegalite.v5.api.Chart:
    boxes = (
        alt.Chart()
        .mark_boxplot()
        .encode(
            x=alt.X("PCT_VOTOS_MUNIC:Q", title="% de Votos", axis=alt.Axis(format='%', labelAngle=-90) ),
            y=alt.Y("uf:N", title="Estado", sort=alt.SortField(field="NM_REGIAO", order='ascending') ),
            color=alt.Color("NM_REGIAO:N", title="Região"),
            tooltip=[
                alt.Tooltip("uf:N", title="Estado"),
                alt.Tooltip("nome:N", title="Município"),
                alt.Tooltip("TOTAL_VOTOS_MUNIC:Q", format=",d", title="Total Geral de Votos"),
                alt.Tooltip("QT_VOTOS_VALIDOS:Q", format=",d", title="Votos no PT"),
                alt.Tooltip("PCT_VOTOS_MUNIC:Q", format=".2%", title="% Votos no PT"),
            ]
        )
    )
    
    bars = (
        alt.Chart()
        .transform_aggregate(
            min="min(PCT_VOTOS_MUNIC):Q",
            max="max(PCT_VOTOS_MUNIC):Q",
            mean="mean(PCT_VOTOS_MUNIC):Q",
            median="median(PCT_VOTOS_MUNIC):Q",
            q1="q1(PCT_VOTOS_MUNIC):Q",
            q3="q3(PCT_VOTOS_MUNIC):Q",
            count="count()",
            groupby=["ANO_ELEICAO","NM_REGIAO", "uf"]
        ).mark_bar(opacity=0)
        .encode(
            y=alt.Y('uf:O', sort=alt.SortField(field="NM_REGIAO", order='ascending')),
            x='q1:Q',
            x2='q3:Q',
            color=alt.Color("NM_REGIAO:N", title="Região"),
            tooltip=[
                alt.Tooltip("NM_REGIAO:N", title="Região"),
                alt.Tooltip("uf:N", title="Estado"),        
                alt.Tooltip('max:Q', title="Máximo", format=".2%"),
                alt.Tooltip('q3:Q', title="3o Quartil", format=".2%"),
                alt.Tooltip('median:Q', title="Mediana", format=".2%"),
                alt.Tooltip('q1:Q', title="1o Quartil", format=".2%"),
                alt.Tooltip('min:Q', title="Mínimo", format=".2%"),
            ]
        )
    )
    
    return (
        alt.layer(boxes, bars, data=df)
        .facet(
            column=alt.Column(f'{facet_column}:N', title=""), 
            title=f"{title}", 
            center=True
        ).configure_title(
            #align="center",
            fontSize=14,
            anchor='middle',
        )
    )

'''
   Box plot com percentual de votos por partido em relação ao somatório dos demais partidos
   
'''
def box_plots_votting_by_region(df:pl.DataFrame, title:str, facet_column:str="ANO_ELEICAO")->alt.vegalite.v5.api.Chart:
    boxes = (
        alt.Chart()
        .mark_boxplot()
        .encode(
        y=alt.Y("PCT_VOTOS_MUNIC:Q", title="Votação", axis=alt.Axis(format='%')).scale(zero=False),
        x=alt.X("NM_REGIAO:N", title=""),
        color=alt.Color("NM_REGIAO:N").legend(None),
       tooltip=[
            alt.Tooltip("NM_REGIAO:N", title="Região"),
            alt.Tooltip("uf:N", title="Estado"),        
            alt.Tooltip('max:Q', title="Máximo", format=".2%"),
            alt.Tooltip('q3:Q', title="3o Quartil", format=".2%"),
            alt.Tooltip('median:Q', title="Mediana", format=".2%"),
            alt.Tooltip('q1:Q', title="1o Quartil", format=".2%"),
            alt.Tooltip('min:Q', title="Mínimo", format=".2%"),
        ]
        ).properties(
            width=200
        )
    )
    
    bars = (
        alt.Chart()
        .transform_aggregate(
            PCT_VOTOS_UF="sum(PCT_VOTOS_MUNIC):Q",
            max="max(PCT_VOTOS_MUNIC):Q",
            mean="mean(PCT_VOTOS_MUNIC):Q",
            median="median(PCT_VOTOS_MUNIC):Q",
            q1="q1(PCT_VOTOS_MUNIC):Q",
            q3="q3(PCT_VOTOS_MUNIC):Q",
            count="count()",
            groupby=["ANO_ELEICAO","NM_REGIAO"]
        ).mark_bar(opacity=0)
        .encode(
            x=alt.X('NM_REGIAO:N', sort=alt.SortField(field="NM_REGIAO", order='ascending')),
            y='q1:Q',
            y2='q3:Q',
            color=alt.Color("NM_REGIAO:N", title="Região"),
            tooltip=[
                alt.Tooltip("NM_REGIAO:N", title="Região"),
                alt.Tooltip('max:Q', title="Máximo", format=".2%"),
                alt.Tooltip('q3:Q', title="3o Quartil", format=".2%"),
                alt.Tooltip('median:Q', title="Mediana", format=".2%"),
                alt.Tooltip('q1:Q', title="1o Quartil", format=".2%"),
                alt.Tooltip('min:Q', title="Mínimo", format=".2%"),
            ]
        ).properties(
            width=200
        )
    )
        
    return (
        alt.layer(boxes, bars, data=df)
        .facet(
            column=alt.Column(f'{facet_column}:N', title=""), 
            title=f"{title}",
            center=True
        ).configure_title(
            #align="center",
            fontSize=14,
            anchor='middle',
        )
    )

def scatter_votting_by_regions(df_tmp:pl.DataFrame, chart_title:str, 
                               axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
                               axis_titles:list[str]=["2018","2022"]
                            )->alt.vegalite.v5.api.Chart:
    scatter_plot = alt.Chart().mark_point().encode(
        x=alt.X(f'{axis_cols[0]}:Q', title=f"{axis_titles[0]}", axis=alt.Axis(labelAngle=-90)),
        y=alt.Y(f'{axis_cols[1]}:Q', title=f"{axis_titles[1]}"),
        color=alt.Color("uf:N", legend=None),
        tooltip=[
            alt.Tooltip("NM_REGIAO:N", title="Região"),
            alt.Tooltip("uf:N", title="Estado"),
            alt.Tooltip("nome:N", title="Município"),
            alt.Tooltip(f'{axis_cols[0]}:Q', format=".2%", title="Perc. Votos em 2018"),
            alt.Tooltip(f'{axis_cols[1]}:Q', format=".2%", title="Perc. Votos em 2022"),
        ],
    ).properties(
        width=170,
        height=170
    )
    
    line_plot =(
        alt.Chart(pl.DataFrame({"x":[0,1], "y":[0,1]}))
        .mark_line(color="#9ECAE9")
        .encode(
            x=alt.X("x:Q"),
            y=alt.Y("y:Q")
        )
    )
    
    return (
    alt.layer(scatter_plot, line_plot, data=df_tmp)
        .facet(
            column = alt.Column("NM_REGIAO:N", title="", sort=alt.SortField("NM_REGIAO")),
            center=True
        )
    ).properties(
        title=f'{chart_title}'
    ).configure_title(
        anchor='middle', fontSize=14    
    )

def scatter_facet_votting_by_regions(df_tmp:pl.DataFrame, chart_title:str,
                               axis_cols:list[str]=["PCT_VOTOS_18","PCT_VOTOS_22"],
                               axis_titles:list[str]=["2018","2022"])->alt.vegalite.v5.api.Chart:
    line_plot =(
        alt.Chart(pl.DataFrame({"x":[0,1], "y":[0,1]}))
        .mark_line(fillOpacity=0, color="#9ECAE9", opacity=.6)
        .encode(
            x=alt.X("x:Q"),
            y=alt.Y("y:Q")
        )
    )
    
    scatter_plot= alt.Chart().mark_point().encode(
        x=alt.X(f'{axis_cols[0]}:Q', title=f"{axis_titles[0]}", axis=alt.Axis(labelAngle=-90)),
        y=alt.Y(f'{axis_cols[1]}:Q', title=f"{axis_titles[1]}"),
        color=alt.Color("NM_REGIAO:N", title="Região", sort=alt.SortField("NM_REGIAO:N")),
        tooltip=[
            alt.Tooltip("NM_REGIAO:N", title="Região"),
            alt.Tooltip("uf:N", title="Estado"),
            alt.Tooltip("nome:N", title="Município"),
            alt.Tooltip(f'{axis_cols[0]}:Q', format=".2%", title=f"Perc. Votos em {axis_titles[0]}"),
            alt.Tooltip(f'{axis_cols[1]}:Q', format=".2%", title=f"Perc. Votos em {axis_titles[1]}"),
        ],
    ).properties(
        width=170,
        height=170
    )
    
    return alt.vconcat(
        *(
            alt.layer(scatter_plot, line_plot, data=df_tmp)
              .facet(facet='uf:N')
              .transform_filter(alt.datum.NM_REGIAO == val)
            for val in df_tmp.get_column("NM_REGIAO").unique().sort().to_list()
        ), title=f"{chart_title}"
    ).configure_axisX(
        orient="top",
    ).configure_facet(
        columns=4, spacing=10
    ).configure_headerFacet(
        labelOrient="bottom",
        title = None    
    ).resolve_scale(
        #color="independent"
    ).configure_title(
        anchor='middle', fontSize=14
    )