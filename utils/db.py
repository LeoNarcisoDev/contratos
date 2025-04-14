import sqlite3
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    # Cursos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # Contratos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_aluno TEXT,
            curso TEXT,
            forma_pagamento TEXT,
            data_criacao TEXT,
            modelo_utilizado TEXT
        )
    ''')

    # Modelos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT
        )
    ''')

    # Alunos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT,
            email TEXT,
            tel_aluno TEXT,
            endereco TEXT,
            curso TEXT
        )
    ''')

    # Usuários (login)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # Admin padrão (usuario: admin / senha: admin)
    cur.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ('admin', 'admin'))

    conn.commit()
    conn.close()


def get_modelos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, nome, descricao, categoria FROM modelos ORDER BY descricao")
    modelos = cur.fetchall()
    conn.close()
    return modelos

def get_cursos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nome FROM cursos ORDER BY nome ASC")
    cursos = [row[0] for row in cur.fetchall()]
    conn.close()
    return cursos
