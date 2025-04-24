import pandas as pd
import json
from datetime import datetime


def top_clientes(X):
    
    #Cargamos archivo json
    with open('data/data_clasified.json', 'r') as f:
            data = json.load(f)
    # Crear DataFrame
    df = pd.DataFrame(data['tickets_emitidos'])

    # Contar incidencias por cliente
    top_clientes = df['cliente'].value_counts().head(X).reset_index()
    top_clientes.columns = ['cliente', 'incidencias']
    return top_clientes.to_dict('records')



def obtener_top_tipos_incidencias(X):
    with open('data/data_clasified.json', 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['tickets_emitidos'])

    # Calcular tiempo de resolución
    df['fecha_apertura'] = pd.to_datetime(df['fecha_apertura'])
    df['fecha_cierre'] = pd.to_datetime(df['fecha_cierre'])
    df['tiempo_resolucion'] = (df['fecha_cierre'] - df['fecha_apertura']).dt.days

    # Sumar tiempo por tipo de incidencia
    top_tipos = df.groupby('tipo_incidencia')['tiempo_resolucion'].sum().head(X).reset_index()
    return top_tipos.to_dict('records')

def obtener_top_empleados(X):
    with open('data/data_clasified.json', 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['tickets_emitidos'])
    
    # Desglosar contactos con empleados
    empleados = df.explode('contactos_con_empleados')
    empleados = pd.json_normalize(empleados['contactos_con_empleados'])
    # Sumar tiempo por empleado
    top_empleados = empleados.groupby('id_emp')['tiempo'].sum().head(X).reset_index()
    return top_empleados.to_dict('records')


#print(top_clientes(10))
#print(obtener_top_tipos_incidencias(3))
#print(obtener_top_empleados(3))