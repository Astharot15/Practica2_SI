import pandas as pd
import json
import requests



def top_clientes(X, JSON_FILE):
    
    #Cargamos archivo json
    with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    # Crear DataFrame
    df = pd.DataFrame(data['tickets_emitidos'])

    # Contar incidencias por cliente
    top_clientes = df['cliente'].value_counts().head(X).reset_index()
    top_clientes.columns = ['cliente', 'incidencias']
    return top_clientes.to_dict('records')



def obtener_top_tipos_incidencias(X, JSON_FILE):
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['tickets_emitidos'])

    # Calcular tiempo de resolución
    df['fecha_apertura'] = pd.to_datetime(df['fecha_apertura'])
    df['fecha_cierre'] = pd.to_datetime(df['fecha_cierre'])
    df['tiempo_resolucion'] = (df['fecha_cierre'] - df['fecha_apertura']).dt.days

    # Sumar tiempo por tipo de incidencia
    top_tipos = df.groupby('tipo_incidencia')['tiempo_resolucion'].sum().head(X).reset_index()
    return top_tipos.to_dict('records')



def obtener_top_empleados(X, JSON_FILE):
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['tickets_emitidos'])
    
    # Desglosar contactos con empleados
    empleados = df.explode('contactos_con_empleados')
    empleados = pd.json_normalize(empleados['contactos_con_empleados'])
    # Sumar tiempo por empleado
    top_empleados = empleados.groupby('id_emp')['tiempo'].sum().head(X).reset_index()
    return top_empleados.to_dict('records')



def get_lasts_CVEs(nCVE=10, url="https://cve.circl.lu/api/last"):

    response = requests.get(url)
    # Verificamos que la petición se realizó correctamente
    if response.status_code == 200:
        last30CVE = response.json()
    else:
        print(f"Error, Status Code: {response.status_code}")

    nLastCVE = []


    for item in last30CVE:
        if 'cveMetadata' in item:
            nLastCVE.append(item['cveMetadata']['cveId'])
        if len(nLastCVE) == 10:
            break

    return nLastCVE


#print(top_clientes(10))
#print(obtener_top_tipos_incidencias(3))
#print(obtener_top_empleados(3))