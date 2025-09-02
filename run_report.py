from functions import *
import numpy as np


# --- CONFIGURACIÓN ---

titulo = "Hielería Azuero Principal"
EXTENDED_REPORT = False # Cambiar a True para el informe completo

nombre_archivo = "h azuero principal.txt"
tipo_energia = 'E.Activa III T'
tipo_demanda = 'DMAX_15min'
tarifas_disponibles = ["BTD", "BTH", "MTD", "MTH"]
periodos_disponibles = ["2025-JUL-DIC"]

# --- PARÁMETROS DE VOLTAJE ---

volt_linea = 480                                # Voltaje de línea en voltios
volt_fase = round(volt_linea / np.sqrt(3),0)    # Raíz cuadrada de 3 para voltaje de fase


# --- CARGA Y PROCESAMIENTO DE DATOS ---
df = cargar_datos(nombre_archivo)
df, df_arm = dividir_dataframe(df)
df_general, df_potencia, df_fasor, df_energia, df_coste, df_secundario = sub_dividir_dataframe(df)

# --- ANÁLISIS DE MÉTRICAS DE CALIDAD DE ENERGÍA ---
analisis_voltaje = voltaje(df, voltaje_referencia_ll=volt_linea, voltaje_referencia_ln=volt_fase, extended_report=EXTENDED_REPORT, graficar=True)
analisis_corriente = corriente(df, extended_report=EXTENDED_REPORT, graficar=True)
analisis_frecuencia = frecuencia(df, graficar=True)
analisis_factor_potencia = factor_potencia(df, graficar=True)
df, dmax_fila = procesar_demanda_maxima(df, graficar=True)
analisis_potencia_activa = potencia_activa(df, extended_report=EXTENDED_REPORT, graficar=True)
analisis_potencia_reactiva = potencia_reactiva(df, extended_report=EXTENDED_REPORT, graficar=True)
analisis_potencia_aparente = potencia_aparente(df, extended_report=EXTENDED_REPORT, graficar=False)
analisis_potencia_inductiva = potencia_inductiva(df, extended_report=EXTENDED_REPORT, graficar=True)
analisis_potencia_capacitiva = potencia_capacitiva(df, extended_report=EXTENDED_REPORT, graficar=True)
analisis_apagones = analisis_de_apagones(df, graficar=False)

# --- ANÁLISIS DE ENERGÍA Y DEMANDA ---
sum_actual, sum_bloque, energia_extrapolada, consumo_bloques_extrapolado = calcular_sumatoria_energia(df, tipo_energia)
dmax_total, dmax_fecha, dmax_bloques = calcular_maxima_demanda_por_bloque(df, tipo_demanda)


# --- CÁLCULOS DE TARIFAS ---
fp_mensual = analisis_factor_potencia["fp_mensual_calculado"]
resultados_tarifas = {}

for periodo in periodos_disponibles:
    resultados_tarifas[periodo] = {}
    for tarifa in tarifas_disponibles:
        if tarifa == "BTS":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTS(consumo_bloques_extrapolado, fp_mensual, dmax_total, periodo)
        elif tarifa == "BTSH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTSH(consumo_bloques_extrapolado, fp_mensual, dmax_total, periodo)
        elif tarifa == "BTD":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTD(consumo_bloques_extrapolado, fp_mensual, dmax_bloques, periodo)
        elif tarifa == "BTH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_BTH(consumo_bloques_extrapolado, dmax_bloques, fp_mensual, periodo)
        elif tarifa == "MTD":
            cargo_energia, cargo_demanda, cargo_fp = calcular_MTD(consumo_bloques_extrapolado, fp_mensual, dmax_bloques, periodo)
        elif tarifa == "MTH":
            cargo_energia, cargo_demanda, cargo_fp = calcular_MTH(consumo_bloques_extrapolado, dmax_bloques, fp_mensual, periodo)
        else:
            continue
        total = cargo_energia + cargo_demanda + cargo_fp
        resultados_tarifas[periodo][tarifa] = {
            "cargo_energia": cargo_energia,
            "cargo_demanda": cargo_demanda,
            "cargo_fp": cargo_fp,
            "total": total,
        }

# --- INFORME FINAL ---
print(f"\n===== INFORME DE ANÁLISIS ELÉCTRICO PARA: {titulo} =====")

# --- Resumen de Consumo y Demanda ---
print("\n\n===== RESUMEN DE CONSUMO Y DEMANDA =====")
print(f"\nEnergía mensual extrapolada: {energia_extrapolada:.2f} kWh")
print("\nConsumo por bloques (kWh, extrapolado):")
for bloque, val in consumo_bloques_extrapolado.items():
    print(f"  {bloque.title()}: {val:.2f} kWh")
print(f"\nDemanda máxima mensual (promedio 15 min): {dmax_total:.2f} kW")
print("Demanda máxima por bloque (kW):")
for bloque, val in dmax_bloques.items():
    print(f"  {bloque.title()}: {val:.2f} kW")

# --- Análisis de Calidad de Energía ---
print("\n\n===== ANÁLISIS DE CALIDAD DE ENERGÍA =====")

# Sección de Voltaje
print("\n--- ANÁLISIS DE VOLTAJE ---")
for nombre, stats in analisis_voltaje["estadisticas"].items():
    print(f"  {nombre}:")
    print(f"    Promedio: {stats['promedio']:.2f} V")
    print(f"    Máximo:   {stats['maximo']:.2f} V")
    print(f"    Mínimo:   {stats['minimo']:.2f} V")

if 'linea_linea' in analisis_voltaje['limites']:
    print("\n  Límites de Voltaje (Línea-Línea):")
    limites_ll = analisis_voltaje['limites']['linea_linea']
    print(f"    Referencia:    {limites_ll['referencia']:.2f} V")
    print(f"    Máx. Permitido: {limites_ll['max_permitido']:.2f} V")
    print(f"    Mín. Permitido: {limites_ll['min_permitido']:.2f} V")

if 'linea_neutro' in analisis_voltaje['limites']:
    print("\n  Límites de Voltaje (Línea-Neutro):")
    limites_ln = analisis_voltaje['limites']['linea_neutro']
    print(f"    Referencia:    {limites_ln['referencia']:.2f} V")
    print(f"    Máx. Permitido: {limites_ln['max_permitido']:.2f} V")
    print(f"    Mín. Permitido: {limites_ln['min_permitido']:.2f} V")

if analisis_voltaje["analisis_de_eventos"]:
    print("\n--- EVENTOS DE VOLTAJE FUERA DE RANGO ---")
    for col, eventos in analisis_voltaje["analisis_de_eventos"].items():
        print(f"  Análisis para: {col}")
        print(f"    Tiempo total fuera de rango: {eventos['tiempo_total_fuera_de_rango']}")
        if eventos['eventos_de_voltaje_alto']:
            print("    Eventos de Voltaje Alto:")
            for ev in eventos['eventos_de_voltaje_alto']:
                print(f"      - De {ev['inicio']} a {ev['fin']} (Duración: {ev['duracion']})")
                print(f"        Valor Máximo: {ev['valor_maximo']:.2f} V en {ev['fecha_valor_maximo']}")
        if eventos['eventos_de_voltaje_bajo']:
            print("    Eventos de Voltaje Bajo:")
            for ev in eventos['eventos_de_voltaje_bajo']:
                print(f"      - De {ev['inicio']} a {ev['fin']} (Duración: {ev['duracion']})")
                print(f"        Valor Mínimo: {ev['valor_minimo']:.2f} V en {ev['fecha_valor_minimo']}")

# Sección de Corriente
print("\n--- ANÁLISIS DE CORRIENTE ---")
for nombre, stats in analisis_corriente.items():
    print(f"  {nombre}:")
    print(f"    Promedio: {stats['promedio']:.2f} A")
    print(f"    Máximo:   {stats['maximo']:.2f} A")
    print(f"    Mínimo:   {stats['minimo']:.2f} A")

# Sección de Frecuencia
if analisis_frecuencia:
    print("\n--- ANÁLISIS DE FRECUENCIA ---")
    stats_frec = analisis_frecuencia['estadisticas']
    print(f"  Frecuencia:")
    print(f"    Promedio: {stats_frec['promedio']:.3f} Hz")
    print(f"    Máximo:   {stats_frec['maximo']:.3f} Hz")
    print(f"    Mínimo:   {stats_frec['minimo']:.3f} Hz")

    if 'permanente' in analisis_frecuencia['limites']:
        print("\n  Límites de Frecuencia (Permanente):")
        limites_perm = analisis_frecuencia['limites']['permanente']
        print(f"    Referencia:    {limites_perm['nominal']:.2f} Hz")
        print(f"    Máx. Permitido: {limites_perm['max_permitido']:.2f} Hz")
        print(f"    Mín. Permitido: {limites_perm['min_permitido']:.2f} Hz")

    if 'temporal' in analisis_frecuencia['limites']:
        print("\n  Límites de Frecuencia (Temporal):")
        limites_temp = analisis_frecuencia['limites']['temporal']
        print(f"    Referencia:    {limites_temp['nominal']:.2f} Hz")
        print(f"    Máx. Permitido: {limites_temp['max_permitido']:.2f} Hz")
        print(f"    Mín. Permitido: {limites_temp['min_permitido']:.2f} Hz")

# Sección de Factor de Potencia
print("\n--- ANÁLISIS DE FACTOR DE POTENCIA ---")
print(f"  FP Mensual Calculado: {analisis_factor_potencia['fp_mensual_calculado']:.4f}")
stats_fp_inst = analisis_factor_potencia['fp_instantaneo_stats']
if stats_fp_inst:
    print("  Estadísticas del FP Instantáneo (P/S):")
    print(f"    Promedio: {stats_fp_inst['promedio']:.4f}")
    print(f"    Máximo:   {stats_fp_inst['maximo']:.4f}")
    print(f"    Mínimo:   {stats_fp_inst['minimo']:.4f}")
limites_fp = analisis_factor_potencia['limites']
print(f"  Límite Superior: {limites_fp['superior']}")
print(f"  Límite Inferior: {limites_fp['inferior']}")

# --- ANÁLISIS DE POTENCIA ---
print("\n\n===== ANÁLISIS DE POTENCIA =====")

def print_power_analysis(title, analysis_result, unit="kW"):
    print(f"\n--- {title} ---")
    for col, data in analysis_result.items():
        print(f"  Análisis para: {col}")
        # General
        print(f"    General:")
        print(f"      Promedio: {data['general']['promedio']:.2f} {unit}")
        print(f"      Máximo:   {data['general']['maximo']:.2f} {unit}")
        print(f"      Mínimo:   {data['general']['minimo']:.2f} {unit}")
        # Por Bloque
        print(f"    Por Bloque:")
        for bloque, stats in data['por_bloque'].items():
            print(f"      {bloque.title()}:")
            print(f"        Promedio: {stats['promedio']:.2f} {unit}")
            print(f"        Máximo:   {stats['maximo']:.2f} {unit}")
            print(f"        Mínimo:   {stats['minimo']:.2f} {unit}")

print_power_analysis("Potencia Activa", analisis_potencia_activa)
print_power_analysis("Potencia Reactiva", analisis_potencia_reactiva, unit="kVAr")
print_power_analysis("Potencia Aparente", analisis_potencia_aparente, unit="kVA")
print_power_analysis("Potencia Inductiva", analisis_potencia_inductiva, unit="kVAr")
print_power_analysis("Potencia Capacitiva", analisis_potencia_capacitiva, unit="kVAr")

# --- Análisis de Apagones ---
print("\n\n===== ANÁLISIS DE APAGONES =====")
if analisis_apagones['numero_total_de_apagones'] > 0:
    print(f"  Número total de apagones: {analisis_apagones['numero_total_de_apagones']}")
    print(f"  Tiempo total sin suministro: {analisis_apagones['tiempo_total_sin_suministro']}")
    print("  Detalle de apagones:")
    for i, apagon in enumerate(analisis_apagones['detalle_de_apagones']):
        print(f"    - Apagón {i+1}: De {apagon['inicio']} a {apagon['fin']} (Duración: {apagon['duracion']})")
else:
    print("  No se detectaron apagones en el periodo analizado.")

# --- Comparación de Tarifas ---
print("\n\n===== COMPARACIÓN DE TARIFAS =====")
for periodo, tarifas in resultados_tarifas.items():
    print(f"\nPERIODO {periodo}:")
    for tarifa, valores in tarifas.items():
        print(f"  TARIFA {tarifa}:")
        print(f"    Cargo por energía:   B/. {valores['cargo_energia']:.2f}")
        print(f"    Cargo por demanda:   B/. {valores['cargo_demanda']:.2f}")
        print(f"    Penalización FP:     B/. {valores['cargo_fp']:.2f}")
        print(f"    TOTAL A PAGAR:       B/. {valores['total']:.2f}")

print("\n===== FIN DEL INFORME =====")
