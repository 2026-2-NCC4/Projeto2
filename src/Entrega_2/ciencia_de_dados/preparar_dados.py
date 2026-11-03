"""
preparar_dados.py
Pipeline reprodutivel de preparacao de dados - PI Ciencia de Dados (CTI Global).

Le o CSV bruto da CTI e gera:
  staging/linhas_nao_identificadas.csv  -> linhas sem nome de conta (quarentena)
  processed/base_analitica.csv          -> 1 linha por (ano, cenario), uso local
  processed/base_dashboard.csv          -> base AGREGADA, e a que alimenta o dashboard
  processed/log_qualidade.json          -> registro das checagens e transformacoes

Uso:
  python preparar_dados.py --entrada Demonstrativo_Fecap_v3.csv --saida dados

Decisoes de tratamento:
  1. Linhas sem conta: ficam em quarentena, fora da base analitica.
  2. Indicadores e formulas seguem o dicionario de KPIs da Contabilidade (BeHolders).
  3. Passivo Circulante: a base armazena passivos com sinal NEGATIVO (Total do Ativo +
     Total do Passivo = 0). Por isso Liquidez Corrente = Ativo Circulante / (-Passivo
     Circulante) e Capital de Giro Liquido = Ativo Circulante + Passivo Circulante.
     Ha linhas com Passivo Circulante positivo (Anos 5-11 quase todas); elas sao
     preservadas, nao corrigidas, e ficam sinalizadas como 'verificar'. A CTI nao
     confirmou a convencao de sinal.
  4. Ano 12: marcado com ano_isolado=True (cobertura reduzida do balanco e margem
     liquida destoante). O painel o exibe com aviso de ano incompleto.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CONTAS = [
    # Balanco
    "BAL - Ativo Circulante", "BAL - Passivo Circulante",
    "BAL - Total do Ativo", "BAL - Total do Passivo",
    # Fluxo de caixa
    "FLU - Saldo Inicial", "FLU - Saldo Final", "FLU - Geração de Caixa",
    "FLU - Investimentos", "FLU - Distribuição para Acionista",
    # DRE
    "DRE - Receita", "DRE - Custos", "DRE - Resultado Operacional",
    "DRE - EBITDA", "DRE - Resultado Líquido",
]

KPIS_PRINCIPAIS = [
    "receita", "resultado_operacional", "ebitda", "resultado_liquido",
    "margem_operacional", "margem_ebitda", "margem_liquida",
    "geracao_caixa", "margem_caixa",
]
KPIS_VERIFICAR = ["capital_giro_liquido", "liquidez_corrente"]
KPIS_AUXILIARES = ["custos"]  # usado pelo simulador de sensibilidade (valor com o sinal da base)

ANO_ISOLADO = 12


def carregar_raw(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(
        caminho, sep=";", encoding="latin-1", decimal=",", thousands=".",
        quotechar='"', header=None, names=["ano", "cenario", "conta", "valor"],
    )


def separar_quarentena(df_raw: pd.DataFrame):
    mask = df_raw["conta"].isna()
    return df_raw[mask].copy(), df_raw[~mask].copy()


def selecionar_e_limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["conta"] = df["conta"].str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[df["conta"].isin(CONTAS)].copy()
    df["ano"] = df["ano"].str.extract(r"(\d+)").astype(int)
    return df


def integrar(df: pd.DataFrame) -> pd.DataFrame:
    largo = df.pivot_table(index=["ano", "cenario"], columns="conta", values="valor")
    largo = largo.reset_index()
    largo.columns.name = None
    return largo.sort_values(["cenario", "ano"]).reset_index(drop=True)


def derivar(largo: pd.DataFrame) -> pd.DataFrame:
    d = largo.copy()
    rec = d["DRE - Receita"]

    # Resultados (valores informados pela CTI)
    d["receita"] = rec
    d["custos"] = d["DRE - Custos"]
    d["resultado_operacional"] = d["DRE - Resultado Operacional"]
    d["ebitda"] = d["DRE - EBITDA"]
    d["resultado_liquido"] = d["DRE - Resultado Líquido"]
    d["geracao_caixa"] = d["FLU - Geração de Caixa"]

    # Margens (denominador: receita > 0)
    d["margem_operacional"] = np.where(rec > 0, d["DRE - Resultado Operacional"] / rec, np.nan)
    d["margem_ebitda"] = np.where(rec > 0, d["DRE - EBITDA"] / rec, np.nan)
    d["margem_liquida"] = np.where(rec > 0, d["DRE - Resultado Líquido"] / rec, np.nan)
    d["margem_caixa"] = np.where(rec > 0, d["FLU - Geração de Caixa"] / rec, np.nan)

    # Liquidez e capital de giro: a base guarda passivos com sinal negativo
    ac, pc = d["BAL - Ativo Circulante"], d["BAL - Passivo Circulante"]
    d["capital_giro_liquido"] = ac + pc
    d["liquidez_corrente"] = np.where(pc != 0, ac / (-pc), np.nan)
    d["passivo_conforme"] = pc < 0  # True = segue a convencao da base (passivo negativo)

    d["ano_isolado"] = d["ano"] == ANO_ISOLADO
    return d


def classificar_desempenho(d: pd.DataFrame):
    """Resultado Liquido acumulado nos 12 anos, mesmo criterio da Entrega 1."""
    acum = d.groupby("cenario")["DRE - Resultado Líquido"].sum()
    p10, p90 = acum.quantile([0.10, 0.90])
    grupo = pd.Series(
        np.select([acum <= p10, acum >= p90], ["Piores 10%", "Melhores 10%"],
                  default="Medianos (10%-90%)"),
        index=acum.index, name="grupo_desempenho",
    )
    d = d.merge(grupo, left_on="cenario", right_index=True, how="left")
    return d, {"p10": float(p10), "p90": float(p90)}


def agregar_dashboard(d: pd.DataFrame) -> pd.DataFrame:
    status = {k: "principal" for k in KPIS_PRINCIPAIS}
    status.update({k: "verificar" for k in KPIS_VERIFICAR})
    status.update({k: "auxiliar" for k in KPIS_AUXILIARES})

    longo = d.melt(
        id_vars=["ano", "cenario", "grupo_desempenho", "ano_isolado"],
        value_vars=KPIS_PRINCIPAIS + KPIS_VERIFICAR + KPIS_AUXILIARES,
        var_name="kpi", value_name="valor",
    )
    todos = longo.assign(grupo_desempenho="Todos")
    longo = pd.concat([longo, todos], ignore_index=True)

    agg = (
        longo.groupby(["kpi", "grupo_desempenho", "ano", "ano_isolado"])["valor"]
        .agg(
            media="mean",
            p10=lambda s: s.quantile(0.10),
            mediana="median",
            p90=lambda s: s.quantile(0.90),
            n_validos="count",
            n_total="size",
        )
        .reset_index()
    )
    agg["status_kpi"] = agg["kpi"].map(status)

    # Cenarios que seguem a convencao da base (Passivo Circulante negativo), por grupo e ano
    conf = d[["ano", "grupo_desempenho", "passivo_conforme"]]
    conf = pd.concat([conf, conf.assign(grupo_desempenho="Todos")], ignore_index=True)
    n_conf = (
        conf.groupby(["grupo_desempenho", "ano"])["passivo_conforme"].sum()
        .rename("n_passivo_negativo").reset_index()
    )
    return agg.merge(n_conf, on=["grupo_desempenho", "ano"], how="left")


def checagens(df_raw, quarentena, largo, d, limiares):
    log = {}

    # Estrutura
    log["linhas_raw"] = int(len(df_raw))
    log["linhas_quarentena"] = int(len(quarentena))
    log["pct_quarentena"] = round(100 * len(quarentena) / len(df_raw), 2)
    log["cenarios"] = int(largo["cenario"].nunique())
    log["anos"] = sorted(int(a) for a in largo["ano"].unique())
    log["contas_selecionadas"] = len(CONTAS)
    log["shape_base_analitica"] = list(d.shape)

    esperado = log["cenarios"] * len(log["anos"])
    if len(largo) != esperado:
        raise ValueError(f"Base integrada com {len(largo)} linhas, esperado {esperado}.")
    if largo[CONTAS].isna().any().any():
        raise ValueError("Ha valores ausentes nas contas selecionadas.")

    # Consistencia contabil: Saldo Final do ano t = Saldo Inicial do ano t+1 (mesmo cenario)
    prox_inicial = largo.groupby("cenario")["FLU - Saldo Inicial"].shift(-1)
    dif = (largo["FLU - Saldo Final"] - prox_inicial).abs().dropna()
    log["saldo_final_vs_inicial"] = {
        "pares": int(len(dif)), "diferenca_maxima": float(dif.max()),
        "pct_acima_de_R$1": round(float((dif > 1).mean() * 100), 4),
    }
    if dif.max() > 1:
        raise ValueError("Saldo Final nao confere com Saldo Inicial do ano seguinte.")

    # Geracao de Caixa = Saldo Final - Saldo Inicial (mesmo ano)
    dif_g = (largo["FLU - Geração de Caixa"]
             - (largo["FLU - Saldo Final"] - largo["FLU - Saldo Inicial"])).abs()
    log["geracao_caixa_vs_saldos"] = {"diferenca_maxima": float(dif_g.max())}
    if dif_g.max() > 1:
        raise ValueError("Geracao de Caixa nao confere com Saldo Final - Saldo Inicial.")

    # Balanco: Total do Ativo + Total do Passivo = 0 (passivo com sinal negativo)
    bal = (largo["BAL - Total do Ativo"] + largo["BAL - Total do Passivo"]).abs()
    log["balanco_ativo_mais_passivo"] = {
        "diferenca_maxima": float(bal.max()),
        "observacao": "Aproximadamente zero em todas as linhas: a base guarda passivos com sinal negativo.",
    }

    # Achados documentados (nao corrigidos)
    pc = largo.groupby("ano")["BAL - Passivo Circulante"].apply(lambda s: round((s < 0).mean() * 100, 1))
    log["passivo_circulante_pct_negativo_por_ano"] = {int(k): float(v) for k, v in pc.items()}
    log["passivo_circulante_linhas_positivas"] = int((largo["BAL - Passivo Circulante"] > 0).sum())
    log["passivo_circulante_linhas_negativas"] = int((largo["BAL - Passivo Circulante"] < 0).sum())
    log["custos_pct_negativo"] = round(float((largo["DRE - Custos"] < 0).mean() * 100), 1)

    marg = d.groupby("ano")["margem_liquida"].mean().round(4)
    log["margem_liquida_media_por_ano"] = {int(k): float(v) for k, v in marg.items()}
    mop = d.groupby("ano")["margem_operacional"].mean().round(4)
    log["margem_operacional_media_por_ano"] = {int(k): float(v) for k, v in mop.items()}
    liq = d.groupby("ano")["liquidez_corrente"].median().round(2)
    log["liquidez_corrente_mediana_por_ano"] = {int(k): float(v) for k, v in liq.items()}

    grupos = d.drop_duplicates("cenario")["grupo_desempenho"].value_counts()
    log["grupos_desempenho"] = {k: int(v) for k, v in grupos.items()}
    log["limiares_resultado_acumulado"] = limiares
    return log


def main():
    ap = argparse.ArgumentParser(description="Prepara os dados da CTI para o dashboard.")
    ap.add_argument("--entrada", required=True, type=Path, help="CSV bruto da CTI")
    ap.add_argument("--saida", default=Path("dados"), type=Path, help="pasta de saida")
    args = ap.parse_args()

    staging = args.saida / "staging"
    processed = args.saida / "processed"
    staging.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    df_raw = carregar_raw(args.entrada)
    quarentena, df_trab = separar_quarentena(df_raw)
    quarentena.to_csv(staging / "linhas_nao_identificadas.csv", index=False)

    largo = integrar(selecionar_e_limpar(df_trab))
    d = derivar(largo)
    d, limiares = classificar_desempenho(d)

    log = checagens(df_raw, quarentena, largo, d, limiares)

    d.to_csv(processed / "base_analitica.csv", index=False)
    agregar_dashboard(d).to_csv(processed / "base_dashboard.csv", index=False)
    with open(processed / "log_qualidade.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("Pipeline concluido sem erros.")
    print(f"  raw: {log['linhas_raw']:,} linhas | quarentena: {log['linhas_quarentena']:,}")
    print(f"  base analitica: {log['shape_base_analitica']}")
    print(f"  grupos: {log['grupos_desempenho']}")
    print(f"  saidas em: {args.saida.resolve()}")


if __name__ == "__main__":
    main()
