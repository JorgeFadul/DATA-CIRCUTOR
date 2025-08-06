"""
Cálculo de cargos Edemet (2025).
Se expone una función por tipo de tarifa: BTS, BTSH, BTH, BTD, MTD, MTH.
"""

from __future__ import annotations

from math import cos, atan

from TARIFAS_NATURGY import tarifas_edemet

# -----------------------------------------------------------------------


def _calcular_fp(cargo_fp: float, consumo: float, fp_m: float) -> float:
    """Penalización por factor de potencia < 0.9."""
    if fp_m >= 0.9:
        return 0.0
    return round(2 * (0.9 - round(fp_m, 2)) * consumo * cargo_fp, 2)


# -------------------- FUNCIONES PÚBLICAS POR TARIFA --------------------


def calcular_BTS(consumo_por_bloque: dict[str, float], fp_m: float, _dmax, periodo):
    t = tarifas_edemet[periodo]["BTS"]
    kwh = sum(consumo_por_bloque.values())
    if kwh <= 300:
        energia = kwh * t["bloques"]["11-300"]
    elif kwh <= 750:
        energia = (290 * t["bloques"]["11-300"]) + ((kwh - 290) * t["bloques"]["301-750"])
    else:
        energia = (
            290 * t["bloques"]["11-300"]
            + 450 * t["bloques"]["301-750"]
            + ((kwh - 740) * t["bloques"]["751+"])
        )
    fp = _calcular_fp(t["cargo_fp"], kwh, fp_m)
    return round(energia, 2), 0.0, fp


def calcular_BTSH(consumo_por_bloque, fp_m, _dmax, periodo):
    t = tarifas_edemet[periodo]["BTSH"]
    energia = sum(
        consumo_por_bloque[b] * t["bloques"][b]
        for b in ("punta", "fuera_punta_medio", "fuera_punta_bajo")
    )
    fp = _calcular_fp(t["cargo_fp"], sum(consumo_por_bloque.values()), fp_m)
    return round(energia, 2), 0.0, fp


def calcular_BTH(consumo_bloq, dmax_bloq, fp_m, periodo):
    t = tarifas_edemet[periodo]["BTH"]
    energia = sum(consumo_bloq[b] * t["bloques"][b] for b in consumo_bloq)
    d_punta = dmax_bloq["punta"]
    d_fuera = max(dmax_bloq["fuera_punta_medio"], dmax_bloq["fuera_punta_bajo"])
    cargo_fuera = (
        t["cargo_demanda_maxima"]["fuera_punta_medio"]
        if dmax_bloq["fuera_punta_medio"] >= dmax_bloq["fuera_punta_bajo"]
        else t["cargo_demanda_maxima"]["fuera_punta_bajo"]
    )
    demanda = d_punta * t["cargo_demanda_maxima"]["punta"] + d_fuera * cargo_fuera
    fp = _calcular_fp(t["cargo_fp"], sum(consumo_bloq.values()), fp_m)
    return round(energia, 2), round(demanda, 2), fp


def calcular_BTD(consumo_bloq, fp_m, dmax_bloq, periodo):
    t = tarifas_edemet[periodo]["BTD"]
    kwh = sum(consumo_bloq.values())
    if kwh <= 10000:
        energia = kwh * t["bloques"]["0-10000"]
    elif kwh <= 30000:
        energia = 10000 * t["bloques"]["0-10000"] + (kwh - 10000) * t["bloques"]["10001-30000"]
    elif kwh <= 50000:
        energia = (
            10000 * t["bloques"]["0-10000"]
            + 20000 * t["bloques"]["10001-30000"]
            + (kwh - 30000) * t["bloques"]["30001-50000"]
        )
    else:
        energia = (
            10000 * t["bloques"]["0-10000"]
            + 20000 * t["bloques"]["10001-30000"]
            + 20000 * t["bloques"]["30001-50000"]
            + (kwh - 50000) * t["bloques"]["50001+"]
        )

    demanda = max(dmax_bloq.values()) * t["cargo_demanda_maxima"]
    fp = _calcular_fp(t["cargo_fp"], kwh, fp_m)
    return round(energia, 2), round(demanda, 2), fp


def calcular_MTD(consumo_bloq, fp_m, dmax_bloq, periodo):
    t = tarifas_edemet[periodo]["MTD"]
    kwh = sum(consumo_bloq.values())
    energia = kwh * t["bloques"]["general"]
    demanda = max(dmax_bloq.values()) * t["cargo_demanda_maxima"]
    fp = _calcular_fp(t["cargo_fp"], kwh, fp_m)
    return round(energia, 2), round(demanda, 2), fp


def calcular_MTH(consumo_bloq, dmax_bloq, fp_m, periodo):
    t = tarifas_edemet[periodo]["MTH"]
    energia = sum(consumo_bloq[b] * t["bloques"][b] for b in consumo_bloq)
    d_punta = dmax_bloq["punta"]
    d_fuera = max(dmax_bloq["fuera_punta_medio"], dmax_bloq["fuera_punta_bajo"])
    cargo_fuera = (
        t["cargo_demanda_maxima"]["fuera_punta_medio"]
        if dmax_bloq["fuera_punta_medio"] >= dmax_bloq["fuera_punta_bajo"]
        else t["cargo_demanda_maxima"]["fuera_punta_bajo"]
    )
    demanda = d_punta * t["cargo_demanda_maxima"]["punta"] + d_fuera * cargo_fuera
    fp = _calcular_fp(t["cargo_fp"], sum(consumo_bloq.values()), fp_m)
    return round(energia, 2), round(demanda, 2), fp
