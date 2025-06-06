# utils/db.py (versão SQLite - opcional para testes locais)

import sqlite3
from config import DB_PATH
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_aluno TEXT,
        curso TEXT,
        forma_pagamento TEXT,
        data_criacao TEXT,
        modelo_utilizado TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS modelos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        categoria TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT,
        email TEXT,
        tel_aluno TEXT,
        endereco TEXT,
        curso TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )''')

    cur.execute("SELECT * FROM usuarios WHERE username = 'LeoNarciso'")
    if not cur.fetchone():
        senha_hash = generate_password_hash('Crfmg19309@2025')
        cur.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ('LeoNarciso', senha_hash))

    conn.commit()
    conn.close()
