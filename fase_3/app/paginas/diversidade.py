"""Cenário de diversidade (gênero, cor/raça e PcD) e diferença salarial. Fonte: gld_ft_diversidade."""
import pandas as pd
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("Diversidade")
st.caption("Representatividade de gênero, cor/raça e pessoas com deficiência, e a diferença salarial entre mulheres e homens.")

selecao = filtros.barra(["cd_genero", "cd_cor_raca_etnia", "cd_atuacao_dados", "cd_senioridade"], "diversidade")
df = filtros.aplicar(dados.fato("gld_ft_diversidade", anos), selecao)

ds_gen, ds_cor, ds_atu, ds_sen = (dados.coluna_ds(c) for c in
                                  ("cd_genero", "cd_cor_raca_etnia", "cd_atuacao_dados", "cd_senioridade"))
FEM, MASC = "Feminino", "Masculino"


def gap_salarial(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Salário médio das mulheres vs. dos homens no mesmo grupo: (fem / masc - 1) * 100."""
    r = m.resumir(df[df[ds_gen].isin([FEM, MASC])], [*por, ds_gen])

    def lado(genero, sufixo):
        return (r[r[ds_gen] == genero].set_index(por)[["salario_medio", "qt_com_salario"]]
                .rename(columns={"salario_medio": f"salario_{sufixo}", "qt_com_salario": f"n_{sufixo}"}))

    out = lado(FEM, "fem").join(lado(MASC, "masc"), how="inner").reset_index()
    out = out.dropna(subset=["salario_fem", "salario_masc"])  # grupo sem salário informado em um dos lados
    out["pct_dif"] = m.razao(out["salario_fem"], out["salario_masc"], 100) - 100
    return out


# base do % de mulheres: quem informou o gênero
genero_inf = (df[(df["cd_genero"] != dados.NAO_INFORMADO) & (df[ds_gen] != "Prefiro não informar")]
              .assign(qt_mulheres=lambda d: (d[ds_gen] == FEM) * d["qt_respondentes"]))


def pct_mulheres(por: list[str]) -> pd.DataFrame:
    r = genero_inf.groupby(por, sort=False)[["qt_mulheres", "qt_respondentes"]].sum().reset_index()
    r["pct_mulheres"] = m.razao(r["qt_mulheres"], r["qt_respondentes"], 100)
    return r


# ---- indicadores --------------------------------------------------------------------------------
resumo = m.resumir(df, ["ano"], ["negros", "pcd"])
resumo["pct_mulheres"] = resumo["ano"].map(pct_mulheres(["ano"]).set_index("ano")["pct_mulheres"])
gap = gap_salarial(df, ["ano"])
resumo["pct_gap"] = resumo["ano"].map(gap.set_index("ano")["pct_dif"]) if not gap.empty else float("nan")
filtros.indicadores(resumo, [
    ("Mulheres", "pct_mulheres", "pct", True, "Base: quem informou gênero."),
    ("Pessoas negras", "pct_negros", "pct", True, "Pretas e pardas. Base: quem informou cor/raça."),
    ("Pessoas com deficiência", "pct_pcd", "pct", True, "Base: quem respondeu sobre deficiência."),
    ("Dif. salarial mulheres", "pct_gap", "pct", True,
     "Diferença do salário médio das mulheres em relação ao dos homens no recorte. Negativo = mulheres ganham menos."),
])

# ---- gênero -------------------------------------------------------------------------------------
st.subheader("Composição de gênero por senioridade")
GRUPOS = [FEM, MASC, "Outro / não informado"]
g = df.assign(grupo=df[ds_gen].where(df[ds_gen].isin([FEM, MASC]), GRUPOS[2]))
r = m.resumir(g, ["ano", ds_sen, "grupo"], salario=False)
r["pct"] = m.razao(r["qt_respondentes"], r.groupby(["ano", ds_sen])["qt_respondentes"].transform("sum"), 100)
t = gr.tema()
gr.mostrar(gr.empilhado_100(r, ds_sen, "grupo", "pct", dados.ordem("cd_senioridade"), GRUPOS,
                            [t["cat"][0], t["cat"][1], t["neutro"]]),
           r.pivot_table(index=["ano", ds_sen], columns="grupo", values="pct", sort=False).round(1).reset_index()
           .rename(columns={ds_sen: "Senioridade"}))

st.subheader("Diferença salarial: mulheres vs. homens")
st.caption("Quanto o salário médio das mulheres fica acima (azul) ou abaixo (vermelho) do dos homens no mesmo grupo. "
           "Grupos com menos de 10 mulheres com salário informado ficam de fora.")
c1, c2 = st.columns(2)
for col, ds, cd, titulo in [(c1, ds_sen, "cd_senioridade", "Por senioridade"),
                            (c2, ds_atu, "cd_atuacao_dados", "Por área de atuação")]:
    with col:
        st.markdown(f"**{titulo}**")
        r = gap_salarial(df[df[cd] != dados.NAO_INFORMADO], ["ano", ds])
        r = r[r["n_fem"] >= 10] if not r.empty else r
        if r.empty:
            st.info("É preciso ter mulheres e homens com salário informado no recorte.")
            continue
        ordem = dados.ordem(cd) if cd == "cd_senioridade" else r.sort_values("pct_dif")[ds].unique().tolist()
        gr.mostrar(gr.barras_divergentes(r, ds, "pct_dif", ordem, n="n_fem"),
                   r[["ano", ds, "n_fem", "salario_fem", "n_masc", "salario_masc", "pct_dif"]].round(1)
                   .rename(columns={ds: titulo.removeprefix("Por ").capitalize(), "n_fem": "Mulheres (n)",
                                    "salario_fem": "Salário mulheres", "n_masc": "Homens (n)",
                                    "salario_masc": "Salário homens", "pct_dif": "Diferença (%)"}),
                   chave=f"gap_{cd}")

st.subheader("Participação de mulheres por área de atuação")
r = pct_mulheres(["ano", ds_atu])
gr.mostrar(gr.barras(r, ds_atu, "pct_mulheres"),
           r[["ano", ds_atu, "qt_respondentes", "pct_mulheres"]].round(1)
           .rename(columns={ds_atu: "Área de atuação", "qt_respondentes": "Informaram gênero", "pct_mulheres": "% mulheres"}))

# ---- cor/raça -----------------------------------------------------------------------------------
c1, c2 = st.columns(2)
r = m.participacao(df, ds_cor)
with c1:
    st.subheader("Cor/raça/etnia")
    st.caption("% dos respondentes do recorte.")
    gr.mostrar(gr.barras(r, ds_cor, "pct_participacao"),
               r[["ano", ds_cor, "qt_respondentes", "pct_participacao"]].round(1)
               .rename(columns={ds_cor: "Cor/raça/etnia", "qt_respondentes": "Respondentes", "pct_participacao": "% do total"}))
with c2:
    st.subheader("Salário médio por cor/raça/etnia")
    st.caption("Grupos com menos de 10 respostas de salário ficam de fora.")
    r = r[r["qt_com_salario"] >= 10]
    gr.mostrar(gr.barras(r, ds_cor, "salario_medio", fmt=m.brl, n="qt_com_salario"),
               r[["ano", ds_cor, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_cor: "Cor/raça/etnia", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))

filtros.avisos(filtros.AVISO_SALARIO,
               "A diferença salarial compara grupos com o mesmo filtro, mas dentro de cada barra ainda há "
               "mistura de cargos e setores: ela indica uma desigualdade, não mede discriminação isoladamente.")
