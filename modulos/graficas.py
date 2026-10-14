"""
Graficas del ERP
- diente de sierra: como va bajando y subiendo el inventario (punto 9 del taller)
- grafico de demanda: las ventas mes a mes

Se hacen con Altair que ya viene con Streamlit.
"""
import math

import altair as alt
import pandas as pd

MESES = {"01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
         "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"}


def etiquetas_meses(meses):
    # cambia "2025-10" por "Oct 2025" para que se vea mejor en la grafica
    # m[5:] es el mes y m[:4] es el año
    return [MESES[m[5:]] + " " + m[:4] for m in meses]


def simular_inventario(Q, d, R, m, ciclos=2.5, demora=0):
    # simula el inventario dia por dia para poder dibujar el diente de sierra
    # todos los dias se venden d unidades
    # cuando el stock baja a R se hace el pedido, y llega m dias despues
    # demora = dias de mas que se demora el proveedor (para probar que pasa si se atrasa)
    # devuelve la tabla de dias e inventario, y los dias en que se pidio y en que llego
    T = Q / d                                   # dias que dura un pedido
    dias_totales = math.ceil(T * ciclos)
    stock = Q                                   # se empieza con un pedido lleno
    llega_el_dia = None                         # None = no hay pedido en camino
    filas, pedidos, llegadas = [], [], []
    for dia in range(dias_totales + 1):
        if llega_el_dia is not None and dia >= llega_el_dia:   # si hoy llega el pedido se suma Q
            stock += Q
            llega_el_dia = None
            llegadas.append(dia)
        filas.append({"Día": dia, "Inventario": stock})
        if llega_el_dia is None and stock <= R:                # si llego a R y no hay pedido en camino, se pide
            llega_el_dia = dia + m + demora
            pedidos.append(dia)
        stock = max(stock - d, 0)                              # se resta lo del dia, max(...,0) para que no quede negativo
    return pd.DataFrame(filas), pedidos, llegadas


def grafica_diente_sierra(tabla, R, SS_Q, pedidos, alto=320):
    # dibuja el inventario con las 2 lineas de alarma (R amarilla y SS roja)
    # y un punto en cada dia que se hizo pedido
    linea = alt.Chart(tabla).mark_line(color="#1f77b4").encode(
        x=alt.X("Día:Q", title="Días"),
        y=alt.Y("Inventario:Q", title="Unidades en bodega"),
    )
    alarmas = pd.DataFrame({
        "Nivel": [R, SS_Q],
        "Alarma": [f"R - Punto de reorden ({R:,.0f})", f"SS - Stock de seguridad ({SS_Q:,.0f})"],
    })
    # mark_rule hace lineas horizontales, strokeDash es para que sean punteadas
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
    # grafica pequeña de las ventas por mes (la que va en el resumen)
    etiquetas = etiquetas_meses(meses)
    datos = pd.DataFrame({"Mes": etiquetas, "Ventas": ventas})
    return alt.Chart(datos).mark_line(point=True).encode(
        x=alt.X("Mes:N", sort=etiquetas, title=None, axis=alt.Axis(labelAngle=-45)),  # sort para que no los ordene alfabetico
        y=alt.Y("Ventas:Q", title=None),
        tooltip=["Mes", "Ventas"],
    ).properties(height=alto)


# prueba con los vasos (Q*=2240, d=34.36, R=202, m=5)
if __name__ == "__main__":
    tabla, pedidos, llegadas = simular_inventario(2240, 34.36, 201.6, 5)
    print("Pedidos en los días:", pedidos)
    print("Llegadas en los días:", llegadas)
    print("Inventario mínimo:", round(tabla["Inventario"].min(), 1))
    tabla2, p2, l2 = simular_inventario(2240, 34.36, 201.6, 5, demora=3)
    print("Con 3 días de demora, mínimo:", round(tabla2["Inventario"].min(), 1))
