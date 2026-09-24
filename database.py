import sqlite3

DB_NOME = "agrotrack.db"


def get_conexao():
    conexao = sqlite3.connect(DB_NOME)
    conexao.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conexao


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
    conexao.commit()
    conexao.close()


def popular_dados_exemplo():
    """Insere 2 máquinas de exemplo se o banco estiver vazio (só pra
    a tela não começar em branco na primeira vez que o professor abrir)."""
    conexao = get_conexao()
    total = conexao.execute("SELECT COUNT(*) FROM maquinas").fetchone()[0]
    if total == 0:
        conexao.executemany("""
            INSERT INTO maquinas
            (nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
             custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Trator MF 4275", "Trator", 1180, 12.5, 6.10, 1000, 250),
            ("Colheitadeira Case 5088", "Colheitadeira", 940, 28.0, 6.10, 700, 200),
        ])
        conexao.commit()
    conexao.close()


def listar_maquinas():
    conexao = get_conexao()
    linhas = conexao.execute("SELECT * FROM maquinas ORDER BY id").fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def buscar_maquina(maquina_id):
    conexao = get_conexao()
    linha = conexao.execute("SELECT * FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def inserir_maquina(dados):
    conexao = get_conexao()
    conexao.execute("""
        INSERT INTO maquinas
        (nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
         custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        dados["nome"], dados["tipo"], dados["horimetro_atual"],
        dados["consumo_diesel_litros_hora"], dados["custo_diesel_litro"],
        dados["ultima_manutencao_horimetro"], dados["intervalo_manutencao_horas"],
    ))
    conexao.commit()
    conexao.close()


def atualizar_maquina(maquina_id, dados):
    conexao = get_conexao()
    conexao.execute("""
        UPDATE maquinas SET
            nome = ?, tipo = ?, horimetro_atual = ?,
            consumo_diesel_litros_hora = ?, custo_diesel_litro = ?,
            ultima_manutencao_horimetro = ?, intervalo_manutencao_horas = ?
        WHERE id = ?
    """, (
        dados["nome"], dados["tipo"], dados["horimetro_atual"],
        dados["consumo_diesel_litros_hora"], dados["custo_diesel_litro"],
        dados["ultima_manutencao_horimetro"], dados["intervalo_manutencao_horas"],
        maquina_id,
    ))
    conexao.commit()
    conexao.close()


def deletar_maquina(maquina_id):
    conexao = get_conexao()
    conexao.execute("DELETE FROM maquinas WHERE id = ?", (maquina_id,))
    conexao.commit()
    conexao.close()
