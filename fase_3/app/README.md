# Dashboard State of Data Brasil

Dashboard em Streamlit que lê a camada **gold** (star schema) do data lake na AWS, pelo catálogo Glue `db_gold`.

**Link do dashbord**: [`datahackers-dashbord`](https://tech-challenge-datahackers-dashbord.streamlit.app/)

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
