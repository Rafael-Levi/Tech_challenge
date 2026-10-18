"""Quais perfis são mais valorizados e quais as diferenças por região e senioridade?
Fonte: gld_ft_remuneracao."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Remuneração")
st.caption("Quais perfis são mais valorizados e como o salário muda com a região e a senioridade.")

selecao = filtros.barra(["cd_regiao", "cd_cargo", "cd_senioridade"], "remuneracao")
df = filtros.aplicar(dados.fato("gld_ft_remuneracao", anos), selecao)

FAIXAS = {"sal_ate_4mil": "Até R$ 4 mil", "sal_4_a_8mil": "R$ 4 a 8 mil",
          "sal_8_a_16mil": "R$ 8 a 16 mil", "sal_acima_16mil": "Acima de R$ 16 mil"}


def resumo_faixas(df, por):
    """Salário médio e % de quem informou salário em cada faixa (base = qt_com_salario)."""
    qt = df.groupby(por, sort=False)[[f"qt_{k}" for k in FAIXAS]].sum().reset_index()
    r = m.resumir(df, por).merge(qt, on=por)
    for k in FAIXAS:
        r[f"pct_{k}"] = m.razao(r[f"qt_{k}"], r["qt_com_salario"], 100)
    return r


filtros.indicadores(resumo_faixas(df, ["ano"]), [
    ("Com salário informado", "qt_com_salario", "int", None, "Respondentes que informaram a faixa salarial."),
    ("Salário médio", "salario_medio", "brl", True, filtros.AVISO_SALARIO),
    ("Ganham até R$ 4 mil", "pct_sal_ate_4mil", "pct", False, "Base: quem informou salário."),
    ("Ganham acima de R$ 16 mil", "pct_sal_acima_16mil", "pct", True, "Base: quem informou salário."),
])

ds_cargo, ds_sen, ds_reg = (dados.coluna_ds(c) for c in ("cd_cargo", "cd_senioridade", "cd_regiao"))
sem_ni = lambda d, cd: d[d[cd] != dados.NAO_INFORMADO]  # noqa: E731

st.subheader("Cargos mais bem pagos")
n_min = st.slider("Mínimo de respondentes com salário por cargo", 10, 100, 30, step=10, key="rem_nmin",
                  help="Cargos com poucas respostas geram médias instáveis e ficam de fora do ranking.")
r = m.resumir(sem_ni(df, "cd_cargo"), ["ano", ds_cargo, "ds_tipo_cargo"])
r = r[r["qt_com_salario"] >= n_min]
if r.empty:
    st.info("Nenhum cargo atinge o mínimo de respostas neste recorte.")
else:
    gr.mostrar(gr.barras(r, ds_cargo, "salario_medio", fmt=m.brl, n="qt_com_salario"),
               r[["ano", ds_cargo, "ds_tipo_cargo", "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_cargo: "Cargo", "ds_tipo_cargo": "Tipo", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Salário médio por senioridade")
    r = m.resumir(df, ["ano", ds_sen])
    gr.mostrar(gr.barras(r, ds_sen, "salario_medio", fmt=m.brl, n="qt_com_salario", ordem=dados.ordem("cd_senioridade")),
               r[["ano", ds_sen, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_sen: "Senioridade", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))
with c2:
    st.subheader("Salário médio por região")
    r = m.resumir(df, ["ano", ds_reg])
    gr.mostrar(gr.barras(r, ds_reg, "salario_medio", fmt=m.brl, n="qt_com_salario"),
               r[["ano", ds_reg, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_reg: "Região", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))

ano_ref = anos[-1]
st.subheader(f"Região × senioridade ({ano_ref})")
st.caption("Salário médio em cada combinação. Células com menos de 10 respostas ficam em branco.")
r = m.resumir(df[(df["ano"] == ano_ref) & (df["cd_senioridade"] != dados.NAO_INFORMADO)
                 & (df["cd_regiao"] != dados.NAO_INFORMADO)], [ds_reg, ds_sen])
r.loc[r["qt_com_salario"] < 10, "salario_medio"] = float("nan")
if r.empty:
    st.info("Sem respondentes com região e senioridade informadas neste recorte.")
else:
    ordem_reg = [x for x in dados.ordem("cd_regiao") if x in set(r[ds_reg])]
    ordem_sen = [x for x in dados.ordem("cd_senioridade") if x in set(r[ds_sen])]
    pivo = r.pivot_table(index=ds_reg, columns=ds_sen, values="salario_medio").reindex(index=ordem_reg, columns=ordem_sen)
    gr.mostrar(gr.mapa_calor(pivo, fmt=m.brl),
               r[[ds_reg, ds_sen, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_reg: "Região", ds_sen: "Senioridade", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))

st.subheader("Distribuição por faixa salarial e senioridade")
st.caption("% de quem informou salário em cada faixa.")
r = resumo_faixas(df, ["ano", ds_sen])
longo = r.melt(id_vars=["ano", ds_sen], value_vars=[f"pct_{k}" for k in FAIXAS], var_name="faixa", value_name="pct")
longo["faixa"] = longo["faixa"].str.removeprefix("pct_").map(FAIXAS)
gr.mostrar(gr.empilhado_100(longo, ds_sen, "faixa", "pct", dados.ordem("cd_senioridade"), list(FAIXAS.values()),
                            gr.rampa(len(FAIXAS))),
           longo.pivot_table(index=["ano", ds_sen], columns="faixa", values="pct", sort=False)
           .round(1).reset_index().rename(columns={ds_sen: "Senioridade"}))

filtros.avisos(filtros.AVISO_SALARIO,
               "Os cargos de gestão aparecem com o prefixo \"Gestão:\"; gestores não informam senioridade.")
