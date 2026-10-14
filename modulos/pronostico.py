"""
Parte 1 del ERP: pronóstico de la demanda.

Variables:
- ventas: lista con las ventas mensuales (lo que ya pasó)
- n: cuántos meses hacia atrás se promedian
- MM (Media Móvil): promedio de los últimos n meses -> pronóstico del próximo mes
- D (Demanda anual): pronóstico mensual x 12

Guía: Regresión lineal.xlsx -> hoja "MM y Ponderados" (columnas Media Movil N=2, N=3, N=4)
      4. Teoria de inventarios.pptx -> diapositiva 11 (D = demanda en unidades/año)
"""
import pandas as pd
tabla = pd.read_csv("datos/ventas.csv")
ventasVasos = tabla["Vasos"].tolist()#[-6:]

def media_movil(ventas, n):
    # MM (Media Móvil): pronóstico del próximo mes
    # Entra: ventas = lista de ventas mensuales | n = cuántos meses promediar (N)
    # Hace:  toma los últimos n meses y los promedia
    # Sale:  pronóstico del próximo mes (unidades)
    ultimos = ventas[-n:]          # últimos n datos de la lista
    return sum(ultimos) / len(ultimos)


def demanda_anual(pronostico_mensual):
    # D (Demanda anual)
    # Entra: pronostico_mensual = lo que se espera vender en un mes
    # Hace:  lo multiplica por 12 meses
    # Sale:  D = demanda anual (unidades/año), la que se usa en Q*
    return pronostico_mensual * 12


def ponderadoN2(ventas, porcentajes):
    # Promedio ponderado N = 2: el último mes pesa más
    # Entra: ventas = lista de ventas | porcentajes = 2 pesos que suman 1, ej. [0.4, 0.6]
    # Hace:  penúltimo mes × 1.er peso + último mes × 2.º peso
    # Sale:  pronóstico del próximo mes (unidades)
    operacion1 = ventas[-2] * porcentajes[-2]
    operacion2 = ventas[-1] * porcentajes[-1]
    suma = operacion1 + operacion2
    return suma


def ponderadoN3(ventas, porcentajes):
    # Promedio ponderado N = 3: el último mes pesa más
    # Entra: ventas = lista de ventas | porcentajes = 3 pesos que suman 1, ej. [0.1, 0.4, 0.5]
    # Hace:  hace 3 meses × 1.er peso + hace 2 meses × 2.º peso + último mes × 3.er peso
    # Sale:  pronóstico del próximo mes (unidades)
    operacion1 = ventas[-3] * porcentajes[-3]
    operacion2 = ventas[-2] * porcentajes[-2]
    operacion3 = ventas[-1] * porcentajes[-1]
    suma = operacion1 + operacion2 + operacion3
    return suma


def MSE(ListaReal, Predichos):
    # MSE (Mean Squared Error, error cuadrático medio): califica un modelo
    # Entra: ListaReal = ventas reales | Predichos = lo que predijo el modelo (mismos meses)
    # Hace:  por cada mes: error = real − predicho, lo eleva al cuadrado y lo suma;
    #        al final divide entre la cantidad de meses (n)
    # Sale:  MSE → entre más pequeño, mejor el modelo
    acumulador = 0
    for real, predicho in zip(ListaReal, Predichos):
        error = real - predicho
        acumulador = acumulador + error ** 2
    resultado = acumulador / len(ListaReal)
    return resultado


def evaluar_mm(ventas, n, inicio):
    # Pone a prueba una media móvil con los meses pasados
    # Entra: ventas = todas las ventas | n = N de la MM | inicio = posición del 1.er mes a predecir
    # Hace:  para cada mes desde inicio, predice con los meses ANTERIORES (historia),
    #        guarda la predicción y al final compara todo con las ventas reales
    # Sale:  MSE de esa media móvil
    predicciones = []
    for i in range(inicio, len(ventas)):
        historia = ventas[:i]                    # meses antes del mes i
        prediccion = media_movil(historia, n)    # predicción del mes i
        predicciones.append(prediccion)
    reales = ventas[inicio:]                     # ventas reales de esos mismos meses
    return MSE(reales, predicciones)

def evaluar_ponderado(ventas, pesos, inicio):
    # Pone a prueba un promedio ponderado con los meses pasados
    # Entra: ventas = todas las ventas | pesos = [0.4, 0.6] o [0.1, 0.4, 0.5] | inicio = 1.er mes a predecir
    # Hace:  para cada mes desde inicio, predice con los meses ANTERIORES (historia)
    #        usando ponderadoN2 o ponderadoN3 según cuántos pesos haya,
    #        guarda la predicción y al final compara todo con las ventas reales
    # Sale:  MSE de ese ponderado
    predicciones = []

    if len(pesos) not in (2, 3):                      # validación: solo 2 o 3 pesos
        raise ValueError("El ponderado solo acepta 2 o 3 porcentajes")
    
    for i in range(inicio, len(ventas)):
        historia = ventas[:i]                          # meses antes del mes i
        if len(pesos) == 2:                            # ← NUEVO: ¿hay 2 pesos?
            prediccion = ponderadoN2(historia, pesos)  # ← NUEVO: sí → ponderado N=2
        else:                                          # ← NUEVO: si no (hay 3)...
            prediccion = ponderadoN3(historia, pesos)  # ← NUEVO: → ponderado N=3
        predicciones.append(prediccion)
    reales = ventas[inicio:]                           # ventas reales de esos mismos meses
    return MSE(reales, predicciones)


# Pesos del profe (Regresión lineal.xlsx → hoja "MM y Ponderados")
PESOS_N2 = [0.4, 0.6]
PESOS_N3 = [0.1, 0.4, 0.5]


def pronostico_modelo(historia, modelo):
    # Predice el próximo mes con el modelo que se le diga por su nombre
    # Entra: historia = ventas pasadas | modelo = nombre, ej. "MM N=3"
    # Hace:  según el nombre, llama a la función que corresponde
    # Sale:  pronóstico del próximo mes
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
    # Examina a los 5 modelos y contrata al de menor error
    # Entra: ventas = todas las ventas del producto | inicio = 1.er mes del examen (4)
    # Hace:  1) saca el MSE (nota) de cada modelo  2) elige el menor
    #        3) con el ganador pronostica el próximo mes  4) calcula D
    # Sale:  resultados (nota de cada uno), ganador, pronóstico, D
    resultados = {
        "MM N=2": evaluar_mm(ventas, 2, inicio),
        "MM N=3": evaluar_mm(ventas, 3, inicio),
        "MM N=4": evaluar_mm(ventas, 4, inicio),
        "Ponderado N=2": evaluar_ponderado(ventas, PESOS_N2, inicio),
        "Ponderado N=3": evaluar_ponderado(ventas, PESOS_N3, inicio),
    }
    ganador = min(resultados, key=resultados.get)    # nombre con el MSE más bajo
    pronostico = pronostico_modelo(ventas, ganador)  # el ganador predice octubre (con TODAS las ventas)
    D = demanda_anual(pronostico)                    # D = pronóstico × 12
    return resultados, ganador, pronostico, D


def predicciones_modelo(ventas, modelo, inicio):
    # Para la gráfica: lo que el modelo predijo en cada mes pasado
    # Entra: ventas | modelo = nombre del ganador | inicio
    # Sale:  lista de predicciones (una por mes desde inicio)
    predicciones = []
    for i in range(inicio, len(ventas)):
        historia = ventas[:i]
        predicciones.append(pronostico_modelo(historia, modelo))
    return predicciones

# ---- Prueba rápida (solo corre si ejecutas este archivo directamente) ----
if __name__ == "__main__":
    print(elegir_mejor(ventasVasos, 4))
