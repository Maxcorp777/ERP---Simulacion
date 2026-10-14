"""
ERP de Inventarios - interfaz (lo que ve el usuario).
Para abrirlo:  python -m streamlit run app.py

Módulo 1: Proyección de demanda      → modulos/pronostico.py
Módulo 2: Lote económico de pedido   → modulos/eoq.py
Módulo 3: Política y punto de reorden → modulos/seguridad.py
Gráficas                              → modulos/graficas.py
Excel de soporte                      → modulos/exportar.py
"""
import altair as alt
import pandas as pd
import streamlit as st

from modulos import pronostico, eoq, seguridad, graficas, exportar

st.set_page_config(page_title="OptiStock ERP", page_icon="📦", layout="wide")
st.title("📦 OptiStock — ERP de Inventarios")
st.caption("Tienda de vajilla · Pronóstico, lote económico y punto de reorden")

# Estilo extra (CSS): tarjetas de resultados en verde claro
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
INICIO = 4                    # 1.er mes del examen de los modelos (para que compita la MM N=4)

# ---------------- Barra lateral ----------------
st.sidebar.title("📦 OptiStock")
st.sidebar.caption("ERP de inventarios EOQ")
producto = st.sidebar.selectbox("Producto", productos["producto"])
fila = productos[productos["producto"] == producto].iloc[0]          # valores del CSV

# Sensibilidad (taller punto 2): cambiar las variables y ver cómo cambia todo
st.sidebar.subheader("Parámetros (sensibilidad)")
st.sidebar.caption("Cámbialos para ver cómo afectan Q*, los costos y las alarmas.")
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
    ["Mensual (desviación de las ventas)", "Anual (σ mensual × √12)"],
    help="Pendiente de confirmar con el profe. Anual = mismo periodo que D.",
)
usar_sigma_anual = tipo_sigma.startswith("Anual")
DIAS = int(fila["dias_operacion"])


def calcular_producto(nombre, Cu, Cp, i, m, Z):
    # Corre los 3 módulos para un producto y devuelve todo junto
    lista = ventas[nombre].tolist()
    resultados, ganador, pron, D = pronostico.elegir_mejor(lista, INICIO)                    # módulo 1
    r = eoq.calcular_eoq(D, Cu, Cp, i, DIAS)                                                  # módulo 2
    p = seguridad.calcular_politica(lista, D, r["Q*"], r["T"], Z, m, DIAS, usar_sigma_anual)  # módulo 3
    return {"lista": lista, "resultados": resultados, "ganador": ganador, "pron": pron,
            "D": D, "r": r, "p": p, "m": m, "Cu": Cu, "Cp": Cp, "i": i, "Z": Z}


# Producto elegido: con los parámetros de la barra lateral
calc = calcular_producto(producto, Cu, Cp, i, m, Z)
lista, resultados, ganador, pron, D, r, p = (calc[k] for k in
                                             ["lista", "resultados", "ganador", "pron", "D", "r", "p"])

tab_datos, tab_pron, tab_eoq, tab_venta, tab_resumen = st.tabs(
    ["Datos", "Pronóstico", "EOQ", "Política y ventas", "Resumen"])

# ---------------- Pestaña Datos ----------------
with tab_datos:
    st.header(f"Datos de {producto}")
    st.info(
        "Aquí están los datos de entrada del producto: las ventas de los últimos "
        "12 meses y sus costos (Cu = costo unitario, Cp = costo de pedir, "
        "i = % de almacenamiento, m = días del proveedor, Z = nivel de servicio). "
        "Los costos se pueden cambiar en la barra lateral."
    )
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
        "Se prueban 5 modelos con los meses pasados: cada uno predice cada mes "
        "usando solo los meses anteriores, y se califica con el MSE. "
        "Gana el de menor MSE, y con él se calcula el pronóstico del próximo mes y la demanda anual (D)."
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
        "El EOQ calcula cuántas unidades pedir cada vez (Q*) para que el costo total "
        "del inventario sea el mínimo: si se pide poco, se paga mucho en pedidos; "
        "si se pide mucho, se paga mucho en bodega. Q* es el punto de equilibrio."
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

    st.caption(f"D = {D:,.0f} und/año (del pronóstico) · Ch = i × Cu = ${r['Ch']:,.0f} por unidad al año")
    st.success(f"Política: cada vez que se pida {producto.lower()}, pedir {r['Q*']:,.0f} unidades.")

# ---------------- Pestaña Política y ventas (módulo 3) ----------------
with tab_venta:
    st.header(f"Política de inventario y punto de reorden - {producto}")
    st.info(
        "Cada vez que se registra una venta, el sistema descuenta el stock y lo compara con dos alarmas: "
        "🟡 el punto de reorden (R), donde hay que llamar al proveedor, y 🔴 el stock de seguridad (SS), "
        "la reserva para cuando el proveedor se demora o se vende más de lo normal."
    )

    st.subheader("Cuándo pedir")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("σ - Desviación de las ventas", f"{p['σ']:,.1f} und")
    c2.metric("SS - Stock de seguridad (Z × σ)", f"{p['SS']:,.1f} und")
    c3.metric("🔴 SS para Q* (alarma crítica)", f"{p['SS_Q']:,.0f} und")
    c4.metric("🟡 R - Punto de reorden", f"{p['R']:,.0f} und")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("d - Demanda diaria", f"{p['d']:,.1f} und/día")
    c6.metric("Días de stock", f"{p['Días de stock']:,.1f} días")
    c7.metric("m - Días del proveedor", f"{m} días")
    c8.metric("Días de SS", f"{p['Días de SS']:,.1f} días")
    st.success(
        f"Política: cuando el inventario de {producto.lower()} baje a {p['R']:,.0f} unidades, "
        f"pedir {r['Q*']:,.0f} unidades."
    )

    # --- Diagrama general de la política (diente de sierra) ---
    st.subheader("Diagrama de la política de inventario")
    demora = st.slider("Días EXTRA que se demora el proveedor (simulación)", 0, 10, 0,
                       key=f"demora_{producto}")
    tabla_inv, pedidos, llegadas = graficas.simular_inventario(r["Q*"], p["d"], p["R"], m, demora=demora)
    st.altair_chart(graficas.grafica_diente_sierra(tabla_inv, p["R"], p["SS_Q"], pedidos), width="stretch")
    minimo = tabla_inv["Inventario"].min()
    if minimo <= 0:
        st.error(f"🔴 Con {demora} días de demora el inventario llega a 0: hay faltante. "
                 f"El stock de seguridad solo cubre {p['Días de SS']:.1f} días de retraso.")
    elif minimo <= p["SS_Q"]:
        st.warning(f"🔴 Con {demora} días de demora se consume el stock de seguridad (mínimo: {minimo:,.0f} und).")
    else:
        st.caption(f"Cada punto amarillo es un pedido. El inventario nunca baja de {minimo:,.0f} und.")

    # --- Stock actual: se guarda en st.session_state para que no se borre entre clics ---
    if "stock" not in st.session_state:
        st.session_state["stock"] = {}             # stock de cada producto
        st.session_state["historial"] = {}         # movimientos de cada producto
    if producto not in st.session_state["stock"]:
        st.session_state["stock"][producto] = round(r["Q*"])   # empieza con un pedido completo
        st.session_state["historial"][producto] = []

    st.subheader("Registrar movimiento")
    col_a, col_b = st.columns(2)
    with col_a:
        cantidad = st.number_input("Unidades vendidas", min_value=1, value=50, step=1)
        if st.button("Registrar venta"):
            if cantidad > st.session_state["stock"][producto]:      # no se puede vender lo que no hay
                st.error("No hay suficiente stock para esa venta.")
            else:
                st.session_state["stock"][producto] -= cantidad
                st.session_state["historial"][producto].append(f"Venta de {cantidad} und")
    with col_b:
        st.write("Cuando llegue el pedido del proveedor:")
        if st.button(f"Recibir pedido ({r['Q*']:,.0f} und)"):
            st.session_state["stock"][producto] += round(r["Q*"])
            st.session_state["historial"][producto].append(f"Llegó pedido de {r['Q*']:,.0f} und")

    stock = st.session_state["stock"][producto]
    st.metric(f"Stock actual de {producto}", f"{stock:,} und")

    estado = seguridad.estado_inventario(stock, p["R"], p["SS_Q"])
    if estado == "critico":
        st.error(
            f"🔴 ¡ALERTA CRÍTICA! El stock ({stock}) está por debajo del stock de seguridad "
            f"({p['SS_Q']:,.0f}). Se está consumiendo la reserva: si no se ha pedido, pida YA {r['Q*']:,.0f} unidades."
        )
    elif estado == "pedir":
        st.warning(
            f"🟡 Punto de reorden alcanzado: el stock ({stock}) bajó a R = {p['R']:,.0f}. "
            f"Llame al proveedor y pida {r['Q*']:,.0f} unidades."
        )
    else:
        st.success(f"✅ Stock suficiente. Faltan {stock - p['R']:,.0f} unidades para llegar al punto de reorden.")

    if st.session_state["historial"][producto]:
        st.caption("Movimientos: " + " → ".join(st.session_state["historial"][producto]))

# ---------------- Pestaña Resumen (los 3 productos) ----------------
with tab_resumen:
    st.header("Resumen de los 3 productos")
    st.info(
        "Cada fila es un producto: su demanda anual (D), su gráfico de demanda, la cantidad a pedir (Q*) "
        "y el diagrama de su política de inventario. El producto elegido usa los parámetros de la barra "
        "lateral; los demás, los valores originales."
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
            st.caption("Gráfico de demanda (ventas mensuales)")
            st.altair_chart(graficas.grafica_demanda(ventas["mes"], c["lista"]), width="stretch")
        with col3:
            st.caption("Política de inventario (diente de sierra)")
            t, ped, _ = graficas.simular_inventario(c["r"]["Q*"], c["p"]["d"], c["p"]["R"], c["m"])
            st.altair_chart(graficas.grafica_diente_sierra(t, c["p"]["R"], c["p"]["SS_Q"], ped, alto=170),
                            width="stretch")
        st.caption(f"Política: cuando queden {c['p']['R']:,.0f} unidades, pedir {c['r']['Q*']:,.0f}.")
        st.divider()

    # Tabla con todos los resultados (también va al Excel)
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
        "SS para Q* (und)": round(c["p"]["SS_Q"], 2),
        "d (und/día)": round(c["p"]["d"], 2),
        "R - Punto de reorden (und)": round(c["p"]["R"], 2),
        "Días de stock": round(c["p"]["Días de stock"], 2),
        "m (días)": c["m"],
        "Días de SS": round(c["p"]["Días de SS"], 2),
    } for n, c in todos.items()])
    st.subheader("Tabla general")
    st.dataframe(resumen, hide_index=True)

    # Excel de soporte (taller punto 11)
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
        st.warning("Para descargar el Excel instala openpyxl:  pip install openpyxl")