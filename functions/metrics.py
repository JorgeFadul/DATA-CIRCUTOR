from __future__ import annotations

import math
import os
from typing import Any

import numpy as np
import pandas as pd

from . import visualize
from .blocks import clasificar_bloque


def _get_image_path(name: str) -> str:
    """Crea el directorio de imágenes si no existe y devuelve la ruta completa."""
    dir_path = "images"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return os.path.join(dir_path, f"{name}.png")


def _fusionar_eventos(eventos: list[dict], max_diff: pd.Timedelta, df_col: pd.Series, tipo_evento: str) -> list[dict]:
    """
    Fusiona eventos consecutivos si el tiempo entre ellos es menor a max_diff.
    """
    if not eventos:
        return []

    eventos_fusionados = []
    if not eventos:
        return eventos_fusionados

    evento_actual = eventos[0].copy()

    for siguiente_evento in eventos[1:]:
        siguiente_evento = siguiente_evento.copy()
        if (siguiente_evento['inicio'] - evento_actual['fin']) <= max_diff:
            # Fusionar evento
            evento_actual['fin'] = siguiente_evento['fin']
        else:
            # Guardar el evento actual y empezar uno nuevo
            eventos_fusionados.append(evento_actual)
            evento_actual = siguiente_evento
    
    eventos_fusionados.append(evento_actual) # No olvidar el último evento

    # Recalcular duración y valores extremos para los eventos fusionados
    for evento in eventos_fusionados:
        evento['duracion'] = evento['fin'] - evento['inicio']
        if tipo_evento != 'apagon':
            periodo_evento = df_col[evento['inicio']:evento['fin']]
            if not periodo_evento.empty:
                if tipo_evento == 'alto':
                    evento['valor_maximo'] = periodo_evento.max()
                    evento['fecha_valor_maximo'] = periodo_evento.idxmax()
                elif tipo_evento == 'bajo':
                    evento['valor_minimo'] = periodo_evento.min()
                    evento['fecha_valor_minimo'] = periodo_evento.idxmin()
            else: # Handle empty period
                if tipo_evento == 'alto':
                    evento['valor_maximo'] = np.nan
                    evento['fecha_valor_maximo'] = None
                elif tipo_evento == 'bajo':
                    evento['valor_minimo'] = np.nan
                    evento['fecha_valor_minimo'] = None

    return eventos_fusionados


def _detectar_eventos_con_estado(estado: pd.Series) -> list[dict]:
    """
    Detecta inicios y fines de eventos usando una máquina de estados para robustez.
    """
    eventos = []
    en_evento = False
    inicio_evento = None

    if not estado.index.is_monotonic_increasing:
        estado = estado.sort_index()

    cambios = estado.astype(int).diff()

    # Manejar el estado inicial
    if estado.iloc[0]:
        en_evento = True
        inicio_evento = estado.index[0]

    for timestamp, cambio in cambios.items():
        if cambio == 1 and not en_evento:
            en_evento = True
            inicio_evento = timestamp
        elif cambio == -1 and en_evento:
            en_evento = False
            if inicio_evento is not None:
                eventos.append({'inicio': inicio_evento, 'fin': timestamp})
                inicio_evento = None

    if en_evento and inicio_evento is not None:
        eventos.append({'inicio': inicio_evento, 'fin': estado.index.max()})

    return eventos


def voltaje(df: pd.DataFrame, voltaje_referencia_ll: float | None = None, voltaje_referencia_ln: float | None = None, extended_report: bool = False, graficar: bool = False) -> dict:
    """
    Calcula estadísticas de voltaje, los compara con límites permitidos y analiza
    los periodos fuera de rango con histéresis y fusión de eventos.
    El análisis de eventos se realiza únicamente sobre la columna 'Tensión L1L2L3'.
    """
    df_copy = df.copy()
    if 'Fecha/hora' not in df_copy.columns:
        raise ValueError("El DataFrame debe tener una columna 'Fecha/hora'.")
    df_copy['Fecha/hora'] = pd.to_datetime(df_copy['Fecha/hora'])
    df_copy = df_copy.sort_values(by='Fecha/hora').set_index('Fecha/hora')

    # Columnas a analizar y reportar
    cols_ll = ['Tensión L1L2L3']
    cols_ln = ['Tensión L1', 'Tensión L2', 'Tensión L3']
    cols_reporte = [col for col in cols_ll + cols_ln if col in df_copy.columns]

    limites = {}
    if voltaje_referencia_ll is not None:
        limites["linea_linea"] = {
            "referencia": voltaje_referencia_ll,
            "max_permitido": voltaje_referencia_ll * 1.05,
            "min_permitido": voltaje_referencia_ll * 0.95,
            "histeresis": voltaje_referencia_ll * 0.01
        }
    if voltaje_referencia_ln is not None:
        limites["linea_neutro"] = {
            "referencia": voltaje_referencia_ln,
            "max_permitido": voltaje_referencia_ln * 1.05,
            "min_permitido": voltaje_referencia_ln * 0.95,
            "histeresis": voltaje_referencia_ln * 0.01
        }
    
    stats_voltaje = {col: {'promedio': df_copy[col].mean(), 'maximo': df_copy[col].max(), 'minimo': df_copy[col].min()} for col in cols_reporte}

    analisis_eventos = {}
    # --- Análisis de eventos solo para Tensión L1L2L3 ---
    col_analisis = 'Tensión L1L2L3'
    if col_analisis in df_copy.columns and "linea_linea" in limites:
        limite_actual = limites["linea_linea"]
        v = df_copy[col_analisis]
        histeresis = limite_actual['histeresis']
        
        # Alto voltaje
        umbral_alto_inicio = limite_actual['max_permitido']
        umbral_alto_fin = umbral_alto_inicio - histeresis
        estado_alto = pd.Series(pd.NA, index=v.index, dtype='boolean')
        estado_alto[v > umbral_alto_inicio] = True
        estado_alto[v < umbral_alto_fin] = False
        estado_alto = estado_alto.ffill().fillna(False)
        eventos_alto_raw = _detectar_eventos_con_estado(estado_alto)

        # Bajo voltaje
        umbral_bajo_inicio = limite_actual['min_permitido']
        umbral_bajo_fin = umbral_bajo_inicio + histeresis
        estado_bajo = pd.Series(pd.NA, index=v.index, dtype='boolean')
        estado_bajo[v < umbral_bajo_inicio] = True
        estado_bajo[v > umbral_bajo_fin] = False
        estado_bajo = estado_bajo.ffill().fillna(False)
        estado_bajo &= (v != 0)
        eventos_bajo_raw = _detectar_eventos_con_estado(estado_bajo)

        max_diff = pd.Timedelta(minutes=10)
        eventos_alto_final = _fusionar_eventos(eventos_alto_raw, max_diff, v, 'alto')
        eventos_bajo_final = _fusionar_eventos(eventos_bajo_raw, max_diff, v, 'bajo')

        if eventos_alto_final or eventos_bajo_final:
            analisis_eventos[col_analisis] = {
                'tiempo_total_fuera_de_rango': sum([e['duracion'] for e in eventos_alto_final], pd.Timedelta(0)) + sum([e['duracion'] for e in eventos_bajo_final], pd.Timedelta(0)),
                'eventos_de_voltaje_alto': eventos_alto_final,
                'eventos_de_voltaje_bajo': eventos_bajo_final
            }

    resultado = {
        "estadisticas": stats_voltaje,
        "limites": limites,
        "analisis_de_eventos": analisis_eventos,
        "graficos_paths": {}
    }

    if graficar:
        # Gráfico General de Voltaje L-L
        if "linea_linea" in limites and col_analisis in df_copy.columns:
            lim_ll = limites["linea_linea"]
            ruta_grafico_general_ll = _get_image_path("voltaje_linea_a_linea_general")
            visualize.graficar_parametros(
                df=df_copy,
                parametros=[col_analisis],
                lineas_horizontales=[
                    (lim_ll['max_permitido'], "red"),
                    (lim_ll['min_permitido'], "red")
                ],
                titulo="Análisis General de Voltaje Línea a Línea",
                guardar=True,
                ruta=ruta_grafico_general_ll
            )
            resultado["graficos_paths"]["general_linea_linea"] = ruta_grafico_general_ll

            # Gráfico de Eventos de Voltaje L-L
            lineas_verticales_ll = []
            if col_analisis in analisis_eventos:
                for evento in analisis_eventos[col_analisis].get('eventos_de_voltaje_alto', []):
                    lineas_verticales_ll.append((evento['inicio'], 'orange'))
                    lineas_verticales_ll.append((evento['fin'], 'orange'))
                for evento in analisis_eventos[col_analisis].get('eventos_de_voltaje_bajo', []):
                    lineas_verticales_ll.append((evento['inicio'], 'purple'))
                    lineas_verticales_ll.append((evento['fin'], 'purple'))
            
            if lineas_verticales_ll:
                ruta_grafico_eventos_ll = _get_image_path("voltaje_linea_a_linea_eventos")
                visualize.graficar_parametros(
                    df=df_copy,
                    parametros=[col_analisis],
                    lineas_horizontales=[
                        (lim_ll['max_permitido'], "red"),
                        (lim_ll['min_permitido'], "red")
                    ],
                    lineas_verticales=lineas_verticales_ll,
                    titulo="Eventos de Voltaje Fuera de Rango (Línea a Línea)",
                    guardar=True,
                    ruta=ruta_grafico_eventos_ll
                )
                resultado["graficos_paths"]["eventos_linea_linea"] = ruta_grafico_eventos_ll

        # Gráfico General de Voltaje L-N
        cols_ln_existentes = [col for col in cols_ln if col in df_copy.columns]
        if "linea_neutro" in limites and cols_ln_existentes:
            lim_ln = limites["linea_neutro"]
            ruta_grafico_ln = _get_image_path("voltaje_fase_a_neutro_general")
            visualize.graficar_parametros(
                df=df_copy,
                parametros=cols_ln_existentes,
                lineas_horizontales=[
                    (lim_ln['max_permitido'], "red"),
                    (lim_ln['min_permitido'], "red")
                ],
                titulo="Análisis General de Voltaje Fase a Neutro",
                guardar=True,
                ruta=ruta_grafico_ln
            )
            resultado["graficos_paths"]["general_linea_neutro"] = ruta_grafico_ln
            
    return resultado


def analisis_de_apagones(df: pd.DataFrame, graficar: bool = False) -> dict:
    """
    Analiza los apagones en el suministro eléctrico, fusionando eventos cercanos y filtrando por duración mínima.
    """
    df_copy = df.copy()
    if 'Fecha/hora' not in df_copy.columns:
        raise ValueError("El DataFrame debe tener una columna 'Fecha/hora'.")
    df_copy['Fecha/hora'] = pd.to_datetime(df_copy['Fecha/hora'])
    df_copy = df_copy.sort_values(by='Fecha/hora').set_index('Fecha/hora')

    condicion_apagon = ((df_copy['Tensión III'] == 0) | (df_copy['Tensión III'].isna())) & ((df_copy['Frecuencia'] == 0) | (df_copy['Frecuencia'].isna()))
    
    if not condicion_apagon.any():
        return {'numero_total_de_apagones': 0, 'tiempo_total_sin_suministro': pd.Timedelta(0), 'detalle_de_apagones': [], 'grafico_path': None}

    apagones_raw = _detectar_eventos_con_estado(condicion_apagon)
    
    apagones_fusionados = _fusionar_eventos(apagones_raw, pd.Timedelta(minutes=10), df_copy['Tensión III'], 'apagon')

    # Filtrar por duración mínima
    min_duration = pd.Timedelta(minutes=3)
    apagones_filtrados = [e for e in apagones_fusionados if e['duracion'] >= min_duration]

    total_tiempo_sin_suministro = sum([a['duracion'] for a in apagones_filtrados], pd.Timedelta(0))
    
    resultado = {
        'numero_total_de_apagones': len(apagones_filtrados),
        'tiempo_total_sin_suministro': total_tiempo_sin_suministro,
        'detalle_de_apagones': apagones_filtrados,
        'grafico_path': None
    }

    if graficar:
        lineas_verticales = []
        for apagon in apagones_filtrados:
            lineas_verticales.append((apagon['inicio'], 'red'))
            lineas_verticales.append((apagon['fin'], 'green'))

        ruta_grafico = _get_image_path("deteccion_de_apagones")
        visualize.graficar_parametros(
            df=df_copy,
            parametros=['Tensión III', 'Frecuencia'],
            titulo="Detección de Apagones",
            lineas_verticales=lineas_verticales,
            guardar=True,
            ruta=ruta_grafico
        )
        resultado['grafico_path'] = ruta_grafico

    return resultado


def corriente(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    """
    Calcula estadísticas de corriente (promedio, máximo, mínimo).
    """
    stats_corriente = {}
    if extended_report:
        corriente_cols = ['Corriente L1', 'Corriente L2', 'Corriente L3', 'Corriente III', 'Corriente de neutro']
    else:
        corriente_cols = ['Corriente III']
    
    cols_existentes = [col for col in corriente_cols if col in df.columns]
    for col in cols_existentes:
        stats_corriente[col] = {
            'promedio': df[col].mean(),
            'maximo': df[col].max(),
            'minimo': df[col].min()
        }

    if graficar and 'Corriente III' in df.columns:
        visualize.graficar_parametros(
            df,
            parametros=['Corriente III'],
            titulo="Análisis de Corriente Trifásica Total",
            guardar=True,
            ruta=_get_image_path("analisis_de_corriente_trifasica_total")
        )

    return stats_corriente    


def frecuencia(df: pd.DataFrame, frec_nominal: float = 60.0, graficar: bool = False) -> dict:
    """
    Calcula estadísticas de frecuencia, los compara con límites permitidos y analiza
    los periodos fuera de rango con histéresis y fusión de eventos.
    """
    df_copy = df.copy()
    if 'Fecha/hora' not in df_copy.columns:
        raise ValueError("El DataFrame debe tener una columna 'Fecha/hora'.")
    df_copy['Fecha/hora'] = pd.to_datetime(df_copy['Fecha/hora'])
    df_copy = df_copy.sort_values(by='Fecha/hora').set_index('Fecha/hora')

    frec_col = 'Frecuencia'
    if frec_col not in df_copy.columns:
        return {}

    # Asegurarse de que la columna de frecuencia es numérica y manejar ceros
    df_copy[frec_col] = pd.to_numeric(df_copy[frec_col], errors='coerce')
    # Filtrar valores cero que usualmente indican ausencia de medición
    frec_series = df_copy[frec_col][df_copy[frec_col] > 0]

    if frec_series.empty:
        return {
            "estadisticas": {'promedio': 0, 'maximo': 0, 'minimo': 0},
            "limites": {},
            "analisis_de_eventos": {},
            "grafico_path": None
        }

    stats_frecuencia = {
        'promedio': frec_series.mean(),
        'maximo': frec_series.max(),
        'minimo': frec_series.min()
    }

    limites = {
        "permanente": {
            "nominal": frec_nominal,
            "max_permitido": frec_nominal + 0.5,
            "min_permitido": frec_nominal - 0.5,
            "histeresis": 0.1  # Hz
        }
    }

    analisis_eventos = {}
    limite_actual = limites["permanente"]
    v = frec_series
    histeresis = limite_actual['histeresis']

    # Alta frecuencia
    umbral_alto_inicio = limite_actual['max_permitido']
    umbral_alto_fin = umbral_alto_inicio - histeresis
    estado_alto = pd.Series(pd.NA, index=v.index, dtype='boolean')
    estado_alto[v > umbral_alto_inicio] = True
    estado_alto[v < umbral_alto_fin] = False
    estado_alto = estado_alto.ffill().fillna(False)
    eventos_alto_raw = _detectar_eventos_con_estado(estado_alto)

    # Baja frecuencia
    umbral_bajo_inicio = limite_actual['min_permitido']
    umbral_bajo_fin = umbral_bajo_inicio + histeresis
    estado_bajo = pd.Series(pd.NA, index=v.index, dtype='boolean')
    estado_bajo[v < umbral_bajo_inicio] = True
    estado_bajo[v > umbral_bajo_fin] = False
    estado_bajo = estado_bajo.ffill().fillna(False)
    eventos_bajo_raw = _detectar_eventos_con_estado(estado_bajo)

    max_diff = pd.Timedelta(minutes=5)
    eventos_alto_final = _fusionar_eventos(eventos_alto_raw, max_diff, v, 'alto')
    eventos_bajo_final = _fusionar_eventos(eventos_bajo_raw, max_diff, v, 'bajo')

    if eventos_alto_final or eventos_bajo_final:
        analisis_eventos[frec_col] = {
            'tiempo_total_fuera_de_rango': sum([e['duracion'] for e in eventos_alto_final], pd.Timedelta(0)) + sum([e['duracion'] for e in eventos_bajo_final], pd.Timedelta(0)),
            'eventos_de_frecuencia_alta': eventos_alto_final,
            'eventos_de_frecuencia_baja': eventos_bajo_final
        }

    resultado = {
        "estadisticas": stats_frecuencia,
        "limites": limites,
        "analisis_de_eventos": analisis_eventos,
        "grafico_path": None
    }

    if graficar:
        # Gráfico General de Frecuencia
        ruta_grafico_general = _get_image_path("frecuencia_general")
        visualize.graficar_parametros(
            df=df_copy,
            parametros=[frec_col],
            lineas_horizontales=[
                (limites['permanente']['max_permitido'], "red"),
                (limites['permanente']['min_permitido'], "red")
            ],
            titulo="Análisis General de Frecuencia",
            guardar=True,
            ruta=ruta_grafico_general
        )
        resultado["grafico_path"] = ruta_grafico_general

        # Gráfico de Eventos de Frecuencia
        lineas_verticales_frec = []
        if frec_col in analisis_eventos:
            for evento in analisis_eventos[frec_col].get('eventos_de_frecuencia_alta', []):
                lineas_verticales_frec.append((evento['inicio'], 'orange'))
                lineas_verticales_frec.append((evento['fin'], 'orange'))
            for evento in analisis_eventos[frec_col].get('eventos_de_frecuencia_baja', []):
                lineas_verticales_frec.append((evento['inicio'], 'purple'))
                lineas_verticales_frec.append((evento['fin'], 'purple'))

        if lineas_verticales_frec:
            ruta_grafico_eventos = _get_image_path("frecuencia_eventos")
            visualize.graficar_parametros(
                df=df_copy,
                parametros=[frec_col],
                lineas_horizontales=[
                    (limites['permanente']['max_permitido'], "red"),
                    (limites['permanente']['min_permitido'], "red")
                ],
                lineas_verticales=lineas_verticales_frec,
                titulo="Eventos de Frecuencia Fuera de Rango",
                guardar=True,
                ruta=ruta_grafico_eventos
            )
            # Sobrescribimos la clave para el reporte, o añadimos una nueva
            resultado["graficos_paths"] = {"general": ruta_grafico_general, "eventos": ruta_grafico_eventos}


    return resultado


def factor_potencia(df: pd.DataFrame, graficar: bool = False) -> dict:
    """
    Calcula y analiza el factor de potencia desde múltiples fuentes.
    """
    _, fp_mensual = agregar_factor_potencia_mensual(df.copy())
    stats_instantaneo = {}
    if 'P/S' in df.columns:
        stats_instantaneo = {
            'promedio': df['P/S'].mean(),
            'maximo': df['P/S'].max(),
            'minimo': df['P/S'].min()
        }

    limites = {"superior": 0.9, "inferior": -0.9}
    
    if graficar and 'P/S' in df.columns:
        visualize.graficar_parametros(
            df, 
            parametros=['P/S'],
            lineas_horizontales=[(limites['superior'], "red"), (limites['inferior'], "red")],
            titulo="Análisis de Factor de Potencia Instantáneo (P/S)",
            guardar=True,
            ruta=_get_image_path("analisis_de_factor_de_potencia_instantaneo")
        )

    return {
        "fp_mensual_calculado": fp_mensual,
        "fp_instantaneo_stats": stats_instantaneo,
        "limites": limites
    }


def _calculate_power_stats_with_blocks(df: pd.DataFrame, power_cols: list[str], graficar: bool = False, titulo: str = "Potencia", unit: str = "kW") -> dict:
    """
    Helper para calcular estadísticas de potencia, general y por bloque horario.
    """
    df_copy = df.copy()
    if 'FechaHora' not in df_copy.columns:
        if 'Fecha/hora' in df_copy.columns:
            df_copy['FechaHora'] = pd.to_datetime(df_copy['Fecha/hora'], dayfirst=True, errors='coerce')
        else:
            raise ValueError("DataFrame must have a datetime column named 'FechaHora' or 'Fecha/hora'")
    df_copy['bloque'] = df_copy['FechaHora'].apply(clasificar_bloque)

    stats = {}
    cols_existentes = [col for col in power_cols if col in df_copy.columns]

    for col in cols_existentes:
        overall_stats = {
            'promedio': df_copy[col].mean(),
            'maximo': df_copy[col].max(),
            'minimo': df_copy[col].min()
        }
        agg_stats = df_copy.groupby('bloque')[col].agg(['mean', 'max', 'min'])
        block_stats = {block: {'promedio': 0.0, 'maximo': 0.0, 'minimo': 0.0} for block in ['punta', 'fuera_punta_medio', 'fuera_punta_bajo']}
        for block_name, row in agg_stats.iterrows():
            block_stats[block_name] = {'promedio': row['mean'], 'maximo': row['max'], 'minimo': row['min']}
        stats[col] = {'general': overall_stats, 'por_bloque': block_stats}
        
    if graficar and any(p in df.columns for p in power_cols):
        file_name = titulo.lower().replace(" ", "_").replace("(", "").replace(")", "")
        visualize.graficar_parametros(
            df,
            parametros=[p for p in power_cols if p in df.columns],
            titulo=titulo,
            guardar=True,
            ruta=_get_image_path(file_name)
        )

    return stats


def potencia_activa(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    cols = ['P.Activa III', 'P.Activa III -', 'P.Activa III T'] if not extended_report else [col for col in df.columns if 'P.Activa' in col]
    return _calculate_power_stats_with_blocks(df, ['P.Activa III T'], graficar, "Análisis de Potencia Activa Total")


def potencia_reactiva(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    cols = ['P.Reactiva III T'] if not extended_report else [col for col in df.columns if 'P.Reactiva' in col]
    return _calculate_power_stats_with_blocks(df, cols, graficar, "Análisis de Potencia Reactiva Total", "kVAr")


def potencia_aparente(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    cols = ['P.Aparente III T'] if not extended_report else [col for col in df.columns if 'P.Aparente' in col]
    return _calculate_power_stats_with_blocks(df, cols, graficar, "Análisis de Potencia Aparente Total", "kVA")


def potencia_inductiva(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    cols = ['P.Inductiva III T'] if not extended_report else [col for col in df.columns if 'P.Inductiva' in col]
    return _calculate_power_stats_with_blocks(df, cols, graficar, "Análisis de Potencia Inductiva Total", "kVAr")


def potencia_capacitiva(df: pd.DataFrame, extended_report: bool = False, graficar: bool = False) -> dict:
    cols = ['P.Capacitiva III T'] if not extended_report else [col for col in df.columns if 'P.Capacitiva' in col]
    return _calculate_power_stats_with_blocks(df, cols, graficar, "Análisis de Potencia Capacitiva Total", "kVAr")


def procesar_demanda_maxima(df_original, graficar: bool = False):
    """
    Procesa la demanda máxima y opcionalmente la grafica.
    """
    try:
        df = df_original.copy()
        if 'Fecha/hora' in df.columns:
            df['Fecha/hora'] = pd.to_datetime(df['Fecha/hora'], dayfirst=True, errors='coerce')
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={'index': 'Fecha/hora'})
        else:
            raise KeyError("El DataFrame no tiene columna o índice 'Fecha/hora' válido.")

        df['P.Activa III NN'] = df['P.Activa III T'].clip(lower=0)
        df = df.dropna(subset=['Fecha/hora', 'P.Activa III NN']).sort_values(by='Fecha/hora').reset_index(drop=True)

        df_dmax = pd.DataFrame({'Fecha/hora': df['Fecha/hora']})
        for offset in range(5):
            sdata_name = f'SDATA{offset + 1}'
            muestras = df['P.Activa III NN'].iloc[offset::5].reset_index(drop=True)
            muestras_expandida = muestras.repeat(5).reset_index(drop=True).iloc[:len(df)]
            df_dmax[sdata_name] = muestras_expandida

        df_max15 = df_dmax[['Fecha/hora']].copy()
        sdata_cols = [col for col in df_dmax.columns if col.startswith("SDATA")]
        for col in sdata_cols:
            df_max15[col] = df_dmax[col].rolling(window=15, min_periods=15).mean()

        df_max15['SDATA_PROM'] = df_max15[sdata_cols].mean(axis=1)
        df['DMAX_15min'] = df_max15['SDATA_PROM'].values
        df_original['DMAX_15min'] = df['DMAX_15min']

        df_max = df.dropna(subset=['DMAX_15min'])
        if df_max.empty:
            return df_original, None

        dmax_fila = df_max.loc[df_max['DMAX_15min'].idxmax()]

        if graficar:
            visualize.graficar_parametros(
                df.set_index('Fecha/hora'),
                parametros=['P.Activa III T', 'DMAX_15min'],
                titulo="Análisis de Demanda Máxima",
                lineas_horizontales=[(dmax_fila['DMAX_15min'], "red")],
                guardar=True,
                ruta=_get_image_path("analisis_de_demanda_maxima")
            )

        return df_original, dmax_fila

    except Exception as e:
        print(f"Error al procesar demanda máxima: {e}")
        return df_original, None


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
    df = df.dropna(subset=['E.Reactiva III M', 'E.Activa III T'])

    acum_kvarh = df['E.Reactiva III M'].cumsum()
    acum_kwh = df['E.Activa III T'].cumsum()
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(acum_kwh != 0, acum_kvarh / acum_kwh, np.nan)
        df['F.P. M'] = np.cos(np.arctan(ratio))

    dias = (df["FechaHora"].max() - df["FechaHora"].min()).total_seconds() / 86400
    factor_ext = 30 / dias if dias and dias < 30 else 1
    kvarh_m = df['E.Reactiva III M'].sum() * factor_ext
    kwh_m = df['E.Activa III T'].sum() * factor_ext

    fp_m = math.cos(math.atan(kvarh_m / kwh_m)) if kwh_m else float("nan")
    return df, fp_m


def calcular_maxima_demanda_por_bloque(
    df: pd.DataFrame,
    tipo_demanda: str,
    *,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    hora_inicio: str = "00:00",
    hora_fin: str = "23:59",
) -> tuple[float, Any, dict[str, dict[str, Any]]]:
    """
    Devuelve demanda máxima total, instante y máxima por bloque con su fecha.
    """
    if tipo_demanda not in df.columns:
        raise KeyError(tipo_demanda)

    df_copy = df.copy()
    if "Fecha/hora" in df_copy.columns:
        df_copy["FechaHora"] = pd.to_datetime(df_copy["Fecha/hora"], dayfirst=True, errors="coerce")
    else:
        raise ValueError("Fecha/hora no encontrada")

    ini = pd.to_datetime(f"{fecha_inicio} {hora_inicio}") if fecha_inicio else df_copy["FechaHora"].min()
    fin = pd.to_datetime(f"{fecha_fin} {hora_fin}") if fecha_fin else df_copy["FechaHora"].max()
    df_copy = df_copy[(df_copy["FechaHora"] >= ini) & (df_copy["FechaHora"] <= fin)]

    if df_copy.empty or df_copy[tipo_demanda].isnull().all():
        return 0.0, None, {}

    fila = df_copy.loc[df_copy[tipo_demanda].idxmax()]
    dmax_total = fila[tipo_demanda]
    dmax_instant = fila["FechaHora"]

    df_copy["bloque"] = df_copy["FechaHora"].apply(clasificar_bloque)
    
    dmax_bloq_con_fecha = {}
    for bloque in ["punta", "fuera_punta_medio", "fuera_punta_bajo"]:
        df_bloque = df_copy[df_copy['bloque'] == bloque]
        if not df_bloque.empty and not df_bloque[tipo_demanda].isnull().all():
            fila_bloque = df_bloque.loc[df_bloque[tipo_demanda].idxmax()]
            dmax_bloq_con_fecha[bloque] = {
                'valor': fila_bloque[tipo_demanda],
                'fecha': fila_bloque['FechaHora']
            }
        else:
            dmax_bloq_con_fecha[bloque] = {'valor': 0.0, 'fecha': None}

    return dmax_total, dmax_instant, dmax_bloq_con_fecha

def analizar_energia(df: pd.DataFrame, tipo_energia: str, graficar: bool = False) -> dict:
    """
    Analiza la energía, calcula la extrapolación y genera gráficos.
    """
    _, _, energia_extrapolada, consumo_bloques_extrapolado = calcular_sumatoria_energia(df, tipo_energia)

    bloques_horarios = {
        "punta": "09:00 - 17:00 (L-V)",
        "fuera_punta_medio": "17:01 - 23:59 (L-V) y 11:00 - 22:59 (Sáb)",
        "fuera_punta_bajo": "00:00 - 08:59 (L-V), 00:00 - 10:59 y 23:00 - 23:59 (Sáb) y todo el Domingo"
    }

    resultado = {
        "energia_extrapolada_total": energia_extrapolada,
        "consumo_extrapolado_por_bloque": consumo_bloques_extrapolado,
        "horarios_bloques": bloques_horarios,
        "grafico_path": None
    }

    if graficar:
        ruta_grafico = _get_image_path("consumo_energia_por_bloque")
        visualize.graficar_consumo_por_bloque(
            consumo_bloques_extrapolado,
            titulo="Consumo de Energía por Bloque Horario",
            guardar=True,
            ruta=ruta_grafico
        )
        resultado["grafico_path"] = ruta_grafico
    
    return resultado

def analizar_demanda(df: pd.DataFrame, tipo_demanda: str, graficar: bool = False) -> dict:
    """
    Analiza la demanda máxima, calcula por bloques y genera gráficos.
    """
    dmax_total, dmax_fecha, dmax_bloques_con_fecha = calcular_maxima_demanda_por_bloque(df, tipo_demanda)

    dmax_bloques_valores = {k: v['valor'] for k, v in dmax_bloques_con_fecha.items()}

    resultado = {
        "demanda_maxima_total": dmax_total,
        "fecha_demanda_maxima_total": dmax_fecha,
        "demanda_maxima_por_bloque": dmax_bloques_con_fecha,
        "grafico_path": None
    }

    if graficar:
        ruta_grafico = _get_image_path("demanda_maxima_por_bloque")
        visualize.graficar_demanda_maxima_por_bloque(
            dmax_bloques_valores,
            titulo="Demanda Máxima por Bloque Horario",
            guardar=True,
            ruta=ruta_grafico
        )
        resultado["grafico_path"] = ruta_grafico
        
    return resultado

def analizar_comparacion_tarifas(resultados_tarifas: dict, graficar: bool = False) -> dict:
    """
    Prepara los datos y genera gráficos de comparación de tarifas para cada periodo.
    """
    if not graficar:
        return {"graficos_paths": {}}

    graficos_paths = {}
    for periodo, tarifas in resultados_tarifas.items():
        datos_grafico = {
            tarifa: {
                "fp": vals.get('cargo_fp', 0),
                "energia": vals.get('cargo_energia', 0),
                "demanda": vals.get('cargo_demanda', 0)
            } 
            for tarifa, vals in tarifas.items()
        }
        
        ruta_grafico = _get_image_path(f"comparacion_tarifas_{periodo}")
        visualize.graficar_comparacion_tarifas(
            datos_grafico,
            titulo=f"Comparación de Costos por Tarifa - {periodo}",
            guardar=True,
            ruta=ruta_grafico
        )
        graficos_paths[periodo] = ruta_grafico
        
    return {"graficos_paths": graficos_paths}
