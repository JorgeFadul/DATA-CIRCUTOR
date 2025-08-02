from pathlib import Path
import pandas as pd


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
    return df
