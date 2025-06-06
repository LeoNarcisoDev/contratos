from flask import Flask, render_template, request, redirect, send_file
from datetime import datetime
import pandas as pd
from unidecode import unidecode
import json
import shutil
import os
import psycopg2
from dotenv import load_dotenv

from config import DB_CONFIG, UPLOAD_FOLDER
from utils.pg import get_pg_conn
from utils.docx_handler import fill_contract

app = Flask(__name__)

@app.route('/')
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
def upload_alunos():
    mensagem = ''
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        if arquivo and arquivo.filename.endswith('.csv'):
            try:
                df = pd.read_csv(arquivo, encoding='utf-8', sep=',')
                df.columns = [col.strip().lower() for col in df.columns]
                alunos = []
                for _, row in df.iterrows():
                    aluno = {
                        'nome': unidecode(str(row.get('nome', ''))).strip(),
                        'cpf': str(row.get('cpf', '')).strip(),
                        'email': str(row.get('email', '')).strip(),
                        'tel_aluno': str((row.get('telefone') or row.get('telefones') or row.get('celular') or '')).split('/')[0].strip(),
                        'endereco': str(row.get('endereco', '')).strip(),
                        'curso': str(row.get('produto', '')).strip()
                    }
                    alunos.append(aluno)

                with open('data/alunos.json', 'w', encoding='utf-8') as f:
                    json.dump(alunos, f, ensure_ascii=False, indent=2)

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
def excluir_curso(curso_id):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM cursos WHERE id = %s', (curso_id,))
    conn.commit()
    conn.close()
    return redirect('/cursos')

if __name__ == '__main__':
    from utils.pg import init_db_pg
    init_db_pg()
    app.run(debug=True)
