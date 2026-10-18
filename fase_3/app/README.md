# Dashboard State of Data Brasil

Dashboard em Streamlit que lê a camada **gold** (star schema) do data lake na AWS, pelo catálogo Glue `db_gold`.

## Estrutura

```
app/
├── app.py                 # entrada: navegação, filtro global de ano e conexão
├── core/
│   ├── dados.py           # leitura das tabelas gld_* (Athena ou catálogo Glue) com cache
│   ├── metricas.py        # agregação SUM(qt_x)/SUM(qt_base_x) e formatação pt-BR
│   ├── graficos.py        # gráficos Plotly (tema claro/escuro)
│   └── filtros.py         # filtros, cartões de indicadores e avisos de leitura
├── paginas/               # uma página por pergunta de negócio (ver especificacao_dash.md)
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml       # credenciais: NÃO versionar (está no .gitignore)
└── requirements.txt
```

## Rodar localmente

```bash
cd app
pip install -r requirements.txt
streamlit run app.py
```

Em rede corporativa com inspeção TLS (erro `CERTIFICATE_VERIFY_FAILED`), aponte o bundle de certificados da
empresa com `ca_bundle = "C:/caminho/ca.pem"` em `[aws]` no `secrets.toml`.


## Publicar no Streamlit Community Cloud

1. Faça push do repositório para o GitHub **sem** o `secrets.toml` (o `.gitignore` desta pasta já o exclui).
2. Em [share.streamlit.io](https://share.streamlit.io) → **Create app** → escolha o repositório e a branch, e informe
   o arquivo principal `fase_3/app/app.py`. O `requirements.txt` desta pasta é detectado automaticamente.
3. Em **Advanced settings → Secrets**, cole o bloco `[aws]` acima com as chaves reais.
4. **Deploy**. A primeira carga lê as 20 tabelas da gold (alguns segundos) e as guarda em cache por 6 horas.
   A página *Sobre os dados* tem um botão para recarregar depois de uma nova execução da ETL.