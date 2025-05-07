from flask import Flask
from flask import Flask, render_template
import os

template_dir = os.path.abspath('../templates')
static_dir = os.path.abspath('../static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/exercise1')
def exercise1():
    return render_template('exercise1.html')

if __name__ == '__main__':
    app.run()