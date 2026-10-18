"""Modelo de trabalho, retenção e desafios para as empresas.
Fontes: gld_ft_modelo_trabalho_retencao e gld_ft_adocao_opcao (motivos de insatisfação e critérios de emprego)."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Modelo de trabalho e retenção")
st.caption("Como os profissionais trabalham, como gostariam de trabalhar e o que isso diz sobre retenção de talentos.")

selecao = filtros.barra(["cd_regiao", "cd_senioridade", "cd_modelo_trabalho_atual", "cd_modelo_trabalho_ideal"], "modelo")
df = filtros.aplicar(dados.fato("gld_ft_modelo_trabalho_retencao", anos), selecao)
ds_atual, ds_ideal = dados.coluna_ds("cd_modelo_trabalho_atual"), dados.coluna_ds("cd_modelo_trabalho_ideal")

INDICADORES = ["satisfeitos", "buscando_mudar", "afetados_layoff", "sairia_retorno_presencial", "modelo_alinhado"]
filtros.indicadores(m.resumir(df, ["ano"], INDICADORES), [
    ("Satisfeitos", "pct_satisfeitos", "pct", True, "Base: quem respondeu sobre satisfação."),
    ("Buscando mudar", "pct_buscando_mudar", "pct", False,
     "Estão em busca de outra oportunidade nos próximos 6 meses."),
    ("Afetados por layoff", "pct_afetados_layoff", "pct", False, "Foram afetados pessoalmente por demissões em massa."),
    ("Sairiam no presencial", "pct_sairia_retorno_presencial", "pct", False,
     "Procurariam outro emprego se a empresa exigisse o retorno ao presencial."),
    ("Modelo atual = ideal", "pct_modelo_alinhado", "pct", True, "Trabalham no modelo que consideram ideal."),
])

ordem_modelo = dados.ordem("cd_modelo_trabalho_atual")
ano_ref = anos[-1]
st.subheader(f"Modelo atual × modelo ideal ({ano_ref})")
st.caption("De quem trabalha em cada modelo (linhas), % que considera ideal cada modelo (colunas). "
           "A diagonal mostra quem está no modelo que prefere.")
x = df[(df["ano"] == ano_ref) & (df["cd_modelo_trabalho_atual"] != dados.NAO_INFORMADO)
       & (df["cd_modelo_trabalho_ideal"] != dados.NAO_INFORMADO)]
r = x.groupby([ds_atual, ds_ideal])["qt_respondentes"].sum().reset_index()
if r.empty:
    st.info("Sem respondentes com modelo atual e ideal informados neste recorte.")
else:
    r["pct"] = m.razao(r["qt_respondentes"], r.groupby(ds_atual)["qt_respondentes"].transform("sum"), 100)
    pivo = r.pivot_table(index=ds_atual, columns=ds_ideal, values="pct").reindex(
        index=[o for o in ordem_modelo if o in set(r[ds_atual])], columns=[o for o in ordem_modelo if o in set(r[ds_ideal])])
    gr.mostrar(gr.mapa_calor(pivo, titulo_x="Modelo ideal →"),
               r.round(1).rename(columns={ds_atual: "Modelo atual", ds_ideal: "Modelo ideal",
                                          "qt_respondentes": "Respondentes", "pct": "% da linha"}))

r = m.resumir(df[df["cd_modelo_trabalho_atual"] != dados.NAO_INFORMADO], ["ano", ds_atual], INDICADORES)
tabela = (r[["ano", ds_atual, "qt_respondentes", "salario_medio", *[f"pct_{i}" for i in INDICADORES]]].round(1)
          .rename(columns={ds_atual: "Modelo atual", "qt_respondentes": "Respondentes", "salario_medio": "Salário médio",
                           "pct_satisfeitos": "% satisfeitos", "pct_buscando_mudar": "% buscando mudar",
                           "pct_afetados_layoff": "% afetados layoff",
                           "pct_sairia_retorno_presencial": "% sairia c/ retorno presencial",
                           "pct_modelo_alinhado": "% modelo alinhado"}))
c1, c2, c3 = st.columns(3)
for col, ind, titulo in [(c1, "satisfeitos", "% satisfeitos"), (c2, "buscando_mudar", "% buscando mudar de emprego"),
                         (c3, "sairia_retorno_presencial", "% que sairia com retorno presencial")]:
    with col:
        st.subheader(titulo)
        st.caption("Por modelo de trabalho atual.")
        gr.mostrar(gr.barras(r, ds_atual, f"pct_{ind}", n=f"qt_base_{ind}", ordem=ordem_modelo), tabela,
                   chave=f"modelo_{ind}")

# ---- desafios para as empresas (respostas de múltipla escolha; só o filtro de senioridade se aplica) ----
st.subheader("Desafios para as empresas reterem talentos")
st.caption("Respostas de múltipla escolha. Aqui só o filtro de senioridade se aplica.")
op = dados.fato("gld_ft_adocao_opcao", anos)
op = filtros.aplicar(op, {"cd_senioridade": selecao["cd_senioridade"]})
c1, c2 = st.columns(2)
for col, tema, titulo in [(c1, "Motivos de insatisfação", "Motivos de insatisfação com a empresa atual"),
                          (c2, "Critérios de escolha de emprego", "O que mais pesa na escolha de um emprego")]:
    with col:
        st.markdown(f"**{titulo}**")
        a = m.adocao(op[op["ds_tema"] == tema], ["ano", "ds_opcao"])
        if a.empty:
            st.info("Pergunta sem respostas neste recorte.")
            continue
        gr.mostrar(gr.barras(a, "ds_opcao", "pct_adocao", n="qt_base"),
                   a[["ano", "ds_opcao", "qt_base", "qt_selecionado", "pct_adocao"]].round(1)
                   .rename(columns={"ds_opcao": "Opção", "qt_base": "Viram a pergunta", "qt_selecionado": "Marcaram",
                                    "pct_adocao": "%"}), chave=f"modelo_{tema}")

filtros.avisos("Percentuais calculados sobre quem respondeu cada pergunta (bases nas tabelas \"Ver dados\").")
