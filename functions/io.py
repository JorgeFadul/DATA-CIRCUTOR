from pathlib import Path
import pandas as pd

from pathlib import Path
import pandas as pd


def cargar_datos(
    nombre_archivo: str | None = None,
    *,
    encoding: str = "latin-1",
    sep: str = ",",
    col_fecha: str = "Fecha/hora",
    formato: str = "%d/%m/%y %H:%M:%S",
) -> pd.DataFrame:
    """
    Carga un CSV/TXT y convierte in-place la columna `Fecha/hora` a datetime
    sin cambiar su nombre.

    Parameters
    ----------
    nombre_archivo : str
        Ruta al fichero.
    encoding : str, default 'latin-1'
        Codificación.
    sep : str, default ','
        Separador de campos.
    col_fecha : str, default 'Fecha/hora'
        Columna que contiene la fecha-hora.
    formato : str, default '%d/%m/%y %H:%M:%S'
        Formato exacto de la cadena de fecha-hora.

    Returns
    -------
    pd.DataFrame
    """
    if not nombre_archivo:
        raise ValueError("Debes indicar 'nombre_archivo'")

    ruta = Path(nombre_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {nombre_archivo}")

    # Leer el fichero con el separador indicado
    df = pd.read_csv(ruta, encoding=encoding, sep=sep)

    # Parsear la fecha EN LA MISMA COLUMNA, sin renombrarla
    if col_fecha in df.columns:
        df[col_fecha] = pd.to_datetime(df[col_fecha], format=formato, errors="coerce")

    # # Vista rápida
    # print(df.head())
    return df




'''
def cargar_datos(nombre_archivo: str | None = None, *, encoding: str = "latin-1") -> pd.DataFrame | None:
    """
    Carga un CSV por nombre o lanza una excepción si el archivo no existe.

    Parameters
    ----------
    nombre_archivo : str | None
        Ruta al fichero CSV.
    encoding : str
        Codificación.

    Returns
    -------
    pd.DataFrame | None
    """
    if not nombre_archivo:
        raise ValueError("Debes indicar 'nombre_archivo'")

    ruta = Path(nombre_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {nombre_archivo}")

    df = pd.read_csv(ruta, encoding=encoding)
    print(df.head())  # Muestra las primeras filas del DataFrame
    return df
'''