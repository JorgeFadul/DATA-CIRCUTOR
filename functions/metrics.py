from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from .blocks import clasificar_bloque


def calcular_sumatoria_energia(
    df: pd.DataFrame,
    tipo_energia: str,
    *,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    hora_inicio: str = "00:00",
    hora_fin: str = "23:59",
) -> tuple[float, dict[str, float], float, dict[str, float]]:
    """
    Devuelve:
      energia_actual_total,
      energia_actual_por_bloque,
      energia_extrap_30d_total,
      energia_extrap_30d_por_bloque
    """
    df = df.copy()
    if "Fecha/hora" in df.columns:
        df["FechaHora"] = pd.to_datetime(df["Fecha/hora"], dayfirst=True, errors="coerce")
    elif {"Fecha", "Hora"} <= set(df.columns):
        df["FechaHora"] = pd.to_datetime(
            df["Fecha"].astype(str) + " " + df["Hora"].astype(str), dayfirst=True, errors="coerce"
        )
    else:
        raise ValueError("No se encontró columna de fecha/hora válida")

    df = df.dropna(subset=["FechaHora"])

    ini = pd.to_datetime(f"{fecha_inicio} {hora_inicio}") if fecha_inicio else df["FechaHora"].min()
    fin = pd.to_datetime(f"{fecha_fin} {hora_fin}") if fecha_fin else df["FechaHora"].max()
    df = df[(df["FechaHora"] >= ini) & (df["FechaHora"] <= fin)]

    if tipo_energia not in df.columns:
        raise KeyError(f"{tipo_energia} no existe")

    df["bloque"] = df["FechaHora"].apply(clasificar_bloque)

    energia_total = df[tipo_energia].sum()
    energia_bloq = df.groupby("bloque")[tipo_energia].sum().to_dict()

    dias = (fin - ini).total_seconds() / 86400
    factor = 30 / dias if dias > 0 else float("nan")
    energia_total_ext = energia_total * factor
    energia_bloq_ext = {k: v * factor for k, v in energia_bloq.items()}

    return energia_total, energia_bloq, energia_total_ext, energia_bloq_ext


def agregar_factor_potencia_mensual(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """
    Añade columna 'F.P. M' acumulada y devuelve el FP mensual medido/extrapolado.
    """
    df = df.copy()
    if "Fecha/hora" in df.columns:
        df["FechaHora"] = pd.to_datetime(df["Fecha/hora"], dayfirst=True, errors="coerce")
    elif {"Fecha", "Hora"} <= set(df.columns):
        df["FechaHora"] = pd.to_datetime(
            df["Fecha"].astype(str) + " " + df["Hora"].astype(str), dayfirst=True, errors="coerce"
        )
    else:
        raise ValueError("Fecha/hora no encontrada")

    df = df.dropna(subset=["FechaHora"]).sort_values("FechaHora").reset_index(drop=True)
    df = df.dropna(subset=["E.Reactiva III M", "E.Activa III T"])

    acum_kvarh = df["E.Reactiva III M"].cumsum()
    acum_kwh = df["E.Activa III T"].cumsum()
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(acum_kwh != 0, acum_kvarh / acum_kwh, np.nan)
        df["F.P. M"] = np.cos(np.arctan(ratio))

    dias = (df["FechaHora"].max() - df["FechaHora"].min()).total_seconds() / 86400
    factor_ext = 30 / dias if dias and dias < 30 else 1
    kvarh_m = df["E.Reactiva III M"].sum() * factor_ext
    kwh_m = df["E.Activa III T"].sum() * factor_ext

    fp_m = math.cos(math.atan(kvarh_m / kwh_m)) if kwh_m else float("nan")
    return df, fp_m


def procesar_demanda_maxima(df_original: pd.DataFrame) -> pd.DataFrame:
    """
    Genera la columna 'DMAX_15min' según la metodología SDATA*.
    """
    df = df_original.copy()
    if "Fecha/hora" in df.columns:
        df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"], dayfirst=True, errors="coerce")
    else:
        raise KeyError("'Fecha/hora' no encontrada")

    df["P.Activa III NN"] = df["P.Activa III T"].clip(lower=0)
    df = df.dropna(subset=["Fecha/hora"]).sort_values("Fecha/hora").reset_index(drop=True)

    sdata = pd.DataFrame({"Fecha/hora": df["Fecha/hora"]})
    for offset in range(5):
        col = f"SDATA{offset+1}"
        samples = df["P.Activa III NN"].iloc[offset::5].reset_index(drop=True)
        samples = samples.repeat(5).reset_index(drop=True).iloc[: len(df)]
        sdata[col] = samples

    rolling = sdata.set_index("Fecha/hora").rolling("15min").mean().reset_index()
    sdata_cols = [c for c in rolling.columns if c.startswith("SDATA")]
    df_original["DMAX_15min"] = rolling[sdata_cols].mean(axis=1)

    return df_original


def calcular_maxima_demanda_por_bloque(
    df: pd.DataFrame,
    tipo_demanda: str,
    *,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    hora_inicio: str = "00:00",
    hora_fin: str = "23:59",
) -> tuple[float, Any, dict[str, float]]:
    """
    Devuelve demanda máxima total, instante y máxima por bloque.
    """
    if tipo_demanda not in df.columns:
        raise KeyError(tipo_demanda)

    if "Fecha/hora" in df.columns:
        df["FechaHora"] = pd.to_datetime(df["Fecha/hora"], dayfirst=True, errors="coerce")
    else:
        raise ValueError("Fecha/hora no encontrada")

    ini = pd.to_datetime(f"{fecha_inicio} {hora_inicio}") if fecha_inicio else df["FechaHora"].min()
    fin = pd.to_datetime(f"{fecha_fin} {hora_fin}") if fecha_fin else df["FechaHora"].max()
    df = df[(df["FechaHora"] >= ini) & (df["FechaHora"] <= fin)]

    fila = df.loc[df[tipo_demanda].idxmax()]
    dmax_total = fila[tipo_demanda]
    dmax_instant = fila["FechaHora"]

    df["bloque"] = df["FechaHora"].apply(clasificar_bloque)
    dmax_bloq = df.groupby("bloque")[tipo_demanda].max().to_dict()
    for b in ["punta", "fuera_punta_medio", "fuera_punta_bajo"]:
        dmax_bloq.setdefault(b, 0)

    return dmax_total, dmax_instant, dmax_bloq
