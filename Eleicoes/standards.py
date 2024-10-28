import polars as pl

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