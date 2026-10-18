"""Gráficos Plotly com a mesma linguagem visual em todas as páginas.

- Cor segue a entidade: o ano da pesquisa tem sempre a mesma cor (2025 azul, 2024 laranja).
- Grandeza = um só matiz (azul), do claro ao escuro; polaridade = vermelho <-> cinza <-> azul.
- Barras finas com ponta arredondada, grade em linha fina, rótulos de texto em tons neutros.
- Todo gráfico tem a tabela de dados ao lado (expander "Ver dados").
- Claro/escuro: cada modo tem seus próprios tons, escolhidos pelo tema ativo do Streamlit.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core import metricas as m

FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

TEMAS = {
    "light": {
        "fundo": "#ffffff", "texto": "#0b0b0b", "texto2": "#52514e", "apagado": "#898781",
        "grade": "#e1e0d9", "eixo": "#c3c2b7", "neutro": "#b5b3aa",
        "cat": ["#2a78d6", "#eb6834", "#1baf7a"],
        # rampa azul 250 -> 700 (ordinal: o passo mais claro ainda contrasta com o fundo)
        "rampa": ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95",
                  "#104281", "#0d366b"],
        "seq": ["#cde2fb", "#9ec5f4", "#5598e7", "#256abf", "#0d366b"],
        "div": ["#e34948", "#f0efec", "#2a78d6"],
    },
    "dark": {
        "fundo": "#0e1117", "texto": "#f0efec", "texto2": "#c3c2b7", "apagado": "#898781",
        "grade": "#2c2c2a", "eixo": "#383835", "neutro": "#5f5e5a",
        "cat": ["#3987e5", "#d95926", "#199e70"],
        "rampa": ["#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5", "#5598e7", "#6da7ec", "#86b6ef",
                  "#9ec5f4", "#b7d3f6"],
        "seq": ["#104281", "#1c5cab", "#3987e5", "#86b6ef", "#cde2fb"],
        "div": ["#e66767", "#383835", "#3987e5"],
    },
}


def tema() -> dict:
    try:
        modo = st.context.theme.type or "light"
    except Exception:  # noqa: BLE001 - versões antigas do Streamlit não expõem o tema
        modo = "light"
    return TEMAS.get(modo, TEMAS["light"])


def cor_ano(ano: int) -> str:
    cat = tema()["cat"]
    return cat[0] if int(ano) == 2025 else cat[1]


def rampa(n: int) -> list[str]:
    """n tons ordenados (menor -> maior) da rampa azul, igualmente espaçados."""
    r = tema()["rampa"]
    if n == 1:
        return [r[len(r) // 2]]
    return [r[round(i * (len(r) - 1) / (n - 1))] for i in range(n)]


def quebrar(texto: str, largura: int = 34) -> str:
    """Quebra um rótulo longo em linhas (<br>) para não ser cortado no eixo."""
    linhas, atual = [], ""
    for palavra in str(texto).split():
        if atual and len(atual) + 1 + len(palavra) > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    return "<br>".join([*linhas, atual])


def _rotulos_categoria(eixo, ordem: list[str], largura: int = 34) -> int:
    """Mostra as categorias com quebra de linha; retorna o maior número de linhas usado."""
    textos = [quebrar(c, largura) for c in ordem]
    eixo.update(tickmode="array", tickvals=ordem, ticktext=textos)
    return max((t.count("<br>") + 1 for t in textos), default=1)


def _texto_sobre(hex_cor: str) -> str:
    """Branco ou preto sobre um preenchimento, pela luminância."""
    r, g, b = (int(hex_cor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return "#0b0b0b" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.55 else "#ffffff"


def _layout(fig: go.Figure, altura: int, legenda: bool) -> go.Figure:
    t = tema()
    fig.update_layout(
        height=altura, margin=dict(l=4, r=56, t=36 if legenda else 8, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONTE, size=13, color=t["texto2"]), separators=",.",
        barcornerradius=4, bargap=0.28, bargroupgap=0.06,
        hoverlabel=dict(bgcolor=t["fundo"], bordercolor=t["eixo"], font=dict(family=FONTE, color=t["texto"])),
        showlegend=legenda,
        legend=dict(orientation="h", x=0, xanchor="left", y=1.02, yanchor="bottom", title_text="",
                    font=dict(color=t["texto2"]), traceorder="normal"),
    )
    eixos = dict(gridcolor=t["grade"], gridwidth=1, zerolinecolor=t["eixo"], zerolinewidth=1, linecolor=t["eixo"],
                 tickfont=dict(color=t["apagado"]), title_font=dict(color=t["texto2"], size=12), automargin=True)
    fig.update_xaxes(**eixos)
    fig.update_yaxes(**eixos)
    for a in fig.layout.annotations:
        if a.xref == "paper":  # títulos de subplots (os valores do mapa de calor têm cor própria)
            a.font = dict(family=FONTE, size=13, color=t["texto2"])
    return fig


def _eixo_valor(fmt) -> dict:
    if fmt is m.pct:
        return dict(ticksuffix="%")
    if fmt is m.brl:
        return dict(tickprefix="R$ ", tickformat=",.0f")
    return dict(tickformat=",.0f")


def barras(df: pd.DataFrame, cat: str, valor: str, fmt=m.pct, ordem: list[str] | None = None,
           n: str | None = "qt_respondentes", titulo_valor: str = "", altura: int | None = None) -> go.Figure:
    """Barras horizontais de `valor` por `cat`; com dois anos, uma barra por ano (cor = ano)."""
    anos = sorted(df["ano"].unique())
    varios = len(anos) > 1
    if ordem is None:  # do maior para o menor, pelo ano mais recente
        ordem = df[df["ano"] == anos[-1]].sort_values(valor, ascending=False)[cat].tolist()
        ordem += [c for c in df[cat].unique() if c not in ordem]
    else:
        ordem = [c for c in ordem if c in set(df[cat])]
    t = tema()
    fig = go.Figure()
    for ano in anos:
        d = df[df["ano"] == ano]
        extra = d[n].map(m.inteiro) if n else pd.Series("", index=d.index)
        fig.add_bar(
            y=d[cat], x=d[valor], orientation="h", name=str(ano), marker_color=cor_ano(ano),
            text=None if varios else d[valor].map(fmt), textposition="outside", cliponaxis=False,
            textfont=dict(color=t["texto2"]),
            customdata=list(zip(d[valor].map(fmt), extra)),
            hovertemplate="<b>%{y}</b><br>" + f"{ano}: " + "%{customdata[0]}"
                          + ("<br>n = %{customdata[1]}" if n else "") + "<extra></extra>",
        )
    fig.update_yaxes(categoryorder="array", categoryarray=ordem, autorange="reversed", showgrid=False, title=None)
    maximo = df[valor].max()
    fig.update_xaxes(title=titulo_valor or None, range=[0, maximo * 1.2] if maximo and maximo > 0 else None,
                     nticks=5, **_eixo_valor(fmt))
    if not varios:  # toda barra já tem o valor na ponta: o eixo de valores seria redundante
        fig.update_xaxes(showticklabels=False, showgrid=False)
    n_linhas = _rotulos_categoria(fig.layout.yaxis, ordem)
    altura = altura or max(170, len(ordem) * ((46 if varios else 30) + 12 * (n_linhas - 1)) + 70)
    return _layout(fig, altura, legenda=varios)


def barras_divergentes(df: pd.DataFrame, cat: str, valor: str, ordem: list[str], n: str,
                       titulo_valor: str = "") -> go.Figure:
    """Barras horizontais com sinal (ex.: diferença salarial): negativo vermelho, positivo azul."""
    t = tema()
    anos = sorted(df["ano"].unique())
    fig = make_subplots(rows=1, cols=len(anos), shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=[str(a) for a in anos] if len(anos) > 1 else None)
    for i, ano in enumerate(anos, start=1):
        d = df[df["ano"] == ano]
        fig.add_bar(
            y=d[cat], x=d[valor], orientation="h", showlegend=False,
            marker_color=[t["div"][0] if v < 0 else t["div"][2] for v in d[valor].fillna(0)],
            text=d[valor].map(m.pct_sinal), textposition="outside", cliponaxis=False,
            textfont=dict(color=t["texto2"]),
            customdata=list(zip(d[valor].map(m.pct_sinal), d[n].map(m.inteiro))),
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>n = %{customdata[1]}<extra></extra>",
            row=1, col=i,
        )
    lim = max(5.0, float(df[valor].abs().max() or 0)) * 1.7  # folga para o rótulo das barras negativas
    fig.update_xaxes(range=[-lim, lim], ticksuffix="%", title=titulo_valor or None, zeroline=True, nticks=5)
    fig.update_yaxes(categoryorder="array", categoryarray=ordem, autorange="reversed", showgrid=False, ticklabelstandoff=8)
    n_linhas = _rotulos_categoria(fig.layout.yaxis, ordem, largura=24)
    altura = max(170, len(ordem) * (32 + 12 * (n_linhas - 1)) + 80)
    fig = _layout(fig, altura, legenda=False)
    fig.update_layout(margin=dict(t=36 if len(anos) > 1 else 8))
    return fig


def empilhado_100(df: pd.DataFrame, cat: str, serie: str, valor: str, ordem_cat: list[str],
                  ordem_serie: list[str], cores: list[str]) -> go.Figure:
    """Barras 100% empilhadas (composição) por `cat`; um painel por ano."""
    t = tema()
    anos = sorted(df["ano"].unique())
    ordem_cat = [c for c in ordem_cat if c in set(df[cat])]
    fig = make_subplots(rows=len(anos), cols=1, shared_xaxes=True, vertical_spacing=0.12 if len(anos) > 1 else 0,
                        subplot_titles=[str(a) for a in anos] if len(anos) > 1 else None)
    for i, ano in enumerate(anos, start=1):
        d = df[df["ano"] == ano]
        for s, cor in zip(ordem_serie, cores):
            ds = d[d[serie] == s].set_index(cat).reindex(ordem_cat)
            v = ds[valor]
            fig.add_bar(
                y=ordem_cat, x=v, orientation="h", name=s, legendgroup=s, showlegend=(i == 1),
                marker=dict(color=cor, line=dict(color=t["fundo"], width=2)),
                text=[m.pct(x) if x >= 9 else "" for x in v.fillna(0)], textposition="inside",
                insidetextanchor="middle", textfont=dict(color=_texto_sobre(cor)),
                customdata=[m.pct(x) for x in v],
                hovertemplate=f"<b>%{{y}}</b><br>{s}: " + "%{customdata}<extra></extra>",
                row=i, col=1,
            )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=False)
    fig.update_yaxes(categoryorder="array", categoryarray=ordem_cat, autorange="reversed", showgrid=False)
    altura = len(anos) * (len(ordem_cat) * 30 + 30) + 70
    return _legenda_acima_dos_paineis(_layout(fig, altura, legenda=True), len(anos), altura)


def linhas(df: pd.DataFrame, x: str, serie: str, valor: str, ordem_x: list[str], ordem_serie: list[str],
           fmt=m.pct) -> go.Figure:
    """Linhas (uma por série) sobre um eixo x ordinal; um painel por ano."""
    t = tema()
    anos = sorted(df["ano"].unique())
    ordem_x = [c for c in ordem_x if c in set(df[x])]
    fig = make_subplots(rows=1, cols=len(anos), shared_yaxes=True, horizontal_spacing=0.05,
                        subplot_titles=[str(a) for a in anos] if len(anos) > 1 else None)
    for i, ano in enumerate(anos, start=1):
        d = df[df["ano"] == ano]
        for s, cor in zip(ordem_serie, t["cat"]):
            ds = d[d[serie] == s].set_index(x).reindex(ordem_x)
            fig.add_scatter(
                x=ordem_x, y=ds[valor], name=s, legendgroup=s, showlegend=(i == 1), mode="lines+markers",
                line=dict(color=cor, width=2), marker=dict(size=9, color=cor, line=dict(color=t["fundo"], width=2)),
                customdata=[fmt(v) for v in ds[valor]],
                hovertemplate=f"<b>%{{x}}</b><br>{s}: " + "%{customdata}<extra></extra>",
                row=1, col=i,
            )
    fig.update_xaxes(categoryorder="array", categoryarray=ordem_x, showgrid=False, tickangle=-35)
    fig.update_yaxes(rangemode="tozero", **_eixo_valor(fmt))
    return _legenda_acima_dos_paineis(_layout(fig, 400, legenda=True), len(anos), 400)


def _legenda_acima_dos_paineis(fig: go.Figure, n_paineis: int, altura: int) -> go.Figure:
    """Com títulos de painel (um por ano), sobe a legenda para não encostar neles."""
    if n_paineis > 1:
        fig.update_layout(margin=dict(t=64), legend=dict(y=1 + 30 / (altura - 72)))
    return fig


def mapa_calor(pivo: pd.DataFrame, fmt=m.pct, titulo_x: str = "", titulo_y: str = "",
               escala: str = "seq") -> go.Figure:
    """Mapa de calor de um pivô (linhas x colunas); células vazias ficam em branco."""
    t = tema()
    cores = t["seq"]
    escala_cores = [[i / (len(cores) - 1), c] for i, c in enumerate(cores)]
    texto = pivo.map(lambda v: "" if pd.isna(v) else fmt(v))
    fig = go.Figure(go.Heatmap(
        z=pivo.values, x=list(pivo.columns), y=list(pivo.index), text=texto.values,
        colorscale=escala_cores, xgap=2, ygap=2, hoverongaps=False,
        hovertemplate="<b>%{y}</b> · %{x}<br>%{text}<extra></extra>",
        colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=t["apagado"]), **_eixo_valor(fmt)),
    ))
    # valor em cada célula, em branco ou preto conforme o tom da célula (contraste nos dois temas)
    zmin, zmax = pivo.min().min(), pivo.max().max()
    for y in pivo.index:
        for x in pivo.columns:
            v = pivo.loc[y, x]
            if pd.isna(v):
                continue
            passo = 0 if zmax == zmin else round((v - zmin) / (zmax - zmin) * (len(cores) - 1))
            fig.add_annotation(x=x, y=y, text=fmt(v), showarrow=False,
                               font=dict(family=FONTE, size=12, color=_texto_sobre(cores[passo])))
    fig.update_xaxes(side="top", showgrid=False, title=titulo_x or None, tickangle=0)
    fig.update_yaxes(autorange="reversed", showgrid=False, title=titulo_y or None)
    linhas_x = _rotulos_categoria(fig.layout.xaxis, list(pivo.columns), largura=13)
    n_linhas = _rotulos_categoria(fig.layout.yaxis, list(pivo.index), largura=24)
    altura = len(pivo.index) * (38 + 12 * (n_linhas - 1)) + 60 + 16 * linhas_x
    fig = _layout(fig, max(220, altura), legenda=False)
    fig.update_layout(margin=dict(t=8, r=8))
    return fig


def mostrar(fig: go.Figure, tabela: pd.DataFrame | None = None, chave: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", theme=None, key=chave, config={"displayModeBar": False})
    if tabela is not None:
        with st.expander("Ver dados"):
            st.dataframe(tabela, hide_index=True, width="stretch")
