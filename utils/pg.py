# utils/pg.py
import psycopg2
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

    # Tabela de usuários com username
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
