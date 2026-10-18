"""Como está estruturado o mercado de dados (profissionais)?  Fonte: gld_ft_estrutura_mercado."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Estrutura do mercado de dados")
st.caption("Quem são os profissionais de dados no Brasil: onde atuam, em que nível de carreira e em que região.")

selecao = filtros.barra(["cd_regiao", "cd_atuacao_dados", "cd_senioridade"], "mercado")
df = filtros.aplicar(dados.fato("gld_ft_estrutura_mercado", anos), selecao)

PERFIL = ["gestor", "pos_graduado", "ate_2_anos_exp"]
filtros.indicadores(m.resumir(df, ["ano"], PERFIL), [
    ("Respondentes", "qt_respondentes", "int", None, "Profissionais no recorte filtrado."),
    ("Salário médio", "salario_medio", "brl", True, filtros.AVISO_SALARIO),
    ("Gestores", "pct_gestor", "pct", None, "Base: quem respondeu se atua como gestor."),
    ("Pós-graduados", "pct_pos_graduado", "pct", None, "Pós-graduação, mestrado ou doutorado."),
    ("Até 2 anos na área", "pct_ate_2_anos_exp", "pct", None, "Tempo de experiência em dados de até 2 anos."),
])

ds_atu, ds_sen, ds_reg = (dados.coluna_ds(c) for c in ("cd_atuacao_dados", "cd_senioridade", "cd_regiao"))


def tabela_participacao(r, ds, nome):
    return (r[["ano", ds, "qt_respondentes", "pct_participacao"]]
            .rename(columns={ds: nome, "qt_respondentes": "Respondentes", "pct_participacao": "% do total"})
            .round(1))


c1, c2 = st.columns(2)
with c1:
    st.subheader("Área de atuação")
    st.caption("% dos respondentes do recorte em cada área.")
    r = m.participacao(df, ds_atu)
    gr.mostrar(gr.barras(r, ds_atu, "pct_participacao"), tabela_participacao(r, ds_atu, "Área de atuação"))
with c2:
    st.subheader("Senioridade")
    st.caption("Gestores e quem não está trabalhando não informam senioridade (\"Não informado\").")
    r = m.participacao(df, ds_sen)
    gr.mostrar(gr.barras(r, ds_sen, "pct_participacao", ordem=dados.ordem("cd_senioridade")),
               tabela_participacao(r, ds_sen, "Senioridade"))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Região de residência")
    r = m.participacao(df, ds_reg)
    gr.mostrar(gr.barras(r, ds_reg, "pct_participacao"), tabela_participacao(r, ds_reg, "Região"))
with c2:
    st.subheader("Salário médio por área de atuação")
    r = m.resumir(df, ["ano", ds_atu])
    gr.mostrar(gr.barras(r, ds_atu, "salario_medio", fmt=m.brl, n="qt_com_salario"),
               r[["ano", ds_atu, "qt_com_salario", "salario_medio"]]
               .rename(columns={ds_atu: "Área de atuação", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}).round(0))

st.subheader("Perfil de cada área de atuação")
st.caption("Formação, experiência e salário em cada área. Percentuais calculados sobre quem respondeu cada pergunta.")
r = m.resumir(df, ["ano", ds_atu], PERFIL)
st.dataframe(
    r[["ano", ds_atu, "qt_respondentes", "salario_medio", "pct_pos_graduado", "pct_ate_2_anos_exp"]]
    .round({"salario_medio": 0}).sort_values(["ano", "qt_respondentes"], ascending=[False, False]),
    hide_index=True, width="stretch",
    column_config={
        "ano": st.column_config.NumberColumn("Ano", format="%d"),
        ds_atu: "Área de atuação",
        "qt_respondentes": st.column_config.NumberColumn("Respondentes", format="localized"),
        "salario_medio": st.column_config.NumberColumn("Salário médio (R$)", format="localized"),
        "pct_pos_graduado": st.column_config.ProgressColumn("% pós-graduados", format="%.1f%%", min_value=0, max_value=100),
        "pct_ate_2_anos_exp": st.column_config.ProgressColumn("% até 2 anos na área", format="%.1f%%", min_value=0, max_value=100),
    },
)

filtros.avisos(filtros.AVISO_SALARIO)
