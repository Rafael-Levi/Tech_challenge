"""Origem dos dados, modelo e regras de leitura do dashboard."""
import streamlit as st

from core import dados, filtros

st.title("Sobre os dados")

st.markdown("""
**Fonte:** pesquisa *State of Data Brasil* (Data Hackers), edições **2024** e **2025**.

**Pipeline no data lake (AWS S3 + Glue):**

| Camada | O que faz |
|---|---|
| Landing | CSVs originais da pesquisa, um por ano |
| Bronze | Parquet com nomes de colunas padronizados entre os anos; múltipla escolha em formato longo |
| Silver | Modelo normalizado no grão do respondente, com códigos (`cd_`), PKs e FKs validadas |
| **Gold** | **Star schema**: dimensões (filtros) + um fato agregado por tema de análise. **É a camada que este dashboard lê.** |
""")

st.subheader("Perguntas de negócio e tabelas da gold")
st.markdown("""
| Página | Fato | Dimensões (filtros) |
|---|---|---|
| Estrutura do mercado | `gld_ft_estrutura_mercado` | pesquisa, região, atuação, senioridade |
| Empresas e maturidade | `gld_ft_estrutura_empresas` | pesquisa, setor, porte |
| Remuneração | `gld_ft_remuneracao` | pesquisa, região, cargo, senioridade |
| Diversidade | `gld_ft_diversidade` | pesquisa, gênero, cor/raça, atuação, senioridade |
| Tecnologias | `gld_ft_adocao_opcao` | pesquisa, opção/tecnologia, atuação, senioridade |
| IA generativa | `gld_ft_ia_generativa` | pesquisa, uso de IA, atuação, senioridade |
| Modelo de trabalho e retenção | `gld_ft_modelo_trabalho_retencao` | pesquisa, região, senioridade, modelo atual, modelo ideal |
""")

st.subheader("Como os números são calculados")
st.markdown("""
- **Base = quem respondeu.** Todo percentual usa como denominador quem respondeu a pergunta, não o total de respondentes.
- **Agregação correta.** As colunas `qt_*` e `qt_base_*` da gold são somadas sob o filtro escolhido e o percentual é
  recalculado como `SUM(qt_x) / SUM(qt_base_x)`. O salário médio é `SUM(vl_salario_soma) / SUM(qt_com_salario)`.
  As colunas `pct_*` prontas só valem no grão do fato, por isso não são reagregadas.
- **"Não informado" (código -1).** Quem não viu a pergunta continua nas contagens, para o filtro não perder linhas.
- **Amostras pequenas.** Rankings e médias por grupo escondem grupos com poucas respostas (o mínimo aparece em cada gráfico).
""")

st.subheader("Cuidados na leitura")
for aviso in [
    filtros.AVISO_SALARIO,
    filtros.AVISO_ANOS,
    "O impacto da IA é uma correlação: quem usa IA paga pela empresa tende a ser mais sênior.",
    "Em 2025 a pergunta de linguagens teve opções removidas: SQL, Python e R comparam bem entre os anos; Java e JavaScript não.",
    "A senioridade \"Não informado\" é grande porque gestores e quem não trabalha não preenchem esse campo.",
]:
    st.markdown(f"- {aviso}")

st.subheader("Conexão")
nome_motor, motivo = dados.motor()
cfg = st.secrets["aws"]
st.markdown(f"- Database do catálogo Glue: `{cfg['database']}` (região `{cfg['region']}`)\n"
            f"- Leitura: **{'Amazon Athena, workgroup `' + cfg['workgroup'] + '`' if nome_motor == 'athena' else 'catálogo Glue → Parquet no S3'}**\n"
            f"- Cache: as tabelas são lidas uma vez e reaproveitadas por {dados.TTL // 3600} horas")
if motivo:
    st.caption(f"O Athena não respondeu, então a leitura usa o catálogo Glue. Motivo: {motivo}")
if st.button("Recarregar dados da gold", icon=":material/refresh:"):
    dados.carregar_gold.clear()
    dados.motor.clear()
    st.rerun()
with st.expander("Tabelas carregadas"):
    st.dataframe(dados.linhas_por_tabela(), hide_index=True, width="stretch")
