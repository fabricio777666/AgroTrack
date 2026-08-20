from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return "<h1> Sistema AgroTrack Rodando!</h1><p>A estrutura base foi criada com sucesso.</p>"

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome_maquina = request.form['nome']
        return f"Sucesso! A máquina '{nome_maquina}' foi cadastrada."
    return render_template('cadastro.html')

@app.route('/relatorio')
def relatorio():
    return render_template('relatorio.html', maquinas=[])

if __name__ == '__main__':
    app.run(debug=True)