from flask import Flask, render_template, request, redirect, url_for
import database

app = Flask(__name__)

# Garante que a tabela existe e tem dados de exemplo assim que o
# servidor sobe (funciona tanto local quanto no PythonAnywhere).
database.criar_tabela()
database.popular_dados_exemplo()


def calcular_indicadores(maquina):
    """Calcula custo por hora e status de manutenção de uma máquina."""
    custo_hora = maquina["consumo_diesel_litros_hora"] * maquina["custo_diesel_litro"]
    horas_desde_manutencao = maquina["horimetro_atual"] - maquina["ultima_manutencao_horimetro"]
    horas_restantes = maquina["intervalo_manutencao_horas"] - horas_desde_manutencao
    alerta_manutencao = horas_restantes <= 0

    return {
        **maquina,
        "custo_hora": round(custo_hora, 2),
        "horas_desde_manutencao": horas_desde_manutencao,
        "horas_restantes": horas_restantes,
        "alerta_manutencao": alerta_manutencao,
    }


def ler_formulario(form):
    """Converte os dados do formulário HTML em um dicionário pronto
    para salvar no banco."""
    return {
        "nome": form["nome"],
        "tipo": form["tipo"],
        "horimetro_atual": float(form["horimetro_atual"]),
        "consumo_diesel_litros_hora": float(form["consumo_diesel_litros_hora"]),
        "custo_diesel_litro": float(form["custo_diesel_litro"]),
        "ultima_manutencao_horimetro": float(form["ultima_manutencao_horimetro"]),
        "intervalo_manutencao_horas": float(form["intervalo_manutencao_horas"]),
    }


@app.route('/')
def index():
    maquinas_calc = [calcular_indicadores(m) for m in database.listar_maquinas()]

    total_maquinas = len(maquinas_calc)
    alertas_ativos = sum(1 for m in maquinas_calc if m["alerta_manutencao"])
    custo_medio_hora = (
        round(sum(m["custo_hora"] for m in maquinas_calc) / total_maquinas, 2)
        if total_maquinas > 0 else 0
    )

    return render_template(
        'index.html',
        total_maquinas=total_maquinas,
        alertas_ativos=alertas_ativos,
        custo_medio_hora=custo_medio_hora,
        maquinas=maquinas_calc,
    )


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        database.inserir_maquina(ler_formulario(request.form))
        return redirect(url_for('relatorio'))

    return render_template('cadastro.html')


@app.route('/relatorio')
def relatorio():
    maquinas_calc = [calcular_indicadores(m) for m in database.listar_maquinas()]
    return render_template('relatorio.html', maquinas=maquinas_calc)


@app.route('/editar/<int:maquina_id>', methods=['GET', 'POST'])
def editar(maquina_id):
    if request.method == 'POST':
        database.atualizar_maquina(maquina_id, ler_formulario(request.form))
        return redirect(url_for('relatorio'))

    maquina = database.buscar_maquina(maquina_id)
    if maquina is None:
        return redirect(url_for('relatorio'))
    return render_template('editar.html', maquina=maquina)


@app.route('/deletar/<int:maquina_id>', methods=['POST'])
def deletar(maquina_id):
    database.deletar_maquina(maquina_id)
    return redirect(url_for('relatorio'))


if __name__ == '__main__':
    app.run(debug=True)
