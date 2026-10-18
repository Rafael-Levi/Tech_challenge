"""Acesso à camada gold (database `db_gold` do catálogo AWS Glue).

As tabelas da gold são pequenas (alguns milhares de linhas no total), então cada uma é lida
uma única vez, guardada em cache e filtrada em pandas pelas páginas.

Motor de leitura (`engine` em `[aws]` no secrets.toml):
- "athena": `SELECT * FROM <tabela>` no workgroup configurado;
- "glue":   lê o Parquet direto do S3, no local registrado no catálogo Glue;
- "auto" (padrão): tenta o Athena e, se ele estiver indisponível, usa o catálogo Glue.
"""
import os
from concurrent.futures import ThreadPoolExecutor

import awswrangler as wr
import boto3
import numpy as np
import pandas as pd
import streamlit as st

TTL = 6 * 60 * 60  # a gold é recarregada pela ETL, não em tempo real
NAO_INFORMADO = -1

# coluna cd_ usada nos fatos -> (dimensão, código na dimensão, descrição na dimensão, rótulo no BI)
DIMENSOES = {
    "cd_pesquisa":              ("gld_dim_pesquisa",        "cd_pesquisa",        "ds_pesquisa",        "Pesquisa"),
    "cd_regiao":                ("gld_dim_regiao",          "cd_regiao",          "ds_regiao",          "Região"),
    "cd_atuacao_dados":         ("gld_dim_atuacao",         "cd_atuacao_dados",   "ds_atuacao_dados",   "Área de atuação"),
    "cd_cargo":                 ("gld_dim_cargo",           "cd_cargo",           "ds_cargo",           "Cargo"),
    "cd_senioridade":           ("gld_dim_senioridade",     "cd_senioridade",     "ds_senioridade",     "Senioridade"),
    "cd_setor":                 ("gld_dim_setor",           "cd_setor",           "ds_setor",           "Setor"),
    "cd_porte_empresa":         ("gld_dim_porte_empresa",   "cd_porte_empresa",   "ds_porte_empresa",   "Porte da empresa"),
    "cd_modelo_trabalho_atual": ("gld_dim_modelo_trabalho", "cd_modelo_trabalho", "ds_modelo_trabalho", "Modelo atual"),
    "cd_modelo_trabalho_ideal": ("gld_dim_modelo_trabalho", "cd_modelo_trabalho", "ds_modelo_trabalho", "Modelo ideal"),
    "cd_genero":                ("gld_dim_genero",          "cd_genero",          "ds_genero",          "Gênero"),
    "cd_cor_raca_etnia":        ("gld_dim_cor_raca_etnia",  "cd_cor_raca_etnia",  "ds_cor_raca_etnia",  "Cor/raça/etnia"),
    "cd_uso_ia":                ("gld_dim_uso_ia",          "cd_uso_ia",          "ds_uso_ia",          "Uso de IA generativa"),
    "cd_opcao":                 ("gld_dim_opcao",           "cd_opcao",           "ds_opcao",           "Opção"),
}

FATOS = [
    "gld_ft_estrutura_mercado", "gld_ft_estrutura_empresas", "gld_ft_remuneracao", "gld_ft_diversidade",
    "gld_ft_adocao_opcao", "gld_ft_ia_generativa", "gld_ft_modelo_trabalho_retencao",
]

# rótulos curtos para descrições longas demais para eixo de gráfico
ENCURTAR = {
    "gld_dim_modelo_trabalho": {
        "Modelo 100% presencial": "100% presencial",
        "Modelo 100% remoto": "100% remoto",
        "Modelo híbrido com dias fixos de trabalho presencial": "Híbrido (dias fixos)",
        "Modelo híbrido flexível (o funcionário tem liberdade para escolher quando estar no escritório presencialmente)": "Híbrido flexível",
    },
}


def _cfg():
    return st.secrets["aws"]


def _sessao() -> boto3.Session:
    cfg = _cfg()
    if cfg.get("ca_bundle"):  # rede corporativa com inspeção TLS (só para rodar localmente)
        os.environ["AWS_CA_BUNDLE"] = cfg["ca_bundle"]
    return boto3.Session(aws_access_key_id=cfg["access_key_id"], aws_secret_access_key=cfg["secret_access_key"],
                         region_name=cfg["region"])


def _ler_athena(tabela: str, sessao: boto3.Session) -> pd.DataFrame:
    cfg = _cfg()
    return wr.athena.read_sql_query(f'SELECT * FROM "{tabela}"', database=cfg["database"], workgroup=cfg["workgroup"],
                                    ctas_approach=False, boto3_session=sessao)


def _ler_glue(tabela: str, sessao: boto3.Session) -> pd.DataFrame:
    return wr.s3.read_parquet_table(database=_cfg()["database"], table=tabela, boto3_session=sessao)


@st.cache_resource(ttl=TTL, show_spinner=False)
def motor() -> tuple[str, str | None]:
    """Motor de leitura em uso e, se o Athena foi descartado no modo auto, o motivo."""
    preferido = _cfg().get("engine", "auto")
    if preferido in ("athena", "glue"):
        return preferido, None
    try:
        _ler_athena("gld_dim_pesquisa", _sessao())
        return "athena", None
    except Exception as e:  # noqa: BLE001 - qualquer falha do Athena cai no catálogo Glue
        return "glue", str(e).splitlines()[0][:300]


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """Tipos nullable do Athena/Parquet -> tipos numpy (códigos int, medidas float com NaN)."""
    df = df.copy()
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c]):
            if c.startswith("cd_") and not df[c].isna().any():
                df[c] = df[c].astype("int64")
            else:
                df[c] = df[c].to_numpy(dtype="float64", na_value=np.nan)
        else:
            df[c] = df[c].astype("object")
    return df


@st.cache_data(ttl=TTL, show_spinner="Carregando a camada gold do data lake...")
def carregar_gold() -> dict[str, pd.DataFrame]:
    nome_motor, _ = motor()
    ler = _ler_athena if nome_motor == "athena" else _ler_glue
    tabelas = sorted({d[0] for d in DIMENSOES.values()} | set(FATOS))
    # uma sessão por tarefa: boto3.Session não é thread-safe
    with ThreadPoolExecutor(max_workers=8) as ex:
        lidas = dict(ex.map(lambda t: (t, _normalizar(ler(t, _sessao()))), tabelas))
    for dim, mapa in ENCURTAR.items():
        ds = next(v[2] for v in DIMENSOES.values() if v[0] == dim)
        lidas[dim][ds] = lidas[dim][ds].replace(mapa)
    return lidas


def coluna_ds(cd: str) -> str:
    """Nome da coluna de descrição que `fato()` cria para um código (cd_x -> ds_x)."""
    return "ds_" + cd.removeprefix("cd_")


def rotulo(cd: str) -> str:
    return DIMENSOES[cd][3]


def ordem(cd: str) -> list[str]:
    """Descrições de uma dimensão na ordem de exibição; 'Não informado' e 'Exterior' no fim."""
    tabela, cd_dim, ds_dim, _ = DIMENSOES[cd]
    d = carregar_gold()[tabela]
    chave = d["nr_ordem"] if "nr_ordem" in d.columns else d[cd_dim].astype(float)
    especial = d[cd_dim] < 0
    d = d.assign(_esp=especial, _k=chave.where(~especial, d[cd_dim])).sort_values(["_esp", "_k"])
    return d[ds_dim].tolist()


def fato(nome: str, anos: list[int]) -> pd.DataFrame:
    """Fato filtrado pelos anos, com a descrição de cada dimensão ao lado do código e a coluna `ano`."""
    gold = carregar_gold()
    df = gold[nome]
    df = df[df["cd_pesquisa"].isin(anos)].copy()
    df["ano"] = df["cd_pesquisa"].astype(int)
    for cd, (tabela, cd_dim, ds_dim, _) in DIMENSOES.items():
        if cd not in df.columns or cd == "cd_pesquisa":
            continue
        dim = gold[tabela].drop(columns=["nr_ordem"], errors="ignore")
        dim = dim.rename(columns={cd_dim: cd, ds_dim: coluna_ds(cd)})
        df = df.merge(dim, on=cd, how="left")
    return df


def linhas_por_tabela() -> pd.DataFrame:
    gold = carregar_gold()
    return pd.DataFrame({"tabela": list(gold), "linhas": [len(d) for d in gold.values()]})
