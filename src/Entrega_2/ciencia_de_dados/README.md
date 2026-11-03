# CTI - Plataforma Analítica de Planejamento Financeiro

Projeto Interdisciplinar, **Ciência de Dados** (FECAP, CCOMP 4, 2026-2) - **Entrega 2: script em Python e dashboard publicado na nuvem**.

**Dashboard publicado:** https://cti-dashboard-financeiro.streamlit.app/

O painel apoia decisões estratégicas e operacionais a partir da projeção financeira de 12 anos em 1.200 cenários simulados, fornecida pela CTI. Ele integra os dados preparados na Entrega 1 e segue o dicionário de KPIs da Contabilidade.

---

## 1. O que o painel mostra

**Indicadores (9):** Receita, Resultado Operacional, EBITDA, Resultado Líquido, Margem Operacional, Margem EBITDA, Margem Líquida, Geração de Caixa e Margem de Caixa. Capital de Giro Líquido e Liquidez Corrente ficam em aba própria, marcados como *verificar* (ver Limitações).

**Filtros (barra lateral):** indicador, grupo de desempenho, intervalo de anos, inclusão do Ano 12 e estatística (média ou mediana).

**Abas:**

| Aba | Conteúdo |
|---|---|
| Painel financeiro | Cartões com as médias dos 12 anos, tabela anual com meta de margem operacional (60%, editável), gráfico das margens, nota sobre ticket médio e simulador de sensibilidade (desconto, custos e volume). |
| Evolução | Cartões dos 9 indicadores e gráfico por ano com faixa P10 a P90 dos cenários. |
| Comparação entre grupos | Barras de Piores 10%, Medianos, Melhores 10% e Todos em um ano escolhido, mais tabela com todos os indicadores. |
| Liquidez e Capital de Giro | Indicadores que dependem do sinal do Passivo Circulante, com aviso e contagem de cenários que seguem a regra da base. |
| Metodologia | Fonte, fórmulas, leitura do painel, limitações e verificações. |

**Grupos de desempenho:** cada cenário é classificado pelo Resultado Líquido acumulado nos 12 anos. *Piores 10%* (133 cenários) ficam abaixo de R$ 38,57 bi; *Melhores 10%* (120) ficam acima de R$ 41,02 bi; *Medianos* (947) ficam entre os dois. O cenário é uma trajetória, então não muda de grupo de um ano para o outro.

---

## 2. Estrutura da pasta

```
ciencia_de_dados/
├── app.py                          # dashboard (Streamlit)
├── preparar_dados.py               # script de preparação dos dados (Python)
├── requirements.txt                # dependências
├── README.md
└── dados/
    └── processed/
        └── base_dashboard.csv      # base agregada que alimenta o painel
```

O tema visual fica em `.streamlit/config.toml`, na raiz do repositório.

---

## 3. Como executar

Requer Python 3.12 ou superior.

**Dashboard (usa a base agregada já incluída):**

```
pip install -r requirements.txt
streamlit run app.py
```

No Windows, se `pip` ou `streamlit` não forem reconhecidos, use `py -m pip install -r requirements.txt` e `py -m streamlit run app.py`. O painel abre em `http://localhost:8501`.

**Regerar a base a partir do arquivo da CTI** (o `Demonstrativo_Fecap_v3.csv` não é versionado no repositório):

```
python preparar_dados.py --entrada Demonstrativo_Fecap_v3.csv --saida dados
```

Gera `dados/staging/linhas_nao_identificadas.csv` (quarentena), `dados/processed/base_analitica.csv` (14.400 linhas, uso local), `dados/processed/base_dashboard.csv` (576 linhas, alimenta o painel) e `dados/processed/log_qualidade.json` (checagens).

**Atualizar o painel publicado:** ao alterar a base ou o código no GitHub, o app se atualiza sozinho. Se continuar mostrando a versão antiga, use *Manage app* e *Reboot app* na Streamlit.

---

## 4. Fontes dos dados

- **Origem:** demonstrativo financeiro projetado fornecido pela CTI (`Demonstrativo_Fecap_v3.csv`, agosto/2026), único arquivo de dados do projeto. São 1.002.000 linhas no formato longo (ano, cenário, conta, valor): 12 anos, 1.200 cenários e 69 contas de balanço, DRE e fluxo de caixa.
- **Seleção:** 14 contas (Ativo Circulante, Passivo Circulante, Total do Ativo, Total do Passivo, Saldo Inicial, Saldo Final, Geração de Caixa, Investimentos, Distribuição para Acionista, Receita, Custos, Resultado Operacional, EBITDA e Resultado Líquido). A Entrega 1 usou 10 dessas contas; a Entrega 2 acrescentou Resultado Operacional, Geração de Caixa, Total do Ativo e Total do Passivo, para alinhar os indicadores ao dicionário da Contabilidade.
- **Tratamento:** as 43.200 linhas sem nome de conta (4,31%) ficam em quarentena e fora da análise; espaços duplicados nos nomes são removidos; os dados são pivotados em uma linha por ano e cenário (14.400 linhas).
- **Publicação:** a base agregada (`base_dashboard.csv`), sem dados cenário a cenário, foi liberada pela CTI para publicação.

---

## 5. Fórmulas

| Indicador | Fórmula | Unidade |
|---|---|---|
| Receita | `DRE - Receita` | R$ |
| Resultado Operacional | `DRE - Resultado Operacional` (Receita + Tributos + Custos + Depreciação/Amortização) | R$ |
| EBITDA | `DRE - EBITDA` | R$ |
| Resultado Líquido | `DRE - Resultado Líquido` | R$ |
| Margem Operacional | Resultado Operacional ÷ Receita (vazio se Receita ≤ 0) | % |
| Margem EBITDA | EBITDA ÷ Receita (vazio se Receita ≤ 0) | % |
| Margem Líquida | Resultado Líquido ÷ Receita (vazio se Receita ≤ 0) | % |
| Geração de Caixa | `FLU - Geração de Caixa` (= Saldo Final − Saldo Inicial) | R$ |
| Margem de Caixa | Geração de Caixa ÷ Receita (vazio se Receita ≤ 0) | % |
| Capital de Giro Líquido (*verificar*) | Ativo Circulante + Passivo Circulante (passivo armazenado com sinal negativo) | R$ |
| Liquidez Corrente (*verificar*) | Ativo Circulante ÷ (− Passivo Circulante) | x |

**Estatísticas:** a base do painel traz, por indicador, grupo e ano, a média, a mediana, o P10 e o P90 entre os cenários, além do número de cenários válidos.

**Simulador de sensibilidade** (parâmetros: desconto *d*, aumento de custos *c*, variação de volume *v*), sobre as médias dos 12 anos do grupo escolhido:

- Receita ajustada = Receita × (1 + v) × (1 − d)
- Custos ajustados = |Custos| × (1 + v) × (1 + c)
- Resultado operacional estimado = Resultado Operacional × (1 + v) − Receita × (1 + v) × d − |Custos| × (1 + v) × c
- Margem operacional estimada = Resultado operacional estimado ÷ Receita ajustada

É uma aproximação sobre médias agregadas; não substitui a DRE nem uma projeção oficial.

---

## 6. Verificações realizadas

- Saldo Final de um ano igual ao Saldo Inicial do ano seguinte, no mesmo cenário (13.200 pares, diferença máxima 0).
- Geração de Caixa igual a Saldo Final − Saldo Inicial (diferença máxima de R$ 0,00002).
- Total do Ativo + Total do Passivo ≈ 0 em todas as linhas (diferença máxima de R$ 0,03), o que confirma que a base guarda os passivos com sinal negativo.
- Base integrada com 14.400 linhas (1.200 cenários × 12 anos) e sem valores ausentes nas 14 contas selecionadas.
- Médias anuais, margens, liquidez e simulação conferidas contra a planilha de validação da Contabilidade (diferença relativa abaixo de 10⁻¹³).

---

## 7. Limitações

- **Ano 12 incompleto:** o balanço tem cobertura reduzida e a margem líquida destoa dos demais anos (a Margem de Caixa também). Ele fica fora por padrão nos filtros e é sinalizado no Painel financeiro.
- **Sinal do Passivo Circulante:** a base guarda passivos com sinal negativo, mas o Passivo Circulante fica positivo em quase todos os cenários dos Anos 5 a 11 (e em cerca de metade no Ano 12). A CTI não confirmou a convenção, então Liquidez Corrente e Capital de Giro ficam em aba própria, marcados como *verificar*, com os valores originais preservados e sem correção. A Liquidez Corrente tem valores extremos (de −31.263 a 1.488); use a mediana.
- **Ticket médio:** não calculável, pois a base não tem quantidade de vendas, pedidos ou transações.
- **Margens muito altas** (EBITDA entre 75% e 97% da receita) são características das projeções e não foram validadas com a CTI.
- **Geração de Caixa** inclui investimentos e distribuições aos acionistas; não é geração operacional de caixa. Não há abertura da DFC por atividade, nem dados para Necessidade de Capital de Giro ou DVA.
- **Valores simulados:** são projeções, não dados realizados.

---

## 8. Relação com as demais entregas

- **Entrega 1 (Ciência de Dados):** coleta, descrição, exploração, seleção, limpeza e integração dos dados em notebook no Colab e relatório. O `preparar_dados.py` reproduz esse tratamento em script.
- **Contabilidade:** os indicadores, as fórmulas e as regras de validação seguem o dicionário de KPIs e a planilha de validação da equipe BeHolders.
