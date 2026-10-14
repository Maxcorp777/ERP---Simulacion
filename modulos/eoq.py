"""
Módulo 2 del ERP: Lote Económico de Pedido (EOQ = Economic Order Quantity).
Responde: ¿CUÁNTO pedir cada vez y cuánto cuesta al año?

Guía: 4. Teoria de inventarios.pptx -> diapositivas 11 a 15, 17 y 18
      Tablero de clase (notación del profe: Cp, Cu, Ch)
"""
import math


def calcular_Ch(i, Cu):
    # Ch = Costo de posesión por unidad al año            [Guía diap. 11, 13 y tablero]
    # Entra: i = % de posesión al año (ej. 0.20) | Cu = costo unitario ($)
    # Hace:  Ch = i × Cu
    # Sale:  Ch = lo que cuesta guardar UNA unidad durante un año
    return i * Cu


def calcular_Q_optimo(D, Cp, Ch):
    # Q* = Cantidad óptima a pedir                          [Guía diap. 15]
    # Entra: D = demanda anual | Cp = costo de hacer un pedido | Ch
    # Hace:  Q* = raíz(2 × D × Cp / Ch)
    # Sale:  Q* = cuántas unidades pedir cada vez (costo total mínimo)
    return math.sqrt(2 * D * Cp / Ch)


def calcular_N(D, Q):
    # N = Número de pedidos por año                          [Guía diap. 12]
    # Entra: D | Q
    # Hace:  N = D / Q
    # Sale:  N = cuántas veces al año se le pide al proveedor
    return D / Q


def costo_anual_pedir(D, Q, Cp):
    # Costo anual de pedir = Número de pedidos × Costo por pedido   [Guía diap. 12]
    # Entra: D | Q | Cp
    # Hace:  (D / Q) × Cp
    # Sale:  $ al año en pedidos
    return (D / Q) * Cp


def costo_anual_posesion(Q, Ch):
    # Costo anual de posesión = Nivel promedio de inventario × Ch   [Guía diap. 12]
    # Entra: Q | Ch
    # Hace:  (Q / 2) × Ch   (Q/2 = nivel promedio de inventario)
    # Sale:  $ al año en almacenamiento
    return (Q / 2) * Ch


def costo_compra_unidades(D, C):
    # Costo en compra de unidades (al año)                   [Guía diap. 12]
    # Entra: D | C = costo unitario (Cu en el tablero)
    # Hace:  D × C   (no depende de Q)
    # Sale:  $ al año en mercancía
    return D * C


def calcular_CT(D, C, Q, Cp, Ch):
    # CT = Costo total anual                                 [Guía diap. 12 y 18]
    # Entra: D | C | Q | Cp | Ch
    # Hace:  CT = D×C + (D/Q)×Cp + (Q/2)×Ch
    # Sale:  costo total del inventario en el año
    return costo_compra_unidades(D, C) + costo_anual_pedir(D, Q, Cp) + costo_anual_posesion(Q, Ch)


def calcular_T(Q, D, dias_laborales):
    # T = Tiempo de ciclo                                    [Guía diap. 17]
    # Entra: Q | D | dias_laborales = días laborales al año (365)
    # Hace:  T = (Q / D) × días laborales al año
    # Sale:  T = cuántos días dura cada pedido en almacenamiento
    return (Q / D) * dias_laborales


def calcular_eoq(D, Cu, Cp, i, dias_operacion):
    # Junta todo el módulo 2 para un producto
    # Entra: D (del módulo 1) | Cu, Cp, i, días (de productos.csv)
    # Sale:  diccionario con todos los resultados
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


# ---- Prueba: ejemplo de las cervezas de la guía (diap. 13-15) ----
if __name__ == "__main__":
    r = calcular_eoq(D=104000, Cu=16000, Cp=64000, i=0.25, dias_operacion=365)
    for nombre, valor in r.items():
        print(nombre, "=", round(valor, 2))
    # Debe dar: Ch = 4000, Q* = 1824.28, N = 57.01, CT ≈ 1671297122