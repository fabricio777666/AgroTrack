from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Lista para armazenar o maquinário cadastrado em memória
maquinas = []

@app.route('/')
def index():
    return render_template('index.html', maquinas=maquinas)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form.get('nome')
        marca = request.form.get('marca')
        horimetro = float(request.form.get('horimetro', 0))

        # Estrutura base com cálculos fictícios para exibição no relatório
        maquina = {
            'nome': f"{nome} - {marca}",
            'marca': marca,
            'horimetro_atual': horimetro,
            'total_horas': horimetro,
            'custo_combustivel': horimetro * 45.0,  # Valor estimativo para preencher o template
            'custo_por_hora': 112.40,
            'alerta_manutencao': horimetro > 100    # Regra simples de alerta
        }
        
        maquinas.append(maquina)
        return redirect(url_for('relatorio'))
        
    return render_template('cadastro.html')

@app.route('/relatorio')
def relatorio():
    return render_template('relatorio.html', maquinas=maquinas)

if __name__ == '__main__':
    app.run(debug=True)