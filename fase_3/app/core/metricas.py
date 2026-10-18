"""Agregação dos fatos da gold e formatação de números em pt-BR.

Regra da especificação: as colunas `qt_*`, `qt_base_*` e `vl_salario_soma` são somáveis sob qualquer
filtro; as `pct_*` e `vl_salario_medio` só valem no grão do fato. Por isso todo indicador é
recalculado aqui a partir das somas: pct = SUM(qt_x) / SUM(qt_base_x), salário = SUM(soma) / SUM(qt).
"""
import math

import numpy as np
import pandas as pd


def razao(num, den, fator: float = 1.0):
    """num / den, com NaN onde o denominador é zero (funciona com escalares e Series)."""
    if isinstance(den, pd.Series):
        return fator * num / den.where(den > 0)
    return fator * num / den if den else np.nan


def resumir(df: pd.DataFrame, por: list[str], indicadores: list[str] = (), salario: bool = True) -> pd.DataFrame:
    """Agrega o fato por `por` (sempre inclua 'ano') e recalcula salário médio e percentuais.

    `indicadores`: nomes `x` dos pares `qt_x` / `qt_base_x` -> gera `pct_x` (base = quem respondeu).
    """
    somas = ["qt_respondentes"] if "qt_respondentes" in df.columns else []
    if salario:
        somas += ["vl_salario_soma", "qt_com_salario"]
    for n in indicadores:
        somas += [f"qt_{n}", f"qt_base_{n}"]
    r = df.groupby(por, observed=True, dropna=False, sort=False)[somas].sum().reset_index()
    if salario:
        r["salario_medio"] = razao(r["vl_salario_soma"], r["qt_com_salario"])
    for n in indicadores:
        r[f"pct_{n}"] = razao(r[f"qt_{n}"], r[f"qt_base_{n}"], 100)
    return r


def participacao(df: pd.DataFrame, por: str, ano: str = "ano") -> pd.DataFrame:
    """Respondentes por categoria e % sobre o total do ano (dentro do recorte filtrado)."""
    r = resumir(df, [ano, por])
    r["pct_participacao"] = razao(r["qt_respondentes"], r.groupby(ano)["qt_respondentes"].transform("sum"), 100)
    return r


def adocao(df: pd.DataFrame, por: list[str]) -> pd.DataFrame:
    """Para `gld_ft_adocao_opcao`: % de adoção e salário médio de quem selecionou a opção."""
    r = df.groupby(por, observed=True, sort=False)[
        ["qt_base", "qt_selecionado", "vl_salario_soma_selecionado", "qt_selecionado_com_salario"]].sum().reset_index()
    r["pct_adocao"] = razao(r["qt_selecionado"], r["qt_base"], 100)
    r["salario_medio_usuarios"] = razao(r["vl_salario_soma_selecionado"], r["qt_selecionado_com_salario"])
    return r


# ---- formatação pt-BR -------------------------------------------------------------------------

def br(valor: float, casas: int) -> str:
    return f"{valor:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _vazio(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or x is pd.NA


def inteiro(x) -> str:
    return "—" if _vazio(x) else br(x, 0)


def pct(x) -> str:
    return "—" if _vazio(x) else br(x, 1) + "%"


def brl(x) -> str:
    return "—" if _vazio(x) else "R$ " + br(x, 0)


def pct_sinal(x) -> str:
    return "—" if _vazio(x) else ("+" if x > 0 else "") + br(x, 1) + "%"


FORMATOS = {"int": inteiro, "pct": pct, "brl": brl}
