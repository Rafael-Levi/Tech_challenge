## Perguntas de negócio e suas respectivas fontes de dados

| Pergunta do desafio | Fato | Dimensões (filtros) |
|---------------------|------|---------------------|
| Estrutura do mercado | gld_ft_estrutura_mercado | pesquisa, região, atuação, senioridade |
| Estrutura do mercado (empresas, maturidade) | gld_ft_estrutura_empresas | pesquisa, setor, porte |
| Perfis mais valorizados, diferenças regionais | gld_ft_remuneracao | pesquisa, região, cargo, senioridade |
| Diversidade | gld_ft_diversidade | pesquisa, gênero, cor/raça, atuação, senioridade |
| Tecnologias mais adotadas | gld_ft_adocao_opcao | pesquisa, opção/tecnologia, atuação, senioridade |
| Adoção de IA e impacto | gld_ft_ia_generativa | pesquisa, uso de IA, atuação, senioridade |
| Modelo de trabalho, retenção, desafios para empresas | gld_ft_modelo_trabalho_retencao | pesquisa, região, senioridade, modelo atual, modelo ideal |


## Indicadores criados

### Os indicadores são calculados por respondente na ETL e depois agregados:

- *Remuneração*: quantidade com salário, soma, média e mediana, e 4 faixas (até R$ 4 mil, 4 a 8 mil, 8 a 16 mil, acima de 16 mil).
- *Percentuais*: `pct_gestor`, ``pct_pos_graduado``, ``pct_negros`` e `pct_pcd`, ``pct_satisfeitos``, ``pct_buscando_mudar``, ``pct_afetados_layoff``, ``pct_sairia_retorno_presencial``, ``pct_modelo_alinhado (atual = ideal)``, ``pct_data_lake``, ``pct_data_warehouse`` e ``pct_ia_prioridade_alta``.
- *Diversidade*: ``pct_participacao_no_grupo`` e ``pct_dif_salario_vs_masculino``, a diferença salarial já calculada contra os homens do mesmo ano, atuação e senioridade.
- *Tecnologias*: ``pct_adocao`` e o salário médio de quem usa cada tecnologia.
- *IA*: uma categoria nova de uso de IA generativa (não usa, gratuita, Copilot, paga do bolso, empresa paga), que permite comparar salário e satisfação por nível de uso.


## Como o BI le os números
- *Quem respondeu*: todo percentual usa como base quem respondeu a pergunta, não o total. As bases ficam em colunas ``qt_base_*``.
- *Colunas somáveis*: as ``qt_*`` e ``qt_base_*`` podem ser somadas sob qualquer filtro. A pct_participacao_pesquisa também (soma 100% por ano).
- *Percentuais no grão do fato*: as colunas ``pct_*`` são válidas quando o gráfico usa as mesmas dimensões do grão. Se o BI agregar além disso, use ``SUM(qt_x) / SUM(qt_base_x)``.


## Decisões de modelagem
- *Sem FK nula na Gold*: quem não viu a pergunta cai no código -1 *“Não informado”*. Assim o filtro do BI não perde linhas.
- *Drill-through*: os códigos das dimensões são os mesmos da Silver. Para ver o detalhe de um número, basta filtrar ``slv_evt_respondente`` pelos mesmos códigos.
- *Dimensões derivadas (verdes no diagrama)*: região (vem da UF; inclui “Exterior”), cargo (junta cargos individuais e cargos de gestão), uso de IA e opção (com um “tema” para filtrar: linguagens, BI, cloud, barreiras de IA, motivos de insatisfação...).
- *Validação*: além de PK e FK, a reconciliação com a Silver falharia se algum agregado não batesse com o granular.

## Pontos de atenção
- O “salário” da pesquisa é uma faixa. Todos os valores são médias de pontos médios das faixas, então são estimativas.
- O impacto da IA é uma correlação. Quem usa IA paga pela empresa tende a ser mais sênior, então filtre por senioridade antes de concluir algo.
- Em 2025, a pergunta de linguagens teve opções removidas. SQL, Python e R comparam bem entre os anos, mas Java e JavaScript não.
- A amostra de 2024 só tem pessoas de 18 a 27 anos, enquanto a de 2025 vai até 71. Se não for a base completa, as comparações entre anos ficam enviesadas.
- A senioridade “Não informado” é grande (277 respondentes em 2025), porque gestores e quem não trabalha não preenchem esse campo.