"""
Funciones de clasificación de bloques horarios de Edemet.
"""

from __future__ import annotations

import pandas as pd


def _hora(dt) -> tuple[int, int, int]:
    """Devuelve (HH,MM,SS) para evitar múltiples `pd.to_datetime`."""
    t = dt.time()
    return t.hour, t.minute, t.second


def clasificar_bloque(dt) -> str:
    """
    Asigna 'punta', 'fuera_punta_medio' o 'fuera_punta_bajo' según
    día y hora (regla Edemet).
    """
    h, m, _ = _hora(dt)
    dia = dt.weekday()  # lunes = 0

    def in_range(hh_mm, hh_mm2):
        h1, m1 = hh_mm
        h2, m2 = hh_mm2
        return (h, m) >= (h1, m1) and (h, m) <= (h2, m2)

    if dia < 5:  # L-V
        if in_range((9, 0), (17, 0)):
            return "punta"
        if in_range((17, 1), (23, 59)):
            return "fuera_punta_medio"
        return "fuera_punta_bajo"
    if dia == 5:  # sábado
        if in_range((11, 0), (22, 59)):
            return "fuera_punta_medio"
        return "fuera_punta_bajo"
    return "fuera_punta_bajo"
