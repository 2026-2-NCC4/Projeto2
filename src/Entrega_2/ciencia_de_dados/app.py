from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CTI - Planejamento Financeiro", layout="wide")

CAMINHO = Path(__file__).parent / "dados" / "processed" / "base_dashboard.csv"

# Link do repositório no GitHub (deixe vazio para ocultar)
REPOSITORIO = "https://github.com/2026-2-NCC4/Projeto2"

# Indicadores principais (barra lateral, cartões, gráficos)
NOMES_KPI = {
    "receita": "Receita",
    "resultado_operacional": "Resultado Operacional",
    "ebitda": "EBITDA",
    "resultado_liquido": "Resultado Líquido",
    "margem_operacional": "Margem Operacional",
    "margem_ebitda": "Margem EBITDA",
    "margem_liquida": "Margem Líquida",
    "geracao_caixa": "Geração de Caixa",
    "margem_caixa": "Margem de Caixa",
}
# Indicadores que dependem do sinal do Passivo Circulante (aba própria, com aviso)
NOMES_VERIFICAR = {
    "capital_giro_liquido": "Capital de Giro Líquido",
    "liquidez_corrente": "Liquidez Corrente",
}
NOMES_TODOS = {**NOMES_KPI, **NOMES_VERIFICAR}

GRUPOS = ["Todos", "Piores 10%", "Medianos (10%-90%)", "Melhores 10%"]

# (fator de escala, rótulo da unidade, formato do número)
UNIDADES = {
    "receita": (1e9, "R$ bi", ".2f"),
    "resultado_operacional": (1e9, "R$ bi", ".2f"),
    "ebitda": (1e9, "R$ bi", ".2f"),
    "resultado_liquido": (1e9, "R$ bi", ".2f"),
    "geracao_caixa": (1e9, "R$ bi", ".2f"),
    "capital_giro_liquido": (1e9, "R$ bi", ".2f"),
    "custos": (1e9, "R$ bi", ".2f"),
    "margem_operacional": (0.01, "%", ".1f"),
    "margem_ebitda": (0.01, "%", ".1f"),
    "margem_liquida": (0.01, "%", ".1f"),
    "margem_caixa": (0.01, "%", ".1f"),
    "liquidez_corrente": (1, "x", ".2f"),
}
CORES = {
    "Todos": "#1F2A24",
    "Piores 10%": "#C0392B",
    "Medianos (10%-90%)": "#2E75B6",
    "Melhores 10%": "#00543C",
}
CORES_MARGENS = {
    "margem_operacional": "#00543C",
    "margem_ebitda": "#2E75B6",
    "margem_liquida": "#E69F00",
    "margem_caixa": "#7B3294",
}

FORMULAS = [
    ("Receita", "Valor informado na DRE", "R$ bi", "DRE - Receita"),
    ("Resultado Operacional", "Valor informado na DRE (Receita + Tributos + Custos + Depreciação/Amortização)", "R$ bi", "DRE - Resultado Operacional"),
    ("EBITDA", "Valor informado na DRE", "R$ bi", "DRE - EBITDA"),
    ("Resultado Líquido", "Valor informado na DRE", "R$ bi", "DRE - Resultado Líquido"),
    ("Margem Operacional", "Resultado Operacional ÷ Receita (vazio se Receita ≤ 0)", "%", "DRE - Resultado Operacional e DRE - Receita"),
    ("Margem EBITDA", "EBITDA ÷ Receita (vazio se Receita ≤ 0)", "%", "DRE - EBITDA e DRE - Receita"),
    ("Margem Líquida", "Resultado Líquido ÷ Receita (vazio se Receita ≤ 0)", "%", "DRE - Resultado Líquido e DRE - Receita"),
    ("Geração de Caixa", "Valor informado no fluxo (= Saldo Final − Saldo Inicial)", "R$ bi", "FLU - Geração de Caixa"),
    ("Margem de Caixa", "Geração de Caixa ÷ Receita (vazio se Receita ≤ 0)", "%", "FLU - Geração de Caixa e DRE - Receita"),
    ("Capital de Giro Líquido (verificar)", "Ativo Circulante + Passivo Circulante (passivo armazenado com sinal negativo)", "R$ bi", "BAL - Ativo Circulante e BAL - Passivo Circulante"),
    ("Liquidez Corrente (verificar)", "Ativo Circulante ÷ (− Passivo Circulante)", "x", "BAL - Ativo Circulante e BAL - Passivo Circulante"),
]


@st.cache_data
def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(CAMINHO)


def br(numero: float, casas: int) -> str:
    """Formata no padrão brasileiro: 1.234,56."""
    return f"{numero:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_valor(kpi_id: str, v: float) -> str:
    fator, unidade, _ = UNIDADES[kpi_id]
    if unidade == "%":
        return f"{br(v / fator, 1)}%"
    if unidade == "x":
        return f"{br(v, 2)}x"
    return f"R$ {br(v / fator, 2)} bi"


def hex_para_rgba(cor: str, alfa: float) -> str:
    r, g, b = (int(cor[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def serie_media(base: pd.DataFrame, kpi_id: str) -> pd.Series:
    return base[base["kpi"] == kpi_id].set_index("ano")["media"].sort_index()


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
        title=f"{NOMES_TODOS[kpi_id]} no Ano {ano}: {estatistica.lower()} por grupo (barra de erro = P10 a P90)",
        yaxis=dict(title=unidade), xaxis=dict(title="Grupo de desempenho"),
        margin=dict(t=60, b=40), showlegend=False,
    )
    return fig


def grafico_margens(base, meta_pct):
    """Quatro margens por ano (média do grupo) e a linha da meta de margem operacional."""
    fig = go.Figure()
    for k, cor in CORES_MARGENS.items():
        s = serie_media(base, k)
        fig.add_trace(go.Scatter(
            x=s.index, y=s * 100, mode="lines+markers", name=NOMES_KPI[k],
            line=dict(color=cor, width=2.5), marker=dict(size=6),
            hovertemplate=f"Ano %{{x}}<br>{NOMES_KPI[k]}: %{{y:.1f}}%<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=[1, 12], y=[meta_pct, meta_pct], mode="lines",
        line=dict(color="#C0392B", dash="dash", width=2),
        name=f"Meta de margem operacional ({br(meta_pct, 0)}%)", hoverinfo="skip",
    ))
    fig.add_vline(
        x=12, line_dash="dot", line_color="#888",
        annotation_text="Ano 12 incompleto", annotation_position="top left",
    )
    fig.update_layout(
        title="Margens por ano (média dos cenários do grupo)",
        xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="%", zeroline=True),
        legend=dict(orientation="h", y=-0.2), margin=dict(t=60, b=40),
    )
    return fig


def cartao(coluna_estat, kpi_id, base):
    """Valor do último ano do filtro e variação em relação ao primeiro."""
    fator, unidade, _ = UNIDADES[kpi_id]
    serie = base[base["kpi"] == kpi_id].sort_values("ano")
    primeiro, ultimo = serie.iloc[0], serie.iloc[-1]
    v0, v1 = primeiro[coluna_estat], ultimo[coluna_estat]
    if unidade == "%":
        valor = f"{br(v1 / fator, 1)}%"
        delta = f"{br((v1 - v0) / fator, 1)} p.p."
    elif kpi_id == "geracao_caixa":  # pode mudar de sinal: variação absoluta
        valor = f"R$ {br(v1 / fator, 2)} bi"
        delta = f"{br((v1 - v0) / fator, 2)} bi"
    else:
        valor = f"R$ {br(v1 / fator, 2)} bi"
        delta = f"{br((v1 / v0 - 1) * 100, 1)}%"
    sinal = "+" if (v1 - v0) > 0 else ""
    st.metric(NOMES_KPI[kpi_id], valor, f"{sinal}{delta}")


df = carregar_dados()

st.title("CTI - Plataforma Analítica de Planejamento Financeiro")
st.caption("Projeção de 12 anos em 1.200 cenários simulados. Fonte: CTI (agosto/2026).")
st.markdown(
    "**9 indicadores** · **filtros** na barra lateral (indicador, grupo de desempenho, anos, Ano 12, estatística) · "
    "**comparação** entre Piores, Medianos e Melhores · **fórmulas, fontes e limitações** na aba *Metodologia*."
)
with st.expander("Sobre este painel"):
    st.markdown(
        "- **Objetivo:** apoiar decisões estratégicas e operacionais a partir da projeção financeira da CTI.\n"
        "- **Indicadores:** Receita, Resultado Operacional, EBITDA, Resultado Líquido, Margem Operacional, Margem EBITDA, "
        "Margem Líquida, Geração de Caixa e Margem de Caixa. Capital de Giro e Liquidez Corrente ficam em aba própria, "
        "com aviso, porque dependem do sinal do Passivo Circulante.\n"
        "- **Abas:** *Painel financeiro* (margens, meta, ticket e simulação de sensibilidade), *Evolução*, "
        "*Comparação entre grupos*, *Liquidez e Capital de Giro* e *Metodologia*.\n"
        "- **Grupos de desempenho:** os cenários são divididos pelo Resultado Líquido acumulado nos 12 anos "
        "(Piores 10%, Medianos e Melhores 10%).\n"
        "- **Atenção:** valores são projeções simuladas, e o Ano 12 é incompleto."
    )

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

(aba_painel, aba_evolucao, aba_comparacao, aba_liquidez, aba_metodologia) = st.tabs(
    ["Painel financeiro", "Evolução", "Comparação entre grupos",
     "Liquidez e Capital de Giro", "Metodologia"]
)

# ---------- Aba 1: painel financeiro (margens, meta, ticket, sensibilidade) ----------
with aba_painel:
    st.subheader("Painel financeiro operacional")
    grupo_painel = st.selectbox("Grupo de cenários", GRUPOS, key="grupo_painel")
    base_painel = df[df["grupo_desempenho"] == grupo_painel]

    # Cartões: média dos 12 anos (mesma leitura da planilha de validação da Contabilidade)
    st.caption("Média dos 12 anos e dos cenários do grupo (inclui o Ano 12, que é incompleto).")
    cartoes = [
        ("Receita média", "receita"),
        ("Resultado operacional médio", "resultado_operacional"),
        ("Margem operacional média", "margem_operacional"),
        ("Margem EBITDA média", "margem_ebitda"),
        ("Margem líquida média", "margem_liquida"),
    ]
    for coluna_st, (rotulo, k) in zip(st.columns(5), cartoes):
        coluna_st.metric(rotulo, fmt_valor(k, serie_media(base_painel, k).mean()))

    # Evolução anual com meta
    st.subheader("Evolução anual e meta")
    st.caption("Valores médios dos cenários do grupo em cada ano.")
    meta = st.number_input(
        "Meta de margem operacional (%)", min_value=0.0, max_value=100.0,
        value=60.0, step=1.0,
        help="Meta indicativa. O padrão (60%) é o da planilha de validação da Contabilidade.",
    )
    s_mop = serie_media(base_painel, "margem_operacional")
    atingida = s_mop * 100 >= meta
    tabela = pd.DataFrame({
        "Ano": [f"Ano {a}" + (" (incompleto)" if a == 12 else "") for a in s_mop.index],
        "Receita (R$ bi)": serie_media(base_painel, "receita") / 1e9,
        "Resultado operacional (R$ bi)": serie_media(base_painel, "resultado_operacional") / 1e9,
        "EBITDA (R$ bi)": serie_media(base_painel, "ebitda") / 1e9,
        "Resultado líquido (R$ bi)": serie_media(base_painel, "resultado_liquido") / 1e9,
        "Margem operacional (%)": s_mop * 100,
        "Margem EBITDA (%)": serie_media(base_painel, "margem_ebitda") * 100,
        "Margem líquida (%)": serie_media(base_painel, "margem_liquida") * 100,
        "Margem de caixa (%)": serie_media(base_painel, "margem_caixa") * 100,
        "Meta (%)": meta,
        "Situação da meta": ["Meta atingida" if x else "Abaixo da meta" for x in atingida],
    }).reset_index(drop=True)
    st.dataframe(
        tabela, hide_index=True, width="stretch", height=460,
        column_config={
            c: st.column_config.NumberColumn(c, format="%.2f")
            for c in tabela.columns if "(R$ bi)" in c
        } | {
            c: st.column_config.NumberColumn(c, format="%.1f")
            for c in tabela.columns if "(%)" in c
        },
    )
    st.caption(
        f"Meta de {br(meta, 0)}% atingida em {int(atingida.sum())} dos 12 anos "
        "(a margem de caixa pode ser negativa quando o caixa diminui no ano)."
    )
    st.plotly_chart(grafico_margens(base_painel, meta), width="stretch")

    # Ticket médio
    st.subheader("Ticket médio")
    st.info(
        "**Não calculável com esta base.** Ela traz receita e resultados financeiros, mas não a "
        "quantidade de vendas, pedidos ou transações. Para calcular o ticket médio seria preciso uma "
        "medida de volume, aplicando Receita ÷ Quantidade de transações."
    )

    # Sensibilidade
    st.subheader("Análise de sensibilidade (simulação simplificada)")
    st.caption(
        "Altere os parâmetros para ver o impacto sobre a receita, os custos e a margem operacional. "
        f"Base de referência: médias dos 12 anos do grupo *{grupo_painel}*."
    )
    c1, c2, c3 = st.columns(3)
    desconto = c1.slider("Desconto aplicado (%)", 0, 30, 5) / 100
    aumento_custos = c2.slider("Aumento de custos (%)", 0, 30, 3) / 100
    volume = c3.slider("Variação de volume (%)", -30, 30, 10) / 100

    rec_base = serie_media(base_painel, "receita").mean()
    custos_base = abs(serie_media(base_painel, "custos").mean())  # magnitude
    resop_base = serie_media(base_painel, "resultado_operacional").mean()

    rec_sim = rec_base * (1 + volume) * (1 - desconto)
    custos_sim = custos_base * (1 + volume) * (1 + aumento_custos)
    resop_sim = (
        resop_base * (1 + volume)
        - rec_base * (1 + volume) * desconto
        - custos_base * (1 + volume) * aumento_custos
    )
    # Referência igual à da planilha da Contabilidade: média das margens operacionais anuais
    mop_base = serie_media(base_painel, "margem_operacional").mean()
    mop_sim = resop_sim / rec_sim if rec_sim else 0.0

    def pct(novo, velho):
        return f"{br((novo / velho - 1) * 100, 1)}%"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Receita ajustada", f"R$ {br(rec_sim / 1e9, 2)} bi", pct(rec_sim, rec_base))
    m2.metric("Custos ajustados", f"R$ {br(custos_sim / 1e9, 2)} bi", pct(custos_sim, custos_base),
              delta_color="inverse")
    m3.metric("Resultado operacional estimado", f"R$ {br(resop_sim / 1e9, 2)} bi", pct(resop_sim, resop_base))
    m4.metric("Margem operacional estimada", f"{br(mop_sim * 100, 1)}%",
              f"{br((mop_sim - mop_base) * 100, 1)} p.p. vs. base ({br(mop_base * 100, 1)}%)")
    st.caption(
        "**Premissas:** o desconto reduz a receita; a variação de volume altera receita, custos e demais itens "
        "proporcionalmente; o aumento de custos eleva a magnitude dos custos. O resultado é uma aproximação "
        "com base nas médias agregadas e não substitui a DRE nem uma projeção oficial. A margem estimada é "
        "Resultado operacional ÷ Receita ajustados; a referência (base) é a média das margens operacionais anuais, "
        "por isso, com os parâmetros zerados, a estimativa fica um pouco acima da base (diferença de agregação)."
    )

# ---------- Aba 2: cartões + gráfico de evolução ----------
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
            ids = list(NOMES_KPI)
            for i in range(0, len(ids), 3):
                for coluna_st, k in zip(st.columns(3), ids[i : i + 3]):
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

# ---------- Aba 3: comparação entre grupos em um ano ----------
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

# ---------- Aba 4: liquidez e capital de giro (dependem do sinal do Passivo) ----------
with aba_liquidez:
    st.warning(
        "**Verificar antes de interpretar.** A base guarda os passivos com sinal negativo "
        "(Total do Ativo + Total do Passivo = 0), então **Liquidez Corrente = Ativo Circulante ÷ (−Passivo Circulante)** "
        "e **Capital de Giro = Ativo Circulante + Passivo Circulante**. Nos Anos 1 a 4 todos os cenários seguem essa regra; "
        "nos Anos 5 a 11 quase nenhum (o Passivo Circulante fica positivo em 99% a 100% dos cenários), o que "
        "gera liquidez negativa; no Ano 12 cerca de metade. A CTI não confirmou a convenção de sinal, "
        "e os valores originais foram preservados, sem correção."
    )
    esq, dir_ = st.columns(2)
    kpi_iso = esq.radio(
        "Indicador", list(NOMES_VERIFICAR),
        format_func=lambda k: NOMES_VERIFICAR[k], horizontal=True,
    )
    estat_iso = dir_.radio(
        "Estatística (aba de liquidez)", ["Mediana", "Média"], horizontal=True,
        help="Prefira a mediana: a média da Liquidez Corrente é distorcida por valores extremos "
             "(de −31.263 a 1.488 na base).",
    )
    col_iso = "mediana" if estat_iso == "Mediana" else "media"

    dados_iso = df[
        (df["kpi"] == kpi_iso) & df["grupo_desempenho"].isin(grupos) & dentro_do_intervalo
    ]
    if dados_iso.empty:
        st.info("Sem dados para este filtro. Escolha ao menos um grupo de desempenho.")
    else:
        st.plotly_chart(
            montar_grafico(dados_iso, col_iso, kpi_iso, estat_iso, incluir_ano12),
            width="stretch",
        )
        st.subheader("Cenários que seguem a regra da base (Passivo Circulante negativo)")
        tabela_n = dados_iso.pivot(index="ano", columns="grupo_desempenho", values="n_passivo_negativo")
        st.dataframe(tabela_n[[g for g in GRUPOS if g in tabela_n.columns]])
        st.caption(
            "Número de cenários com Passivo Circulante negativo em cada ano. Cada grupo tem, no total, "
            "1.200 (Todos), 133 (Piores), 947 (Medianos) e 120 (Melhores) cenários. "
            "Onde o número é baixo, o indicador está marcado como *verificar*."
        )

# ---------- Aba 5: metodologia ----------
with aba_metodologia:
    st.header("Metodologia")

    st.subheader("Fonte dos dados")
    st.markdown(
        "- **Origem:** demonstrativo financeiro projetado fornecido pela CTI "
        "(`Demonstrativo_Fecap_v3.csv`, agosto/2026), com 12 anos de projeção em 1.200 cenários simulados.\n"
        "- **Tratamento:** o script `preparar_dados.py` (Projeto Interdisciplinar) seleciona 14 contas, "
        "limpa e integra os dados e calcula os indicadores. O painel lê apenas a base já agregada "
        "(`dados/processed/base_dashboard.csv`), sem dados cenário a cenário.\n"
        "- **Indicadores e fórmulas** seguem o dicionário de KPIs da Contabilidade (equipe BeHolders).\n"
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
        "- **Margens** usam a razão sobre a Receita; **p.p.** nos cartões significa pontos percentuais.\n"
        "- **Meta:** a meta de 60% para a margem operacional é indicativa e pode ser alterada no painel financeiro.\n"
        "- **Simulação de sensibilidade:** aproximação sobre as médias agregadas, com as premissas descritas na aba."
    )

    st.subheader("Limitações")
    st.markdown(
        "- **Ano 12 incompleto:** o balanço tem cobertura reduzida e a margem líquida destoa dos demais anos "
        "(a Margem de Caixa também). Por isso ele fica fora por padrão nos filtros e é sinalizado no Painel financeiro.\n"
        "- **Sinal do Passivo Circulante:** a base guarda passivos com sinal negativo, mas o Passivo Circulante fica positivo "
        "em quase todos os cenários dos Anos 5 a 11. A CTI não confirmou a convenção, então Liquidez Corrente e Capital de Giro "
        "ficam em aba própria, marcados como *verificar*, com os valores preservados.\n"
        "- **Ticket médio:** não calculável, pois a base não tem quantidade de vendas ou transações.\n"
        "- **Linhas sem nome de conta:** 43.200 das 1.002.000 linhas do arquivo original (4,31%) ficaram em quarentena e fora da análise.\n"
        "- **Margens muito altas** (EBITDA entre 75% e 97% da receita) são características das projeções e não foram validadas com a CTI.\n"
        "- **Geração de Caixa** inclui investimentos e distribuições aos acionistas; não é geração operacional de caixa. "
        "Não há abertura da DFC por atividade, nem dados para Necessidade de Capital de Giro ou DVA."
    )

    st.subheader("Verificações realizadas")
    st.markdown(
        "- Saldo Final de um ano igual ao Saldo Inicial do ano seguinte, no mesmo cenário (13.200 pares, diferença máxima 0).\n"
        "- Geração de Caixa igual a Saldo Final − Saldo Inicial (diferença máxima de R$ 0,00002).\n"
        "- Total do Ativo + Total do Passivo ≈ 0 em todas as linhas (diferença máxima de R$ 0,03).\n"
        "- Base integrada com 14.400 linhas (1.200 cenários × 12 anos) e sem valores ausentes nas 14 contas selecionadas.\n"
        "- Médias anuais, margens, liquidez e simulação conferidas contra a planilha de validação da Contabilidade "
        "(diferença relativa abaixo de 10⁻¹³)."
    )
