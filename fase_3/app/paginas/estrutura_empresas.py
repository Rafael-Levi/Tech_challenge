"""Estrutura do mercado do ponto de vista das empresas: setor, porte e maturidade em dados / IA.
Fonte: gld_ft_estrutura_empresas."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Empresas e maturidade em dados")
st.caption("Em que setores e empresas os profissionais trabalham, e quão maduras elas são em dados e IA.")

selecao = filtros.barra(["cd_setor", "cd_porte_empresa"], "empresas")
df = filtros.aplicar(dados.fato("gld_ft_estrutura_empresas", anos), selecao)

MATURIDADE = {"data_lake": "Possui data lake", "data_warehouse": "Possui data warehouse",
              "ia_prioridade_alta": "IA generativa é prioridade"}
CLIMA = ["satisfeitos", "buscando_mudar"]
filtros.indicadores(m.resumir(df, ["ano"], [*MATURIDADE, *CLIMA]), [
    ("Respondentes", "qt_respondentes", "int", None, "Profissionais no recorte filtrado."),
    ("Com data lake", "pct_data_lake", "pct", True, "Base: quem respondeu sobre a arquitetura da empresa."),
    ("Com data warehouse", "pct_data_warehouse", "pct", True, "Base: quem respondeu sobre a arquitetura da empresa."),
    ("IA é prioridade", "pct_ia_prioridade_alta", "pct", True,
     "Empresas em que a IA generativa é prioridade alta, segundo os respondentes."),
    ("Satisfeitos", "pct_satisfeitos", "pct", True, "Base: quem respondeu sobre satisfação."),
])

ds_setor, ds_porte = dados.coluna_ds("cd_setor"), dados.coluna_ds("cd_porte_empresa")

st.subheader("Maturidade em dados e IA por porte da empresa")
st.caption("Quanto maior a empresa, mais estruturada a arquitetura de dados? (% sobre quem respondeu; "
           "pontos com menos de 30 respostas ficam de fora)")
r = m.resumir(df[df["cd_porte_empresa"] != dados.NAO_INFORMADO], ["ano", ds_porte], list(MATURIDADE), salario=False)
for k in MATURIDADE:  # pontos com menos de 30 respostas são ruído de amostra
    r.loc[r[f"qt_base_{k}"] < 30, f"pct_{k}"] = float("nan")
longo = r.melt(id_vars=["ano", ds_porte], value_vars=[f"pct_{k}" for k in MATURIDADE],
               var_name="indicador", value_name="pct")
longo["indicador"] = longo["indicador"].str.removeprefix("pct_").map(MATURIDADE)
gr.mostrar(gr.linhas(longo, ds_porte, "indicador", "pct", dados.ordem("cd_porte_empresa"), list(MATURIDADE.values())),
           longo.pivot_table(index=["ano", ds_porte], columns="indicador", values="pct", sort=False)
           .round(1).reset_index().rename(columns={ds_porte: "Porte da empresa"}))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Setor de atuação da empresa")
    st.caption("% dos respondentes do recorte em cada setor.")
    r = m.participacao(df, ds_setor)
    gr.mostrar(gr.barras(r, ds_setor, "pct_participacao"),
               r[["ano", ds_setor, "qt_respondentes", "pct_participacao"]].round(1)
               .rename(columns={ds_setor: "Setor", "qt_respondentes": "Respondentes", "pct_participacao": "% do total"}))
with c2:
    st.subheader("IA generativa como prioridade, por setor")
    n_min = st.slider("Mínimo de respostas por setor", 10, 100, 30, step=10, key="empresas_nmin",
                      help="Setores com poucas respostas geram percentuais instáveis e ficam de fora.")
    r = m.resumir(df[df["cd_setor"] != dados.NAO_INFORMADO], ["ano", ds_setor], ["ia_prioridade_alta"], salario=False)
    r = r[r["qt_base_ia_prioridade_alta"] >= n_min]
    if r.empty:
        st.info("Nenhum setor atinge o mínimo de respostas neste recorte.")
    else:
        gr.mostrar(gr.barras(r, ds_setor, "pct_ia_prioridade_alta", n="qt_base_ia_prioridade_alta"),
                   r[["ano", ds_setor, "qt_base_ia_prioridade_alta", "pct_ia_prioridade_alta"]].round(1)
                   .rename(columns={ds_setor: "Setor", "qt_base_ia_prioridade_alta": "Responderam",
                                    "pct_ia_prioridade_alta": "% prioridade alta"}))

st.subheader("Salário médio por porte da empresa")
r = m.resumir(df[df["cd_porte_empresa"] != dados.NAO_INFORMADO], ["ano", ds_porte])
gr.mostrar(gr.barras(r, ds_porte, "salario_medio", fmt=m.brl, n="qt_com_salario", ordem=dados.ordem("cd_porte_empresa")),
           r[["ano", ds_porte, "qt_com_salario", "salario_medio"]].round(0)
           .rename(columns={ds_porte: "Porte da empresa", "qt_com_salario": "Com salário informado",
                            "salario_medio": "Salário médio (R$)"}))

filtros.avisos(filtros.AVISO_SALARIO,
               "Os indicadores de empresa vêm da percepção dos profissionais: uma empresa com vários "
               "respondentes pesa mais que uma com um só.")
