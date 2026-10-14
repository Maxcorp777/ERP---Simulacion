"""
Modulo 1: pronostico de la demanda

Aca se prueban varios metodos para pronosticar las ventas del proximo mes
y se escoge el que menos se equivoca (el de menor MSE).
Con ese pronostico se saca D (demanda anual), que es lo que usa el EOQ.

Lo saque de:
- Regresion lineal.xlsx, hoja "MM y Ponderados" (media movil N=2, 3, 4 y ponderados)
- 4. Teoria de inventarios.pptx, diapositiva 11 (D = demanda en unidades al año)
"""
import pandas as pd
tabla = pd.read_csv("datos/ventas.csv")
ventasTazas = tabla["Tazas"].tolist()   # ventas de tazas para probar las funciones

def media_movil(ventas, n):
    # media movil: promedio de los ultimos n meses
    # ej: con n=3 suma los 3 ultimos meses y divide entre 3
    # eso da lo que se espera vender el proximo mes
    ultimos = ventas[-n:]          # [-n:] coge los ultimos n datos de la lista
    return sum(ultimos) / len(ultimos)


def demanda_anual(pronostico_mensual):
    # D = demanda del año, el pronostico es de un mes entonces se multiplica por 12
    return pronostico_mensual * 12


def ponderadoN2(ventas, porcentajes):
    # ponderado con 2 meses, el ultimo mes pesa mas porque es lo mas reciente
    # pesos del profe: [0.4, 0.6] (tienen que sumar 1)
    # = penultimo mes x 0.4 + ultimo mes x 0.6
    operacion1 = ventas[-2] * porcentajes[-2]
    operacion2 = ventas[-1] * porcentajes[-1]
    suma = operacion1 + operacion2
    return suma


def ponderadoN3(ventas, porcentajes):
    # igual que el de arriba pero con 3 meses
    # pesos del profe: [0.1, 0.4, 0.5]
    # = hace 3 meses x 0.1 + hace 2 meses x 0.4 + ultimo mes x 0.5
    operacion1 = ventas[-3] * porcentajes[-3]
    operacion2 = ventas[-2] * porcentajes[-2]
    operacion3 = ventas[-1] * porcentajes[-1]
    suma = operacion1 + operacion2 + operacion3
    return suma


def MSE(ListaReal, Predichos):
    # MSE = error cuadratico medio, sirve para ver que tan bueno es un metodo
    # por cada mes: error = lo que se vendio - lo que se predijo
    # el error se eleva al cuadrado (para que los negativos no se cancelen con los positivos)
    # se suman todos y se divide entre la cantidad de meses
    # entre mas pequeño el MSE mejor
    acumulador = 0
    for real, predicho in zip(ListaReal, Predichos):   # zip recorre las 2 listas al tiempo
        error = real - predicho
        acumulador = acumulador + error ** 2
    resultado = acumulador / len(ListaReal)
    return resultado


def evaluar_mm(ventas, n, inicio):
    # prueba la media movil con los meses que ya pasaron para ver que tanto falla
    # para cada mes desde "inicio" predice usando solo los meses de antes
    # (como si estuvieramos en ese mes y no supieramos lo que se iba a vender)
    # al final compara las predicciones con lo real y saca el MSE
    predicciones = []
    for i in range(inicio, len(ventas)):
        historia = ventas[:i]                    # los meses antes del mes i
        prediccion = media_movil(historia, n)
        predicciones.append(prediccion)
    reales = ventas[inicio:]                     # lo que de verdad se vendio esos meses
    return MSE(reales, predicciones)

def evaluar_ponderado(ventas, pesos, inicio):
    # lo mismo que evaluar_mm pero con el ponderado
    # si le pasan 2 pesos usa ponderadoN2 y si son 3 usa ponderadoN3
    predicciones = []

    if len(pesos) not in (2, 3):                      # si no son 2 o 3 pesos da error
        raise ValueError("El ponderado solo acepta 2 o 3 porcentajes")

    for i in range(inicio, len(ventas)):
        historia = ventas[:i]                          # meses antes del mes i
        if len(pesos) == 2:
            prediccion = ponderadoN2(historia, pesos)
        else:
            prediccion = ponderadoN3(historia, pesos)
        predicciones.append(prediccion)
    reales = ventas[inicio:]
    return MSE(reales, predicciones)


# pesos que puso el profe en el excel (hoja "MM y Ponderados")
PESOS_N2 = [0.4, 0.6]
PESOS_N3 = [0.1, 0.4, 0.5]


def pronostico_modelo(historia, modelo):
    # recibe el nombre del metodo (ej "MM N=3") y llama la funcion que toca
    # devuelve el pronostico del proximo mes
    if modelo == "MM N=2":
        return media_movil(historia, 2)
    elif modelo == "MM N=3":
        return media_movil(historia, 3)
    elif modelo == "MM N=4":
        return media_movil(historia, 4)
    elif modelo == "Ponderado N=2":
        return ponderadoN2(historia, PESOS_N2)
    else:
        return ponderadoN3(historia, PESOS_N3)


def elegir_mejor(ventas, inicio):
    # aca se escoge el mejor metodo:
    # 1. saca el MSE de los 5 metodos
    # 2. se queda con el de menor MSE
    # 3. con ese hace el pronostico del proximo mes
    # 4. calcula D
    # inicio = 4 porque la MM N=4 necesita 4 meses para poder predecir,
    # asi todos se prueban con los mismos meses y es justo
    resultados = {
        "MM N=2": evaluar_mm(ventas, 2, inicio),
        "MM N=3": evaluar_mm(ventas, 3, inicio),
        "MM N=4": evaluar_mm(ventas, 4, inicio),
        "Ponderado N=2": evaluar_ponderado(ventas, PESOS_N2, inicio),
        "Ponderado N=3": evaluar_ponderado(ventas, PESOS_N3, inicio),
    }
    ganador = min(resultados, key=resultados.get)    # el nombre que tiene el MSE mas bajo
    pronostico = pronostico_modelo(ventas, ganador)  # aca si usa todas las ventas para predecir octubre
    D = demanda_anual(pronostico)
    return resultados, ganador, pronostico, D


def predicciones_modelo(ventas, modelo, inicio):
    # esto es para la grafica de real vs pronostico
    # devuelve lo que el metodo hubiera predicho en cada mes
    predicciones = []
    for i in range(inicio, len(ventas)):
        historia = ventas[:i]
        predicciones.append(pronostico_modelo(historia, modelo))
    return predicciones

# prueba: solo corre si se ejecuta este archivo solo (python pronostico.py)
if __name__ == "__main__":
    print(media_movil([1120,1300], 2))
