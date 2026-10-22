import sqlite3
from pathlib import Path
from contextlib import closing

from flask import current_app, has_app_context, g, has_request_context

DB_NOME = str(Path(__file__).resolve().with_name("agrotrack.db"))


def get_conexao():
    caminho = current_app.config["DATABASE"] if has_app_context() else DB_NOME
    conexao = sqlite3.connect(caminho, timeout=10)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conexao


def fazenda_atual():
    """A fazenda autenticada é a única fronteira de leitura e escrita."""
    if not has_request_context() or not getattr(g, 'usuario', None):
        raise PermissionError('É necessária uma fazenda autenticada.')
    return g.usuario['fazenda_id']


def criar_tabela():
    """Cria a tabela de máquinas caso ela ainda não exista."""
    conexao = get_conexao()
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            horimetro_atual REAL NOT NULL,
            consumo_diesel_litros_hora REAL NOT NULL,
            custo_diesel_litro REAL NOT NULL,
            ultima_manutencao_horimetro REAL NOT NULL,
            intervalo_manutencao_horas REAL NOT NULL
        )
    """)
    conexao.executescript("""
        CREATE TABLE IF NOT EXISTS fazendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK (perfil IN ('admin', 'operador', 'leitor'))
        );
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            acao TEXT NOT NULL,
            maquina_id INTEGER,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id INTEGER NOT NULL REFERENCES maquinas(id) ON DELETE RESTRICT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            tipo TEXT NOT NULL CHECK (tipo IN ('operacao', 'abastecimento', 'manutencao')),
            descricao TEXT NOT NULL,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            horimetro_inicial REAL,
            horimetro_final REAL,
            litros REAL,
            valor_total REAL
        );
        CREATE INDEX IF NOT EXISTS idx_registros_maquina ON registros(maquina_id, id);
    """)
    # Atualiza bancos SQLite existentes sem apagar máquinas, usuários ou diário.
    for tabela in ('usuarios', 'maquinas', 'auditoria'):
        colunas = {linha['name'] for linha in conexao.execute(f'PRAGMA table_info({tabela})')}
        if 'fazenda_id' not in colunas:
            conexao.execute(f'ALTER TABLE {tabela} ADD COLUMN fazenda_id INTEGER REFERENCES fazendas(id)')
    conexao.execute("INSERT OR IGNORE INTO fazendas (id, nome) VALUES (1, 'Fazenda inicial')")
    for tabela in ('usuarios', 'maquinas', 'auditoria'):
        conexao.execute(f'UPDATE {tabela} SET fazenda_id = 1 WHERE fazenda_id IS NULL')
    conexao.execute('CREATE INDEX IF NOT EXISTS idx_maquinas_fazenda ON maquinas(fazenda_id, id)')
    conexao.execute('CREATE INDEX IF NOT EXISTS idx_auditoria_fazenda ON auditoria(fazenda_id, id)')
    conexao.commit()
    conexao.close()


def popular_dados_exemplo():
    """Insere 2 máquinas de exemplo se o banco estiver vazio (só pra
    a tela não começar em branco na primeira vez que o professor abrir)."""
    conexao = get_conexao()
    total = conexao.execute("SELECT COUNT(*) FROM maquinas WHERE fazenda_id = 1").fetchone()[0]
    if total == 0:
        conexao.executemany("""
            INSERT INTO maquinas
            (nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
             custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas, fazenda_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, [
            ("Trator MF 4275", "Trator", 1180, 12.5, 6.10, 1000, 250),
            ("Colheitadeira Case 5088", "Colheitadeira", 940, 28.0, 6.10, 700, 200),
        ])
        conexao.commit()
    conexao.close()


def listar_maquinas():
    conexao = get_conexao()
    linhas = conexao.execute("SELECT * FROM maquinas WHERE fazenda_id = ? ORDER BY id", (fazenda_atual(),)).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def buscar_maquina(maquina_id):
    conexao = get_conexao()
    linha = conexao.execute("SELECT * FROM maquinas WHERE id = ? AND fazenda_id = ?", (maquina_id, fazenda_atual())).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def inserir_maquina(dados, usuario_id=None):
    conexao = get_conexao()
    cursor = conexao.execute("""
        INSERT INTO maquinas
        (nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
         custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas, fazenda_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dados["nome"], dados["tipo"], dados["horimetro_atual"],
        dados["consumo_diesel_litros_hora"], dados["custo_diesel_litro"],
        dados["ultima_manutencao_horimetro"], dados["intervalo_manutencao_horas"], fazenda_atual(),
    ))
    maquina_id = cursor.lastrowid
    conexao.execute("INSERT INTO auditoria (usuario_id, acao, maquina_id, fazenda_id) VALUES (?, ?, ?, ?)",
                    (usuario_id, "maquina_criada", maquina_id, fazenda_atual()))
    conexao.commit()
    conexao.close()
    return maquina_id


def atualizar_maquina(maquina_id, dados, usuario_id=None):
    conexao = get_conexao()
    conexao.execute('BEGIN IMMEDIATE')
    atual = conexao.execute('SELECT * FROM maquinas WHERE id = ? AND fazenda_id = ?', (maquina_id, fazenda_atual())).fetchone()
    if atual is None:
        conexao.rollback(); conexao.close(); return
    possui_diario = conexao.execute('SELECT 1 FROM registros WHERE maquina_id = ? LIMIT 1', (maquina_id,)).fetchone()
    if atual and possui_diario and any(dados[campo] != atual[campo] for campo in
            ('horimetro_atual', 'ultima_manutencao_horimetro')):
        conexao.rollback()
        conexao.close()
        raise ValueError('Esta máquina possui diário. Atualize o horímetro e a manutenção por lançamentos no diário.')
    cursor = conexao.execute("""
        UPDATE maquinas SET
            nome = ?, tipo = ?, horimetro_atual = ?,
            consumo_diesel_litros_hora = ?, custo_diesel_litro = ?,
            ultima_manutencao_horimetro = ?, intervalo_manutencao_horas = ?
        WHERE id = ? AND fazenda_id = ?
    """, (
        dados["nome"], dados["tipo"], dados["horimetro_atual"],
        dados["consumo_diesel_litros_hora"], dados["custo_diesel_litro"],
        dados["ultima_manutencao_horimetro"], dados["intervalo_manutencao_horas"],
        maquina_id, fazenda_atual(),
    ))
    if cursor.rowcount:
        conexao.execute("INSERT INTO auditoria (usuario_id, acao, maquina_id, fazenda_id) VALUES (?, ?, ?, ?)",
                        (usuario_id, "maquina_atualizada", maquina_id, fazenda_atual()))
    conexao.commit()
    conexao.close()


def deletar_maquina(maquina_id, usuario_id=None):
    conexao = get_conexao()
    try:
        cursor = conexao.execute("DELETE FROM maquinas WHERE id = ? AND fazenda_id = ?", (maquina_id, fazenda_atual()))
    except sqlite3.IntegrityError:
        conexao.close()
        raise ValueError('Esta máquina possui histórico e não pode ser excluída. Preserve os registros do diário.') from None
    if cursor.rowcount:
        conexao.execute("INSERT INTO auditoria (usuario_id, acao, maquina_id, fazenda_id) VALUES (?, ?, ?, ?)",
                        (usuario_id, "maquina_excluida", maquina_id, fazenda_atual()))
    conexao.commit()
    conexao.close()


def buscar_usuario(nome=None, usuario_id=None):
    with closing(get_conexao()) as conexao:
        if usuario_id is not None:
            linha = conexao.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        else:
            linha = conexao.execute("SELECT * FROM usuarios WHERE nome = ?", (nome,)).fetchone()
        return dict(linha) if linha else None


def criar_usuario(nome, senha_hash, perfil, fazenda_id=1):
    with closing(get_conexao()) as conexao, conexao:
        conexao.execute("INSERT INTO usuarios (nome, senha_hash, perfil, fazenda_id) VALUES (?, ?, ?, ?)",
                        (nome, senha_hash, perfil, fazenda_id))


def cadastrar_fazenda(nome_fazenda, nome_usuario, senha_hash):
    with closing(get_conexao()) as conexao, conexao:
        cursor = conexao.execute('INSERT INTO fazendas (nome) VALUES (?)', (nome_fazenda,))
        conexao.execute("INSERT INTO usuarios (nome, senha_hash, perfil, fazenda_id) VALUES (?, ?, 'admin', ?)",
                        (nome_usuario, senha_hash, cursor.lastrowid))


def listar_equipe():
    with closing(get_conexao()) as conexao:
        return [dict(linha) for linha in conexao.execute(
            'SELECT id, nome, perfil FROM usuarios WHERE fazenda_id = ? ORDER BY id', (fazenda_atual(),))]


def adicionar_equipe(nome, senha_hash, perfil):
    if perfil not in ('operador', 'leitor'):
        raise ValueError('Perfil inválido.')
    criar_usuario(nome, senha_hash, perfil, fazenda_atual())


def registrar_evento(usuario_id, acao):
    # Nunca registrar senhas, cookies ou tokens de sessão.
    with closing(get_conexao()) as conexao, conexao:
        if usuario_id is not None:
            linha = conexao.execute('SELECT fazenda_id FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
            fazenda_id = linha['fazenda_id'] if linha else None
        else:
            fazenda_id = None
        conexao.execute("INSERT INTO auditoria (usuario_id, acao, fazenda_id) VALUES (?, ?, ?)", (usuario_id, acao, fazenda_id))


def listar_eventos():
    with closing(get_conexao()) as conexao:
        return [dict(linha) for linha in conexao.execute("""
            SELECT a.id, u.nome AS usuario, a.acao, a.maquina_id, a.criado_em
            FROM auditoria a LEFT JOIN usuarios u ON u.id = a.usuario_id
            WHERE a.fazenda_id = ? ORDER BY a.id DESC LIMIT 200
        """, (fazenda_atual(),))]


def listar_registros(maquina_id):
    with closing(get_conexao()) as conexao:
        return [dict(linha) for linha in conexao.execute("""
            SELECT r.*, u.nome AS usuario FROM registros r
            JOIN usuarios u ON u.id = r.usuario_id
            WHERE r.maquina_id = ? AND EXISTS (SELECT 1 FROM maquinas m WHERE m.id = r.maquina_id AND m.fazenda_id = ?)
            ORDER BY r.id DESC
        """, (maquina_id, fazenda_atual()))]


def registrar_diario(maquina_id, usuario_id, dados):
    """Atualiza diário e máquina na mesma transação, sem perder lançamentos concorrentes."""
    with closing(get_conexao()) as conexao, conexao:
        conexao.execute('BEGIN IMMEDIATE')
        maquina = conexao.execute('SELECT * FROM maquinas WHERE id = ? AND fazenda_id = ?', (maquina_id, fazenda_atual())).fetchone()
        if maquina is None:
            raise ValueError('Máquina não encontrada.')
        inicial = maquina['horimetro_atual']
        final = dados.get('horimetro_final')
        if dados['tipo'] == 'operacao':
            if final <= inicial:
                raise ValueError('O horímetro final deve ser maior que o atual.')
            conexao.execute('UPDATE maquinas SET horimetro_atual = ? WHERE id = ?', (final, maquina_id))
        elif dados['tipo'] == 'manutencao':
            conexao.execute('UPDATE maquinas SET ultima_manutencao_horimetro = ? WHERE id = ?',
                            (inicial, maquina_id))
        conexao.execute("""
            INSERT INTO registros (maquina_id, usuario_id, tipo, descricao,
                horimetro_inicial, horimetro_final, litros, valor_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (maquina_id, usuario_id, dados['tipo'], dados['descricao'],
              inicial if dados['tipo'] in ('operacao', 'manutencao') else None,
              final, dados.get('litros'), dados.get('valor_total')))
        conexao.execute('INSERT INTO auditoria (usuario_id, acao, maquina_id, fazenda_id) VALUES (?, ?, ?, ?)',
                        (usuario_id, 'registro_' + dados['tipo'], maquina_id, fazenda_atual()))
