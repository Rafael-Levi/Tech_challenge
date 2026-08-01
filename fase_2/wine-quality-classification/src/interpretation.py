"""
interpretation.py
-----------------
Responsável pela Etapa 6 (Interpretação dos Resultados):
- Extrai a importância das variáveis para modelos baseados em árvore
  (Random Forest / Gradient Boosting)
- Extrai os coeficientes padronizados da Regressão Logística
  (interpretáveis em termos de direção e magnitude do efeito)
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def get_tree_feature_importance(model, feature_names: list[str]) -> pd.DataFrame:
    """
    Extrai a importância de variáveis (impurity-based) de um modelo baseado
    em árvore (RandomForest, GradientBoosting) já treinado.
    """
    importances = model.feature_importances_
    df = pd.DataFrame({"feature": feature_names, "importance": importances})
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def get_logistic_coefficients(model, feature_names: list[str]) -> pd.DataFrame:
    """
    Extrai os coeficientes da Regressão Logística (dados padronizados),
    permitindo interpretar a direção (positiva/negativa) e a magnitude
    relativa do efeito de cada variável sobre a probabilidade de o vinho
    ser classificado como "alta qualidade".
    """
    coefs = model.coef_[0]
    df = pd.DataFrame({"feature": feature_names, "coefficient": coefs})
    df["abs_coefficient"] = df["coefficient"].abs()
    return df.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)


def plot_feature_importance(importance_df: pd.DataFrame, title: str, top_n: int = 10, save_path: str | None = None):
    """
    Plota as top_n variáveis mais importantes em um gráfico de barras horizontais.
    """
    plot_df = importance_df.head(top_n).sort_values("importance")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_df["feature"], plot_df["importance"], color="#4C72B0")
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Importância")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_logistic_coefficients(coef_df: pd.DataFrame, top_n: int = 10, save_path: str | None = None):
    """
    Plota os coeficientes (com sinal) da Regressão Logística, permitindo
    visualizar quais variáveis aumentam (positivo) ou diminuem (negativo)
    a chance de o vinho ser de alta qualidade.
    """
    plot_df = coef_df.head(top_n).sort_values("coefficient")
    colors = ["#C44E52" if c < 0 else "#55A868" for c in plot_df["coefficient"]]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Coeficientes da Regressão Logística (padronizados)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Coeficiente (efeito sobre log-odds)")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
