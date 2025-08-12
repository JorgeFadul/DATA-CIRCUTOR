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


def procesar_demanda_maxima(df_original):
    """
    Procesa la demanda máxima calculando la media móvil de 15 minutos desplazada
    cada 5 minutos en 5 conjuntos (SDATA1..SDATA5). Aplica la misma lógica tanto
    para datos históricos como para datos promediados (1900-01-01).

    Args:
        df_original (pd.DataFrame): Debe tener columna o índice 'Fecha/hora' y 'P.Activa III'.

    Returns:
        tuple: (DataFrame con 'DMAX_15min', fila con demanda máxima)
    """
    try:
        df = df_original.copy()

        # Verificar si Fecha/hora es columna o índice
        if 'Fecha/hora' in df.columns:
            df['Fecha/hora'] = pd.to_datetime(df['Fecha/hora'], dayfirst=True, errors='coerce')
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={'index': 'Fecha/hora'})
        else:
            raise KeyError("El DataFrame no tiene columna o índice 'Fecha/hora' válido.")

        # Limpiar datos
        df['P.Activa III NN'] = df['P.Activa III T'].clip(lower=0)

        df = df.dropna(subset=['Fecha/hora', 'P.Activa III NN']).sort_values(by='Fecha/hora').reset_index(drop=True)


        # Crear DataFrame para SDATAS
        df_dmax = pd.DataFrame({'Fecha/hora': df['Fecha/hora']})

        # Crear SDATA1 a SDATA5 desplazadas cada 5 minutos
        for offset in range(5):
            sdata_name = f'SDATA{offset + 1}'
            muestras = df['P.Activa III NN'].iloc[offset::5].reset_index(drop=True)
            muestras_expandida = muestras.repeat(5).reset_index(drop=True).iloc[:len(df)]
            df_dmax[sdata_name] = muestras_expandida

        # Calcular media móvil de 15 minutos por SDATA
        df_max15 = df_dmax[['Fecha/hora']].copy()
        sdata_cols = [col for col in df_dmax.columns if col.startswith("SDATA")]

        for col in sdata_cols:
            df_max15[col] = df_dmax[col].rolling(window=15, min_periods=15).mean()

        # Promedio entre todas las SDATA
        df_max15['SDATA_PROM'] = df_max15[sdata_cols].mean(axis=1)

        # Resultado final
        df['DMAX_15min'] = df_max15['SDATA_PROM'].values
        df_original['DMAX_15min'] = df['DMAX_15min']

        # Buscar el máximo (ignorando NaN)
        df_max = df.dropna(subset=['DMAX_15min'])
        if df_max.empty:
            print("No hay suficientes datos para calcular la media móvil de 15 minutos.")
            return None, None

        dmax_fila = df_max.loc[df_max['DMAX_15min'].idxmax()]

        print(f"\nDemanda máxima encontrada: {dmax_fila['Fecha/hora']} → {dmax_fila['DMAX_15min']:.2f} kW")

        return df

    except Exception as e:
        print(f"Error al procesar demanda máxima: {e}")
        return None, None



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


