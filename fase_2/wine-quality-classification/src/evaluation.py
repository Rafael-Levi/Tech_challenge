"""
evaluation.py
-------------
Responsável pela Etapa 5 (Avaliação dos Modelos):
- Calcula métricas adequadas para um problema de classificação binária
  desbalanceado (accuracy sozinha é enganosa aqui — priorizamos
  precision, recall, F1 e ROC-AUC / PR-AUC).
- Gera matriz de confusão e curvas ROC para comparação visual entre modelos.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    """
    Calcula um conjunto de métricas para um modelo já treinado.

    Métricas escolhidas e justificativa:
    - Accuracy: métrica geral, mas pouco informativa isoladamente em
      dataset desbalanceado (~14% de casos positivos).
    - Precision: dentre os vinhos previstos como "alta qualidade",
      quantos realmente são — relevante se o custo de um falso positivo
      (classificar um vinho comum como premium) for alto.
    - Recall: dentre os vinhos realmente de alta qualidade, quantos o
      modelo conseguiu identificar — relevante se o custo de deixar
      passar um vinho premium for alto.
    - F1-score: média harmônica entre precision e recall, métrica-resumo
      mais robusta que accuracy para classes desbalanceadas.
    - ROC-AUC: mede a capacidade de discriminação do modelo entre as
      classes, independente do limiar de decisão escolhido.
    - PR-AUC (average precision): mais informativa que ROC-AUC quando a
      classe positiva é minoritária.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba),
        "pr_auc": average_precision_score(y_test, y_proba),
    }
    return metrics


def evaluate_all_models(fitted_models: dict, X_test, y_test) -> pd.DataFrame:
    """
    Avalia todos os modelos treinados e retorna uma tabela comparativa
    ordenada pelo F1-score (métrica-resumo mais adequada ao problema).
    """
    rows = [evaluate_model(model, X_test, y_test, name) for name, model in fitted_models.items()]
    results_df = pd.DataFrame(rows).sort_values("f1_score", ascending=False).reset_index(drop=True)
    return results_df


def plot_confusion_matrices(fitted_models: dict, X_test, y_test, save_path: str | None = None):
    """
    Plota lado a lado a matriz de confusão de cada modelo treinado.
    """
    n_models = len(fitted_models)
    fig, axes = plt.subplots(1, n_models, figsize=(5.5 * n_models, 4.5))
    if n_models == 1:
        axes = [axes]

    for ax, (name, model) in zip(axes, fitted_models.items()):
        y_pred = model.predict(X_test)
        ConfusionMatrixDisplay.from_predictions(
            y_test,
            y_pred,
            display_labels=["Baixa/Média", "Alta"],
            cmap="Blues",
            ax=ax,
            colorbar=False,
        )
        ax.set_title(name)

    fig.suptitle("Matriz de Confusão por Modelo", fontsize=14, fontweight="bold")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_roc_curves(fitted_models: dict, X_test, y_test, save_path: str | None = None):
    """
    Plota as curvas ROC de todos os modelos no mesmo gráfico para comparação direta.
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, model in fitted_models.items():
        RocCurveDisplay.from_estimator(model, X_test, y_test, name=name, ax=ax)

    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Aleatório (AUC=0.50)")
    ax.set_title("Curvas ROC — Comparação entre Modelos", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_metrics_comparison(results_df: pd.DataFrame, save_path: str | None = None):
    """
    Gráfico de barras comparando as principais métricas entre os modelos.
    """
    metrics_to_plot = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    plot_df = results_df.melt(
        id_vars="model", value_vars=metrics_to_plot, var_name="metric", value_name="value"
    )

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.barplot(data=plot_df, x="metric", y="value", hue="model", ax=ax)
    ax.set_ylim(0, 1)
    ax.set_title("Comparação de Métricas entre Modelos", fontsize=13, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.legend(title="Modelo", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
