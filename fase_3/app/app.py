"""Dashboard State of Data Brasil (Tech Challenge - fase 3).

Consome a camada gold (star schema) do data lake na AWS pelo catálogo Glue `db_gold`.
Executar localmente:  streamlit run app.py   (a partir da pasta app/)
"""
import streamlit as st

from core import dados, filtros

st.set_page_config(page_title="State of Data Brasil", page_icon=":material/insights:", layout="wide")

pg = st.navigation({
    "Mercado de dados": [
        st.Page("paginas/estrutura_mercado.py", title="Estrutura do mercado", icon=":material/groups:", default=True),
        st.Page("paginas/estrutura_empresas.py", title="Empresas e maturidade", icon=":material/apartment:"),
        st.Page("paginas/remuneracao.py", title="Remuneração", icon=":material/payments:"),
    ],
    "Pessoas": [
        st.Page("paginas/diversidade.py", title="Diversidade", icon=":material/diversity_3:"),
        st.Page("paginas/modelo_trabalho.py", title="Modelo de trabalho e retenção", icon=":material/home_work:"),
    ],
    "Tecnologia": [
        st.Page("paginas/tecnologias.py", title="Tecnologias", icon=":material/memory:"),
        st.Page("paginas/ia_generativa.py", title="IA generativa", icon=":material/smart_toy:"),
    ],
    "Projeto": [
        st.Page("paginas/sobre.py", title="Sobre os dados", icon=":material/info:"),
    ],
})

with st.sidebar:
    st.markdown("### State of Data Brasil")
    filtros.seletor_anos()

try:
    dados.carregar_gold()
except Exception as e:  # noqa: BLE001 - sem dados não há o que mostrar; explica o motivo
    st.error("Não foi possível ler a camada gold no AWS Glue. Confira as credenciais em `[aws]` nos secrets.")
    st.exception(e)
    st.stop()

with st.sidebar:
    nome_motor, motivo = dados.motor()
    fonte = "Amazon Athena" if nome_motor == "athena" else "Catálogo Glue → S3"
    st.caption(f"Fonte: `{st.secrets['aws']['database']}` via {fonte}",
               help=f"Athena indisponível, leitura direta pelo catálogo Glue. Motivo: {motivo}" if motivo else None)
    st.caption("Dados: pesquisa State of Data Brasil (Data Hackers), edições 2024 e 2025.")

pg.run()
