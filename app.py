from flask import Flask, render_template, request
import os
from utils.service import top_clientes, obtener_top_tipos_incidencias, obtener_top_empleados

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/exercise1', methods=['GET', 'POST'])
def exercise1():
    top_clients = []
    top_types = []
    top_employees = []
    show_employees = False  # Variable para controlar si se muestran los empleados

    if request.method == 'POST':
        x = int(request.form.get('top_x', 5))  # Valor por defecto: 5
        show_employees = 'show_employees' in request.form  # Verificar si el checkbox está marcado
        json_file = os.path.join('static', 'data', 'data_clasified.json')  # Ruta al archivo JSON

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

if __name__ == '__main__':
    app.run()
