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
        "Alarma": [f"Alarma R ({R:,.0f})", f"SS - Stock de seguridad ({SS_Q:,.0f})"],
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


def _dibujo_ciclo(Q, T, R, SS_Q, dia_alarma, x_min, x_max, y_min, y_max, tramos, alto, titulo, texto_pr=None):
    # dibuja el ciclo con la escala que se le pase (se usa para la grafica completa y para el zoom)
    eje_y = alt.Axis(labelExpr="datum.value < 0 ? '' : format(datum.value, ',')")   # no mostrar numeros negativos
    linea = alt.Chart(pd.DataFrame({"Día": [0, T], "Inventario": [Q, 0]})).mark_line(
        color="#1f77b4", strokeWidth=3, clip=True).encode(
        x=alt.X("Día:Q", title="Días", scale=alt.Scale(domain=[x_min, x_max])),
        y=alt.Y("Inventario:Q", title="Unidades", scale=alt.Scale(domain=[y_min, y_max]), axis=eje_y),
    )
    # zona de riesgo: desde que suena la alarma hasta que se acaba el inventario
    zona = alt.Chart(pd.DataFrame({"Día": [dia_alarma, T], "Inventario": [R, 0]})).mark_area(
        color="#D62728", opacity=0.25, clip=True).encode(x="Día:Q", y="Inventario:Q", y2=alt.datum(0))
    niveles = pd.DataFrame({"y": [R, SS_Q], "color": ["#E6A700", "#D62728"],
                            "texto": [f"Alarma = {R:,.0f} und", f"SS = {SS_Q:,.1f} und"], "dy": [-8, 12]})
    lineas = alt.Chart(niveles).mark_rule(strokeDash=[6, 4], size=2).encode(
        y="y:Q", color=alt.Color("color:N", scale=None))
    texto_alarma = alt.Chart(niveles.iloc[[0]]).mark_text(align="left", dx=4, dy=-8, fontSize=12, fontWeight="bold").encode(
        x=alt.datum(x_min), y="y:Q", text="texto:N", color=alt.Color("color:N", scale=None))
    texto_ss = alt.Chart(niveles.iloc[[1]]).mark_text(align="left", dx=4, dy=12, fontSize=12, fontWeight="bold").encode(
        x=alt.datum(x_min), y="y:Q", text="texto:N", color=alt.Color("color:N", scale=None))
    vertical = alt.Chart(pd.DataFrame({"x": [dia_alarma]})).mark_rule(strokeDash=[2, 3], color="gray").encode(x="x:Q")
    capas = [zona, linea, lineas, texto_alarma, texto_ss, vertical]
    if texto_pr:
        capas.append(alt.Chart(pd.DataFrame({"x": [dia_alarma], "y": [y_max * 0.55], "t": [texto_pr]})).mark_text(
            align="right", dx=-6, fontSize=12, color="#333").encode(x="x:Q", y="y:Q", text="t:N"))
    # medidas de abajo (como las flechas del dibujo del profe)
    tramos = tramos.copy()
    tramos["medio"] = (tramos["x"] + tramos["x2"]) / 2
    capas.append(alt.Chart(tramos).mark_rule(color="#555").encode(x="x:Q", x2="x2:Q", y="y:Q"))
    marcas = pd.DataFrame({"x": list(tramos["x"]) + list(tramos["x2"]), "y": list(tramos["y"]) * 2})
    capas.append(alt.Chart(marcas).mark_tick(orient="vertical", color="#555", thickness=1.5, size=10).encode(x="x:Q", y="y:Q"))
    capas.append(alt.Chart(tramos).mark_text(dy=-8, fontSize=11, color="#333").encode(x="medio:Q", y="y:Q", text="texto:N"))
    return alt.layer(*capas).properties(height=alto, title=titulo)


def grafica_politica_clase(Q, T, R, SS_Q, dias_stock, m, dias_SS, PR, alto=320, con_zoom=True):
    # la grafica que hizo el profe en los apuntes: un ciclo de inventario
    # empieza en Q* y baja hasta 0 en T dias, con la Alarma, el SS y la zona de riesgo
    # abajo los dias: dias de stock + m + dias de SS = T
    # como la zona de riesgo sale muy pequeña, se agrega una segunda grafica con zoom a esa parte
    dia_alarma = dias_stock                      # el dia en que el inventario llega a la alarma
    # grafica completa
    y1, y2 = -Q * 0.08, -Q * 0.17
    tramos = pd.DataFrame({"x": [0, 0], "x2": [dia_alarma, T], "y": [y1, y2],
                           "texto": [f"Días de stock: {dias_stock:,.1f}", f"T = {T:,.1f} días"]})
    completa = _dibujo_ciclo(Q, T, R, SS_Q, dia_alarma, 0, T * 1.05, -Q * 0.22, Q * 1.08, tramos, alto,
                             "Ciclo completo", f"Aquí se pide el PR = {PR:,.0f} und")
    if not con_zoom:                             # en el resumen solo va la grafica completa
        return completa
    # zoom a la zona de riesgo
    ancho = T - dia_alarma
    x_min, x_max = dia_alarma - ancho * 0.8, T + ancho * 0.25
    y_max = R * 1.9
    z1 = -y_max * 0.15
    tramos_zoom = pd.DataFrame({"x": [dia_alarma, dia_alarma + m], "x2": [dia_alarma + m, T], "y": [z1, z1],
                                "texto": [f"m = {m} días", f"SS = {dias_SS:,.1f} días"]})
    zoom = _dibujo_ciclo(Q, T, R, SS_Q, dia_alarma, x_min, x_max, -y_max * 0.25, y_max, tramos_zoom, alto * 0.75,
                         "Zoom a la zona de riesgo")
    return alt.vconcat(completa, zoom)


# prueba con numeros de ejemplo (Q*=2240, d=34.36, R=202, m=5)
if __name__ == "__main__":
    tabla, pedidos, llegadas = simular_inventario(2240, 34.36, 201.6, 5)
    print("Pedidos en los días:", pedidos)
    print("Llegadas en los días:", llegadas)
    print("Inventario mínimo:", round(tabla["Inventario"].min(), 1))
    tabla2, p2, l2 = simular_inventario(2240, 34.36, 201.6, 5, demora=3)
    print("Con 3 días de demora, mínimo:", round(tabla2["Inventario"].min(), 1))
