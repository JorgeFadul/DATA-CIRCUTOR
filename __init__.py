"""
Paquete Circutor Data Analytics.

Re-exporta las principales APIs para que el usuario final solo tenga que
importar desde `circutor_da`.
"""
from .io import cargar_datos
from .preprocess import (
    dividir_dataframe,
    sub_dividir_dataframe,
    promediar_df_por_min,
)
from .metrics import (
    calcular_sumatoria_energia,
    agregar_factor_potencia_mensual,
    procesar_demanda_maxima,
    calcular_maxima_demanda_por_bloque,
)
from .tariffs import (
    calcular_BTS,
    calcular_BTSH,
    calcular_BTD,
    calcular_BTH,
    calcular_MTD,
    calcular_MTH,
)
from .visualize import (
    graficar_parametros,
    graficar_consumo_por_bloque,
    graficar_demanda_maxima_por_bloque,
    graficar_consumo_anillo,
    graficar_demanda_maxima_anillo,
    graficar_consumo_polar,
    graficar_demanda_maxima_polar,
)

__all__ = [
    # io
    "cargar_datos",
    # preprocess
    "dividir_dataframe",
    "sub_dividir_dataframe",
    "promediar_df_por_min",
    # metrics
    "calcular_sumatoria_energia",
    "agregar_factor_potencia_mensual",
    "procesar_demanda_maxima",
    "calcular_maxima_demanda_por_bloque",
    # tariffs
    "calcular_BTS",
    "calcular_BTSH",
    "calcular_BTD",
    "calcular_BTH",
    "calcular_MTD",
    "calcular_MTH",
    # visualize
    "graficar_parametros",
    "graficar_consumo_por_bloque",
    "graficar_demanda_maxima_por_bloque",
    "graficar_consumo_anillo",
    "graficar_demanda_maxima_anillo",
    "graficar_consumo_polar",
    "graficar_demanda_maxima_polar",
]