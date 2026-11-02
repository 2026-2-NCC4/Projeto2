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

Decisoes de isolamento (sem resposta da CTI ate o momento):
  1. Linhas sem conta: ficam em quarentena, fora da base analitica.
  2. Passivo Circulante: muda de sinal por ano (negativo nos Anos 1-4, positivo nos 5-11).
     Os valores sao preservados, mas os indicadores que dependem dele
     (capital_giro_liquido, liquidez_corrente) ficam com status 'isolado'.
  3. Ano 12: marcado com ano_isolado=True (cobertura reduzida do balanco e margem
     liquida destoante). O dashboard o exibe apenas por opcao do usuario.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CONTAS = [
    "BAL - Ativo Circulante", "BAL - Passivo Circulante",
    "FLU - Saldo Inicial", "FLU - Saldo Final",
    "FLU - Investimentos", "FLU - Distribuição para Acionista",
    "DRE - Receita", "DRE - Custos", "DRE - EBITDA", "DRE - Resultado Líquido",
]

KPIS_PRINCIPAIS = [
    "receita", "ebitda", "resultado_liquido",
    "margem_ebitda", "margem_liquida", "variacao_caixa",
]
KPIS_ISOLADOS = ["capital_giro_liquido", "liquidez_corrente"]

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
    d["receita"] = rec
    d["ebitda"] = d["DRE - EBITDA"]
    d["resultado_liquido"] = d["DRE - Resultado Líquido"]
    d["margem_ebitda"] = np.where(rec > 0, d["DRE - EBITDA"] / rec, np.nan)
    d["margem_liquida"] = np.where(rec > 0, d["DRE - Resultado Líquido"] / rec, np.nan)
    d["variacao_caixa"] = d["FLU - Saldo Final"] - d["FLU - Saldo Inicial"]

    # Isolados: dependem do Passivo Circulante, cuja convencao de sinal nao foi confirmada
    ac, pc = d["BAL - Ativo Circulante"], d["BAL - Passivo Circulante"]
    d["capital_giro_liquido"] = ac - pc
    d["liquidez_corrente"] = np.where(pc > 0, ac / pc, np.nan)

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
    status.update({k: "isolado" for k in KPIS_ISOLADOS})

    longo = d.melt(
        id_vars=["ano", "cenario", "grupo_desempenho", "ano_isolado"],
        value_vars=KPIS_PRINCIPAIS + KPIS_ISOLADOS,
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
    return agg


def checagens(df_raw, quarentena, largo, d, limiares):
    log = {}

    # Estrutura
    log["linhas_raw"] = int(len(df_raw))
    log["linhas_quarentena"] = int(len(quarentena))
    log["pct_quarentena"] = round(100 * len(quarentena) / len(df_raw), 2)
    log["cenarios"] = int(largo["cenario"].nunique())
    log["anos"] = sorted(int(a) for a in largo["ano"].unique())
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

    # Achados documentados (nao corrigidos)
    pc = largo.groupby("ano")["BAL - Passivo Circulante"].apply(lambda s: round((s < 0).mean() * 100, 1))
    log["passivo_circulante_pct_negativo_por_ano"] = {int(k): float(v) for k, v in pc.items()}
    log["custos_pct_negativo"] = round(float((largo["DRE - Custos"] < 0).mean() * 100), 1)

    marg = d.groupby("ano")["margem_liquida"].mean().round(4)
    log["margem_liquida_media_por_ano"] = {int(k): float(v) for k, v in marg.items()}

    grupos = d.drop_duplicates("cenario")["grupo_desempenho"].value_counts()
    log["grupos_desempenho"] = {k: int(v) for k, v in grupos.items()}
    log["limiares_resultado_acumulado"] = limiares
    log["liquidez_corrente_calculavel"] = int(d["liquidez_corrente"].notna().sum())
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
