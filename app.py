from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/exercise1')
def exercise1():
    return render_template('exercise1.html')

if __name__ == '__main__':
    app.run()