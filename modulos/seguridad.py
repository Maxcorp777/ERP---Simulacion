"""
Módulo 3 del ERP: Política con puntos de reorden (stock de seguridad y alarmas).
Responde: ¿CUÁNDO pedir? y ¿qué reserva guardar por si el proveedor se demora?

Guía: 4. Teoria de inventarios.pptx -> diapositivas 16 y 17 (R = d × m, T)
      Tablero de clase -> SS = Z × σ, SS para Q* (regla de tres), alarma, días de SS
      Regresión lineal.xlsx -> hoja "MM y Ponderados" (Z y Desv. Estándar de las ventas)
"""
import math
import statistics


def calcular_sigma(ventas):
    # σ = Desviación estándar de las ventas          [Hoja "MM y Ponderados": Desv. Estándar]
    # Entra: ventas = lista de ventas mensuales
    # Hace:  mide qué tanto suben y bajan las ventas respecto a su promedio
    # Sale:  σ (unidades). Entre más grande, más variables son las ventas
    return statistics.stdev(ventas)


def sigma_anual(sigma_mensual):
    # σ anual a partir de la σ mensual                 [Conversión estándar: × raíz(12)]
    # Entra: σ de las ventas mensuales
    # Hace:  σ_anual = σ_mensual × raíz(12)  (las subidas y bajadas de cada mes se compensan en parte)
    # Sale:  σ en el mismo periodo que D (anual), como en el tablero (D = 5.000 con σ = 50)
    return sigma_mensual * math.sqrt(12)


def calcular_d(D, dias_laborales):
    # d = Demanda diaria                              [Guía diap. 16]
    # Entra: D = demanda anual | dias_laborales = 365
    # Hace:  d = D / días
    # Sale:  unidades que se venden por día
    return D / dias_laborales


def calcular_SS(Z, sigma):
    # SS = Stock de seguridad de la demanda            [Tablero: SS = Z × σ]
    # Entra: Z = nivel de servicio (1.65 = 95 %) | σ
    # Hace:  SS = Z × σ
    # Sale:  unidades extra de reserva para la demanda
    return Z * sigma


def calcular_SS_Q(Q, SS, D):
    # SS para Q* (regla de tres)                       [Tablero: 3162,3 × 82,5 / 5000]
    # Entra: Q = Q* | SS | D
    # Hace:  si a D le corresponde SS, a Q* le corresponde SS_Q = Q* × SS / D
    # Sale:  stock de seguridad por pedido → ALARMA CRÍTICA 🔴
    return Q * SS / D


def unidades_durante_entrega(d, m):
    # Unidades que se venden mientras llega el pedido  [Guía diap. 16: R = d × m]
    # Entra: d = demanda diaria | m = días del proveedor
    # Hace:  d × m
    # Sale:  unidades que se gastan esperando al proveedor
    return d * m


def calcular_R(d, m, SS_Q):
    # R = Punto de reorden (alarma en unidades)        [Guía diap. 16 + tablero]
    # Entra: d | m | SS_Q
    # Hace:  R = d × m + SS_Q
    # Sale:  cuando el inventario baje a R, se llama al proveedor → ALARMA 🟡
    return unidades_durante_entrega(d, m) + SS_Q


def dias_de_SS(SS_Q, T, Q):
    # Días que dura el stock de seguridad              [Tablero: regla de tres → 3,81 días]
    # Entra: SS_Q | T = tiempo de ciclo | Q = Q*
    # Hace:  si Q* dura T días, SS_Q dura SS_Q × T / Q*
    # Sale:  días de reserva
    return SS_Q * T / Q


def dias_de_stock(T, m, dias_SS):
    # Días de stock antes de la alarma                 [Tablero: 231,01 = 220,2 + 7 + 3,81]
    # Entra: T | m | días de SS
    # Hace:  T − m − días de SS
    # Sale:  días en que el inventario baja sin necesidad de pedir
    return T - m - dias_SS


def calcular_politica(ventas, D, Q, T, Z, m, dias_laborales, usar_sigma_anual=False):
    # Junta todo el módulo 3 para un producto
    # Entra: ventas (lista) | D (módulo 1) | Q* y T (módulo 2) | Z, m, días (productos.csv)
    #        usar_sigma_anual = True para llevar σ a anual (mismo periodo que D)
    # Sale:  diccionario con σ, SS, SS_Q, d, R y los días
    sigma = calcular_sigma(ventas)
    if usar_sigma_anual:
        sigma = sigma_anual(sigma)
    SS = calcular_SS(Z, sigma)
    SS_Q = calcular_SS_Q(Q, SS, D)
    d = calcular_d(D, dias_laborales)
    R = calcular_R(d, m, SS_Q)
    dSS = dias_de_SS(SS_Q, T, Q)
    return {
        "σ": sigma,
        "SS": SS,
        "SS_Q": SS_Q,
        "d": d,
        "Unidades durante entrega": unidades_durante_entrega(d, m),
        "R": R,
        "Días de SS": dSS,
        "Días de stock": dias_de_stock(T, m, dSS),
    }


def estado_inventario(stock, R, SS_Q):
    # Revisa en qué zona está el inventario después de una venta   [Módulo 3 del profe]
    # Entra: stock actual | R = alarma 🟡 | SS_Q = alarma crítica 🔴
    # Hace:  compara el stock con las dos alarmas
    # Sale:  "ok", "pedir" o "critico"
    if stock <= SS_Q:
        return "critico"          # 🔴 ya se está gastando la reserva
    elif stock <= R:
        return "pedir"            # 🟡 llegó al punto de reorden: llamar al proveedor
    else:
        return "ok"               # ✅ todo bien


# ---- Prueba: ejemplo del tablero (D=5000, σ=50, Z=1,65, m=7, Q*=3162,3, T=231,01) ----
if __name__ == "__main__":
    Q, D, T = 3162.28, 5000, 231.01
    SS = calcular_SS(1.65, 50)
    SS_Q = calcular_SS_Q(Q, SS, D)
    d = calcular_d(D, 365)
    print("SS =", round(SS, 2))                               # 82.5
    print("SS_Q =", round(SS_Q, 2))                           # 52.17
    print("R =", round(calcular_R(d, 7, SS_Q), 2))            # ≈ 148 (tablero: 147,99)
    print("Días de SS =", round(dias_de_SS(SS_Q, T, Q), 2))   # 3.81
    print(estado_inventario(300, 148, 52), estado_inventario(140, 148, 52), estado_inventario(40, 148, 52))