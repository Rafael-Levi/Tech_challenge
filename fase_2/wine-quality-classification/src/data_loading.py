"""
data_loading.py
----------------
Responsável pela Etapa 1 (Compreensão do Problema):
- Carregar a base de dados WineQT.csv
- Padronizar nomes de colunas
- Criar a variável alvo binária (qualidade_alta) a partir da nota de qualidade

Regra de negócio definida no desafio:
    Vinho de Alta Qualidade      -> quality >= 7  -> 1
    Vinho de Baixa/Média Qualidade -> quality < 7  -> 0
"""

from pathlib import Path
import pandas as pd

# Limiar de corte definido no enunciado do Tech Challenge
QUALITY_THRESHOLD = 7

# Colunas físico-químicas (features) — tudo, exceto identificador e alvo
ID_COLUMN = "Id"
RAW_TARGET_COLUMN = "quality"
TARGET_COLUMN = "high_quality"


def load_raw_data(csv_path: str | Path) -> pd.DataFrame:
    """
    Carrega o CSV bruto do Wine Quality Dataset.

    Parameters
    ----------
    csv_path : str | Path
        Caminho para o arquivo WineQT.csv

    Returns
    -------
    pd.DataFrame
        DataFrame com os dados brutos, colunas padronizadas (snake_case).
    """
    df = pd.read_csv(csv_path)

    # Padroniza nomes de colunas: minúsculas, espaços -> underscore
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    return df


def create_binary_target(
    df: pd.DataFrame,
    threshold: int = QUALITY_THRESHOLD,
    raw_col: str = RAW_TARGET_COLUMN,
    target_col: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """
    Cria a variável alvo binária a partir da nota de qualidade (0-10).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame contendo a coluna de qualidade original.
    threshold : int
        Nota mínima (inclusiva) para ser considerado "alta qualidade".
    raw_col : str
        Nome da coluna de qualidade original.
    target_col : str
        Nome da nova coluna binária a ser criada.

    Returns
    -------
    pd.DataFrame
        Cópia do DataFrame com a coluna binária adicionada.
    """
    out = df.copy()
    out[target_col] = (out[raw_col] >= threshold).astype(int)
    return out


def load_and_prepare(csv_path: str | Path) -> pd.DataFrame:
    """
    Pipeline de conveniência: carrega o CSV e já aplica a criação do alvo binário.
    """
    df = load_raw_data(csv_path)
    df = create_binary_target(df)
    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Retorna a lista de colunas físico-químicas (features), excluindo
    identificador, a nota original e o alvo binário.
    """
    exclude = {ID_COLUMN.lower(), RAW_TARGET_COLUMN, TARGET_COLUMN}
    return [c for c in df.columns if c not in exclude]
