"""
Gráficas del ERP.
- Diente de sierra: diagrama general de la política de inventario     [Guía diap. 17 + taller punto 9]
- Gráfico de demanda: ventas mes a mes (la "W" del tablero del profe)
 
Usa Altair (viene incluido con Streamlit).
"""
import math
 
import altair as alt
import pandas as pd
 
MESES = {"01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
         "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"}
 
 
def etiquetas_meses(meses):
    # Convierte "2025-10" en "Oct 2025"
    # Entra: lista de textos "AAAA-MM" | Sale: lista de textos "Mes AAAA"
    return [MESES[m[5:]] + " " + m[:4] for m in meses]
 
 
def simular_inventario(Q, d, R, m, ciclos=2.5, demora=0):
    # Simula el inventario día por día (lo que hace la tienda en la vida real)
    # Entra: Q = Q* | d = demanda diaria | R = punto de reorden | m = días del proveedor
    #        ciclos = cuántos ciclos mostrar | demora = días EXTRA que se demora el proveedor
    # Hace:  cada día se vende d; si el stock llega a R se hace un pedido,
    #        que llega m (+ demora) días después y suma Q unidades
    # Sale:  tabla (DataFrame) con Día, Inventario y los días en que se pidió / llegó
    T = Q / d                                   # días que dura un pedido
    dias_totales = math.ceil(T * ciclos)
    stock = Q                                   # empieza con un pedido completo
    llega_el_dia = None                         # día en que llega el pedido en camino (None = no hay)
    filas, pedidos, llegadas = [], [], []
    for dia in range(dias_totales + 1):
        if llega_el_dia is not None and dia >= llega_el_dia:   # ¿llegó el pedido hoy?
            stock += Q
            llega_el_dia = None
            llegadas.append(dia)
        filas.append({"Día": dia, "Inventario": stock})
        if llega_el_dia is None and stock <= R:                # ¿llegamos al punto de reorden?
            llega_el_dia = dia + m + demora
            pedidos.append(dia)
        stock = max(stock - d, 0)                              # se vende lo del día (no baja de 0)
    return pd.DataFrame(filas), pedidos, llegadas
 
 
def grafica_diente_sierra(tabla, R, SS_Q, pedidos, alto=320):
    # Dibuja el diente de sierra con las dos alarmas
    # Entra: tabla de simular_inventario | R (🟡) | SS_Q (🔴) | días de pedido
    # Sale:  gráfica de Altair
    linea = alt.Chart(tabla).mark_line(color="#1f77b4").encode(
        x=alt.X("Día:Q", title="Días"),
        y=alt.Y("Inventario:Q", title="Unidades en bodega"),
    )
    alarmas = pd.DataFrame({
        "Nivel": [R, SS_Q],
        "Alarma": [f"R - Punto de reorden ({R:,.0f})", f"SS - Stock de seguridad ({SS_Q:,.0f})"],
    })
    lineas_alarma = alt.Chart(alarmas).mark_rule(strokeDash=[6, 4], size=2).encode(
        y="Nivel:Q",
        color=alt.Color("Alarma:N", title="",
                        scale=alt.Scale(range=["#E6A700", "#D62728"]),
                        legend=alt.Legend(orient="bottom")),
    )
    puntos_pedido = alt.Chart(tabla[tabla["Día"].isin(pedidos)]).mark_point(
        color="#E6A700", size=80, filled=True).encode(x="Día:Q", y="Inventario:Q",
                                                       tooltip=["Día", "Inventario"])
    return (linea + lineas_alarma + puntos_pedido).properties(height=alto)
 
 
def grafica_demanda(meses, ventas, alto=140):
    # Gráfico de demanda: ventas mes a mes (pequeño, para el resumen)
    # Entra: meses ("AAAA-MM") | ventas | alto en píxeles
    # Sale:  gráfica de Altair
    etiquetas = etiquetas_meses(meses)
    datos = pd.DataFrame({"Mes": etiquetas, "Ventas": ventas})
    return alt.Chart(datos).mark_line(point=True).encode(
        x=alt.X("Mes:N", sort=etiquetas, title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Ventas:Q", title=None),
        tooltip=["Mes", "Ventas"],
    ).properties(height=alto)
 
 
# ---- Prueba: vasos (Q*=2240, d=34.4, R=202, m=5) ----
if __name__ == "__main__":
    tabla, pedidos, llegadas = simular_inventario(2240, 34.36, 201.6, 5)
    print("Pedidos en los días:", pedidos)
    print("Llegadas en los días:", llegadas)
    print("Inventario mínimo:", round(tabla["Inventario"].min(), 1))
    tabla2, p2, l2 = simular_inventario(2240, 34.36, 201.6, 5, demora=3)
    print("Con 3 días de demora, mínimo:", round(tabla2["Inventario"].min(), 1))

