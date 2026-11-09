# Registro de uso de Inteligência Artificial no projeto

Projeto Interdisciplinar (PI), CTI - Plataforma Analítica de Planejamento Financeiro (FECAP, 2026-2).

Este documento reúne o uso de IA declarado pelos integrantes do grupo, conforme o *Guia para o Uso Responsável de Inteligência Artificial na FECAP*. As fichas individuais de declaração (Art. 7º do Guia) estão nesta mesma pasta.

## 1. Resumo por integrante

| Integrante | Disciplina / trabalho | Ferramenta | Ficha |
|---|---|---|---|
| Letícia Rodrigues da Silva | Ciência de Dados (Entregas 1 e 2) | Claude (Sonnet 5.5) | `Ficha_de_Declaracao_Uso_IA_-_FECAP_-_Letícia.docx` |
| Gian Carlos Lemes Vieira | Contabilidade e Finanças (Entrega 2) | ChatGPT (GPT-6) | `Ficha_de_Declaracao_Uso_IA_-_FECAP_-_Gian.docx` |
| Said Sales de Sousa | Estatística Inferencial (Entrega 2) | Claude (Sonnet 5.5) | `Ficha_de_Declaracao_Uso_IA_-_FECAP_-_Said.docx` |
| Gabriel Vazquez Mamede Diniz | Engenharia de Software | Gemini (3.8) | `Ficha_de_Declara__o_de_Uso_de_IA.docx` |

---

## 2. Letícia Rodrigues da Silva: Ciência de Dados

- **Ferramenta utilizada:** Claude.
- **Versão/modelo:** Sonnet 5.5.
- **Disciplina / trabalho:** Projeto Interdisciplinar (PI), Ciência de Dados: Entrega 1 (coleta, descrição, exploração, seleção, limpeza, derivação, integração e formatação dos dados da CTI, em notebook no Colab e relatório) e Entrega 2 (script em Python e dashboard publicado na nuvem, com análise dos dados financeiros da CTI).
- **Finalidade de uso:** a ferramenta foi usada como apoio ao desenvolvimento técnico e à documentação. Auxiliou no planejamento das etapas de cada entrega, na escrita e revisão do código em Python (pandas, matplotlib, Streamlit e Plotly), na interpretação de erros, na verificação dos resultados contra os dados brutos e contra a planilha de validação da Contabilidade, e na redação e revisão do relatório da Entrega 1 e do README da Entrega 2. Também orientou os passos de publicação na Streamlit Cloud. As decisões de tratamento dos dados (isolamento do Ano 12, quarentena das linhas sem nome de conta, preservação e sinalização do Passivo Circulante, critério de ranking dos cenários) foram tomadas pelo grupo.
- **Prompts principais utilizados:**
  1. "Calcular média, mediana, moda, desvio-padrão, histogramas e boxplots e conferir se batem com a entrega de Estatística."
  2. "Ajudar na criação do ranking dos melhores e piores cenários pelo Resultado Líquido acumulado, com histogramas e boxplots de cada grupo."
  3. "Listar o que as entregas exigem e criar cronograma de desenvolvimento."
  4. "Ajudar na construção do dashboard em Streamlit."
  5. "Alinhar o dashboard ao dicionário e à planilha de validação da Contabilidade (painel financeiro, meta, sensibilidade, liquidez, custos, saldo de caixa e endividamento) e conferir os números."
- **Trechos ou entregas afetadas:** notebook da Entrega 1 e relatório; script `preparar_dados.py`; `app.py` do dashboard; `README.md`; e a documentação de fontes, fórmulas e limitações. A ferramenta apoiou a interpretação e a descrição dos resultados e das limitações da base.

---

## 3. Gian Carlos Lemes Vieira: Contabilidade e Finanças

- **Ferramenta utilizada:** ChatGPT (OpenAI).
- **Versão/modelo:** GPT-6.
- **Disciplina / trabalho:** Projeto Integrador (PI), Segunda Entrega; atividade de Contabilidade e Finanças: Dicionário e Planilha de Validação de KPIs, com análise dos dados financeiros da CTI.
- **Finalidade de uso:** a ferramenta foi utilizada como apoio, revisão e complementação da planilha de indicadores financeiros. Auxiliou na estruturação do dicionário de KPIs, na explicação dos indicadores, na organização de estatísticas e rankings, na elaboração/revisão de fórmulas e verificações de consistência e validação, além da documentação dos itens de DFC, capital de giro e DVA.
- **Prompts principais utilizados:**
  1. "Complete o Dicionário e a Planilha de Validação de KPIs com base nos arquivos concedidos. Facilitando a visualização de todos os dados concedidos."
  2. "Organize e simplifique a planilha de validação e o dicionário de KPIs para facilitar a análise por pessoas, mantendo os requisitos da entrega."
  3. "Revise a planilha para a pré-entrega, incluindo os indicadores de DFC, capital de giro, fluxo de caixa e DVA, calculando o que for possível com os dados disponíveis."
- **Trechos ou entregas afetadas:** planilha de Contabilidade e Finanças, especialmente as abas de Consistências, Validação dos Índices, Detalhamento e Painel Financeiro. A ferramenta também apoiou a interpretação e a descrição dos resultados e das limitações da base de dados. CGL, NCG e DVA completa foram identificados como não calculáveis com os campos disponíveis, e a DFC foi registrada como parcial, com base nas informações disponibilizadas.

## 4. Said Sales de Sousa: Estatística Inferencial

- **Ferramenta utilizada:** Claude.
- **Versão/modelo:** Sonnet 5.5.
- **Disciplina / trabalho:** Estatística Inferencial, Segunda Entrega; compreender a relação entre as variáveis de maneira a interpretar, avaliar e apresentar métricas, diagnósticos e registrar as limitações da análise.
- **Finalidade de uso:** a ferramenta foi utilizada como apoio, revisão e complementação dos scripts utilizados no Google Colab e no auxílio da documentação da segunda entrega.
- **Prompts principais utilizados:**
  1. "[print] esse script está apresentando problemas, me ajude a identificá-los e corrigi-los."
  2. "Facilite a visualização dos dados presentes nessa tabela."
  3. "Revise os scripts e a documentação para a entrega, incluindo as variáveis, tabelas e gráfico utilizados."
- **Trechos ou entregas afetadas:** documentação e scripts, especialmente na visualização e interpretação das contas-chave e no auxílio à produção dos códigos. Na documentação, a ferramenta foi usada para revisões e correções ortográficas.

## 5. Gabriel Vazquez Mamede Diniz: Engenharia de Software

- **Ferramenta utilizada:** Gemini.
- **Versão/modelo:** Gemini 3.8.
- **Disciplina / trabalho:** Engenharia de Software.
- **Finalidade de uso:** a ferramenta foi utilizada para estruturar uma versão inicial do documento com base na ideia desenvolvida pelo grupo, servindo como base para a elaboração do trabalho, bem como para a revisão textual e técnica da documentação.
- **Prompts principais utilizados:**
  1. "Com base na seguinte ideia e requisitos que desenvolvemos para o projeto de Engenharia de Software, estruture uma versão inicial da documentação técnica para servir como base de desenvolvimento."
  2. "Revise a documentação criada para a entrega de Engenharia de Software, aprimorando a clareza, a coesão textual, a padronização terminológica e a organização das seções, mantendo o conteúdo técnico original."
- **Trechos ou entregas afetadas:** entrega de Engenharia de Software, especialmente na revisão e estruturação da documentação criada.

---

## 6. Declaração

Cada integrante declara, em sua ficha individual, que o uso descrito está em conformidade com o *Guia para o Uso Responsável de Inteligência Artificial na FECAP* e que o conteúdo final é de sua plena responsabilidade autoral.
