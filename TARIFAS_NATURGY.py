
## Archivo que solo contiene las tarifas en un diccionario desde el 2025 hacia adelante, por favor colocar las siguientes luego de "2025-JUL-DIC"
# (Puede que en el futuro necesite hacerse mejor)


tarifas_edemet = {
    "2025-ENE-JUN": {                                               # TARIFAS EDEMET - 2025 - ENE - JUN
        "BTS": {
            "tipo": "Baja Tensión Simple",
            "cargo_fijo": 3.16,
            "bloques": {
                "11-300": 0.14718,
                "301-750": 0.20998,
                "751+": 0.30851
            },
            "conexion": 16.68,
            "cargo_fp": round(0.00874 + 0.00879 + 0.00142, 5)
        },
        "BTSH": {
            "tipo": "Baja Tensión Simple Horaria",
            "cargo_fijo": 3.07,
            "bloques": {
                "punta": 0.37708,
                "fuera_punta_medio": 0.18126,
                "fuera_punta_bajo": 0.10926
            },
            "conexion": 16.68,
            "cargo_fp": round(0.00831 + 0.00870 + 0.00140, 5)
        },
        "Prepago": {
            "tipo": "Baja Tensión Prepago",
            "cargo_fijo": 0.0,
            "bloques": {
                "0-300": 0.15458
            },
            "conexion": 16.68,
            "cargo_fp": round(0.00887 + 0.00891 + 0.00145, 5)
        },
        "BTD": {
            "tipo": "Baja Tensión con Demanda Máxima",
            "cargo_fijo": 5.68,
            "bloques": {
                "0-10000": 0.13580,
                "10001-30000": 0.14176,
                "30001-50000": 0.15333,
                "50001+": 0.16469
            },
            "conexion": 71.82,
            "cargo_fp": round(0.00815 + 0.00763 + 0.00134, 5),
            "cargo_demanda_maxima": 18.31
        },
        "BTH": {
            "tipo": "Baja Tensión por Bloque Horario",
            "cargo_fijo": 5.69,
            "bloques": {
                "punta": 0.26465,
                "fuera_punta_medio": 0.14420,
                "fuera_punta_bajo": 0.08021
            },
            "conexion": 71.82,
            "cargo_fp": round(0.01 + 0.00991 + 0.00133, 5),
            "cargo_demanda_maxima": {
                "punta": 18.81,
                "fuera_punta_medio": 2.71,
                "fuera_punta_bajo": 2.71
            }
        },
        "MTD": {
            "tipo": "Media Tensión con Demanda Máxima",
            "cargo_fijo": 14.32,
            "bloques": {
                "general": 0.14445
            },
            "conexion": 142.00,
            "cargo_fp": round(0.00815 + 0.00763 + 0.00134, 5),
            "cargo_demanda_maxima": 20.38
        },
        "MTH": {
            "tipo": "Media Tensión por Bloque Horario",
            "cargo_fijo": 14.38,
            "bloques": {
                "punta": 0.27184,
                "fuera_punta_medio": 0.15294,
                "fuera_punta_bajo": 0.08352
            },
            "conexion": 142.00,
            "cargo_fp": round(0.01 + 0.01000 + 0.00133, 5),
            "cargo_demanda_maxima": {
                "punta": 17.89,
                "fuera_punta_medio": 3.10,
                "fuera_punta_bajo": 3.10
            }
        }
    },
    "2025-JUL-DIC": {                                                   # TARIFAS EDEMET - 2025 - JUL - DIC
        "BTS": {
            "tipo": "Baja Tensión Simple",
            "cargo_fijo": 3.15,
            "bloques": {
                "11-300": 0.16170,
                "301-750": 0.23216,
                "751+": 0.34471
            },
            "conexion": 16.63,
            "cargo_fp": round(0.00869 + 0.01126 + 0.00142, 5)
        },
        "BTSH": {
            "tipo": "Baja Tensión Simple Horaria",
            "cargo_fijo": 3.05,
            "bloques": {
                "punta": 0.42650,
                "fuera_punta_medio": 0.20015,
                "fuera_punta_bajo": 0.11740
            },
            "conexion": 16.63,
            "cargo_fp": round(0.00825 + 0.01114 + 0.00140, 5)
        },
        "Prepago": {
            "tipo": "Baja Tensión Prepago",
            "cargo_fijo": 0.0,
            "bloques": {
                "0-300": 0.16823
            },
            "conexion": 16.63,
            "cargo_fp": round(0.00881 + 0.01141 + 0.00145, 5)
        },
        "BTD": {
            "tipo": "Baja Tensión con Demanda Máxima",
            "cargo_fijo": 5.64,
            "bloques": {
                "0-10000": 0.15634,
                "10001-30000": 0.16309,
                "30001-50000": 0.17619,
                "50001+": 0.18905
            },
            "conexion": 71.58,
            "cargo_fp": round(0.00809 + 0.00977 + 0.00134, 5),
            "cargo_demanda_maxima": 18.62
        },
        "BTH": {
            "tipo": "Baja Tensión por Bloque Horario",
            "cargo_fijo": 5.65,
            "bloques": {
                "punta": 0.30933,
                "fuera_punta_medio": 0.16917,
                "fuera_punta_bajo": 0.09491
            },
            "conexion": 71.58,
            "cargo_fp": round(0.00808 + 0.01268 + 0.00133, 5),
            "cargo_demanda_maxima": {
                "punta": 19.37,
                "fuera_punta_medio": 2.55,
                "fuera_punta_bajo": 2.55
            }
        },
        "MTD": {
            "tipo": "Media Tensión con Demanda Máxima",
            "cargo_fijo": 14.23,
            "bloques": {
                "general": 0.16591
            },
            "conexion": 142.00,
            "cargo_fp": round(0.00809 + 0.00977 + 0.00134, 5),
            "cargo_demanda_maxima": 20.86
        },
        "MTH": {
            "tipo": "Media Tensión por Bloque Horario",
            "cargo_fijo": 14.29,
            "bloques": {
                "punta": 0.31767,
                "fuera_punta_medio": 0.17930,
                "fuera_punta_bajo": 0.09873
            },
            "conexion": 142.00,
            "cargo_fp": round(0.00808 + 0.01280 + 0.00133, 5),
            "cargo_demanda_maxima": {
                "punta": 18.58,
                "fuera_punta_medio": 2.87,
                "fuera_punta_bajo": 2.87
            }
        }
    }
                                                                        # NOTA: COLOCAR AQUÍ TARIFAS 2026
}