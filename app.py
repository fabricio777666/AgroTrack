from flask import Flask, render_template, request, redirect, url_for
import database  # Importa o arquivo de banco de dados otimizado

app = Flask(__name__)

# Inicializa o banco de dados e insere dados de teste se estiver vazio
database.criar_tabela()
database.popular_dados_exemplo()

@app.route('/')
def index():
    maquinas = database.listar_maquinas()
    return render_template('index.html', maquinas=maquinas)

@app.route('/relatorio')
def relatorio():
    maquinas = database.listar_maquinas()
    return render_template('relatorio.html', maquinas=maquinas)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        # Captura todos os campos enviados pelo formulário
        dados = {
            "nome": request.form['nome'],
            "tipo": request.form['tipo'],
            "horimetro_atual": float(request.form['horimetro_atual']),
            "consumo_diesel_litros_hora": float(request.form['consumo_diesel_litros_hora']),
            "custo_diesel_litro": float(request.form['custo_diesel_litro']),
            "ultima_manutencao_horimetro": float(request.form['ultima_manutencao_horimetro']),
            "intervalo_manutencao_horas": float(request.form['intervalo_manutencao_horas'])
        }
        
        database.inserir_maquina(dados)
        return redirect(url_for('index'))  # Redireciona para a página inicial após salvar
        
    return render_template('cadastrar.html')

@app.route('/deletar/<int:id>')
def deletar(id):
    database.deletar_maquina(id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)