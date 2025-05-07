from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os

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
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        if usuario == USER and contrasena == PASS:
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            return "Credenciales inválidas. <a href='/login'>Intentar de nuevo</a>"
    return '''
        <form method="post">
            Usuario: <input type="text" name="usuario"><br>
            Contraseña: <input type="password" name="contrasena"><br>
            <input type="submit" value="Iniciar sesión">
        </form>
    '''


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


@app.route('/exercise1')
def exercise1():
    return render_template('exercise1.html')

if __name__ == '__main__':
    app.run()