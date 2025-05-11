import json
import requests
import os
import sqlite3
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import pandas as pd
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
    """
    Llama a https://cve.circl.lu/api/last y devuelve
    lista de nCVE IDs: ['CVE-2025-47424', 'CVE-2025-3794', …]
    """
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    cve_ids = []
    for item in data:
        # 1) Si tiene cveMetadata.cveId, lo uso
        if 'cveMetadata' in item and 'cveId' in item['cveMetadata']:
            cve_ids.append(item['cveMetadata']['cveId'])
        else:
            # 2) Si hay aliases, tomo el primero que empiece por 'CVE-'
            if 'aliases' in item:
                for alias in item['aliases']:
                    if alias.startswith('CVE-'):
                        cve_ids.append(alias)
                        break
            # 3) Si no, como fallback miro el campo 'id'
            elif 'id' in item and item['id'].startswith('CVE-'):
                cve_ids.append(item['id'])

        # 4) Si ya tengo suficientes, corto el bucle
        if len(cve_ids) >= nCVE:
            break

    return cve_ids



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

def load_and_preprocess_data():
    """
    Carga los datos desde la base de datos tickets.db y los prepara para modelos ML.
    Usa las columnas: es_mantenimiento, incident_type_id, satisfaccion, es_critico.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'data', 'tickets.db')
    conn = sqlite3.connect(db_path)
    query = """
        SELECT
            es_mantenimiento,
            incident_type_id,
            satisfaccion,
            es_critico
        FROM tickets
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Extraer características y etiquetas
    features = []
    labels = []
    for _, row in df.iterrows():
        feature = [
            int(row['es_mantenimiento']),
            int(row['incident_type_id']),
            int(row['satisfaccion'])
        ]
        features.append(feature)
        labels.append(int(row['es_critico']))

    # Convertir a DataFrame
    df_features = pd.DataFrame(features, columns=['es_mantenimiento', 'incident_type_id', 'satisfaccion_cliente'])
    y = pd.Series(labels)

    # One-hot encode 'incident_type_id'
    incident_types = sorted(df_features['incident_type_id'].unique())
    encoder = OneHotEncoder(categories=[incident_types], sparse_output=False)
    incident_type_encoded = encoder.fit_transform(df_features[['incident_type_id']])
    incident_type_df = pd.DataFrame(incident_type_encoded, columns=encoder.get_feature_names_out(['incident_type_id']))

    # Combinar características codificadas
    X = pd.concat([df_features[['es_mantenimiento', 'satisfaccion_cliente']], incident_type_df], axis=1)

    # Dividir en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test, encoder

def logistic_regression_analysis():
    X_train, X_test, y_train, y_test, encoder = load_and_preprocess_data()
    
    # Train Logistic Regression
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Visualization: Feature coefficients
    plt.figure(figsize=(10, 6))
    plt.bar(X_train.columns, model.coef_[0], color='blue')
    plt.title('Logistic Regression - Feature Coefficients')
    plt.xlabel('Features')
    plt.ylabel('Coefficient Value')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    vis_path = os.path.join(base_dir, 'static/images', 'logistic_regression_coefficients.png')
    plt.savefig(vis_path)
    plt.close()

    return model, accuracy, 'images/logistic_regression_coefficients.png'

def decision_tree_analysis():
    X_train, X_test, y_train, y_test, encoder = load_and_preprocess_data()
    
    # Train Decision Tree
    model = DecisionTreeClassifier(max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Visualization: Tree structure
    plt.figure(figsize=(20, 10))
    plot_tree(model, feature_names=X_train.columns, class_names=['Non-Critical', 'Critical'], filled=True, rounded=True)
    plt.title('Decision Tree - Classification Structure')
    base_dir = os.path.dirname(os.path.dirname(__file__))
    vis_path = os.path.join(base_dir, 'static/images', 'decision_tree.png')
    plt.savefig(vis_path)
    plt.close()

    return model, accuracy, 'images/decision_tree.png'

def random_forest_analysis():
    X_train, X_test, y_train, y_test, encoder = load_and_preprocess_data()
    
    # Train Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Visualization: Feature importance
    plt.figure(figsize=(10, 6))
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    plt.bar(range(X_train.shape[1]), importances[indices], color='green')
    plt.title('Random Forest - Feature Importance')
    plt.xlabel('Features')
    plt.ylabel('Importance Score')
    plt.xticks(range(X_train.shape[1]), [X_train.columns[i] for i in indices], rotation=45, ha='right')
    plt.tight_layout()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    vis_path = os.path.join(base_dir, 'static/images', 'random_forest_importance.png')
    plt.savefig(vis_path)
    plt.close()

    return model, accuracy, 'images/random_forest_importance.png'

def predict_ticket_criticality(model, encoder, ticket_data):
    # Preprocess new ticket
    feature = [
        1 if ticket_data['es_mantenimiento'] else 0,
        ticket_data['incident_type_id'],
        ticket_data['satisfaccion_cliente']
    ]
    input_df = pd.DataFrame([feature], columns=['es_mantenimiento', 'incident_type_id', 'satisfaccion_cliente'])

    # One-hot encode 'incident_type_id'
    incident_type_encoded = encoder.transform(input_df[['incident_type_id']])
    incident_type_df = pd.DataFrame(incident_type_encoded, columns=encoder.get_feature_names_out(['incident_type_id']))

    # Combine encoded features
    input_df = pd.concat([input_df[['es_mantenimiento', 'satisfaccion_cliente']], incident_type_df], axis=1)

    # Predict
    prediction = model.predict(input_df)[0]
    return 'Critical' if prediction == 1 else 'Non-Critical'