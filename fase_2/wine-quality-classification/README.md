# Wine Quality Classification 🍷

Tech Challenge — Fase 2 (Pós-Tech) — Classificação da qualidade de vinhos com Machine Learning.

## 1. Descrição do Projeto

Este projeto desenvolve uma pipeline completa de ciência de dados para prever, a
partir de características físico-químicas mensuradas durante a produção, se um vinho
é de **Alta Qualidade** (nota de especialistas ≥ 7) ou **Baixa/Média Qualidade**
(nota < 7). O objetivo é apoiar enólogos e produtores na tomada de decisão,
reduzindo a dependência exclusiva de avaliações sensoriais subjetivas.

Base de dados: [Wine Quality Dataset](https://www.kaggle.com/datasets/yasserh/wine-quality-dataset)
(Kaggle) — `WineQT.csv`, 1.143 amostras de vinho tinto, 11 variáveis
físico-químicas + nota de qualidade (0–10).

## 2. Estrutura do Repositório

```
wine-quality-classification/
│
├── data/
│   └── WineQT.csv                      # Base de dados original
│
├── notebooks/
│   └── 01_analise_e_modelagem.ipynb    # Notebook principal (EDA + modelagem completa)
│
├── src/                                 # Scripts auxiliares (reutilizáveis pelo notebook)
│   ├── data_loading.py                  # Etapa 1 — carga e definição do alvo binário
│   ├── preprocessing.py                 # Etapa 3 — limpeza, feature engineering, split, scaling
│   ├── modeling.py                      # Etapa 4 — definição e treino dos modelos
│   ├── evaluation.py                    # Etapa 5 — métricas e gráficos comparativos
│   └── interpretation.py                # Etapa 6 — importância de variáveis / coeficientes
│
├── results/
│   ├── figures/                         # Gráficos gerados (EDA, avaliação, interpretação)
│   └── metrics/
│       └── metricas_modelos.csv         # Tabela comparativa final dos modelos
│
├── requirements.txt                     # Dependências do projeto
└── README.md
```

## 3. Como Executar

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd wine-quality-classification

# 2. Criar ambiente virtual (opcional, recomendado)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Rodar o notebook
jupyter notebook notebooks/01_analise_e_modelagem.ipynb
```

O notebook importa diretamente as funções de `src/`, então basta executar as células
em sequência (Run All). Todos os gráficos e a tabela de métricas são salvos
automaticamente em `results/`.

## 4. Metodologia (pipeline)

| Etapa | Descrição | Onde está |
|---|---|---|
| 1. Compreensão do Problema | Definição do alvo binário (`quality >= 7`) | `src/data_loading.py` |
| 2. EDA | Distribuições, correlações, outliers, balanceamento de classes | Notebook, seção 2 |
| 3. Pré-processamento | Tratamento de nulos, *feature engineering*, split estratificado, `StandardScaler` | `src/preprocessing.py` |
| 4. Modelagem | Regressão Logística, Random Forest, Gradient Boosting (`class_weight="balanced"`) | `src/modeling.py` |
| 5. Avaliação | Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC + matriz de confusão + curva ROC | `src/evaluation.py` |
| 6. Interpretação | Importância de variáveis (árvores) e coeficientes (regressão logística) | `src/interpretation.py` |

## 5. Principais Resultados

> Métricas obtidas no conjunto de teste (20% dos dados, split estratificado, `random_state=42`):

| Modelo | Accuracy | Precision | Recall | F1-score | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Gradient Boosting | 0.913 | 0.750 | 0.563 | **0.643** | 0.883 | 0.663 |
| Random Forest | 0.913 | 0.833 | 0.469 | 0.600 | **0.911** | **0.753** |
| Logistic Regression | 0.795 | 0.368 | **0.656** | 0.472 | 0.860 | 0.588 |

*(valores completos e reprodutíveis em `results/metrics/metricas_modelos.csv`)*

- **Gradient Boosting** obteve o melhor equilíbrio entre precisão e recall (maior F1-score).
- **Random Forest** apresentou a melhor capacidade de discriminação entre classes (maior ROC-AUC e PR-AUC).
- **Regressão Logística**, embora com performance inferior, prioriza recall — captura mais vinhos de alta qualidade, ao custo de mais falsos positivos — e oferece a maior interpretabilidade direta (coeficientes).

## 6. Principais Variáveis Identificadas

O **teor alcoólico (`alcohol`)** e a **acidez volátil (`volatile_acidity`)** foram
consistentemente as variáveis mais relevantes nos três modelos — a primeira com
efeito positivo sobre a qualidade, a segunda com efeito negativo. Sulfatos e ácido
cítrico também contribuem positivamente. Detalhes completos, gráficos e discussão
das implicações para o processo produtivo estão na seção 6 do notebook.

## 7. Entregáveis do Tech Challenge

- [x] Repositório GitHub com os códigos (este repositório)
- [ ] Apresentação executiva (storytelling da EDA) — PPT/PDF a ser adicionado neste repositório
- [ ] Vídeo executivo (até 5 min)

## 8. Licença / Fonte dos Dados

Dataset de uso público disponibilizado no Kaggle
([Wine Quality Dataset](https://www.kaggle.com/datasets/yasserh/wine-quality-dataset)),
originalmente de Cortez et al. (2009).
