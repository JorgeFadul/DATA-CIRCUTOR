"""
Funciones de graficación (Matplotlib).
"""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _desempaquetar_item(item):
    if isinstance(item, str):
        return item, None, "-"
    if len(item) == 1:
        return item[0], None, "-"
    if len(item) == 2:
        return item[0], item[1], "-"
    if len(item) == 3:
        return item[0], item[1], item[2]
    raise ValueError(item)


def graficar_parametros(
    df: pd.DataFrame,
    parametros: list,
    *,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    hora_inicio: str = "00:00",
    hora_fin: str = "23:59",
    limite_inferior=None,
    limite_superior=None,
    lineas_verticales=None,
    lineas_horizontales=None,
    titulo: str = "Parámetros vs Tiempo",
    guardar: bool = False,
    ruta: str | None = None,
):
    if not parametros:
        raise ValueError("Se requiere al menos un parámetro")

    plt.figure(figsize=(14, 7))

    # Preparar índice datetime
    if "Fecha/hora" in df.columns:
        df = df.copy()
        df["FechaHora"] = pd.to_datetime(df["Fecha/hora"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["FechaHora"]).set_index("FechaHora")
    else:  # ya es índice
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("Índice no es datetime")

    is_promedio = (df.index.date == pd.Timestamp("1900-01-01").date()).all()

    if is_promedio:
        df = df.between_time(hora_inicio, hora_fin)
        for it in parametros:
            col, color, style = _desempaquetar_item(it)
            plt.plot(df.index, df[col], linestyle=style, color=color, label=col)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    else:
        df = df.between_time(hora_inicio, hora_fin)
        if fecha_inicio:
            df = df[df.index.date >= pd.to_datetime(fecha_inicio).date()]
        if fecha_fin:
            df = df[df.index.date <= pd.to_datetime(fecha_fin).date()]
        for it in parametros:
            col, color, style = _desempaquetar_item(it)
            plt.plot(df.index, df[col], linestyle=style, color=color, label=col)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))

    if lineas_verticales:
        for lv in lineas_verticales:
            lv, col = (lv if isinstance(lv, (list, tuple)) else (lv, "black"))
            plt.axvline(pd.to_datetime(lv), color=col, linestyle="--")
    if lineas_horizontales:
        for lh in lineas_horizontales:
            y, col = (lh if isinstance(lh, (list, tuple)) else (lh, "red"))
            plt.axhline(y, color=col, linestyle="--")

    plt.title(titulo)
    plt.grid(True)
    plt.ylabel("Valor")
    plt.legend()
    if limite_inferior is not None or limite_superior is not None:
        plt.ylim(limite_inferior, limite_superior)
    plt.tight_layout()
    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)
    plt.show()


# --- Barras & anillo ----------------------------------------------------


def graficar_consumo_por_bloque(
    data: dict[str, float],
    *,
    titulo="Consumo por Bloque",
    guardar: bool = False,
    ruta: str | None = None,
):
    bloques = ["punta", "fuera_punta_medio", "fuera_punta_bajo"]
    vals = [data.get(b, 0) for b in bloques]
    plt.figure(figsize=(8, 6))
    plt.bar(bloques, vals, color=["red", "orange", "green"])
    plt.title(titulo)
    plt.ylabel("kWh")
    plt.grid(axis="y")
    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)
    plt.show()


def graficar_demanda_maxima_por_bloque(
    data: dict[str, float],
    *,
    titulo="Demanda Máxima por Bloque",
    guardar: bool = False,
    ruta: str | None = None,
):
    bloques = ["punta", "fuera_punta_medio", "fuera_punta_bajo"]
    vals = [data.get(b, 0) for b in bloques]
    plt.figure(figsize=(8, 6))
    plt.bar(bloques, vals, color=["red", "orange", "green"])
    plt.title(titulo)
    plt.ylabel("kW")
    plt.grid(axis="y")
    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)
    plt.show()


def _donut(data, titulo, ylabel, guardar=False, ruta=None):
    bloques = ["punta", "fuera_punta_medio", "fuera_punta_bajo"]
    vals = [data.get(b, 0) for b in bloques]
    plt.figure(figsize=(8, 8))
    plt.pie(
        vals,
        labels=bloques,
        autopct="%1.1f%%",
        colors=["red", "orange", "green"],
        wedgeprops={"width": 0.4},
    )
    plt.title(titulo)
    plt.ylabel(ylabel)
    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)
    plt.show()


def graficar_consumo_anillo(
    data, 
    *,
    titulo="Consumo por Bloque (Anillo)",
    guardar: bool = False,
    ruta: str | None = None,
):
    _donut(data, titulo, "kWh", guardar=guardar, ruta=ruta)

def graficar_demanda_maxima_anillo(
    data, *, titulo="Demanda Máx (Anillo)", guardar: bool = False, ruta: str | None = None
):
    _donut(data, titulo, "kW", guardar=guardar, ruta=ruta)


# --- Polar --------------------------------------------------------------


def _polar(data, titulo, ylabel, guardar=False, ruta=None):
    bloques = ["fuera_punta_bajo", "punta", "fuera_punta_medio"]
    colores = ["green", "red", "orange"]
    horas = [9, 8, 7]  # anchura relativa
    angulos = [h / 24 * 2 * np.pi for h in horas]
    vals = [data.get(b, 0) for b in bloques]
    start = np.cumsum([0] + angulos[:-1])
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8))
    for s, w, v, c, l in zip(start, angulos, vals, colores, bloques):
        ax.bar(x=s + w / 2, height=v, width=w, bottom=0, color=c, alpha=0.7, label=l)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(titulo, va="bottom")
    ax.legend(loc="upper right")
    plt.ylabel(ylabel)
    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)
    plt.show()


def graficar_consumo_polar(
    data, *, titulo="Consumo (polar)", guardar: bool = False, ruta: str | None = None
):
    _polar(data, titulo, "kWh", guardar=guardar, ruta=ruta)

def graficar_demanda_maxima_polar(
    data, *, titulo="Demanda Máx (polar)", guardar: bool = False, ruta: str | None = None
):
    _polar(data, titulo, "kW", guardar=guardar, ruta=ruta)

# --- Comparación de tarifas ---------------------------------------------

def graficar_comparacion_tarifas(
    data: dict[str, dict[str, float]],
    *,
    titulo="Comparación de Costos por Tarifa",
    guardar: bool = False,
    ruta: str | None = None,
):
    """
    Grafica una comparación de costos entre diferentes tarifas.
    """
    nombres_tarifas = list(data.keys())
    componentes = sorted({comp for costos in data.values() for comp in costos.keys()})
    valores = {comp: [data[tarifa].get(comp, 0) for tarifa in nombres_tarifas] for comp in componentes}

    fig, ax = plt.subplots(figsize=(12, 7))
    bottom = np.zeros(len(nombres_tarifas))

    for componente, valores_componente in valores.items():
        p = ax.bar(nombres_tarifas, valores_componente, label=componente, bottom=bottom)
        bottom += np.array(valores_componente, dtype=float)
        # 👉 Etiquetas con signo $ y separador de miles
        etiquetas = [f"${v:,.2f}" for v in valores_componente]
        ax.bar_label(p, labels=etiquetas, label_type="center")

    ax.set_title(titulo)
    ax.set_ylabel("Costo ($)")
    ax.legend(title="Componentes de Costo")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    if guardar:
        if ruta is None:
            raise ValueError("Se debe especificar una ruta para guardar la gráfica.")
        plt.savefig(ruta)

    plt.show()
