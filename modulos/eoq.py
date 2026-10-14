"""
Modulo 2: lote economico de pedido (EOQ)

Responde cuanto pedir cada vez (Q*) y cuanto cuesta el inventario en el año.
Formulas de 4. Teoria de inventarios.pptx (diapositivas 11 a 18) y del tablero.
Uso la letra del profe: Cp = costo de pedir, Cu = costo unitario, Ch = costo de mantener.
"""
import math


def calcular_Ch(i, Cu):
    # Ch = lo que cuesta tener guardada una unidad durante un año
    # Ch = i x Cu   (i es el % de almacenamiento, ej 0.20 = 20%)
    return i * Cu


def calcular_Q_optimo(D, Cp, Ch):
    # Q* = raiz(2 x D x Cp / Ch)   (diapositiva 15)
    # es la cantidad a pedir con la que el costo total queda en el minimo
    return math.sqrt(2 * D * Cp / Ch)


def calcular_N(D, Q):
    # N = cuantos pedidos se hacen en el año
    return D / Q


def costo_anual_pedir(D, Q, Cp):
    # costo de pedir en el año = numero de pedidos x lo que cuesta cada pedido
    return (D / Q) * Cp


def costo_anual_posesion(Q, Ch):
    # costo de almacenar en el año
    # se usa Q/2 porque el inventario empieza en Q y baja hasta 0,
    # entonces en promedio hay Q/2 unidades guardadas
    return (Q / 2) * Ch


def costo_compra_unidades(D, C):
    # lo que se paga por la mercancia en el año = D x costo unitario
    # este no cambia con Q, se compra lo mismo pidiendo poquito o mucho
    return D * C


def calcular_CT(D, C, Q, Cp, Ch):
    # costo total = mercancia + pedir + almacenar   (diapositivas 12 y 18)
    return costo_compra_unidades(D, C) + costo_anual_pedir(D, Q, Cp) + costo_anual_posesion(Q, Ch)


def calcular_T(Q, D, dias_laborales):
    # T = cada cuantos dias se hace un pedido (lo que dura un pedido)
    # T = (Q / D) x dias del año
    return (Q / D) * dias_laborales


def calcular_eoq(D, Cu, Cp, i, dias_operacion):
    # junta todo lo de arriba para un producto y lo devuelve en un diccionario
    # D sale del modulo 1 y lo demas de productos.csv
    Ch = calcular_Ch(i, Cu)
    Q = calcular_Q_optimo(D, Cp, Ch)
    return {
        "Ch": Ch,
        "Q*": Q,
        "N": calcular_N(D, Q),
        "Costo de pedir": costo_anual_pedir(D, Q, Cp),
        "Costo de almacenar": costo_anual_posesion(Q, Ch),
        "Costo de mercancía": costo_compra_unidades(D, Cu),
        "CT": calcular_CT(D, Cu, Q, Cp, Ch),
        "T": calcular_T(Q, D, dias_operacion),
    }


# prueba con el ejemplo de las cervezas de la guia (diapositivas 13 a 15)
if __name__ == "__main__":
    r = calcular_eoq(D=104000, Cu=16000, Cp=64000, i=0.25, dias_operacion=365)
    for nombre, valor in r.items():
        print(nombre, "=", round(valor, 2))
    # tiene que dar Ch = 4000, Q* = 1824.28, N = 57.01
