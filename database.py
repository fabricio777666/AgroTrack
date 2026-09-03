import sqlite3
from contextlib import contextmanager

DB_NOME = "agrotrack.db"


@contextmanager
def conexao_db():
    """Gerenciador de contexto que abre, comita e fecha a conexão automaticamente."""
    conexao = sqlite3.connect(DB_NOME)
    conexao.row_factory = sqlite3.Row
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_tabela():
    """Cria a tabela de máquinas e habilita WAL mode para maior performance."""
    with conexao_db() as conexao:
        conexao.execute("PRAGMA journal_mode=WAL;")  # Otimiza leitura/escrita concorrente
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


def popular_dados_exemplo():
    """Insere máquinas de exemplo caso o banco esteja vazio."""
    with conexao_db() as conexao:
        total = conexao.execute("SELECT COUNT(*) FROM maquinas").fetchone()[0]
        if total == 0:
            conexao.executemany("""
                INSERT INTO maquinas (
                    nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
                    custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("Trator MF 4275", "Trator", 1180, 12.5, 6.10, 1000, 250),
                ("Colheitadeira Case 5088", "Colheitadeira", 940, 28.0, 6.10, 700, 200),
            ])


def listar_maquinas():
    with conexao_db() as conexao:
        linhas = conexao.execute("SELECT * FROM maquinas ORDER BY id").fetchall()
        return [dict(linha) for linha in linhas]


def buscar_maquina(maquina_id):
    with conexao_db() as conexao:
        linha = conexao.execute("SELECT * FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
        return dict(linha) if linha else None


def inserir_maquina(dados):
    with conexao_db() as conexao:
        conexao.execute("""
            INSERT INTO maquinas (
                nome, tipo, horimetro_atual, consumo_diesel_litros_hora,
                custo_diesel_litro, ultima_manutencao_horimetro, intervalo_manutencao_horas
            ) VALUES (:nome, :tipo, :horimetro_atual, :consumo_diesel_litros_hora,
                      :custo_diesel_litro, :ultima_manutencao_horimetro, :intervalo_manutencao_horas)
        """, dados)  # Aceita o dicionário de dados diretamente


def atualizar_maquina(maquina_id, dados):
    dados_com_id = {**dados, "id": maquina_id}
    with conexao_db() as conexao:
        conexao.execute("""
            UPDATE maquinas SET
                nome = :nome,
                tipo = :tipo,
                horimetro_atual = :horimetro_atual,
                consumo_diesel_litros_hora = :consumo_diesel_litros_hora,
                custo_diesel_litro = :custo_diesel_litro,
                ultima_manutencao_horimetro = :ultima_manutencao_horimetro,
                intervalo_manutencao_horas = :intervalo_manutencao_horas
            WHERE id = :id
        """, dados_com_id)


def deletar_maquina(maquina_id):
    with conexao_db() as conexao:
        conexao.execute("DELETE FROM maquinas WHERE id = ?", (maquina_id,))