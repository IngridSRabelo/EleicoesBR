import basedosdados as bd
import pandas as pd
import json
import os

bd.list_dataset_tables(dataset_id='br_tse_eleicoes', with_description=True)

bd.get_table_columns(
    dataset_id='br_tse_eleicoes',
    table_id='despesas_candidato'
)

bd.get_table_columns(
    dataset_id='br_tse_eleicoes',
    table_id='resultados_candidato'
)

query1 = """
SELECT sigla_uf AS Sigla, nome_partido AS Partido,
valor_despesa, id_candidato_bd, nome_candidato
FROM basedosdados.br_tse_eleicoes.despesas_candidato
WHERE ano = 2018 AND cargo = 'deputado federal'
"""
db1 = bd.read_sql(query1, billing_project_id='natural-axiom-342415')

query2 = """
SELECT id_candidato_bd, resultado
FROM basedosdados.br_tse_eleicoes.resultados_candidato
WHERE ano = 2018 AND cargo = 'deputado federal'
"""
db2 = bd.read_sql(query2, billing_project_id='natural-axiom-342415')

# Base completa: Despesas dos Candidatos a Deputados federais em 2018,
# por partido, estado e candidato
db_final = pd.merge(db1, db2, how='inner', on='id_candidato_bd')
db_final = db_final.groupby(["Sigla", "Partido", "id_candidato_bd", "resultado"]).agg(
    {"valor_despesa": "sum"}).reset_index()
result = db_final.to_json(orient='split')

dir = os.path.dirname(__file__)
out_dir = os.path.abspath(os.path.join(dir, '..', 'out'))
data_file_path = os.path.join(out_dir, 'data.json')

if (not os.path.isdir(out_dir)):
    os.mkdir(out_dir)

with open(data_file_path, 'w') as f:
    f.write(result)
    f.close()
