from httpx import request

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1> Sistema AgroTrack Rodando!</h1><p>A estrutura base foi criada com sucesso.</p>"

if __name__ == '__main__':
    app.run(debug=True)

    @app.route('/registrar', methods=['GET', 'POST'])
    def registrar():
        if request.method == 'POST':
            data = request.form['data']
            horas = request.form['horas']
            combustivel = request.form['combustivel']

        return "Uso registrado com sucesso!"

        return render_template('registrar_uso.html')