import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash
from config import DB_CONFIG

def get_pg_conn():
    return psycopg2.connect(**DB_CONFIG)

def init_db_pg():
    conn = get_pg_conn()
    cur = conn.cursor()

    # Tabela de cursos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # Tabela de contratos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id SERIAL PRIMARY KEY,
            nome_aluno TEXT,
            curso TEXT,
            forma_pagamento TEXT,
            data_criacao TIMESTAMP,
            modelo_utilizado TEXT
        )
    ''')

    # Tabela de modelos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS modelos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT
        )
    ''')

    # Tabela de alunos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            cpf TEXT UNIQUE,
            email TEXT,
            tel_aluno TEXT,
            endereco TEXT,
            curso TEXT
        )
    ''')

    # Tabela de usuários
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # Cria admin padrão se não existir
    cur.execute("SELECT * FROM usuarios WHERE username = 'LeoNarciso'")
    if not cur.fetchone():
        senha_hash = generate_password_hash('Crfmg19309@2025')
        cur.execute("INSERT INTO usuarios (username, senha) VALUES (%s, %s)", ('LeoNarciso', senha_hash))

    conn.commit()
    conn.close()
