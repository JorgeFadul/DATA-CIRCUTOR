from functions import *
import numpy as np


# --- CONFIGURACIÓN ---

titulo = "Hielería Azuero Principal"

nombre_archivo = "h azuero principal.txt"
tipo_energia = 'E.Activa III T'
tipo_demanda = 'DMAX_15min'
tarifas_disponibles = ['BTS', 'BTSH', "BTD", "BTH", "MTD", "MTH"]
periodos_disponibles = ["2025-JUL-DIC"]

# --- PARÁMETROS DE VOLTAJE ---

volt_linea = 480                                # Voltaje de línea en voltios
volt_fase = round(volt_linea / np.sqrt(3),0)    # Raíz cuadrada de 3 para voltaje de fase


# Límites de voltaje
volt_fase_max = volt_fase * 1.05    # Voltaje de fase máximo
volt_fase_min = volt_fase * 0.95    # Voltaje de fase mínimo
volt_linea_max = volt_linea * 1.05       # Voltaje de línea máximo
volt_linea_min = volt_linea * 0.95       # Voltaje de línea mínimo

# --- CARGA Y PROCESAMIENTO DE DATOS ---
df = cargar_datos(nombre_archivo)


df, df_arm = dividir_dataframe(df)
df_general, df_potencia, df_fasor, df_energia, df_coste, df_secundario = sub_dividir_dataframe(df)
df, fp_mensual = agregar_factor_potencia_mensual(df)
df = procesar_demanda_maxima(df)

# --- ANÁLISIS DE ENERGÍA Y DEMANDA ---
sum_actual, sum_bloque, energia_extrapolada, consumo_bloques_extrapolado = calcular_sumatoria_energia(df, tipo_energia)
dmax_total, dmax_fecha, dmax_bloques = calcular_maxima_demanda_por_bloque(df, tipo_demanda)

# --- PROMEDIOS DIARIOS ---

df_sab_dom = promediar_df_por_min(
    df,
    dias_semana=['sábado', 'domingo']
)
df_sab_dom = procesar_demanda_maxima(df_sab_dom)
dmax_prom_total, dmax_hora, dmax_bloq = calcular_maxima_demanda_por_bloque(df_sab_dom, "DMAX_15min")
graficar_parametros(df_sab_dom,["P.Activa III T","DMAX_15min"], lineas_horizontales=[dmax_prom_total])

df_lun_vie = promediar_df_por_min(
    df,
    dias_semana=['lunes', 'martes', 'miércoles', 'jueves', 'viernes']
)
df_lun_vie = procesar_demanda_maxima(df_lun_vie)
dmax_prom_total, dmax_hora, dmax_bloq = calcular_maxima_demanda_por_bloque(df_lun_vie, "DMAX_15min")
graficar_parametros(df_lun_vie,["P.Activa III T","DMAX_15min"], lineas_horizontales=[dmax_prom_total])

df_prom_total = promediar_df_por_min(
    df,
)
df_prom_total = procesar_demanda_maxima(df_prom_total)
dmax_prom_total, dmax_hora, dmax_bloq = calcular_maxima_demanda_por_bloque(df_prom_total, "DMAX_15min")
graficar_parametros(df_prom_total,["P.Activa III T","DMAX_15min"], lineas_horizontales=[dmax_prom_total])


# --- VISUALIZACIONES ---

graficar_parametros(df, [('Tensión L1',"red"), ('Tensión L2',"blue"), ("Tensión L3", "yellow")], lineas_horizontales=[(volt_fase, "green"),volt_fase*0.95,volt_fase*1.05], limite_inferior=volt_fase_min-30, limite_superior=volt_fase_max+30, titulo="Tensión de Fase")
graficar_parametros(df, ["Tensión L1L2L3"], lineas_horizontales=[(volt_linea, "green"),volt_linea_max,volt_linea_min], limite_inferior=volt_linea_min-30, limite_superior=volt_linea_max+30, titulo="Tensión de Línea")
graficar_parametros(df, [('P/S',"orange")], lineas_horizontales=[(1, "green"),0.9,-0.9], limite_inferior=np.min(df["P/S"])-0.1, limite_superior=np.max(df["P/S"])+0.1,titulo="Factor de Potencia Instantáneo")

graficar_parametros(df_sab_dom, ["P.Activa III T", "P.Reactiva III T"])
graficar_parametros(df_lun_vie, ["P.Activa III T", "P.Reactiva III T"])

graficar_consumo_por_bloque(consumo_bloques_extrapolado, titulo="Consumo Mensual por Bloque Horario")
graficar_demanda_maxima_por_bloque(dmax_bloques, titulo="Demanda Máxima Mensual por Bloque Horario")

graficar_consumo_anillo(consumo_bloques_extrapolado, titulo="Consumo Mensual por Bloque Horario (Anillo)")
graficar_demanda_maxima_anillo(dmax_bloques, titulo="Demanda Máxima Mensual por Bloque Horario (Anillo)")

graficar_consumo_polar(consumo_bloques_extrapolado, titulo="Consumo Mensual en Reloj de 24 Horas")
graficar_demanda_maxima_polar(dmax_bloques, titulo="Demanda Máxima Mensual en Reloj de 24 Horas")

print("\nGráfica de Energía Activa y Reactiva:")
graficar_parametros(df, ['E.Activa III T', 'E.Reactiva III T'])
print("\nGráfica de Demanda Máxima (15 minutos):")
graficar_parametros(df, [tipo_demanda], lineas_horizontales=[dmax_total])

# --- VISUALIZACIÓN DE TENSIÓN ---

min_volt = np.min(df["Tensión L12"])
max_volt = np.max(df["Tensión L12"])
print(f"V_min: {min_volt} V")
print(f"V_max: {max_volt} V")

# --- CÁLCULOS DE TARIFAS ---
resultados_tarifas = {}

for periodo in periodos_disponibles:
    print(f"\n\n========== PERIODO: {periodo} ==========")
    resultados_tarifas[periodo] = {}

    for tarifa in tarifas_disponibles:

        # ── Llama a la función correcta ───────────────────────────────────────────
        if tarifa == "BTS":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTS(
                consumo_bloques_extrapolado, fp_mensual, dmax_total, periodo
            )
        elif tarifa == "BTSH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTSH(
                consumo_bloques_extrapolado, fp_mensual, dmax_total, periodo
            )
        elif tarifa == "BTD":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTD(
                consumo_bloques_extrapolado, fp_mensual, dmax_bloques, periodo
            )
        elif tarifa == "BTH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTH(
                consumo_bloques_extrapolado, dmax_bloques, fp_mensual, periodo
            )
        elif tarifa == "MTD":
            cargo_energia, cargo_demanda, cargo_fp = calcular_MTD(
                consumo_bloques_extrapolado, fp_mensual, dmax_bloques, periodo
            )
        elif tarifa == "MTH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_MTH(
                consumo_bloques_extrapolado, dmax_bloques, fp_mensual, periodo
            )
        else:
            continue

        total = cargo_energia + cargo_demanda + cargo_fp

        # ── Guarda TO DO lo que necesitas para el resumen ─────────────────────────
        resultados_tarifas[periodo][tarifa] = {
            "cargo_energia": cargo_energia,
            "cargo_demanda": cargo_demanda,
            "cargo_fp": cargo_fp,
            "total": total,
        }

# --- INFORME FINAL COMPARATIVO ---
print("\n===== INFORME COMPARATIVO ENTRE TARIFAS =====")
print(f"Energía mensual real: {sum_actual:.2f} kWh")
print(f"Energía mensual extrapolada: {energia_extrapolada:.2f} kWh")

print("\nConsumo por bloques (kWh, extrapolado):")
for bloque, val in consumo_bloques_extrapolado.items():
    print(f"  {bloque}: {val:.2f} kWh")

print(f"\nDemanda máxima mensual (promedio 15 min): {dmax_total:.2f} kW")
print("Demanda máxima por bloque (kW):")
for bloque, val in dmax_bloques.items():
    print(f"  {bloque}: {val:.2f} kW")


print(f"\nFactor de potencia mensual: {fp_mensual:.4f}")

print("\n--- COMPARACIÓN DE RESULTADOS POR TARIFA Y PERIODO ---")
for periodo, tarifas in resultados_tarifas.items():
    print(f"\nPERIODO {periodo}:")
    for tarifa, valores in tarifas.items():
        print(f"  TARIFA {tarifa}:")
        print(f"    Cargo por energía:   B/. {valores['cargo_energia']:.2f}")
        print(f"    Cargo por demanda:   B/. {valores['cargo_demanda']:.2f}")
        print(f"    Penalización FP:     B/. {valores['cargo_fp']:.2f}")
        print(f"    TOTAL A PAGAR:       B/. {valores['total']:.2f}")

print("\n===== FIN DEL INFORME =====")