"""Rotas web e API do AgroTrack; execute `flask --app app --help` para tarefas locais."""
import math
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

import click
from flask import (Blueprint, Flask, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import database

web = Blueprint('web', __name__)
TIPOS = ('Trator', 'Colheitadeira', 'Pulverizador', 'Outro')
CAMPOS_NUMERICOS = {
    'horimetro_atual': 'Horímetro atual',
    'consumo_diesel_litros_hora': 'Consumo de diesel',
    'custo_diesel_litro': 'Preço do diesel',
    'ultima_manutencao_horimetro': 'Horímetro na última manutenção',
    'intervalo_manutencao_horas': 'Intervalo entre manutenções',
}


def exigir_perfil(*perfis):
    """Autoriza no servidor; esconder botões não substitui esta verificação."""
    def decorar(funcao):
        @wraps(funcao)
        def protegida(*args, **kwargs):
            if g.usuario is None:
                if request.path.startswith('/api/'):
                    abort(401)
                return redirect(url_for('web.login'))
            if perfis and g.usuario['perfil'] not in perfis:
                abort(403)
            return funcao(*args, **kwargs)
        return protegida
    return decorar


def calcular_indicadores(maquina):
    """Estimativa de diesel por hora; não inclui todos os custos operacionais."""
    custo_hora = maquina['consumo_diesel_litros_hora'] * maquina['custo_diesel_litro']
    horas_desde = maquina['horimetro_atual'] - maquina['ultima_manutencao_horimetro']
    restantes = maquina['intervalo_manutencao_horas'] - horas_desde
    return {**maquina, 'custo_hora': round(custo_hora, 2),
            'horas_desde_manutencao': horas_desde, 'horas_restantes': restantes,
            'alerta_manutencao': restantes <= 0,
            'manutencao_proxima': 0 < restantes <= 20}


def ler_formulario(form):
    """Valida HTML e JSON igualmente, inclusive valores NaN/infinito."""
    if not isinstance(form, dict) and not hasattr(form, 'get'):
        raise ValueError('Envie um objeto com os dados da máquina.')
    nome, modelo, tipo = form.get('nome'), form.get('modelo'), form.get('tipo')
    if not isinstance(nome, str) or not 1 <= len(nome.strip()) <= 120:
        raise ValueError('Informe um nome de 1 a 120 caracteres.')
    if not isinstance(modelo, str) or not 1 <= len(modelo.strip()) <= 120:
        raise ValueError('Informe um modelo de 1 a 120 caracteres.')
    if tipo not in TIPOS:
        raise ValueError('Selecione um tipo de máquina válido.')
    marca = form.get('marca', '')
    if not isinstance(marca, str) or len(marca.strip()) > 120:
        raise ValueError('A marca deve ter até 120 caracteres.')
    ano = form.get('ano', '')
    if ano not in ('', None):
        try:
            ano = int(ano)
        except (TypeError, ValueError, OverflowError):
            raise ValueError('Informe um ano válido.') from None
        if not 1900 <= ano <= datetime.now().year + 1:
            raise ValueError('O ano da máquina está fora do intervalo válido.')
    else:
        ano = None
    dados = {'nome': nome.strip(), 'modelo': modelo.strip(), 'marca': marca.strip(), 'ano': ano, 'tipo': tipo}
    for campo, rotulo in CAMPOS_NUMERICOS.items():
        valor = form.get(campo)
        try:
            if isinstance(valor, bool):
                raise ValueError
            numero = float(valor)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f'{rotulo}: informe um número válido.') from None
        if not math.isfinite(numero) or not 0 <= numero <= 1_000_000_000:
            raise ValueError(f'{rotulo}: use um número entre 0 e 1 bilhão.')
        dados[campo] = numero
    if dados['intervalo_manutencao_horas'] <= 0:
        raise ValueError('O intervalo entre manutenções deve ser maior que zero.')
    if dados['ultima_manutencao_horimetro'] > dados['horimetro_atual']:
        raise ValueError('A última manutenção não pode superar o horímetro atual.')
    return dados


def obter_maquina(maquina_id):
    maquina = database.buscar_maquina(maquina_id)
    if maquina is None:
        abort(404)
    return maquina


@web.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = database.buscar_usuario(nome=request.form.get('nome', '').strip())
        # Hash de comparação evita um caminho muito mais rápido para usuários inexistentes.
        senha_hash = usuario['senha_hash'] if usuario else g.hash_inexistente
        valida = check_password_hash(senha_hash, request.form.get('senha', ''))
        if usuario and valida:
            session.clear()
            session['usuario_id'] = usuario['id']
            session.permanent = True
            database.registrar_evento(usuario['id'], 'login')
            return redirect(url_for('web.index'))
        database.registrar_evento(None, 'login_recusado')
        flash('Usuário ou senha inválidos.', 'erro')
        return render_template('login.html'), 401
    return render_template('login.html')


@web.route('/cadastro', methods=['GET', 'POST'])
def cadastro_conta():
    """Cada conta pública cria uma fazenda independente e seu administrador."""
    if request.method == 'POST':
        fazenda = request.form.get('fazenda', '').strip()
        nome = request.form.get('nome', '').strip()
        senha = request.form.get('senha', '')
        confirmacao = request.form.get('confirmacao', '')
        if not 2 <= len(fazenda) <= 120 or not 3 <= len(nome) <= 80:
            flash('Informe uma fazenda e um usuário válidos.', 'erro')
        elif len(senha) < 12 or senha != confirmacao:
            flash('Use uma senha de pelo menos 12 caracteres e confirme-a corretamente.', 'erro')
        else:
            try:
                database.cadastrar_fazenda(fazenda, nome, generate_password_hash(senha))
            except sqlite3.IntegrityError:
                flash('Esse nome de usuário já está em uso.', 'erro')
            else:
                flash('Conta criada. Entre para acessar sua fazenda.', 'sucesso')
                return redirect(url_for('web.login'))
        return render_template('cadastro_conta.html', valores=request.form), 400
    return render_template('cadastro_conta.html', valores={})


@web.post('/logout')
@exigir_perfil()
def logout():
    database.registrar_evento(g.usuario['id'], 'logout')
    session.clear()
    return redirect(url_for('web.login'))


@web.get('/')
@exigir_perfil()
def index():
    maquinas = [calcular_indicadores(m) for m in database.listar_maquinas()]
    total = len(maquinas)
    return render_template('index.html', maquinas=maquinas, total_maquinas=total,
        alertas_ativos=sum(m['alerta_manutencao'] for m in maquinas),
        custo_medio_hora=round(sum(m['custo_hora'] for m in maquinas) / total, 2) if total else 0)


@web.route('/cadastrar', methods=['GET', 'POST'])
@exigir_perfil('admin', 'operador')
def cadastrar():
    if request.method == 'POST':
        try:
            dados = ler_formulario(request.form)
        except ValueError as erro:
            flash(str(erro), 'erro')
            return render_template('cadastro.html', valores=request.form), 400
        database.inserir_maquina(dados, g.usuario['id'])
        flash('Máquina cadastrada.', 'sucesso')
        return redirect(url_for('web.relatorio'))
    return render_template('cadastro.html', valores={})


@web.get('/relatorio')
@exigir_perfil()
def relatorio():
    resumos = database.resumir_uso_fazenda()
    return render_template('relatorio.html', maquinas=[
        {**calcular_indicadores(m),
         'litros_por_hora_registrados': round(resumos[m['id']]['litros'] / resumos[m['id']]['horas'], 2)
         if m['id'] in resumos and resumos[m['id']]['horas'] > 0 and resumos[m['id']]['litros'] > 0 else None}
        for m in database.listar_maquinas()])


@web.route('/editar/<int:maquina_id>', methods=['GET', 'POST'])
@exigir_perfil('admin', 'operador')
def editar(maquina_id):
    maquina = obter_maquina(maquina_id)
    if request.method == 'POST':
        try:
            dados = ler_formulario(request.form)
            database.atualizar_maquina(maquina_id, dados, g.usuario['id'])
        except ValueError as erro:
            flash(str(erro), 'erro')
            return render_template('editar.html', maquina={**maquina, **request.form}), 400
        flash('Máquina atualizada.', 'sucesso')
        return redirect(url_for('web.relatorio'))
    return render_template('editar.html', maquina=maquina)


@web.post('/deletar/<int:maquina_id>')
@exigir_perfil('admin')
def deletar(maquina_id):
    obter_maquina(maquina_id)
    try:
        database.deletar_maquina(maquina_id, g.usuario['id'])
    except ValueError as erro:
        abort(409, description=str(erro))
    flash('Máquina excluída.', 'sucesso')
    return redirect(url_for('web.relatorio'))


@web.get('/auditoria')
@exigir_perfil('admin')
def auditoria():
    return render_template('auditoria.html', eventos=database.listar_eventos())


@web.route('/equipe', methods=['GET', 'POST'])
@exigir_perfil('admin')
def equipe():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        senha = request.form.get('senha', '')
        perfil = request.form.get('perfil', '')
        if not 3 <= len(nome) <= 80 or len(senha) < 12 or perfil not in ('operador', 'leitor'):
            flash('Use usuário de 3 a 80 caracteres, senha de 12 ou mais e perfil válido.', 'erro')
            return render_template('equipe.html', membros=database.listar_equipe()), 400
        try:
            database.adicionar_equipe(nome, generate_password_hash(senha), perfil)
        except sqlite3.IntegrityError:
            flash('Esse nome de usuário já está em uso.', 'erro')
            return render_template('equipe.html', membros=database.listar_equipe()), 400
        flash('Membro cadastrado para sua fazenda.', 'sucesso')
        return redirect(url_for('web.equipe'))
    return render_template('equipe.html', membros=database.listar_equipe())


@web.get('/api/csrf')
@exigir_perfil()
def api_csrf():
    return jsonify(csrf_token=session['csrf_token'])


@web.get('/api/maquinas')
@exigir_perfil()
def api_listar():
    return jsonify([calcular_indicadores(m) for m in database.listar_maquinas()])


@web.get('/api/maquinas/<int:maquina_id>')
@exigir_perfil()
def api_buscar(maquina_id):
    return jsonify(calcular_indicadores(obter_maquina(maquina_id)))


def dados_api():
    try:
        return ler_formulario(request.get_json())
    except ValueError as erro:
        abort(400, description=str(erro))


@web.post('/api/maquinas')
@exigir_perfil('admin', 'operador')
def api_criar():
    maquina_id = database.inserir_maquina(dados_api(), g.usuario['id'])
    resposta = jsonify(calcular_indicadores(obter_maquina(maquina_id)))
    resposta.status_code = 201
    resposta.headers['Location'] = url_for('web.api_buscar', maquina_id=maquina_id)
    return resposta


@web.put('/api/maquinas/<int:maquina_id>')
@exigir_perfil('admin', 'operador')
def api_atualizar(maquina_id):
    obter_maquina(maquina_id)
    try:
        database.atualizar_maquina(maquina_id, dados_api(), g.usuario['id'])
    except ValueError as erro:
        abort(409, description=str(erro))
    return jsonify(calcular_indicadores(obter_maquina(maquina_id)))


@web.delete('/api/maquinas/<int:maquina_id>')
@exigir_perfil('admin')
def api_excluir(maquina_id):
    obter_maquina(maquina_id)
    try:
        database.deletar_maquina(maquina_id, g.usuario['id'])
    except ValueError as erro:
        abort(409, description=str(erro))
    return '', 204


def ler_registro(form):
    tipo = form.get('tipo')
    descricao = form.get('descricao', '').strip()
    if tipo not in ('operacao', 'abastecimento', 'manutencao'):
        raise ValueError('Selecione um tipo de lançamento válido.')
    if not 1 <= len(descricao) <= 500:
        raise ValueError('Descreva o lançamento em até 500 caracteres.')
    dados = {'tipo': tipo, 'descricao': descricao}
    campos = ('horimetro_final',) if tipo == 'operacao' else ('litros', 'valor_total') if tipo == 'abastecimento' else ('valor_total',)
    for campo in campos:
        try:
            numero = float(form.get(campo, ''))
        except (ValueError, TypeError, OverflowError):
            raise ValueError('Preencha os valores numéricos do lançamento.') from None
        if not math.isfinite(numero) or not 0 <= numero <= 1_000_000_000:
            raise ValueError('Os valores devem estar entre 0 e 1 bilhão.')
        if campo in ('horimetro_final', 'litros') and numero <= 0:
            raise ValueError('Horímetro final e litros devem ser maiores que zero.')
        dados[campo] = numero
    return dados


@web.route('/maquinas/<int:maquina_id>/diario', methods=['GET', 'POST'])
@exigir_perfil()
def diario(maquina_id):
    maquina = obter_maquina(maquina_id)
    status = 200
    if request.method == 'POST':
        if g.usuario['perfil'] not in ('admin', 'operador'):
            abort(403)
        try:
            database.registrar_diario(maquina_id, g.usuario['id'], ler_registro(request.form))
        except ValueError as erro:
            flash(str(erro), 'erro')
            status = 400
        else:
            flash('Lançamento registrado e indicadores atualizados.', 'sucesso')
            return redirect(url_for('web.diario', maquina_id=maquina_id))
    registros = database.listar_registros(maquina_id)
    horas = sum(r['horimetro_final'] - r['horimetro_inicial'] for r in registros if r['tipo'] == 'operacao')
    gastos = sum(r['valor_total'] or 0 for r in registros)
    litros = sum(r['litros'] or 0 for r in registros)
    return render_template('diario.html', maquina=calcular_indicadores(maquina), registros=registros,
        horas=horas, gastos=gastos, litros=litros, custo_registrado=gastos / horas if horas else None,
        litros_por_hora_registrados=litros / horas if horas and litros else None,
        valores=request.form if request.method == 'POST' else {}), status


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        DATABASE=os.environ.get('AGROTRACK_DATABASE', database.DB_NOME),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('AGROTRACK_HTTPS') == '1',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_REFRESH_EACH_REQUEST=False, MAX_CONTENT_LENGTH=64 * 1024,
    )
    if config:
        app.config.update(config)
    if not app.config['SECRET_KEY']:
        if os.environ.get('AGROTRACK_ENV') == 'production':
            raise RuntimeError('Configure SECRET_KEY no ambiente de produção.')
        # Chave local persistente, fora do Git, sem credencial padrão no código.
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        chave_local = Path(app.instance_path) / 'secret_key'
        try:
            with chave_local.open('x', encoding='utf-8') as arquivo:
                arquivo.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config['SECRET_KEY'] = chave_local.read_text(encoding='utf-8').strip()
    hash_inexistente = generate_password_hash(secrets.token_hex(32))

    @app.before_request
    def carregar_sessao_e_proteger():
        g.usuario = database.buscar_usuario(usuario_id=session['usuario_id']) if 'usuario_id' in session else None
        g.hash_inexistente = hash_inexistente
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not isinstance(token, str) or not secrets.compare_digest(token, session['csrf_token']):
                abort(400, description='Formulário expirado ou token inválido. Recarregue a página e tente novamente.')

    @app.context_processor
    def contexto():
        return {'usuario': g.usuario, 'csrf_token': session.get('csrf_token', '')}

    @app.after_request
    def cabecalhos(resposta):
        resposta.headers['X-Content-Type-Options'] = 'nosniff'
        resposta.headers['X-Frame-Options'] = 'DENY'
        resposta.headers['Referrer-Policy'] = 'same-origin'
        if request.endpoint != 'static':
            resposta.headers['Cache-Control'] = 'no-store'
        return resposta

    for codigo in (400, 401, 403, 404, 405, 409, 413, 415):
        def tratar_erro(erro):
            if request.path.startswith('/api/'):
                return jsonify(erro=erro.description), erro.code
            return render_template('erro.html', codigo=erro.code, mensagem=erro.description), erro.code
        app.register_error_handler(codigo, tratar_erro)

    @app.cli.command('criar-usuario')
    @click.option('--nome', prompt=True)
    @click.option('--perfil', type=click.Choice(['admin', 'operador', 'leitor']), default='operador')
    @click.password_option(confirmation_prompt=True)
    def criar_usuario(nome, perfil, password):
        """Cria conta local; a senha é solicitada sem aparecer no terminal."""
        nome = nome.strip()
        if not 1 <= len(nome) <= 80 or len(password) < 12:
            raise click.ClickException('Use nome de 1 a 80 caracteres e senha de pelo menos 12 caracteres.')
        try:
            database.criar_usuario(nome, generate_password_hash(password), perfil)
        except sqlite3.IntegrityError:
            raise click.ClickException('Esse usuário já existe.') from None
        click.echo('Usuário criado.')

    @app.cli.command('dados-exemplo')
    def dados_exemplo():
        """Popula uma base vazia somente mediante comando explícito."""
        database.popular_dados_exemplo()
        click.echo('Carga de exemplo concluída (apenas se a base estava vazia).')

    app.register_blueprint(web)
    with app.app_context():
        database.criar_tabela()
    return app


app = create_app()

if __name__ == '__main__':
    app.run()
