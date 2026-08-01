"""
preprocessing.py
-----------------
Responsável pela Etapa 3 (Pré-processamento de Dados):
- Tratamento de dados faltantes (defensivo — o dataset não possui nulos,
  mas o pipeline está preparado para lidar com eles caso apareçam em produção)
- Feature engineering (novas variáveis com relevância enológica)
- Split treino/teste estratificado
- Padronização (StandardScaler) das variáveis numéricas
"""

from __future__ import annotations

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def handle_missing_values(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """
    Imputa valores faltantes em colunas numéricas usando a mediana.
    Estratégia defensiva: o WineQT.csv não possui valores nulos, mas o
    pipeline deve ser robusto a novas cargas de dados que possam conter.
    """
    out = df.copy()
    n_missing = out[numeric_cols].isna().sum().sum()
    if n_missing > 0:
        imputer = SimpleImputer(strategy="median")
        out[numeric_cols] = imputer.fit_transform(out[numeric_cols])
    return out


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria novas features com embasamento físico-químico/enológico:

    - total_acidity: soma da acidez fixa e volátil (proxy de acidez total percebida)
    - free_so2_ratio: proporção de SO2 livre em relação ao SO2 total
        (indicador relevante de proteção antioxidante/antimicrobiana do vinho)
    - acid_to_sulphate_ratio: relação entre acidez volátil e sulfatos
        (sulfatos atuam como conservante; a razão ajuda a capturar equilíbrio)
    - alcohol_density_ratio: relação entre teor alcoólico e densidade
        (álcool tende a reduzir densidade; a razão ajuda a evidenciar
        combinações atípicas)
    """
    out = df.copy()

    out["total_acidity"] = out["fixed_acidity"] + out["volatile_acidity"]

    # Evita divisão por zero
    out["free_so2_ratio"] = out["free_sulfur_dioxide"] / out["total_sulfur_dioxide"].replace(0, pd.NA)
    out["free_so2_ratio"] = out["free_so2_ratio"].fillna(0)

    out["acid_to_sulphate_ratio"] = out["volatile_acidity"] / out["sulphates"].replace(0, pd.NA)
    out["acid_to_sulphate_ratio"] = out["acid_to_sulphate_ratio"].fillna(0)

    out["alcohol_density_ratio"] = out["alcohol"] / out["density"]

    return out


def split_data(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Divide o dataset em treino e teste de forma estratificada pela variável
    alvo (importante dado o desbalanceamento de classes).
    """
    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test


def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """
    Padroniza (z-score) as variáveis numéricas com base no treino,
    aplicando a mesma transformação ao teste (evita vazamento de dados).
    """
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=X_test.columns, index=X_test.index
    )
    return X_train_scaled, X_test_scaled, scaler


def run_preprocessing_pipeline(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
):
    """
    Pipeline de conveniência que encadeia: engenharia de features -> split -> scaling.
    Retorna os conjuntos prontos para treinamento, junto com o scaler ajustado.
    """
    df_fe = engineer_features(df)
    all_features = feature_cols + [
        "total_acidity",
        "free_so2_ratio",
        "acid_to_sulphate_ratio",
        "alcohol_density_ratio",
    ]

    X_train, X_test, y_train, y_test = split_data(
        df_fe, all_features, target_col, test_size, random_state
    )
    X_train_scaled, X_test_scaled, scaler = scale_features(X_train, X_test)

    return {
        "X_train": X_train_scaled,
        "X_test": X_test_scaled,
        "y_train": y_train,
        "y_test": y_test,
        "X_train_raw": X_train,
        "X_test_raw": X_test,
        "scaler": scaler,
        "feature_names": all_features,
    }
