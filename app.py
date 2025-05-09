from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os

from utils.service import (
    top_clientes,
    obtener_top_tipos_incidencias,
    obtener_top_empleados,
    average_resolution_time_by_type,
    tickets_per_weekday
)

app = Flask(__name__)

# Cargar variables de entorno necesarias
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
USER = os.getenv('USERAPP')
PASS = os.getenv('PASS')


@app.route('/')
def index():

    if 'usuario' in session:
        return render_template('index.html')

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Porque suponemos que al iniciar no hay erro

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
    top_clients = []
    top_types = []
    top_employees = []
    show_employees = False  # Variable para controlar si se muestran los empleados

    if request.method == 'POST':
        x = int(request.form.get('top_x', 5))  # Valor por defecto: 5
        show_employees = 'show_employees' in request.form  # Verificar si el checkbox está marcado
        json_file = os.path.join('data', 'data_clasified.json')  # Ruta al archivo JSON

        # Obtener el top de clientes y tipos de incidencias
        top_clients = top_clientes(x, json_file)
        top_types = obtener_top_tipos_incidencias(x, json_file)

        # Si el usuario seleccionó mostrar empleados, obtener el top de empleados
        if show_employees:
            top_employees = obtener_top_empleados(x, json_file)

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
        json_file = os.path.join('data', 'data_clasified.json')

        # lógica en service.py
        avg_by_type    = average_resolution_time_by_type(json_file)
        tickets_by_day = tickets_per_weekday(json_file)

        resultados = {
            'avg_by_type': avg_by_type,
            'tickets_by_day': tickets_by_day
        }

    return render_template('extra_metrics.html', resultados=resultados)

if __name__ == '__main__':
    app.run()
