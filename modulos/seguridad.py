"""
Modulo 3: politica con punto de reorden

Responde cuando pedir (punto de reorden R) y cuanta reserva tener por si
el proveedor se demora o se vende mas de lo normal (stock de seguridad SS).

Lo saque de:
- 4. Teoria de inventarios.pptx, diapositivas 16 y 17 (R = d x m)
- lo que hizo el profe en el tablero (SS = Z x σ, regla de tres, dias de SS)
- Regresion lineal.xlsx, hoja "MM y Ponderados" (Z y la desviacion estandar)
"""
import math
import statistics


def calcular_sigma(ventas):
    # σ = desviacion estandar de las ventas
    # dice que tanto suben y bajan las ventas, si las ventas son muy parejas da pequeño
    return statistics.stdev(ventas)


def sigma_anual(sigma_mensual):
    # pasa la σ de mensual a anual multiplicando por raiz de 12
    # es para que quede en el mismo periodo que D (que es anual)
    # no se multiplica por 12 porque los meses buenos y malos se compensan un poco
    return sigma_mensual * math.sqrt(12)


def calcular_d(D, dias_laborales):
    # d = lo que se vende en un dia = D / 365
    return D / dias_laborales


def calcular_SS(Z, sigma):
    # SS = Z x σ
    # Z sale del nivel de servicio, 1.65 es el 95% (como en el tablero)
    return Z * sigma


def calcular_SS_Q(Q, SS, D):
    # regla de tres que hizo el profe en el tablero:
    # si para D unidades el SS es SS, para Q* es Q* x SS / D
    # esta es la alarma roja
    return Q * SS / D


def unidades_durante_entrega(d, m):
    # lo que se vende mientras llega el pedido = d x m
    # m = dias que se demora el proveedor
    return d * m


def calcular_R(d, m, SS_Q):
    # R = punto de reorden = d x m + SS
    # cuando el inventario baja a R hay que pedir (alarma amarilla)
    return unidades_durante_entrega(d, m) + SS_Q


def dias_de_SS(SS_Q, T, Q):
    # cuantos dias alcanza el stock de seguridad (otra regla de tres)
    # si Q* dura T dias, el SS dura SS x T / Q*
    return SS_Q * T / Q


def dias_de_stock(T, m, dias_SS):
    # dias que el inventario va bajando antes de que toque pedir
    # T - m - dias de SS (en el tablero: 231.01 = 220.2 + 7 + 3.81)
    return T - m - dias_SS


def calcular_PR(D, Q, SS_Q):
    # PR = cuanto se pide cuando suena la alarma (como en los apuntes del profe)
    # en el tablero: 5000 - 3162.3 = 1837.7 (lo que falta para completar el año)
    #                PR = 1837.7 - 52.17 = 1785.53
    # se le resta el SS porque cuando llega el pedido todavia quedan esas unidades
    # si en el año caben varios pedidos (N mayor a 2) los primeros son de Q*
    # y el PR es el ultimo pedido, el que completa la demanda del año
    pedidos_completos = math.floor(D / Q)        # floor = redondear hacia abajo
    faltante = D - pedidos_completos * Q         # lo que falta para completar D
    if faltante - SS_Q <= 0:                     # si lo que falta es menor que el SS no vale la pena otro pedido,
        pedidos_completos = pedidos_completos - 1  # entonces se junta con el ultimo pedido completo
        faltante = faltante + Q
    return pedidos_completos, faltante, faltante - SS_Q


def calcular_politica(ventas, D, Q, T, Z, m, dias_laborales, usar_sigma_anual=False):
    # junta todo el modulo 3 para un producto
    # D viene del modulo 1, Q* y T del modulo 2, Z y m de productos.csv
    # usar_sigma_anual es para escoger σ mensual o anual desde la pagina
    sigma = calcular_sigma(ventas)
    if usar_sigma_anual:
        sigma = sigma_anual(sigma)
    SS = calcular_SS(Z, sigma)
    SS_Q = calcular_SS_Q(Q, SS, D)
    d = calcular_d(D, dias_laborales)
    R = calcular_R(d, m, SS_Q)
    dSS = dias_de_SS(SS_Q, T, Q)
    completos, faltante, PR = calcular_PR(D, Q, SS_Q)
    return {
        "σ": sigma,
        "SS": SS,
        "SS_Q": SS_Q,
        "d": d,
        "Unidades durante entrega": unidades_durante_entrega(d, m),
        "R": R,
        "Días de SS": dSS,
        "Días de stock": dias_de_stock(T, m, dSS),
        "Pedidos completos": completos,
        "Faltante del año": faltante,
        "PR": PR,
    }


def estado_inventario(stock, R, SS_Q):
    # despues de cada venta revisa como esta el inventario
    # primero mira la alarma roja y despues la amarilla
    if stock <= SS_Q:
        return "critico"          # ya se esta gastando la reserva
    elif stock <= R:
        return "pedir"            # llego al punto de reorden
    else:
        return "ok"


# prueba con los numeros del tablero (D=5000, σ=50, Z=1.65, m=7, Q*=3162.3, T=231.01)
if __name__ == "__main__":
    Q, D, T = 3162.28, 5000, 231.01
    SS = calcular_SS(1.65, 50)
    SS_Q = calcular_SS_Q(Q, SS, D)
    d = calcular_d(D, 365)
    print("SS =", round(SS, 2))                               # 82.5
    print("SS_Q =", round(SS_Q, 2))                           # 52.17
    print("R =", round(calcular_R(d, 7, SS_Q), 2))            # en el tablero dio 147.99
    print("Días de SS =", round(dias_de_SS(SS_Q, T, Q), 2))   # 3.81
    print("PR =", round(calcular_PR(D, Q, SS_Q)[2], 2))       # 1785.53
    print(estado_inventario(300, 148, 52), estado_inventario(140, 148, 52), estado_inventario(40, 148, 52))
