"""
OptiStock - ERP de inventarios (esta es la pagina, lo que ve el usuario)
Para abrirlo: python -m streamlit run app.py

Los calculos estan en la carpeta modulos:
- pronostico.py: modulo 1, pronostico de la demanda
- eoq.py: modulo 2, lote economico
- seguridad.py: modulo 3, stock de seguridad y punto de reorden
- graficas.py: el diente de sierra y la grafica de ventas
- exportar.py: el excel que se descarga

como ejecutar todo python -m streamlit run app.py
"""
import altair as alt
import pandas as pd
import streamlit as st

from modulos import pronostico, eoq, seguridad, graficas, exportar

st.set_page_config(page_title="OptiStock ERP", page_icon="📦", layout="wide")
st.title("📦 OptiStock - ERP de Inventarios")
st.caption("Tienda de vajilla: pronóstico, lote económico y punto de reorden")

# CSS para que los cuadros de resultados salgan verdes
st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: #E8F5E9;
        border-left: 5px solid #2E9E6B;
        padding: 12px 16px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Datos ----------------
productos = pd.read_csv("datos/productos.csv")
ventas = pd.read_csv("datos/ventas.csv")
INICIO = 4                    # desde el mes 4 se prueban los metodos (la MM N=4 necesita 4 meses)

# ---------------- Barra lateral ----------------
st.sidebar.title("📦 OptiStock")
st.sidebar.caption("ERP de inventarios EOQ")
producto = st.sidebar.selectbox("Producto", productos["producto"])
fila = productos[productos["producto"] == producto].iloc[0]          # la fila del producto en productos.csv

# sensibilidad (punto 2 del taller): se pueden cambiar los valores y todo se recalcula
st.sidebar.subheader("Parámetros")
st.sidebar.caption("Si cambia un valor, se recalcula todo (análisis de sensibilidad).")
Cu = st.sidebar.number_input("Cu - Costo unitario ($)", min_value=1.0,
                             value=float(fila["Cu"]), step=500.0, key=f"Cu_{producto}")
Cp = st.sidebar.number_input("Cp - Costo de pedir ($)", min_value=1.0,
                             value=float(fila["Cp"]), step=10000.0, key=f"Cp_{producto}")
i = st.sidebar.number_input("i - % de almacenamiento al año", min_value=0.01, max_value=1.0,
                            value=float(fila["i"]), step=0.01, key=f"i_{producto}")
m = st.sidebar.number_input("m - Días del proveedor", min_value=1,
                            value=int(fila["m"]), step=1, key=f"m_{producto}")
NIVELES = {"90 % (Z = 1.28)": 1.28, "95 % (Z = 1.65)": 1.65, "99 % (Z = 2.33)": 2.33}
nivel = st.sidebar.selectbox("Nivel de servicio", list(NIVELES), index=1, key=f"Z_{producto}")
Z = NIVELES[nivel]
tipo_sigma = st.sidebar.radio(
    "σ para el stock de seguridad",
    ["Mensual", "Anual (σ × √12)"],
    help="La anual es para que quede en el mismo periodo que D.",
)
usar_sigma_anual = tipo_sigma.startswith("Anual")

# cambiar la demanda anual y ver que pasa
st.sidebar.subheader("Demanda")
usar_D_manual = st.sidebar.checkbox("Cambiar la demanda anual D", key=f"chkD_{producto}")
D_manual = None                      # None = se usa el pronóstico
if usar_D_manual:
    D_manual = st.sidebar.number_input("D - Demanda anual (und)", min_value=1,
                                       value=1000, step=100, key=f"D_{producto}")
    
DIAS = int(fila["dias_operacion"])


def calcular_producto(nombre, Cu, Cp, i, m, Z, D_manual=None):
    # corre los 3 modulos para un producto y devuelve todo en un diccionario
    lista = ventas[nombre].tolist()
    resultados, ganador, pron, D = pronostico.elegir_mejor(lista, INICIO) 
    if D_manual is not None:         # si puso una D, se usa esa en vez del pronóstico
        D = D_manual                 # módulo 1
    r = eoq.calcular_eoq(D, Cu, Cp, i, DIAS)                                                  # módulo 2
    p = seguridad.calcular_politica(lista, D, r["Q*"], r["T"], Z, m, DIAS, usar_sigma_anual)  # módulo 3
    return {"lista": lista, "resultados": resultados, "ganador": ganador, "pron": pron,
            "D": D, "r": r, "p": p, "m": m, "Cu": Cu, "Cp": Cp, "i": i, "Z": Z}


# el producto escogido usa los valores de la barra lateral
calc = calcular_producto(producto, Cu, Cp, i, m, Z, D_manual)
lista, resultados, ganador, pron, D, r, p = (calc[k] for k in
                                             ["lista", "resultados", "ganador", "pron", "D", "r", "p"])

tab_datos, tab_pron, tab_eoq, tab_venta, tab_resumen = st.tabs(
    ["Datos", "Pronóstico", "EOQ", "Política y ventas", "Resumen"])

# ---------------- Pestaña Datos ----------------
with tab_datos:
    st.header(f"Datos de {producto}")
    st.info(
        "Ventas de los últimos 24 meses y costos del producto. "
        "Cu = costo unitario, Cp = costo de pedir, i = % de almacenamiento, "
        "m = días que tarda el proveedor, Z = nivel de servicio."
    )
    st.caption("Datos reales: ventas de una tienda online pequeña del Reino Unido (dataset Online Retail II, "
               "UCI Machine Learning Repository), de diciembre 2009 a noviembre 2011. Productos de la colección "
               "Red Retrospot. Precios pasados a pesos con 1 £ = 4.550 COP. Cp, i y m son supuestos.")
    st.subheader(f"Costos - {producto}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cu - Costo unitario", f"${Cu:,.0f}")
    c2.metric("Cp - Costo de pedir", f"${Cp:,.0f}")
    c3.metric("i - % de almacenamiento al año", f"{i:.0%}")
    c4, c5, c6 = st.columns(3)
    c4.metric("m - Días del proveedor", f"{m} días")
    c5.metric("Z - Nivel de servicio", f"{Z}  ({nivel[:4].strip()})")
    c6.metric("Días de operación al año", f"{DIAS}")

    st.subheader(f"Ventas mensuales - {producto}")
    st.dataframe(
        ventas[["mes", producto]].rename(columns={"mes": "Mes", producto: "Ventas (unidades)"}),
        hide_index=True,
    )

# ---------------- Pestaña Pronóstico (módulo 1) ----------------
with tab_pron:
    st.header(f"Pronóstico de {producto}")
    st.info(
        "Probamos 5 modelos (media móvil y ponderado) y sacamos el MSE de cada uno. "
        "El que tenga menor MSE es el que usamos para el pronóstico del próximo mes, "
        "y D = pronóstico x 12."
    )
    st.subheader("Comparación de modelos (MSE)")
    tabla_mse = pd.DataFrame({"Modelo": list(resultados.keys()), "MSE": list(resultados.values())})
    st.dataframe(tabla_mse.style.format({"MSE": "{:,.1f}"}), hide_index=True)
    st.success(f"Modelo ganador: {ganador} (menor error)")

    c1, c2 = st.columns(2)
    c1.metric(f"{producto}: pronóstico próximo mes", f"{pron:,.2f}")
    c2.metric(f"{producto}: demanda anual (D)", f"{D:,.2f}")

    st.subheader("Ventas reales vs. pronóstico")
    predichos = pronostico.predicciones_modelo(lista, ganador, INICIO)
    etiquetas = graficas.etiquetas_meses(ventas["mes"])
    datos = pd.DataFrame({
        "Mes": etiquetas,
        "Ventas reales": lista,
        f"Pronóstico ({ganador})": [None] * INICIO + predichos,
    })
    largo = datos.melt("Mes", var_name="Serie", value_name="Unidades")
    grafico = alt.Chart(largo).mark_line(point=True).encode(
        x=alt.X("Mes:N", sort=etiquetas, title="Mes"),
        y=alt.Y("Unidades:Q", title="Unidades"),
        color=alt.Color("Serie:N", title=""),
    )
    st.altair_chart(grafico, width="stretch")

# ---------------- Pestaña EOQ (módulo 2) ----------------
with tab_eoq:
    st.header(f"Lote económico de pedido (EOQ) - {producto}")
    st.info(
        "Q* es la cantidad que hay que pedir cada vez para que el costo total sea el menor. "
        "Si se pide poco toca hacer muchos pedidos, y si se pide mucho sale caro almacenar."
    )
    st.subheader("Cuánto pedir")
    c1, c2, c3 = st.columns(3)
    c1.metric("Q* - Cantidad óptima por pedido", f"{r['Q*']:,.0f} und")
    c2.metric("N - Pedidos al año", f"{r['N']:,.2f}")
    c3.metric("T - Días que dura cada pedido", f"{r['T']:,.1f} días")

    st.subheader("Costos anuales")
    c4, c5, c6, c7 = st.columns(4)
    c4.metric("Costo de pedir", f"${r['Costo de pedir']:,.0f}")
    c5.metric("Costo de almacenar", f"${r['Costo de almacenar']:,.0f}")
    c6.metric("Costo de mercancía", f"${r['Costo de mercancía']:,.0f}")
    c7.metric("CT - Costo total", f"${r['CT']:,.0f}")

    st.caption(f"D = {D:,.0f} und/año, Ch = i x Cu = ${r['Ch']:,.0f} por unidad al año")
    st.success(f"Cada pedido de {producto.lower()} debe ser de {r['Q*']:,.0f} unidades.")

# ---------------- Pestaña Política y ventas (módulo 3) ----------------
with tab_venta:
    st.header(f"Política de inventario y punto de reorden - {producto}")
    st.info(
        "Al registrar una venta se resta del stock y se revisan dos alarmas: "
        "🟡 alarma (R): hay que hacer el pedido. "
        "🔴 reserva de seguridad (SS_Q): ya se está usando."
    )

    st.subheader("Cuándo pedir")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("σ - Desviación de las ventas", f"{p['σ']:,.1f} und")
    c2.metric("SS - Stock de seguridad del año (Z × σ)", f"{p['SS']:,.1f} und")
    c3.metric("🔴 SS_Q (alarma crítica)", f"{p['SS_Q']:,.0f} und")
    c4.metric("🟡 Alarma (R = d x m + SS)", f"{p['R']:,.0f} und")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("d - Demanda diaria", f"{p['d']:,.1f} und/día")
    c6.metric("Días de stock", f"{p['Días de stock']:,.1f} días")
    c7.metric("m - Días del proveedor", f"{m} días")
    c8.metric("Días de SS", f"{p['Días de SS']:,.1f} días")
    st.subheader("Cuánto pedir cuando suena la alarma")
    c9, c10, c11 = st.columns(3)
    c9.metric("Pedidos completos de Q* en el año", f"{p['Pedidos completos']}")
    c10.metric("Faltante del año (D - pedidos x Q*)", f"{p['Faltante del año']:,.0f} und")
    c11.metric("PR - Punto de reorden (último pedido)", f"{p['PR']:,.0f} und")
    st.caption("PR = lo que falta para completar la demanda del año menos el SS (como en el tablero: 5000 - 3162,3 - 52,17 = 1785,53).")
    st.success(
        f"Cuando queden {p['R']:,.0f} {producto.lower()} suena la alarma y se pide: "
        f"{r['Q*']:,.0f} und en los pedidos normales y {p['PR']:,.0f} und (PR) en el último del año."
    )

    # grafica de la politica como la de los apuntes del profe
    st.subheader("Gráfica de la política de inventario")
    st.altair_chart(graficas.grafica_politica_clase(r["Q*"], r["T"], p["R"], p["SS_Q"], p["Días de stock"],
                                                    m, p["Días de SS"], p["PR"]), width="stretch")

    # diente de sierra (punto 9 del taller)
    st.subheader("Simulación de varios ciclos (diente de sierra)")
    demora = st.slider("Días de retraso del proveedor", 0, 10, 0,
                       key=f"demora_{producto}")
    tabla_inv, pedidos, llegadas = graficas.simular_inventario(r["Q*"], p["d"], p["R"], m, demora=demora)
    st.altair_chart(graficas.grafica_diente_sierra(tabla_inv, p["R"], p["SS_Q"], pedidos), width="stretch")
    minimo = tabla_inv["Inventario"].min()
    if minimo <= 0:
        st.error(f"🔴 Con {demora} días de retraso el inventario llega a 0 (faltante). "
                 f"El SS alcanza para {p['Días de SS']:.1f} días.")
    elif minimo <= p["SS_Q"]:
        st.warning(f"🔴 Con {demora} días de retraso se usa el stock de seguridad (baja hasta {minimo:,.0f} und).")
    else:
        st.caption(f"Los puntos amarillos son los pedidos. Lo mínimo que llega el inventario es {minimo:,.0f} und.")

    # el stock se guarda en session_state porque streamlit vuelve a correr todo el codigo con cada clic
    # y si fuera una variable normal se reiniciaria
    if "stock" not in st.session_state:
        st.session_state["stock"] = {}             # stock de cada producto
        st.session_state["historial"] = {}         # movimientos de cada producto
    if producto not in st.session_state["stock"]:
        st.session_state["stock"][producto] = round(r["Q*"])   # arranca con un pedido lleno
        st.session_state["historial"][producto] = []

    st.subheader("Registrar movimiento")
    col_a, col_b = st.columns(2)
    with col_a:
        cantidad = st.number_input("Unidades vendidas", min_value=1, value=50, step=1)
        if st.button("Registrar venta"):
            if cantidad > st.session_state["stock"][producto]:      # no deja vender mas de lo que hay
                st.error("No hay stock suficiente.")
            else:
                st.session_state["stock"][producto] -= cantidad
                st.session_state["historial"][producto].append(f"Venta de {cantidad} und")
    with col_b:
        st.write("Llegó el pedido:")
        if st.button(f"Recibir pedido ({r['Q*']:,.0f} und)"):
            st.session_state["stock"][producto] += round(r["Q*"])
            st.session_state["historial"][producto].append(f"Llegó pedido de {r['Q*']:,.0f} und")

    stock = st.session_state["stock"][producto]
    st.metric(f"Stock actual de {producto}", f"{stock:,} und")

    estado = seguridad.estado_inventario(stock, p["R"], p["SS_Q"])
    if estado == "critico":
        st.error(
            f"🔴 Alerta: el stock ({stock}) está por debajo del SS ({p['SS_Q']:,.0f}). "
            f"Se está usando la reserva, hay que pedir {r['Q*']:,.0f} unidades ya."
        )
    elif estado == "pedir":
        st.warning(
            f"🟡 Sonó la alarma (R = {p['R']:,.0f}). Stock: {stock}. "
            f"Hay que pedir {r['Q*']:,.0f} unidades."
        )
    else:
        st.success(f"✅ Stock bien. Faltan {stock - p['R']:,.0f} unidades para llegar a la alarma.")

    if st.session_state["historial"][producto]:
        st.caption("Movimientos: " + " → ".join(st.session_state["historial"][producto]))

# ---------------- Pestaña Resumen (los 3 productos) ----------------
with tab_resumen:
    st.header("Resumen de los 3 productos")
    st.info(
        "Por producto: D, gráfico de demanda, Q* y gráfica de inventario. "
        "El producto seleccionado usa los valores de la barra lateral."
    )

    todos = {}
    for nombre in productos["producto"]:
        if nombre == producto:
            todos[nombre] = calc
        else:
            f = productos[productos["producto"] == nombre].iloc[0]
            todos[nombre] = calcular_producto(nombre, float(f["Cu"]), float(f["Cp"]),
                                              float(f["i"]), int(f["m"]), float(f["Z"]))

    for nombre, c in todos.items():
        st.subheader(nombre)
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            st.metric("D - Demanda anual", f"{c['D']:,.0f}")
            st.metric("Q* - Unidades por pedido", f"{c['r']['Q*']:,.0f}")
        with col2:
            st.caption("Gráfico de demanda")
            st.altair_chart(graficas.grafica_demanda(ventas["mes"], c["lista"]), width="stretch")
        with col3:
            st.caption("Gráfica de inventario")
            st.altair_chart(graficas.grafica_politica_clase(c["r"]["Q*"], c["r"]["T"], c["p"]["R"], c["p"]["SS_Q"],
                                                            c["p"]["Días de stock"], c["m"], c["p"]["Días de SS"],
                                                            c["p"]["PR"], alto=220, con_zoom=False), width="stretch")
        st.caption(f"Alarma: cuando queden {c['p']['R']:,.0f} unidades. Se piden {c['r']['Q*']:,.0f} "
                   f"(el último pedido del año, PR = {c['p']['PR']:,.0f}).")
        st.divider()

    # tabla con todo (esta misma va al excel)
    resumen = pd.DataFrame([{
        "Producto": n,
        "Modelo ganador": c["ganador"],
        "D (und/año)": round(c["D"], 2),
        "Ch ($/und/año)": round(c["r"]["Ch"], 2),
        "Q* (und)": round(c["r"]["Q*"], 2),
        "N (pedidos/año)": round(c["r"]["N"], 2),
        "T (días)": round(c["r"]["T"], 2),
        "Costo de pedir ($)": round(c["r"]["Costo de pedir"], 0),
        "Costo de almacenar ($)": round(c["r"]["Costo de almacenar"], 0),
        "Costo de mercancía ($)": round(c["r"]["Costo de mercancía"], 0),
        "CT ($)": round(c["r"]["CT"], 0),
        "σ (und)": round(c["p"]["σ"], 2),
        "SS (und)": round(c["p"]["SS"], 2),
        "SS_Q (und)": round(c["p"]["SS_Q"], 2),
        "d (und/día)": round(c["p"]["d"], 2),
        "Alarma R (und)": round(c["p"]["R"], 2),
        "PR - Punto de reorden (und)": round(c["p"]["PR"], 2),
        "Días de stock": round(c["p"]["Días de stock"], 2),
        "m (días)": c["m"],
        "Días de SS": round(c["p"]["Días de SS"], 2),
    } for n, c in todos.items()])
    st.subheader("Tabla general")
    st.dataframe(resumen, hide_index=True)

    # excel de soporte (punto 11 del taller)
    detalles = {"Ventas": ventas}
    for n, c in todos.items():
        detalles[f"MSE {n}"] = pd.DataFrame({"Modelo": list(c["resultados"]),
                                             "MSE": [round(v, 2) for v in c["resultados"].values()]})
    try:
        archivo = exportar.crear_excel(resumen, detalles)
        st.download_button("📥 Descargar Excel con los cálculos", archivo,
                           file_name="ERP_inventarios_resultados.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except ImportError:
        st.warning("Falta instalar openpyxl: pip install openpyxl")