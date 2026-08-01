"""
modeling.py
-----------
Responsável pela Etapa 4 (Desenvolvimento de Modelos):
- Treina pelo menos dois modelos de classificação distintos
- Usa class_weight="balanced" para lidar com o desbalanceamento de classes
  identificado na EDA (apenas ~14% dos vinhos são de alta qualidade)
"""

from __future__ import annotations

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression


def get_models(random_state: int = 42) -> dict:
    """
    Retorna um dicionário {nome_do_modelo: estimador_nao_treinado}.

    Modelos escolhidos e justificativa:
    - Regressão Logística: modelo linear, altamente interpretável (coeficientes
      indicam direção e magnitude do efeito de cada variável), serve de baseline.
    - Random Forest: modelo de ensemble (bagging), captura relações não-lineares
      e interações entre variáveis, robusto a outliers, fornece importância de
      variáveis.
    - Gradient Boosting: ensemble sequencial (boosting), geralmente com maior
      poder preditivo, usado aqui como terceiro modelo para enriquecer a
      comparação.
    """
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=random_state,
        ),
    }
    return models


def train_models(models: dict, X_train, y_train) -> dict:
    """
    Treina cada modelo do dicionário com os dados de treino fornecidos.
    Retorna o mesmo dicionário, agora com os modelos ajustados (fit).
    """
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        fitted[name] = model
    return fitted
