from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Lista para armazenar o maquinário cadastrado em memória
maquinas = []

@app.route('/')
def index():
    return render_template('index.html', maquinas=maquinas)

@app.route('/cadastrar-produto')
def cadastrar_produto():
    return render_template('produto.html')

@app.route('/relatorio')
def relatorio():
    return render_template('relatorio.html', maquinas=maquinas)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome_maquina = request.form['nome']
        maquinas.append({'nome': nome_maquina})
        return f"Sucesso! A máquina '{nome_maquina}' foi cadastrada."
    return render_template('cadastrar.html')

if __name__ == '__main__':
    app.run(debug=True)