"""
Para descargar los resultados en Excel (el excel de soporte del punto 11 del taller)
"""
import io

import pandas as pd


def crear_excel(resumen, detalles):
    # arma el excel en memoria (no lo guarda en el pc, lo manda al boton de descarga)
    # resumen = tabla con los 3 productos, va en la primera hoja
    # detalles = diccionario {nombre de la hoja: tabla}, cada uno va en otra hoja
    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as libro:
        resumen.to_excel(libro, sheet_name="Resumen", index=False)
        for nombre, tabla in detalles.items():
            tabla.to_excel(libro, sheet_name=nombre[:31], index=False)   # excel no deja nombres de hoja de mas de 31 letras
        for hoja in libro.book.worksheets:                               # esto es para que las columnas no queden tan angostas
            for columna in hoja.columns:
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in columna)
                hoja.column_dimensions[columna[0].column_letter].width = min(ancho + 2, 45)
    return salida.getvalue()
