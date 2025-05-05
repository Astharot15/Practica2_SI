from flask import Flask, render_template
app = Flask(__name__)

# INDEX
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/exercise1')
def exercise1():
    return render_template('exercise1.html')
