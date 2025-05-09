import requests
import os
import sqlite3
from flask import g

DB_PATH = os.getenv('DB_PATH', 'data/tickets.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def top_clientes(X):
    """
    Devuelve los X clientes con más incidencias:
      [{ 'cliente': 123, 'incidencias': 17 }, ...]
    """
    db = get_db()
    rows = db.execute("""
      SELECT client_id   AS cliente,
             COUNT(*)      AS incidencias
        FROM tickets
       GROUP BY client_id
       ORDER BY incidencias DESC
       LIMIT ?
    """, (X,)).fetchall()
    return [dict(r) for r in rows]



def obtener_top_tipos_incidencias(X):
    """
    Devuelve los X tipos de incidencia que más tiempo suman en resolución:
      [{ 'tipo_incidencia': 5, 'tiempo_resolucion': 120 }, …]
    """
    db = get_db()
    rows = db.execute("""
        SELECT incident_type_id   AS tipo_incidencia,
               ROUND(SUM(
                 julianday(fecha_cierre)
                 - julianday(fecha_apertura)
               ), 1)              AS tiempo_resolucion
          FROM tickets
         GROUP BY incident_type_id
         ORDER BY tiempo_resolucion DESC
         LIMIT ?
    """, (X,)).fetchall()
    return [dict(r) for r in rows]


def obtener_top_empleados(X):
    """
    Devuelve los X empleados que más tiempo han trabajado:
      [{ 'id_emp': 12, 'tiempo': 34.5 }, …]
    """
    db = get_db()
    rows = db.execute("""
      SELECT employee_id   AS id_emp,
             ROUND(SUM(tiempo), 1)  AS tiempo
        FROM contacts
       GROUP BY employee_id
       ORDER BY tiempo DESC
       LIMIT ?
    """, (X,)).fetchall()
    return [dict(r) for r in rows]



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



def average_resolution_time_by_type():
    """
    Devuelve un dict { tipo_incidencia: media_en_días }
    """
    db = get_db()
    rows = db.execute("""
        SELECT
          incident_type_id      AS tipo_incidencia,
          ROUND(
            AVG(
              julianday(fecha_cierre)
              - julianday(fecha_apertura)
            ), 1
          )                    AS media_dias
        FROM tickets
        GROUP BY incident_type_id
    """).fetchall()
    return { row['tipo_incidencia']: row['media_dias'] for row in rows }


def tickets_per_weekday():
    """
    Devuelve un dict { 'Monday': n, 'Tuesday': m, ... }
    """
    # Mapa de número de día (0=Sunday … 6=Saturday) a nombre en inglés
    day_names = {
        '0': 'Sunday', '1': 'Monday', '2': 'Tuesday',
        '3': 'Wednesday', '4': 'Thursday',
        '5': 'Friday', '6': 'Saturday'
    }
    db = get_db()
    rows = db.execute("""
        SELECT
          strftime('%w', fecha_apertura) AS dow,
          COUNT(*)                      AS count
        FROM tickets
        GROUP BY dow
    """).fetchall()
    # Traducimos los códigos a nombres
    return {
        day_names[row['dow']]: row['count']
        for row in rows
    }


#print(top_clientes(10))
#print(obtener_top_tipos_incidencias(3))
#print(obtener_top_empleados(3))