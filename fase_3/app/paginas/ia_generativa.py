"""Adoção de IA generativa e seu impacto. Fontes: gld_ft_ia_generativa e gld_ft_adocao_opcao (temas de IA)."""
import streamlit as st

from core import dados, filtros
from core import graficos as gr
from core import metricas as m

anos = filtros.anos()
st.title("IA generativa")
st.caption("Quanto os profissionais usam IA generativa no trabalho e como isso se relaciona com salário e satisfação.")

selecao = filtros.barra(["cd_uso_ia", "cd_atuacao_dados", "cd_senioridade"], "ia")
df = filtros.aplicar(dados.fato("gld_ft_ia_generativa", anos), selecao)
ds_uso, ds_sen = dados.coluna_ds("cd_uso_ia"), dados.coluna_ds("cd_senioridade")
NAO_USA, EMPRESA_PAGA = 1, 5

informado = df[df["cd_uso_ia"] != dados.NAO_INFORMADO]
resumo = m.resumir(df, ["ano"], ["ia_prioridade_alta"])
uso = (informado.assign(qt_usa=lambda d: (d["cd_uso_ia"] > NAO_USA) * d["qt_respondentes"],
                        qt_empresa=lambda d: (d["cd_uso_ia"] == EMPRESA_PAGA) * d["qt_respondentes"])
       .groupby("ano")[["qt_usa", "qt_empresa", "qt_respondentes"]].sum())
resumo["pct_usa"] = resumo["ano"].map(m.razao(uso["qt_usa"], uso["qt_respondentes"], 100))
resumo["pct_empresa"] = resumo["ano"].map(m.razao(uso["qt_empresa"], uso["qt_respondentes"], 100))
sal = m.resumir(informado.assign(usa=informado["cd_uso_ia"] > NAO_USA), ["ano", "usa"])
for flag, col in [(True, "sal_usa"), (False, "sal_nao_usa")]:
    resumo[col] = resumo["ano"].map(sal[sal["usa"] == flag].set_index("ano")["salario_medio"])
filtros.indicadores(resumo, [
    ("Usam IA generativa", "pct_usa", "pct", None, "Qualquer uso (gratuito, Copilot, pago). Base: quem respondeu."),
    ("Empresa paga a IA", "pct_empresa", "pct", None, "Base: quem respondeu sobre uso de IA."),
    ("IA é prioridade", "pct_ia_prioridade_alta", "pct", None, "Base: quem respondeu sobre a prioridade."),
    ("Salário: usa IA", "sal_usa", "brl", None, filtros.AVISO_SALARIO),
    ("Salário: não usa IA", "sal_nao_usa", "brl", None, filtros.AVISO_SALARIO),
])

ordem_uso = dados.ordem("cd_uso_ia")
st.subheader("Nível de uso de IA generativa no trabalho")
st.caption("% de quem respondeu, do menor ao maior investimento em IA.")
r = m.participacao(informado, ds_uso)
gr.mostrar(gr.barras(r, ds_uso, "pct_participacao", ordem=ordem_uso),
           r[["ano", ds_uso, "qt_respondentes", "pct_participacao"]].round(1)
           .rename(columns={ds_uso: "Uso de IA", "qt_respondentes": "Respondentes", "pct_participacao": "% do total"}))

r = m.resumir(informado, ["ano", ds_uso], ["satisfeitos", "buscando_mudar"])
c1, c2 = st.columns(2)
with c1:
    st.subheader("Salário médio por nível de uso")
    gr.mostrar(gr.barras(r, ds_uso, "salario_medio", fmt=m.brl, n="qt_com_salario", ordem=ordem_uso),
               r[["ano", ds_uso, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_uso: "Uso de IA", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))
with c2:
    st.subheader("Satisfação por nível de uso")
    st.caption("% satisfeitos com a empresa atual.")
    gr.mostrar(gr.barras(r, ds_uso, "pct_satisfeitos", n="qt_base_satisfeitos", ordem=ordem_uso),
               r[["ano", ds_uso, "qt_base_satisfeitos", "pct_satisfeitos", "pct_buscando_mudar"]].round(1)
               .rename(columns={ds_uso: "Uso de IA", "qt_base_satisfeitos": "Responderam",
                                "pct_satisfeitos": "% satisfeitos", "pct_buscando_mudar": "% buscando mudar"}))

ano_ref = anos[-1]
st.subheader(f"Salário por nível de uso, dentro de cada senioridade ({ano_ref})")
st.caption("Quem usa IA paga pela empresa tende a ser mais sênior. Comparar dentro da mesma senioridade "
           "separa parte desse efeito. Células com menos de 10 respostas ficam em branco.")
r = m.resumir(informado[(informado["ano"] == ano_ref) & (informado["cd_senioridade"] != dados.NAO_INFORMADO)],
              [ds_sen, ds_uso])
r.loc[r["qt_com_salario"] < 10, "salario_medio"] = float("nan")
if r.empty:
    st.info("Sem respondentes com senioridade informada neste recorte.")
else:
    pivo = r.pivot_table(index=ds_sen, columns=ds_uso, values="salario_medio").reindex(
        index=[s for s in dados.ordem("cd_senioridade") if s in set(r[ds_sen])],
        columns=[u for u in ordem_uso if u in set(r[ds_uso])])
    gr.mostrar(gr.mapa_calor(pivo, fmt=m.brl),
               r[[ds_sen, ds_uso, "qt_com_salario", "salario_medio"]].round(0)
               .rename(columns={ds_sen: "Senioridade", ds_uso: "Uso de IA", "qt_com_salario": "Com salário informado",
                                "salario_medio": "Salário médio (R$)"}))

# ---- respostas de múltipla escolha sobre IA (mesmos filtros de atuação e senioridade) ----------
op = filtros.aplicar(dados.fato("gld_ft_adocao_opcao", anos), selecao)
c1, c2 = st.columns(2)
for col, tema, titulo in [(c1, "IA generativa: uso na empresa", "Como as empresas usam IA generativa"),
                          (c2, "IA generativa: barreiras", "Por que as empresas não usam IA generativa")]:
    with col:
        st.subheader(titulo)
        a = m.adocao(op[op["ds_tema"] == tema], ["ano", "ds_opcao"])
        if a.empty:
            st.info("Pergunta sem respostas neste recorte.")
            continue
        st.caption(f"% de quem viu a pergunta. Base: {m.inteiro(a.groupby('ano')['qt_base'].max().iloc[-1])} respondentes.")
        gr.mostrar(gr.barras(a, "ds_opcao", "pct_adocao", n="qt_base"),
                   a[["ano", "ds_opcao", "qt_base", "qt_selecionado", "pct_adocao"]].round(1)
                   .rename(columns={"ds_opcao": "Opção", "qt_base": "Viram a pergunta", "qt_selecionado": "Marcaram",
                                    "pct_adocao": "%"}), chave=f"ia_{tema}")

filtros.avisos("O impacto da IA é uma **correlação**, não causa: quem usa IA paga pela empresa tende a ser mais "
               "sênior. Filtre por senioridade antes de tirar conclusões.", filtros.AVISO_SALARIO)
