"""
Exportar los resultados del ERP a Excel (soporte de los cálculos)   [Taller punto 11]
"""
import io

import pandas as pd


def crear_excel(resumen, detalles):
    # Arma un archivo Excel en memoria
    # Entra: resumen = tabla con los 3 productos | detalles = {nombre de hoja: tabla}
    # Hace:  pone el resumen en la primera hoja y cada detalle en su propia hoja
    # Sale:  bytes del archivo .xlsx (para el botón de descarga)
    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as libro:
        resumen.to_excel(libro, sheet_name="Resumen", index=False)
        for nombre, tabla in detalles.items():
            tabla.to_excel(libro, sheet_name=nombre[:31], index=False)   # Excel acepta máx. 31 letras
        for hoja in libro.book.worksheets:                               # columnas más anchas
            for columna in hoja.columns:
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in columna)
                hoja.column_dimensions[columna[0].column_letter].width = min(ancho + 2, 45)
    return salida.getvalue()