import sqlite3
from pathlib import Path
from datetime import datetime

# Onde o banco de dados fica guardado: dentro da pasta "dados"
PASTA_PROJETO = Path(__file__).parent
CAMINHO_BANCO = PASTA_PROJETO / "dados" / "artthy.db"

PERFIL_PADRAO = "padrao"


def conectar():
    """Abre a conexão com o banco de dados."""
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    """Cria as tabelas, caso ainda não existam."""
    conexao = conectar()
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS memorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,           -- foto, video, audio ou texto
            titulo TEXT NOT NULL,
            descricao TEXT DEFAULT '',    -- descrição manual
            transcricao TEXT DEFAULT '',  -- texto do áudio (opcional)
            caminho_arquivo TEXT DEFAULT '',
            criado_em TEXT NOT NULL
        )
    """)
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfil TEXT NOT NULL DEFAULT 'padrao',
            memoria_id INTEGER NOT NULL,
            sentimento TEXT DEFAULT '',
            contexto TEXT DEFAULT '',
            avaliacao TEXT NOT NULL,      -- gostei, nao_gostei ou irrelevante
            criado_em TEXT NOT NULL,
            FOREIGN KEY (memoria_id) REFERENCES memorias(id) ON DELETE CASCADE
        )
    """)
    conexao.commit()
    conexao.close()


# ---------- MEMÓRIAS ----------

def adicionar_memoria(tipo, titulo, descricao="", transcricao="", caminho_arquivo=""):
    """Salva uma nova lembrança e devolve o id dela."""
    conexao = conectar()
    cursor = conexao.execute(
        """INSERT INTO memorias (tipo, titulo, descricao, transcricao, caminho_arquivo, criado_em)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tipo, titulo, descricao, transcricao, caminho_arquivo,
         datetime.now().isoformat(timespec="seconds")),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id


def listar_memorias():
    """Devolve todas as lembranças, da mais nova para a mais antiga."""
    conexao = conectar()
    linhas = conexao.execute("SELECT * FROM memorias ORDER BY id DESC").fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def buscar_memoria(memoria_id):
    """Devolve uma lembrança pelo id (ou None se não existir)."""
    conexao = conectar()
    linha = conexao.execute("SELECT * FROM memorias WHERE id = ?", (memoria_id,)).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def atualizar_memoria(memoria_id, titulo, descricao, transcricao):
    """Edita título, descrição e transcrição de uma lembrança."""
    conexao = conectar()
    conexao.execute(
        "UPDATE memorias SET titulo = ?, descricao = ?, transcricao = ? WHERE id = ?",
        (titulo, descricao, transcricao, memoria_id),
    )
    conexao.commit()
    conexao.close()


def excluir_memoria(memoria_id):
    """Apaga a lembrança (e as avaliações ligadas a ela)."""
    conexao = conectar()
    conexao.execute("DELETE FROM memorias WHERE id = ?", (memoria_id,))
    conexao.commit()
    conexao.close()


# ---------- AVALIAÇÕES ----------

def registrar_avaliacao(memoria_id, avaliacao, sentimento="", contexto="", perfil=PERFIL_PADRAO):
    """Guarda um 'gostei', 'nao_gostei' ou 'irrelevante'."""
    if avaliacao not in ("gostei", "nao_gostei", "irrelevante"):
        raise ValueError("avaliacao deve ser: gostei, nao_gostei ou irrelevante")
    conexao = conectar()
    conexao.execute(
        """INSERT INTO avaliacoes (perfil, memoria_id, sentimento, contexto, avaliacao, criado_em)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (perfil, memoria_id, sentimento, contexto, avaliacao,
         datetime.now().isoformat(timespec="seconds")),
    )
    conexao.commit()
    conexao.close()


def listar_avaliacoes(perfil=PERFIL_PADRAO):
    """Devolve todo o histórico de avaliações de um perfil."""
    conexao = conectar()
    linhas = conexao.execute(
        "SELECT * FROM avaliacoes WHERE perfil = ? ORDER BY id", (perfil,)
    ).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


# Roda só quando você executa "python banco.py" diretamente
if __name__ == "__main__":
    criar_tabelas()
    print("Banco criado com sucesso!")
    print("Lembranças cadastradas:", len(listar_memorias()))
    print("Avaliações registradas:", len(listar_avaliacoes()))