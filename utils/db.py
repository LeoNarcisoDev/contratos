# utils/db.py
import sqlite3
from config import DB_PATH
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tabela de cursos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # Tabela de contratos
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

    # Tabela de modelos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT
        )
    ''')

    # Tabela de alunos
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

    # Tabela de usuarios
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # Cria admin padrao se nao existir
    cur.execute("SELECT * FROM usuarios WHERE username = 'LeoNarciso'")
    if not cur.fetchone():
        senha_hash = generate_password_hash('Crfmg19309@2025')
        cur.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ('LeoNarciso', senha_hash))

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
