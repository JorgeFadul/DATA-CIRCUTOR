from __future__ import annotations

import numpy as np
import pandas as pd


def dividir_dataframe(df: pd.DataFrame, *, ver_df: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separa el DataFrame original en:
      • df       → mediciones eléctricas generales
      • df_arm   → armónicos (`Arm.` o `Fund.`)
    """
    mask_arm = (
        df.columns.str.startswith("Arm.")
        | df.columns.str.contains("Fund.")
        | df.columns.str.contains("Fecha/hora")
    )
    df_arm = df.loc[:, mask_arm].copy()

    mask_drop = (
        df.columns.str.startswith("Arm.")
        | df.columns.str.contains("Fund.")
        | df.columns.str.contains("mín", case=False)
        | df.columns.str.contains("máx", case=False)
    )
    df_main = df.drop(columns=df.columns[mask_drop])

    if ver_df:
        print("df_arm →", list(df_arm.columns))
        print("df     →", list(df_main.columns))

    return df_main, df_arm


def sub_dividir_dataframe(df: pd.DataFrame, *, ver_cols: bool = False):
    """
    Crea subconjuntos de columnas por categoría:
      general, potencia, fasor, energía, coste, secundario
    """
    def select_cols(patterns: list[str]) -> list[str]:
        return [c for c in df.columns if any(pat in c for pat in patterns)]

    # POTENCIAS
    df = df.copy()
    df["P.Activa III T"] = df["P.Activa III"] - df["P.Activa III -"]
    df["P.Inductiva III T"] = df["P.Inductiva III"] - df["P.Inductiva III -"]
    df["P.Capacitiva III T"] = df["P.Capacitiva III"] - df["P.Capacitiva III -"]
    df["P.Reactiva III T"] = df["P.Inductiva III T"] + df["P.Capacitiva III T"]
    df["P.Aparente III T"] = np.sqrt(df["P.Activa III T"] ** 2 + df["P.Reactiva III T"] ** 2)

    pactiva = select_cols(["P.Activa"])
    pcap = select_cols(["P.Capacitiva"])
    pind = select_cols(["P.Inductiva"])
    potencia_cols = pactiva + pcap + pind + [
        "P.Activa III T",
        "P.Inductiva III T",
        "P.Capacitiva III T",
        "P.Reactiva III T",
        "P.Aparente III T",
    ]
    df_potencia = df[potencia_cols]

    # ENERGÍA derivada de potencia
    for col_p in ["P.Activa III T", "P.Reactiva III T", "P.Aparente III T"]:
        df[f"E{col_p[1:]}"] = df[col_p] * (1 / 60)  # 1 min → kWh

    # GENERAL
    general_cols = select_cols(
        [
            "Tensión",
            "Corriente",
            "F.P.",
            "Cos Phi",
            "Frecuencia",
        ]
    ) + ["P/S"]
    df["P/S"] = np.where(df["P.Aparente III T"] == 0, 0, df["P.Activa III T"] / df["P.Aparente III T"])
    df_general = df[general_cols].copy()

    df_fasor = df[[c for c in df.columns if "Fasores" in c]]
    energia_cols = [c for c in df.columns if "E." in c]
    df_energia = df[energia_cols]
    df_coste = df[[c for c in df.columns if "Coste" in c]]

    secundario_cols = select_cols(
        [
            "directa",
            "homopolar",
            "inversa",
            "Factor cresta",
            "THD/d",
            "Distorsión",
            "Ka ",
            "Kd ",
            "Factor K",
        ]
    )
    df_secundario = df[secundario_cols]

    if ver_cols:
        for nombre, d in [
            ("general", df_general),
            ("potencia", df_potencia),
            ("fasor", df_fasor),
            ("energía", df_energia),
            ("coste", df_coste),
            ("secundario", df_secundario),
        ]:
            print(f"\nColumnas {nombre}:")
            print(list(d.columns))

    return (
        df_general,
        df_potencia,
        df_fasor,
        df_energia,
        df_coste,
        df_secundario,
    )


def promediar_df_por_min(df: pd.DataFrame, dias_semana: list[str] | None = None) -> pd.DataFrame:
    """
    Devuelve un DataFrame con el promedio de cada minuto del día, opcionalmente
    filtrando por lista de días en español.
    """
    df = df.copy()
    df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"])
    df["day_name_en"] = df["Fecha/hora"].dt.day_name()

    day_map = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miércoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sábado",
        "Sunday": "domingo",
    }
    df["dia_nombre"] = df["day_name_en"].map(day_map)

    if dias_semana:
        dias_semana = [d.lower() for d in dias_semana]
        df = df[df["dia_nombre"].isin(dias_semana)]

    df["Fecha/hora"] = pd.to_datetime(
        "1900-01-01 " + df["Fecha/hora"].dt.strftime("%H:%M"), format="%Y-%m-%d %H:%M"
    )

    numeric = df.select_dtypes(include="number").columns
    return df.groupby("Fecha/hora")[numeric].mean().sort_index()
