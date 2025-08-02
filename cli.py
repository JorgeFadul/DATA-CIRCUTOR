"""
CLI de ejemplo: permite procesar un archivo CSV y mostrar
la energía total activa extrapolada a 30 días.
"""
import argparse
from pathlib import Path

import pandas as pd

from .io import cargar_datos
from .metrics import calcular_sumatoria_energia

TYPE_ENERGY = "E.Activa III T"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analítica Circutor MYeBOX 150")
    parser.add_argument("csv", type=Path, help="Ruta al CSV exportado")
    args = parser.parse_args()

    df = cargar_datos(str(args.csv))
    energia_total, _, energia_30d, _ = calcular_sumatoria_energia(df, TYPE_ENERGY)
    print(f"Energía medida  : {energia_total:.2f} kWh")
    print(f"Energía 30 días : {energia_30d:.2f} kWh")


if __name__ == "__main__":
    main()
