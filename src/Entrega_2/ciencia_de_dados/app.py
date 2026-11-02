from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CTI - Planejamento Financeiro", layout="wide")

CAMINHO = Path(__file__).parent / "dados" / "processed" / "base_dashboard.csv"

NOMES_KPI = {
    "receita": "Receita",
    "ebitda": "EBITDA",
    "resultado_liquido": "Resultado Líquido",
    "margem_ebitda": "Margem EBITDA",
    "margem_liquida": "Margem Líquida",
    "variacao_caixa": "Variação de Caixa",
}
NOMES_ISOLADOS = {
    "capital_giro_liquido": "Capital de Giro Líquido",
    "liquidez_corrente": "Liquidez Corrente",
}
NOMES_TODOS = {**NOMES_KPI, **NOMES_ISOLADOS}
# Preencha com o link do repositório no GitHub (deixe vazio para ocultar)
REPOSITORIO = ""

FORMULAS = [
    ("Receita", "DRE - Receita", "R$ bi", "DRE - Receita"),
    ("EBITDA", "DRE - EBITDA", "R$ bi", "DRE - EBITDA"),
    ("Resultado Líquido", "DRE - Resultado Líquido", "R$ bi", "DRE - Resultado Líquido"),
    ("Margem EBITDA", "EBITDA ÷ Receita (vazio se Receita ≤ 0)", "%", "DRE - EBITDA e DRE - Receita"),
    ("Margem Líquida", "Resultado Líquido ÷ Receita (vazio se Receita ≤ 0)", "%", "DRE - Resultado Líquido e DRE - Receita"),
    ("Variação de Caixa", "Saldo Final − Saldo Inicial", "R$ bi", "FLU - Saldo Final e FLU - Saldo Inicial"),
    ("Capital de Giro Líquido (isolado)", "Ativo Circulante − Passivo Circulante", "R$ bi", "BAL - Ativo Circulante e BAL - Passivo Circulante"),
    ("Liquidez Corrente (isolado)", "Ativo Circulante ÷ Passivo Circulante (vazio se Passivo ≤ 0)", "x", "BAL - Ativo Circulante e BAL - Passivo Circulante"),
]
GRUPOS = ["Todos", "Piores 10%", "Medianos (10%-90%)", "Melhores 10%"]

# (fator de escala, rótulo da unidade, formato do número)
UNIDADES = {
    "receita": (1e9, "R$ bi", ".2f"),
    "ebitda": (1e9, "R$ bi", ".2f"),
    "resultado_liquido": (1e9, "R$ bi", ".2f"),
    "variacao_caixa": (1e9, "R$ bi", ".2f"),
    "margem_ebitda": (0.01, "%", ".1f"),
    "margem_liquida": (0.01, "%", ".1f"),
    "capital_giro_liquido": (1e9, "R$ bi", ".2f"),
    "liquidez_corrente": (1, "x", ".2f"),
}
CORES = {
    "Todos": "#1F2A24",
    "Piores 10%": "#C0392B",
    "Medianos (10%-90%)": "#2E75B6",
    "Melhores 10%": "#00543C",
}


def hex_para_rgba(cor: str, alfa: float) -> str:
    r, g, b = (int(cor[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def montar_grafico(dados, coluna, kpi, estatistica, mostrar_ano12):
    fator, unidade, formato = UNIDADES[kpi]
    fig = go.Figure()
    for grupo in GRUPOS:
        g = dados[dados["grupo_desempenho"] == grupo].sort_values("ano")
        if g.empty:
            continue
        cor = CORES[grupo]
        # Faixa P10-P90: borda inferior invisível + borda superior preenchida
        fig.add_trace(go.Scatter(
            x=g["ano"], y=g["p10"] / fator, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=g["ano"], y=g["p90"] / fator, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor=hex_para_rgba(cor, 0.15),
            showlegend=False, hoverinfo="skip",
        ))
        # Linha principal (média ou mediana)
        fig.add_trace(go.Scatter(
            x=g["ano"], y=g[coluna] / fator, mode="lines+markers", name=grupo,
            line=dict(color=cor, width=2.5), marker=dict(size=6),
            customdata=g[["p10", "p90"]].to_numpy() / fator,
            hovertemplate=(
                f"Ano %{{x}}<br>{estatistica}: %{{y:{formato}}} {unidade}"
                f"<br>P10: %{{customdata[0]:{formato}}} | P90: %{{customdata[1]:{formato}}}"
                "<extra>" + grupo + "</extra>"
            ),
        ))
    if mostrar_ano12:
        fig.add_vline(
            x=12, line_dash="dash", line_color="#888",
            annotation_text="Ano 12 incompleto", annotation_position="top left",
        )
    fig.update_layout(
        title=f"{NOMES_TODOS[kpi]}: {estatistica.lower()} por ano (faixa = P10 a P90 dos cenários)",
        xaxis=dict(title="Ano", dtick=1),
        yaxis=dict(title=unidade, zeroline=False),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=60, b=40), hovermode="closest",
    )
    return fig


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(CAMINHO)


df = carregar_dados()

st.title("CTI - Plataforma Analítica de Planejamento Financeiro")
st.caption("Projeção de 12 anos em 1.200 cenários simulados. Fonte: CTI (agosto/2026).")

# ---------- Filtros (barra lateral) ----------
st.sidebar.header("Filtros")

kpi = st.sidebar.selectbox(
    "Indicador", list(NOMES_KPI), format_func=lambda k: NOMES_KPI[k]
)
grupos = st.sidebar.multiselect("Grupo de desempenho", GRUPOS, default=["Todos"])
anos = st.sidebar.slider("Intervalo de anos", 1, 11, (1, 11))
incluir_ano12 = st.sidebar.checkbox("Incluir Ano 12 (incompleto)", value=False)
estatistica = st.sidebar.radio("Estatística", ["Média", "Mediana"])

# ---------- Aplicação dos filtros ----------
coluna = "media" if estatistica == "Média" else "mediana"
dentro_do_intervalo = df["ano"].between(anos[0], anos[1])
if incluir_ano12:
    dentro_do_intervalo |= df["ano"] == 12

filtrado = df[
    (df["kpi"] == kpi) & df["grupo_desempenho"].isin(grupos) & dentro_do_intervalo
]

def br(numero: float, casas: int) -> str:
    """Formata no padrão brasileiro: 1.234,56."""
    return f"{numero:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cartao(coluna_estat, kpi_id, base):
    """Valor do último ano do filtro e variação em relação ao primeiro."""
    fator, unidade, _ = UNIDADES[kpi_id]
    serie = base[base["kpi"] == kpi_id].sort_values("ano")
    primeiro, ultimo = serie.iloc[0], serie.iloc[-1]
    v0, v1 = primeiro[coluna_estat], ultimo[coluna_estat]
    if unidade == "%":
        valor = f"{br(v1 / fator, 1)}%"
        delta = f"{br((v1 - v0) / fator, 1)} p.p."
    elif kpi_id == "variacao_caixa":  # pode mudar de sinal: variação absoluta
        valor = f"R$ {br(v1 / fator, 2)} bi"
        delta = f"{br((v1 - v0) / fator, 2)} bi"
    else:
        valor = f"R$ {br(v1 / fator, 2)} bi"
        delta = f"{br((v1 / v0 - 1) * 100, 1)}%"
    sinal = "+" if (v1 - v0) > 0 else ""
    st.metric(NOMES_KPI[kpi_id], valor, f"{sinal}{delta}")


def fmt_valor(kpi_id: str, v: float) -> str:
    fator, unidade, _ = UNIDADES[kpi_id]
    if unidade == "%":
        return f"{br(v / fator, 1)}%"
    return f"R$ {br(v / fator, 2)} bi"


def grafico_comparacao(dados, kpi_id, coluna_estat, estatistica, ano):
    fator, unidade, formato = UNIDADES[kpi_id]
    dados = dados.set_index("grupo_desempenho").reindex(GRUPOS).dropna(subset=[coluna_estat])
    valores = dados[coluna_estat] / fator
    fig = go.Figure(go.Bar(
        x=dados.index, y=valores,
        marker_color=[CORES[g] for g in dados.index],
        error_y=dict(
            type="data", symmetric=False,
            array=(dados["p90"] / fator - valores),
            arrayminus=(valores - dados["p10"] / fator),
        ),
        customdata=dados[["p10", "p90"]].to_numpy() / fator,
        hovertemplate=(
            f"{estatistica}: %{{y:{formato}}} {unidade}"
            f"<br>P10: %{{customdata[0]:{formato}}} | P90: %{{customdata[1]:{formato}}}"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=f"{NOMES_KPI[kpi_id]} no Ano {ano}: {estatistica.lower()} por grupo (barra de erro = P10 a P90)",
        yaxis=dict(title=unidade), xaxis=dict(title="Grupo de desempenho"),
        margin=dict(t=60, b=40), showlegend=False,
    )
    return fig


aba_evolucao, aba_comparacao, aba_liquidez, aba_metodologia = st.tabs(
    ["Evolução", "Comparação entre grupos", "Liquidez (isolado)", "Metodologia"]
)

# ---------- Aba 1: cartões + gráfico de evolução ----------
with aba_evolucao:
    if grupos:
        grupo_cartoes = next(g for g in GRUPOS if g in grupos)
        base_cartoes = df[(df["grupo_desempenho"] == grupo_cartoes) & dentro_do_intervalo]
        if not base_cartoes.empty:
            a0, a1 = base_cartoes["ano"].min(), base_cartoes["ano"].max()
            st.caption(
                f"Indicadores do grupo **{grupo_cartoes}**: valor do Ano {a1} "
                f"({estatistica.lower()}) e variação contra o Ano {a0}."
            )
            for linha in (list(NOMES_KPI)[:3], list(NOMES_KPI)[3:]):
                for coluna_st, k in zip(st.columns(3), linha):
                    with coluna_st:
                        cartao(coluna, k, base_cartoes)

    st.subheader(f"{NOMES_KPI[kpi]} - {estatistica.lower()} por ano")

    if filtrado.empty:
        st.info("Sem dados para este filtro. Escolha ao menos um grupo de desempenho.")
    else:
        st.plotly_chart(
            montar_grafico(filtrado, coluna, kpi, estatistica, incluir_ano12),
            width="stretch",
        )
        with st.expander("Ver tabela de dados"):
            st.dataframe(
                filtrado[["grupo_desempenho", "ano", coluna, "p10", "p90"]],
                hide_index=True,
            )

# ---------- Aba 2: comparação entre grupos em um ano ----------
with aba_comparacao:
    anos_disponiveis = list(range(1, 12)) + ([12] if incluir_ano12 else [])
    ano_escolhido = st.selectbox("Ano", anos_disponiveis, index=len(anos_disponiveis) - 1)
    if ano_escolhido == 12:
        st.warning("O Ano 12 é incompleto (balanço com cobertura reduzida); interprete com cautela.")

    do_ano = df[df["ano"] == ano_escolhido]
    st.plotly_chart(
        grafico_comparacao(do_ano[do_ano["kpi"] == kpi], kpi, coluna, estatistica, ano_escolhido),
        width="stretch",
    )

    st.subheader(f"Todos os indicadores no Ano {ano_escolhido} ({estatistica.lower()})")
    linhas = {}
    for k in NOMES_KPI:
        d = do_ano[do_ano["kpi"] == k].set_index("grupo_desempenho")[coluna]
        linhas[NOMES_KPI[k]] = {g: fmt_valor(k, d[g]) for g in GRUPOS if g in d.index}
    st.dataframe(pd.DataFrame(linhas).T[GRUPOS])

# ---------- Aba 3: indicadores isolados (dependem do Passivo Circulante) ----------
with aba_liquidez:
    st.warning(
        "**Indicadores isolados - não interpretar como liquidez real.** "
        "Capital de Giro e Liquidez Corrente dependem do Passivo Circulante, cujo sinal "
        "não foi confirmado pela CTI: ele é negativo em 100% dos cenários nos Anos 1 a 4, "
        "quase nunca negativo nos Anos 5 a 11 (0,9% a 0,1%) e negativo em 50,4% no Ano 12. "
        "Por isso a Liquidez Corrente só é calculada quando o Passivo é positivo "
        "(sem dados nos Anos 1 a 4). Os valores originais foram preservados, sem correção."
    )
    esq, dir_ = st.columns(2)
    kpi_iso = esq.radio(
        "Indicador isolado", list(NOMES_ISOLADOS),
        format_func=lambda k: NOMES_ISOLADOS[k], horizontal=True,
    )
    estat_iso = dir_.radio(
        "Estatística (aba de liquidez)", ["Mediana", "Média"], horizontal=True,
        help="Para a Liquidez Corrente, prefira a mediana: a média é distorcida quando o Passivo fica perto de zero.",
    )
    col_iso = "mediana" if estat_iso == "Mediana" else "media"

    dados_iso = df[
        (df["kpi"] == kpi_iso) & df["grupo_desempenho"].isin(grupos) & dentro_do_intervalo
    ]
    if dados_iso.empty:
        st.info("Sem dados para este filtro. Escolha ao menos um grupo de desempenho.")
    else:
        sem_dados = sorted(dados_iso.loc[dados_iso["n_validos"] == 0, "ano"].unique())
        if sem_dados:
            st.info("Sem dados válidos nos Anos: " + ", ".join(str(a) for a in sem_dados) + ".")
        st.plotly_chart(
            montar_grafico(dados_iso, col_iso, kpi_iso, estat_iso, incluir_ano12),
            width="stretch",
        )
        st.subheader("Cenários com valor calculável (n_validos)")
        tabela_n = dados_iso.pivot(index="ano", columns="grupo_desempenho", values="n_validos")
        st.dataframe(tabela_n[[g for g in GRUPOS if g in tabela_n.columns]])
        st.caption("Cada grupo tem, no total, 1.200 (Todos), 133 (Piores), 947 (Medianos) e 120 (Melhores) cenários.")

# ---------- Aba 4: metodologia ----------
with aba_metodologia:
    st.header("Metodologia")

    st.subheader("Fonte dos dados")
    st.markdown(
        "- **Origem:** demonstrativo financeiro projetado fornecido pela CTI "
        "(`Demonstrativo_Fecap_v3.csv`, agosto/2026), com 12 anos de projeção em 1.200 cenários simulados.\n"
        "- **Tratamento:** o script `preparar_dados.py` (Projeto Interdisciplinar, Entrega 1) seleciona 10 contas, "
        "limpa e integra os dados e calcula os indicadores. O painel lê apenas a base já agregada "
        "(`dados/processed/base_dashboard.csv`), sem dados cenário a cenário.\n"
        "- **Valores:** projeções simuladas, não dados realizados."
    )
    if REPOSITORIO:
        st.markdown(f"- **Código e documentação de execução:** [{REPOSITORIO}]({REPOSITORIO})")

    st.subheader("Indicadores e fórmulas")
    st.dataframe(
        pd.DataFrame(FORMULAS, columns=["Indicador", "Fórmula", "Unidade", "Conta de origem"]),
        hide_index=True,
    )

    st.subheader("Como ler o painel")
    st.markdown(
        "- **Média, mediana, P10 e P90** são calculadas entre os cenários de cada grupo, ano a ano. "
        "A faixa sombreada dos gráficos vai do P10 ao P90 (80% dos cenários).\n"
        "- **Grupos de desempenho:** cada cenário é classificado pelo **Resultado Líquido acumulado nos 12 anos**. "
        "*Piores 10%* (133 cenários) ficam abaixo de R$ 38,57 bi; *Melhores 10%* (120) ficam acima de R$ 41,02 bi; "
        "*Medianos* (947) estão entre os dois. O cenário é uma trajetória: ele não muda de grupo de um ano para o outro. "
        "*Todos* reúne os 1.200 cenários.\n"
        "- **Margens** usam a razão sobre a Receita; **p.p.** nos cartões significa pontos percentuais."
    )

    st.subheader("Limitações")
    st.markdown(
        "- **Ano 12 incompleto:** o balanço tem cobertura reduzida e a margem líquida destoa dos demais anos. "
        "Por isso ele fica fora por padrão e só entra pela opção da barra lateral.\n"
        "- **Passivo Circulante com sinal inconsistente:** negativo em 100% dos cenários nos Anos 1 a 4 e quase nunca nos Anos 5 a 11. "
        "A CTI não confirmou a convenção, então Capital de Giro e Liquidez Corrente ficam isolados na aba própria. "
        "Os valores foram preservados, sem correção.\n"
        "- **Linhas sem nome de conta:** 43.200 das 1.002.000 linhas do arquivo original (4,31%) ficaram em quarentena e fora da análise.\n"
        "- **Margens muito altas** (EBITDA entre 75% e 97% da receita) são características das projeções e não foram validadas com a CTI.\n"
        "- **Variação de Caixa** inclui investimentos e distribuições aos acionistas; não é geração operacional de caixa."
    )

    st.subheader("Verificações realizadas")
    st.markdown(
        "- Saldo Final de um ano igual ao Saldo Inicial do ano seguinte, no mesmo cenário (13.200 pares, diferença máxima 0).\n"
        "- Base integrada com 14.400 linhas (1.200 cenários × 12 anos) e sem valores ausentes nas 10 contas selecionadas."
    )
