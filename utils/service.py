import pandas as pd
import json
from collections import defaultdict
import requests
import datetime

from samba.dcerpc.dcerpc import response


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



def get_last_CVEs(nCVE=10, url="https://cve.circl.lu/api/last"):

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


# Es vulnerable a inyecciones pero no es el cometido de esta practica
def get_CVE_org(CVE_id, url_base="https://cve.circl.lu/api/cve/"):

    url = url_base + CVE_id
    response = requests.get(url)
    if response.status_code == 200:
        cve_info = response.json()
    else:
        print(f"Error, Status Code: {response.status_code}")

    org_id = cve_info["cveMetadata"]["assignerOrgId"]
    org_name = cve_info["cveMetadata"]['assignerShortName']


    return org_id, org_name


def average_resolution_time_by_type(json_path):
    """
    Devuelve un dict { tipo_incidencia: media_en_días }
    """
    with open(json_path, encoding='utf-8') as f:
        raw = json.load(f)

    tickets = raw.get('tickets_emitidos', [])
    tiempos = defaultdict(list)

    for ticket in tickets:
        # parseamos apertura y cierre
        t0 = datetime.datetime.fromisoformat(ticket['fecha_apertura'])
        t1 = datetime.datetime.fromisoformat(ticket['fecha_cierre'])
        dias = (t1 - t0).days
        tipos = ticket['tipo_incidencia']
        tiempos[tipos].append(dias)

    # redondeamos a 1 decimal
    return {
        tipo: round(sum(lista)/len(lista), 1)
        for tipo, lista in tiempos.items() if lista
    }


def tickets_per_weekday(json_path):
    """
    Devuelve un dict { 'Monday': n, 'Tuesday': m, ... }
    """
    with open(json_path, encoding='utf-8') as f:
        raw = json.load(f)

    tickets = raw.get('tickets_emitidos', [])
    conteo = defaultdict(int)

    for ticket in tickets:
        fecha = datetime.datetime.fromisoformat(ticket['fecha_apertura'])
        dia_sem = fecha.strftime('%A')  # 'Monday', 'Tuesday', etc.
        conteo[dia_sem] += 1

    return dict(conteo)


#print(top_clientes(10))
#print(obtener_top_tipos_incidencias(3))
#print(obtener_top_empleados(3))