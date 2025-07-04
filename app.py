from flask import Flask, render_template, request, redirect, send_file, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import pandas as pd
from unidecode import unidecode
import json
import shutil
import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from config import DB_CONFIG, UPLOAD_FOLDER
from utils.pg import get_pg_conn, init_db_pg
from utils.docx_handler import fill_contract

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-padrao")
load_dotenv()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, senha_hash):
        self.id = id
        self.username = username
        self.senha_hash = senha_hash

    @staticmethod
    def get_by_username(username):
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, username, senha_hash FROM usuarios WHERE username = %s", (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            return User(*row)
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, username, senha_hash FROM usuarios WHERE id = %s", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return User(*row)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        user = User.get_by_username(username)
        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            return redirect(url_for('form'))
        else:
            flash('Login inválido. Verifique o nome de usuário e a senha.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def form():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM cursos ORDER BY nome ASC")
    cursos = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT id, nome, descricao, categoria FROM modelos ORDER BY descricao")
    modelos = cur.fetchall()
    conn.close()

    if os.path.exists('data/alunos.json'):
        shutil.copyfile('data/alunos.json', 'static/alunos.json')
    return render_template('form.html', cursos=cursos, modelos=modelos)

@app.route('/submit_contract', methods=['POST'])
@login_required
def submit_contract():
    hoje = datetime.today()
    meses = {
        '01': 'janeiro', '02': 'fevereiro', '03': 'março', '04': 'abril',
        '05': 'maio', '06': 'junho', '07': 'julho', '08': 'agosto',
        '09': 'setembro', '10': 'outubro', '11': 'novembro', '12': 'dezembro'
    }
    dia = hoje.strftime('%d')
    mes = meses[hoje.strftime('%m')]
    ano = hoje.strftime('%Y')
    data_contrato_formatada = f'Belo Horizonte, {dia} de {mes} de {ano}'

    modelo = request.form.get('modelo', '')
    data = {key: request.form.get(key, '') for key in request.form}
    data['data_contrato'] = data_contrato_formatada
    data['contratante'] = data['nome_aluno']
    data['modelo'] = modelo

    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO contratos (nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado)
        VALUES (%s, %s, %s, %s, %s)
    ''', (
        data['nome_aluno'],
        data['curso'],
        data['forma_de_pagamento'],
        datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        data['modelo']
    ))
    conn.commit()
    conn.close()

    docx_path = fill_contract(data, modelo)
    return send_file(docx_path, as_attachment=True)

@app.route('/alunos_csv', methods=['GET', 'POST'])
@login_required
def upload_alunos():
    mensagem = ''
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename.endswith('.csv'):
            try:
                df = pd.read_csv(arquivo, encoding='utf-8', sep=',')

                # Normaliza os nomes das colunas
                df.columns = [col.strip().upper() for col in df.columns]

                alunos = []
                for _, row in df.iterrows():
                    nome = str(row.get('NOME', '')).strip()
                    cpf = str(row.get('CPF', '')).replace('.', '').replace('-', '').strip()
                    email = str(row.get('EMAIL', '')).strip()
                    telefone = str(row.get('TELEFONES', '')).split('//')[0].strip()
                    endereco = str(row.get('ENDERECO', '')).strip()
                    curso = str(row.get('PRODUTO', '')).strip()

                    if not nome:
                        continue  # pula registros sem nome

                    aluno = {
                        'nome': nome,
                        'cpf': cpf,
                        'email': email,
                        'tel_aluno': telefone,
                        'endereco': endereco,
                        'curso': f"CURSO: {curso}"  # opcional, para padronizar com sistema
                    }
                    alunos.append(aluno)

                # Salva JSON para autocomplete
                with open('data/alunos.json', 'w', encoding='utf-8') as f:
                    json.dump(alunos, f, ensure_ascii=False, indent=2)

                # Inserção no banco (opcional)
                conn = get_pg_conn()
                cur = conn.cursor()
                for aluno in alunos:
                    cur.execute('SELECT id FROM alunos WHERE cpf = %s', (aluno['cpf'],))
                    if not cur.fetchone():
                        cur.execute('''
                            INSERT INTO alunos (nome, cpf, email, tel_aluno, endereco, curso)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (aluno['nome'], aluno['cpf'], aluno['email'], aluno['tel_aluno'], aluno['endereco'], aluno['curso']))
                conn.commit()
                conn.close()

                mensagem = 'Alunos importados com sucesso!'
            except Exception as e:
                mensagem = f'Erro no processamento: {str(e)}'
        else:
            mensagem = 'Apenas arquivos CSV são aceitos.'
    return render_template('alunos_csv.html', mensagem=mensagem)

@app.route('/modelos', methods=['GET', 'POST'])
@login_required
def gerenciar_modelos():
    mensagem = ''
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')

        if arquivo and arquivo.filename.endswith('.docx'):
            caminho = os.path.join(UPLOAD_FOLDER, arquivo.filename)
            arquivo.save(caminho)

            conn = get_pg_conn()
            cur = conn.cursor()
            cur.execute('INSERT INTO modelos (nome, descricao, categoria) VALUES (%s, %s, %s)',
                        (arquivo.filename, descricao, categoria))
            conn.commit()
            conn.close()
            mensagem = 'Modelo enviado com sucesso!'
        else:
            mensagem = 'Envie um arquivo .docx válido.'

    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, nome, descricao, categoria FROM modelos ORDER BY descricao')
    modelos = cur.fetchall()
    conn.close()

    return render_template('modelos.html', modelos=modelos, mensagem=mensagem)

@app.route('/excluir_modelo/<int:modelo_id>')
@login_required
def excluir_modelo(modelo_id):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('SELECT nome FROM modelos WHERE id = %s', (modelo_id,))
    resultado = cur.fetchone()

    if resultado:
        nome_arquivo = resultado[0]
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        cur.execute('DELETE FROM modelos WHERE id = %s', (modelo_id,))
        conn.commit()

    conn.close()
    return redirect('/modelos')

@app.route('/cursos', methods=['GET', 'POST'])
@login_required
def gerenciar_cursos():
    mensagem = ''
    conn = get_pg_conn()
    cur = conn.cursor()

    if request.method == 'POST':
        novo = request.form.get('novo_curso', '').strip()
        if novo:
            try:
                cur.execute('INSERT INTO cursos (nome) VALUES (%s)', (novo,))
                conn.commit()
                mensagem = 'Curso cadastrado com sucesso!'
            except psycopg2.IntegrityError:
                mensagem = 'Este curso já está cadastrado.'

    cur.execute('SELECT id, nome FROM cursos ORDER BY nome')
    cursos = cur.fetchall()
    conn.close()
    return render_template('cursos.html', cursos=cursos, mensagem=mensagem)

@app.route('/excluir_curso/<int:curso_id>')
@login_required
def excluir_curso(curso_id):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM cursos WHERE id = %s', (curso_id,))
    conn.commit()
    conn.close()
    return redirect('/cursos')

if __name__ == '__main__':
    init_db_pg()
    app.run(debug=True)
