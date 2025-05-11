from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from utils.service import *
import os

from utils.service import (
    get_db, close_db,
    top_clientes,
    obtener_top_tipos_incidencias,
    obtener_top_empleados,
    average_resolution_time_by_type,
    tickets_per_weekday,
    get_last_CVEs,
    get_CVE_org
)

logreg_model, logreg_acc, logreg_vis = logistic_regression_analysis()
dt_model, dt_acc, dt_vis = decision_tree_analysis()
rf_model, rf_acc, rf_vis = random_forest_analysis()
_, _, _, _, encoder = load_and_preprocess_data()

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
USER = os.getenv('USERAPP')
PASS = os.getenv('PASS')

# Cierra la conexión a la DB al terminar cada petición
app.teardown_appcontext(close_db)

@app.route('/')
def index():
    if 'usuario' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario == USER and contrasena == PASS:
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            error = "Usuario o contraseña incorrectos."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/exercise1', methods=['GET', 'POST'])
def exercise1():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    top_clients = []
    top_types   = []
    top_employees = []
    show_employees = False

    if request.method == 'POST':
        x = int(request.form.get('top_x', 5))
        show_employees = 'show_employees' in request.form

        # Ahora tiramos de SQLite, no del JSON
        top_clients   = top_clientes(x)
        top_types     = obtener_top_tipos_incidencias(x)
        if show_employees:
            top_employees = obtener_top_empleados(x)

    return render_template(
        'exercise1.html',
        top_clients=top_clients,
        top_types=top_types,
        top_employees=top_employees,
        show_employees=show_employees
    )

@app.route('/extra-metrics', methods=['GET', 'POST'])
def extra_metrics():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    resultados = None
    if request.method == 'POST':
        avg_by_type    = average_resolution_time_by_type()
        tickets_by_day = tickets_per_weekday()

        resultados = {
            'avg_by_type': avg_by_type,
            'tickets_by_day': tickets_by_day
        }

    return render_template('extra_metrics.html', resultados=resultados)

@app.route('/last-cves')
def last_cves():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    cves = get_last_CVEs(10)
    return render_template('last_cves.html', cves=cves)

@app.route('/cve-info', methods=['GET', 'POST'])
def cve_info():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    org_id = org_name = None
    if request.method == 'POST':
        CVE_id = request.form.get('CVE_id')
        org_id, org_name = get_CVE_org(CVE_id)
    return render_template('cve_info.html', org_id=org_id, org_name=org_name)

@app.route('/predict', methods=['GET','POST'])
def predict():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    # Si es GET, devolvemos el formulario iaCMI.html sin resultados
    if request.method == 'GET':
        return render_template('predict.html')

    # Si es POST, recogemos los datos del formulario
    es_mantenimiento = 'es_mantenimiento' in request.form
    incident_type_id = int(request.form.get('incident_type_id', 1))
    satisfaccion = int(request.form.get('satisfaccion', 5))
    method = request.form.get('ia_method', 'logistic')

    ticket = {
        'es_mantenimiento': es_mantenimiento,
        'incident_type_id': incident_type_id,
        'satisfaccion_cliente': satisfaccion
    }

    # Selección de modelo y visualización
    if method == 'logistic':
        model, acc, vis = logreg_model, logreg_acc, logreg_vis
    elif method == 'tree':
        model, acc, vis = dt_model, dt_acc, dt_vis
    elif method == 'forest':
        model, acc, vis = rf_model, rf_acc, rf_vis
    else:
        return render_template('predict.html', error='Método no válido')

    # Predecir criticidad
    result = predict_ticket_criticality(model, encoder, ticket)

    # Renderizar iaCMI.html con los resultados
    return render_template(
        'predict.html',
        result=result,
        accuracy=round(acc, 2),
        visualization=vis
    )

if __name__ == '__main__':
    app.run()

