"""Filtros e componentes de página compartilhados."""
import pandas as pd
import streamlit as st

from core import dados
from core import metricas as m

ANOS = [2024, 2025]


def seletor_anos() -> None:
    """Filtro global (barra lateral): edições da pesquisa exibidas em todas as páginas."""
    st.pills("Edição da pesquisa", ANOS, selection_mode="multi", default=[2025], key="anos",
             format_func=lambda a: f"State of Data {a}",
             help="Selecione as duas edições para comparar os anos.")


def anos() -> list[int]:
    selecionados = sorted(st.session_state.get("anos") or [])
    if not selecionados:
        st.info("Selecione ao menos uma edição da pesquisa na barra lateral.")
        st.stop()
    return selecionados


def barra(campos: list[str], pagina: str) -> dict[str, list[str]]:
    """Linha de filtros no topo da página (vazio = todos). Retorna {cd_x: [descrições escolhidas]}."""
    selecao = {}
    for col, cd in zip(st.columns(len(campos)), campos):
        selecao[cd] = col.multiselect(dados.rotulo(cd), dados.ordem(cd), placeholder="Todos",
                                      key=f"{pagina}_{cd}")
    return selecao


def aplicar(df: pd.DataFrame, selecao: dict[str, list[str]]) -> pd.DataFrame:
    """Aplica as seleções cujas dimensões existem no fato (as demais são ignoradas)."""
    for cd, valores in selecao.items():
        ds = dados.coluna_ds(cd)
        if valores and ds in df.columns:
            df = df[df[ds].isin(valores)]
    return df


def indicadores(resumo: pd.DataFrame, specs: list[tuple]) -> None:
    """Linha de cartões. `resumo` tem uma linha por ano; specs = (rótulo, coluna, formato, alta_é_boa, ajuda).

    Mostra o ano mais recente selecionado e, com dois anos, a variação contra o anterior.
    """
    r = resumo.sort_values("ano")
    if r.empty:
        st.warning("Nenhum respondente no recorte selecionado.")
        st.stop()
    atual = r.iloc[-1]
    anterior = r.iloc[-2] if len(r) > 1 else None
    st.caption(f"Indicadores da edição {int(atual['ano'])}"
               + (f", com a variação em relação a {int(anterior['ano'])}" if anterior is not None else ""))
    for col, (rot, coluna, formato, alta_boa, ajuda) in zip(st.columns(len(specs)), specs):
        valor, delta = atual[coluna], None
        if anterior is not None and pd.notna(valor) and pd.notna(anterior[coluna]):
            d = valor - anterior[coluna]
            texto = {"pct": m.br(d, 1) + " p.p.", "brl": "R$ " + m.br(d, 0), "int": m.br(d, 0)}[formato]
            delta = ("+" if d > 0 else "") + texto + f" vs {int(anterior['ano'])}"
        cor = "off" if alta_boa is None else ("normal" if alta_boa else "inverse")
        col.metric(rot, m.FORMATOS[formato](valor), delta, delta_color=cor, border=True, help=ajuda)


AVISO_ANOS = ("**Comparação entre anos:** a amostra de 2024 só tem pessoas de 18 a 27 anos, enquanto a de 2025 "
              "vai até 71. Diferenças entre os anos refletem também essa mudança de público.")
AVISO_SALARIO = ("O salário da pesquisa é informado em **faixas**: os valores são médias dos pontos médios das "
                 "faixas, ou seja, estimativas.")


def avisos(*textos: str) -> None:
    """Cuidados de leitura (da especificação do dashboard), mostrados no rodapé da página."""
    if len(st.session_state.get("anos") or []) > 1:
        textos = (AVISO_ANOS, *textos)
    if textos:
        with st.container(border=True):
            st.markdown("**Como ler estes números**")
            for t in textos:
                st.caption(t)
