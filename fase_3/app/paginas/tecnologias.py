"""Quais tecnologias têm maior adoção? Fonte: gld_ft_adocao_opcao (+ gld_dim_opcao para o tema)."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Tecnologias")
st.caption("Adoção de linguagens, bancos de dados, cloud, ferramentas de BI e ETL e técnicas de ciência de dados.")

base = dados.fato("gld_ft_adocao_opcao", anos)
base = base[base["cd_opcao"] != dados.NAO_INFORMADO]
TEMAS_IA = ("IA generativa", "Diversidade", "Motivos", "Critérios", "Gestão")  # têm páginas próprias
temas = sorted(t for t in base["ds_tema"].unique() if not t.startswith(TEMAS_IA))

c1, c2, c3, c4 = st.columns(4)
tema = c1.selectbox("Tema", temas, index=temas.index("Linguagens de programação"), key="tec_tema")
opcoes = sorted(base.loc[base["ds_tema"] == tema, "ds_opcao"].unique())
escolhidas = c2.multiselect("Opção / tecnologia", opcoes, placeholder="Todas", key=f"tec_opcoes_{tema}")
selecao = {cd: col.multiselect(dados.rotulo(cd), dados.ordem(cd), placeholder="Todos", key=f"tec_{cd}")
           for col, cd in [(c3, "cd_atuacao_dados"), (c4, "cd_senioridade")]}

df = filtros.aplicar(base[base["ds_tema"] == tema], selecao)
if escolhidas:
    df = df[df["ds_opcao"].isin(escolhidas)]
if df.empty:
    st.info("Nenhuma resposta no recorte selecionado.")
    st.stop()

perguntas = df["ds_pergunta"].dropna().unique()
st.caption("Pergunta(s) da pesquisa: " + " · ".join(f"_{p}_" for p in perguntas))

r = m.adocao(df, ["ano", "ds_opcao"])
top_n = st.slider("Quantas opções mostrar", 5, 30, 15, key="tec_top")
ano_ref = int(r["ano"].max())  # edição mais recente em que o tema foi perguntado
ultimo = r[r["ano"] == ano_ref].nlargest(top_n, "pct_adocao")["ds_opcao"]
r_top = r[r["ds_opcao"].isin(ultimo)]

st.subheader(f"{tema}: % de adoção")
st.caption("% de quem viu a pergunta que marcou a opção (múltipla escolha: a soma passa de 100%). "
           f"Ordenado pela edição {ano_ref}.")
gr.mostrar(gr.barras(r_top, "ds_opcao", "pct_adocao", n="qt_base"),
           r_top[["ano", "ds_opcao", "qt_base", "qt_selecionado", "pct_adocao"]].round(1)
           .rename(columns={"ds_opcao": "Opção", "qt_base": "Viram a pergunta", "qt_selecionado": "Marcaram",
                            "pct_adocao": "% adoção"}))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Salário médio de quem usa")
    st.caption("Opções com pelo menos 30 usuários com salário informado.")
    s = r_top[r_top["qt_selecionado_com_salario"] >= 30]
    if s.empty:
        st.info("Nenhuma opção atinge 30 usuários com salário informado.")
    else:
        gr.mostrar(gr.barras(s, "ds_opcao", "salario_medio_usuarios", fmt=m.brl, n="qt_selecionado_com_salario"),
                   s[["ano", "ds_opcao", "qt_selecionado_com_salario", "salario_medio_usuarios"]].round(0)
                   .rename(columns={"ds_opcao": "Opção", "qt_selecionado_com_salario": "Usuários com salário",
                                    "salario_medio_usuarios": "Salário médio (R$)"}))
with c2:
    ds_atu = dados.coluna_ds("cd_atuacao_dados")
    st.subheader(f"Adoção por área de atuação ({ano_ref})")
    st.caption("% de adoção das 10 opções mais adotadas, em cada área.")
    a = m.adocao(df[(df["ano"] == ano_ref) & (df["ds_opcao"].isin(ultimo.head(10)))
                    & (df["cd_atuacao_dados"] != dados.NAO_INFORMADO)], [ds_atu, "ds_opcao"])
    a = a[a["qt_base"] >= 10]
    if a.empty:
        st.info("Poucas respostas por área neste recorte.")
    else:
        pivo = a.pivot_table(index="ds_opcao", columns=ds_atu, values="pct_adocao").reindex(
            index=[o for o in ultimo.head(10) if o in set(a["ds_opcao"])])
        gr.mostrar(gr.mapa_calor(pivo), a[[ds_atu, "ds_opcao", "qt_base", "pct_adocao"]].round(1)
                   .rename(columns={ds_atu: "Área de atuação", "ds_opcao": "Opção", "qt_base": "Viram a pergunta",
                                    "pct_adocao": "% adoção"}))

avisos = [filtros.AVISO_SALARIO]
if tema == "Linguagens de programação":
    avisos.insert(0, "Em 2025 a pergunta de linguagens teve opções removidas: **SQL, Python e R** comparam bem entre "
                     "os anos, mas **Java e JavaScript** não.")
filtros.avisos(*avisos)
