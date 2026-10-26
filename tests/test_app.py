"""Regressões com bancos temporários; nunca usa agrotrack.db do projeto."""
import os
import sqlite3
from contextlib import closing
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

IMPORT_DB = tempfile.TemporaryDirectory()
os.environ['AGROTRACK_DATABASE'] = str(Path(IMPORT_DB.name) / 'import.db')
os.environ['SECRET_KEY'] = 'chave-exclusiva-para-testes'
from app import create_app, calcular_indicadores
import database
from werkzeug.security import generate_password_hash


class AgroTrackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash_senha = generate_password_hash('SenhaDeTeste123!')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'teste.db')
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'teste', 'DATABASE': self.path})
        self.client = self.app.test_client()
        with self.app.app_context():
            for perfil in ('admin', 'operador', 'leitor'):
                database.criar_usuario(perfil, self.hash_senha, perfil)
        self.dados = dict(nome='Trator de teste', modelo='MF 4275', marca='Massey Ferguson', ano=2020,
            tipo='Trator', horimetro_atual=1250,
            consumo_diesel_litros_hora=12.5, custo_diesel_litro=6.1,
            ultima_manutencao_horimetro=1000, intervalo_manutencao_horas=250)

    def token(self):
        with self.client.session_transaction() as sessao:
            return sessao['csrf_token']

    def entrar(self, perfil='admin'):
        self.client.get('/login')
        r = self.client.post('/login', data={'nome': perfil, 'senha': 'SenhaDeTeste123!', 'csrf_token': self.token()})
        self.assertEqual(r.status_code, 302)
        self.client.get('/')

    def gravar(self, method, url, dados=None):
        return self.client.open(url, method=method, json=dados, headers={'X-CSRF-Token': self.token()})

    def test_acesso_anonimo_e_csrf(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.assertEqual(self.client.get('/api/maquinas').status_code, 401)
        self.assertEqual(self.client.post('/login', data={'nome': 'admin'}).status_code, 400)
        self.entrar()
        self.assertEqual(self.client.post('/api/maquinas', json=self.dados).status_code, 400)

    def test_cadastro_separa_fazendas_em_web_api_diario_e_auditoria(self):
        self.entrar()
        resposta = self.gravar('POST', '/api/maquinas', self.dados)
        maquina_a = resposta.json['id']
        self.client.post('/logout', data={'csrf_token': self.token()})
        self.client.get('/cadastro')
        resposta = self.client.post('/cadastro', data={
            'fazenda': 'Sítio B', 'nome': 'adminb', 'senha': 'SenhaForteParaB123!',
            'confirmacao': 'SenhaForteParaB123!', 'csrf_token': self.token()})
        self.assertEqual(resposta.status_code, 302)
        self.client.post('/login', data={'nome': 'adminb', 'senha': 'SenhaForteParaB123!', 'csrf_token': self.token()})
        self.assertEqual(self.client.get('/api/maquinas').json, [])
        self.assertEqual(self.client.get(f'/api/maquinas/{maquina_a}').status_code, 404)
        self.assertEqual(self.client.get(f'/maquinas/{maquina_a}/diario').status_code, 404)
        self.assertNotIn('Trator de teste', self.client.get('/relatorio').text)
        self.assertNotIn('maquina_criada', self.client.get('/auditoria').text)
        self.assertEqual(self.gravar('PUT', f'/api/maquinas/{maquina_a}', self.dados).status_code, 404)
        self.assertEqual(self.gravar('DELETE', f'/api/maquinas/{maquina_a}').status_code, 404)

    def test_crud_http_calculos_e_auditoria(self):
        self.entrar()
        r = self.gravar('POST', '/api/maquinas', self.dados)
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.json['modelo'], r.json['marca'], r.json['ano']), ('MF 4275', 'Massey Ferguson', 2020))
        self.assertEqual(r.json['custo_hora'], 76.25)
        self.assertTrue(r.json['alerta_manutencao'])
        url = r.headers['Location']
        self.assertEqual(self.client.get(url).json['nome'], 'Trator de teste')
        self.dados['horimetro_atual'] = 1200
        r = self.gravar('PUT', url, self.dados)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['horas_restantes'], 50)
        self.assertFalse(r.json['alerta_manutencao'])
        self.assertEqual(self.gravar('DELETE', url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get('/api/maquinas').json, [])
        with self.app.app_context():
            conexao = database.get_conexao()
            acoes = [e['acao'] for e in conexao.execute('SELECT acao FROM auditoria WHERE fazenda_id = 1')]
            conexao.close()
        for acao in ('login', 'maquina_criada', 'maquina_atualizada', 'maquina_excluida'):
            self.assertIn(acao, acoes)

    def test_migracao_preserva_maquina_antiga_e_preenche_modelo(self):
        legado = str(Path(self.temp.name) / 'legado.db')
        with closing(sqlite3.connect(legado)) as conexao, conexao:
            conexao.execute('''CREATE TABLE maquinas (
                id INTEGER PRIMARY KEY, nome TEXT NOT NULL, tipo TEXT NOT NULL,
                horimetro_atual REAL NOT NULL, consumo_diesel_litros_hora REAL NOT NULL,
                custo_diesel_litro REAL NOT NULL, ultima_manutencao_horimetro REAL NOT NULL,
                intervalo_manutencao_horas REAL NOT NULL)''')
            conexao.execute('''INSERT INTO maquinas VALUES
                (1, 'Trator antigo', 'Trator', 100, 10, 6, 0, 250)''')
        create_app({'TESTING': True, 'SECRET_KEY': 'teste', 'DATABASE': legado})
        with closing(sqlite3.connect(legado)) as conexao:
            self.assertEqual(conexao.execute('SELECT nome, modelo, fazenda_id FROM maquinas').fetchone(),
                             ('Trator antigo', 'Trator antigo', 1))

    def test_aviso_de_manutencao_proxima_antes_do_vencimento(self):
        self.entrar()
        self.dados['horimetro_atual'] = 1229
        url = self.gravar('POST', '/api/maquinas', self.dados).headers['Location']
        self.assertFalse(self.client.get(url).json['manutencao_proxima'])
        self.dados['horimetro_atual'] = 1230
        self.gravar('PUT', url, self.dados)
        self.assertTrue(self.client.get(url).json['manutencao_proxima'])
        self.assertIn('Próxima · 20.0 h restantes', self.client.get('/relatorio').text)
        self.dados['horimetro_atual'] = 1250
        self.gravar('PUT', url, self.dados)
        maquina = self.client.get(url).json
        self.assertTrue(maquina['alerta_manutencao'])
        self.assertFalse(maquina['manutencao_proxima'])

    def test_dados_invalidos_nao_gravam(self):
        self.entrar()
        casos = [('nome', '   '), ('modelo', '   '), ('ano', 1800), ('ano', 'inválido'),
                 ('tipo', 'Invalido'), ('custo_diesel_litro', -1),
                 ('horimetro_atual', 'nan'), ('horimetro_atual', 'inf'),
                 ('horimetro_atual', True), ('intervalo_manutencao_horas', 0),
                 ('ultima_manutencao_horimetro', 2000)]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                r = self.gravar('POST', '/api/maquinas', {**self.dados, campo: valor})
                self.assertEqual(r.status_code, 400)
        self.assertEqual(self.gravar('POST', '/api/maquinas', []).status_code, 400)
        self.assertEqual(self.client.get('/api/maquinas').json, [])

    def test_permissoes_servidor(self):
        self.entrar('operador')
        r = self.gravar('POST', '/api/maquinas', self.dados)
        self.assertEqual(r.status_code, 201)
        url = r.headers['Location']
        self.assertEqual(self.gravar('DELETE', url).status_code, 403)
        self.assertEqual(self.client.get('/auditoria').status_code, 403)
        self.entrar('leitor')
        self.assertEqual(self.client.get('/relatorio').status_code, 200)
        self.assertEqual(self.client.get('/cadastrar').status_code, 403)
        self.assertEqual(self.gravar('POST', '/api/maquinas', self.dados).status_code, 403)
        self.assertEqual(self.gravar('PUT', url, self.dados).status_code, 403)
        self.assertEqual(self.gravar('DELETE', url).status_code, 403)

    def test_formularios_erros_e_mensagens(self):
        self.entrar()
        data = {**self.dados, 'csrf_token': self.token()}
        self.assertEqual(self.client.post('/cadastrar', data=data).status_code, 302)
        for rota in ('/', '/relatorio', '/editar/1', '/auditoria', '/cadastrar'):
            self.assertEqual(self.client.get(rota).status_code, 200)
        data['horimetro_atual'] = 'texto'
        r = self.client.post('/editar/1', data=data)
        self.assertEqual(r.status_code, 400)
        self.assertIn('Trator de teste', r.text)
        self.assertIn('informe um número', r.text)
        r = self.client.post('/cadastrar', data=data)
        self.assertEqual(r.status_code, 400)
        self.assertIn('Trator de teste', r.text)
        self.assertEqual(self.client.get('/editar/999').status_code, 404)
        self.assertEqual(self.client.post('/deletar/999', data={'csrf_token': self.token()}).status_code, 404)

    def test_exclusao_total_nao_recria_exemplos(self):
        self.entrar()
        r = self.gravar('POST', '/api/maquinas', self.dados)
        self.gravar('DELETE', r.headers['Location'])
        outro = create_app({'TESTING': True, 'SECRET_KEY': 'teste', 'DATABASE': self.path})
        with outro.app_context():
            conexao = database.get_conexao()
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM maquinas WHERE fazenda_id = 1').fetchone()[0], 0)
            conexao.close()

    def test_logout_e_sessao_expirada(self):
        self.entrar()
        with self.client.session_transaction() as sessao:
            sessao['_permanent'] = True
        self.assertEqual(self.client.post('/logout', data={'csrf_token': self.token()}).status_code, 302)
        self.assertEqual(self.client.get('/api/maquinas').status_code, 401)
        self.entrar()
        cookie = self.client.get_cookie('session').value
        # Assinatura inválida não pode manter o acesso.
        self.client.set_cookie('session', cookie + 'adulterado')
        self.assertEqual(self.client.get('/api/maquinas').status_code, 401)

    def test_senha_errada_e_token_rotacionado(self):
        self.client.get('/login')
        antigo = self.token()
        self.assertEqual(self.client.post('/login', data={'nome': 'admin', 'senha': 'errada', 'csrf_token': antigo}).status_code, 401)
        self.entrar()
        self.assertNotEqual(antigo, self.token())
        self.assertEqual(self.client.post('/logout', data={'csrf_token': antigo}).status_code, 400)

    def test_html_escapa_conteudo_e_sql_nao_executa(self):
        self.entrar()
        dados = {**self.dados, 'nome': '<script>alert(1)</script>'}
        self.gravar('POST', '/api/maquinas', dados)
        pagina = self.client.get('/relatorio').text
        self.assertNotIn('<script>alert(1)</script>', pagina)
        self.assertIn('&lt;script&gt;', pagina)
        self.gravar('POST', '/api/maquinas', {**self.dados, 'nome': "'; DROP TABLE maquinas; --"})
        self.assertEqual(len(self.client.get('/api/maquinas').json), 2)

    def test_criar_usuario_cli(self):
        runner = self.app.test_cli_runner()
        r = runner.invoke(args=['criar-usuario', '--nome', 'novo', '--perfil', 'leitor'], input='SenhaDeTeste456!\nSenhaDeTeste456!\n')
        self.assertEqual(r.exit_code, 0, r.output)
        with self.app.app_context():
            usuario = database.buscar_usuario(nome='novo')
            self.assertEqual(usuario['perfil'], 'leitor')
            self.assertNotEqual(usuario['senha_hash'], 'SenhaDeTeste456!')

    def test_diario_atualiza_horas_gastos_e_manutencao(self):
        self.entrar('operador')
        r = self.gravar('POST', '/api/maquinas', self.dados)
        maquina_id = r.json['id']
        url = f'/maquinas/{maquina_id}/diario'
        self.assertEqual(self.client.get(url).status_code, 200)
        def lancar(**dados):
            return self.client.post(url, data={**dados, 'csrf_token': self.token()})
        self.assertEqual(lancar(tipo='operacao', descricao='Preparo do solo', horimetro_final=1260).status_code, 302)
        self.assertEqual(lancar(tipo='abastecimento', descricao='Diesel', litros=50, valor_total=300).status_code, 302)
        self.assertEqual(lancar(tipo='manutencao', descricao='Troca de óleo', valor_total=200).status_code, 302)
        maquina = self.client.get(f'/api/maquinas/{maquina_id}').json
        self.assertEqual(maquina['horimetro_atual'], 1260)
        self.assertEqual(maquina['ultima_manutencao_horimetro'], 1260)
        self.assertFalse(maquina['alerta_manutencao'])
        pagina = self.client.get(url).text
        self.assertIn('R$ 500.00', pagina)
        self.assertIn('R$ 50.00/h', pagina)
        self.assertIn('10.0 h', pagina)
        self.assertIn('10.0 h trabalhadas', pagina)
        self.assertEqual(lancar(tipo='operacao', descricao='Inválido', horimetro_final=1250).status_code, 400)
        self.assertEqual(lancar(tipo='abastecimento', descricao='Inválido', litros='nan', valor_total=0).status_code, 400)
        self.assertEqual(lancar(tipo='manutencao', descricao='Inválido', valor_total=-1).status_code, 400)
        with self.app.app_context():
            conexao = database.get_conexao()
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM registros WHERE maquina_id = ?', (maquina_id,)).fetchone()[0], 3)
            conexao.close()
        self.entrar('leitor')
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(lancar(tipo='manutencao', descricao='Proibido', valor_total=0).status_code, 403)

    def test_historico_impede_exclusao_e_edicao_inconsistente(self):
        self.entrar()
        r = self.gravar('POST', '/api/maquinas', self.dados)
        maquina_id = r.json['id']
        self.client.post(f'/maquinas/{maquina_id}/diario', data={
            'tipo': 'operacao', 'descricao': 'Campo', 'horimetro_final': 1300, 'csrf_token': self.token()})
        self.assertEqual(self.gravar('DELETE', r.headers['Location']).status_code, 409)
        self.assertEqual(self.client.post(f'/deletar/{maquina_id}', data={'csrf_token': self.token()}).status_code, 409)
        self.assertEqual(self.gravar('PUT', r.headers['Location'], self.dados).status_code, 409)
        self.dados['horimetro_atual'] = 1300
        self.dados['nome'] = 'Nome atualizado'
        self.assertEqual(self.gravar('PUT', r.headers['Location'], self.dados).status_code, 200)

    def test_sessao_expira_apos_30_minutos(self):
        from unittest.mock import patch
        self.entrar()
        with self.client.session_transaction() as sessao:
            conteudo = dict(sessao)
        serializer = self.app.session_interface.get_signing_serializer(self.app)
        passado = int(datetime.now(timezone.utc).timestamp()) - 1801
        with patch('itsdangerous.timed.TimestampSigner.get_timestamp', return_value=passado):
            cookie = serializer.dumps(conteudo)
        self.client.set_cookie('session', cookie)
        self.assertEqual(self.client.get('/api/maquinas').status_code, 401)


if __name__ == '__main__':
    unittest.main()
