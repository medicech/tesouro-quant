from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd


@dataclass
class Cashflow:
    t: float          # tempo em anos a partir de data_base
    amount: float     # valor do fluxo (em "unidades monetárias do PU")
    date: pd.Timestamp


def _yearfrac(d0: pd.Timestamp, d1: pd.Timestamp) -> float:
    return (d1 - d0).days / 365.25


def _freq_from_coupon(cupom_txt: str) -> int:
    # no Tesouro Direto, "com cupom" usualmente é semestral
    return 2 if str(cupom_txt).upper().strip() == "COM CUPOM" else 1


def build_cashflows_from_row(row: pd.Series) -> list[Cashflow]:
    """
    Constrói fluxos "aproximados" para fins de duration (baseline):
    - SEM CUPOM: bullet no vencimento (amount=1)
    - COM CUPOM: cupons semestrais com taxa fixa aproximada (6% a.a. nominal, 3% por semestre)
      + principal no vencimento

    Observação importante (sincera):
    - Para Tesouro IPCA+/Prefixado com cupom, o cupom real do Tesouro é conhecido, mas
      o dataset do Preço/Taxa não traz a taxa de cupom explicitamente.
      Então, no MVP baseline, usamos cupom "padrão" (6% a.a.) apenas para construir
      um cronograma de fluxos e calcular duration. Depois (extensão), refinamos.
    """
    data_base = pd.to_datetime(row["data_base"])
    venc = pd.to_datetime(row["data_vencimento"])

    cupom_txt = str(row.get("cupom_txt", "")).upper().strip()
    com_cupom = cupom_txt == "COM CUPOM"

    # bullet
    if not com_cupom:
        t = _yearfrac(data_base, venc)
        return [Cashflow(t=t, amount=1.0, date=venc)]

    # com cupom: semestral
    freq = 2
    step_months = 12 // freq  # 6
    # cupom padrão (baseline): 6% a.a. => 3% por semestre
    coupon_rate_per_period = 0.06 / freq

    dates: list[pd.Timestamp] = []
    d = venc
    # cria datas retrocedendo a cada 6 meses até passar data_base
    while d > data_base:
        dates.append(d)
        d = d - pd.DateOffset(months=step_months)

    dates = sorted(dates)
    cfs: list[Cashflow] = []
    for dt in dates:
        t = _yearfrac(data_base, dt)
        if t <= 0:
            continue
        # cupom em cada data
        cfs.append(Cashflow(t=t, amount=coupon_rate_per_period, date=dt))

    # adiciona principal no vencimento (última data da lista deve ser venc)
    # somar principal ao último fluxo
    if cfs:
        # garante que o vencimento está lá
        if cfs[-1].date.normalize() != venc.normalize():
            t = _yearfrac(data_base, venc)
            cfs.append(Cashflow(t=t, amount=coupon_rate_per_period, date=venc))
        cfs[-1].amount += 1.0
    else:
        # fallback: se por algum motivo não gerou cupons, vira bullet
        t = _yearfrac(data_base, venc)
        cfs = [Cashflow(t=t, amount=1.0, date=venc)]

    return cfs


def price_from_yield(cashflows: list[Cashflow], y: float, comp: str = "annual") -> float:
    """
    Preço teórico por desconto exponencial discreto:
    - comp="annual": desconto por (1+y)^t
    """
    if not cashflows:
        return float("nan")
    if y <= -0.999:
        return float("nan")

    pv = 0.0
    for cf in cashflows:
        pv += cf.amount / ((1.0 + y) ** cf.t)
    return pv


def macaulay_duration(cashflows: list[Cashflow], y: float) -> float:
    """
    Duration de Macaulay em anos.
    """
    p = price_from_yield(cashflows, y)
    if not cashflows or not math.isfinite(p) or p <= 0:
        return float("nan")

    w_sum = 0.0
    for cf in cashflows:
        pv = cf.amount / ((1.0 + y) ** cf.t)
        w_sum += cf.t * pv

    return w_sum / p


def modified_duration(cashflows: list[Cashflow], y: float) -> float:
    """
    Duration Modificada: D_mod = D_mac / (1+y)
    """
    dmac = macaulay_duration(cashflows, y)
    if not math.isfinite(dmac):
        return float("nan")
    return dmac / (1.0 + y)


def dv01_from_duration(price: float, dmod: float) -> float:
    """
    DV01 aproximado: variação do preço para +1bp (0.0001) em y.
    ΔP ≈ -Dmod * P * Δy
    DV01 = |ΔP| para 1bp
    """
    if not (math.isfinite(price) and math.isfinite(dmod)):
        return float("nan")
    return abs(dmod * price * 0.0001)


def shock_impact(price: float, dmod: float, shock_bps: float) -> float:
    """
    Impacto (ΔP) para choque em bps (aprox linear).
    choque +100 bps => Δy = 0.01
    """
    if not (math.isfinite(price) and math.isfinite(dmod)):
        return float("nan")
    dy = shock_bps / 10000.0
    return -dmod * price * dy


def compute_duration_metrics(row: pd.Series, modo: str = "Compra") -> dict:
    """
    Calcula métricas para um título (uma linha do catálogo):
    - preço observado (PU)
    - y observado (taxa)
    - fluxos aproximados
    - Macaulay / Modified
    - DV01
    - impacto +100 bps (ΔP e %)

    modo: "Compra" ou "Venda"
    """
    taxa_col = "taxa_compra" if modo == "Compra" else "taxa_venda"
    pu_col = "pu_compra" if modo == "Compra" else "pu_venda"

    y = float(pd.to_numeric(row.get(taxa_col), errors="coerce"))
    pu = float(pd.to_numeric(row.get(pu_col), errors="coerce"))

    # taxas no dataset costumam vir em % a.a. (ex: 10.28)
    # converter para decimal (0.1028)
    y_dec = y / 100.0

    cashflows = build_cashflows_from_row(row)
    dmac = macaulay_duration(cashflows, y_dec)
    dmod = modified_duration(cashflows, y_dec)
    dv01 = dv01_from_duration(pu, dmod)
    dP_100 = shock_impact(pu, dmod, 100.0)
    pct_100 = (dP_100 / pu) * 100.0 if pu and math.isfinite(dP_100) else float("nan")

    return {
        "id_titulo": row.get("id_titulo"),
        "tipo_titulo": row.get("tipo_titulo"),
        "indexador": row.get("indexador"),
        "cupom": row.get("cupom_txt"),
        "data_base": pd.to_datetime(row.get("data_base")),
        "data_vencimento": pd.to_datetime(row.get("data_vencimento")),
        "taxa_%": y,
        "pu": pu,
        "duration_macaulay_anos": dmac,
        "duration_modified_anos": dmod,
        "dv01": dv01,
        "impacto_+100bps_R$": dP_100,
        "impacto_+100bps_%": pct_100,
        "n_fluxos": len(cashflows),
    }
