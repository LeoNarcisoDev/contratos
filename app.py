from flask import Flask, render_template, request, redirect, send_file, session, url_for
from datetime import datetime
import sqlite3
import os
import pandas as pd
from unidecode import unidecode
import json
import shutil

from config import UPLOAD_FOLDER, DB_PATH
from utils.db import init_db, get_modelos, get_cursos
from utils.docx_handler import fill_contract

app = Flask(__name__)
app.secret_key = 'segredo_super_seguro'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def form():
    if 'usuario' not in session:
        return redirect('/login')

    cursos = get_cursos()
    modelos = get_modelos()
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

    # Salvar contrato no banco
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO contratos (nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado)
        VALUES (?, ?, ?, ?, ?)
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
    if 'usuario' not in session:
        return redirect('/login')

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
                        'tel_aluno': str(
                            (row.get('telefone') or row.get('telefones') or row.get('celular') or '')
                        ).split('/')[0].strip(),
                        'endereco': str(row.get('endereco', '')).strip(),
                        'curso': str(row.get('produto', '')).strip()
                    }
                    alunos.append(aluno)

                with open('data/alunos.json', 'w', encoding='utf-8') as f:
                    json.dump(alunos, f, ensure_ascii=False, indent=2)

                # Salvar no banco sem duplicar por CPF
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                for aluno in alunos:
                    cur.execute('SELECT id FROM alunos WHERE cpf = ?', (aluno['cpf'],))
                    if not cur.fetchone():
                        cur.execute('''
                            INSERT INTO alunos (nome, cpf, email, tel_aluno, endereco, curso)
                            VALUES (?, ?, ?, ?, ?, ?)
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
    if 'usuario' not in session:
        return redirect('/login')

    mensagem = ''
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')

        if arquivo and arquivo.filename.endswith('.docx'):
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(caminho)

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute('INSERT INTO modelos (nome, descricao, categoria) VALUES (?, ?, ?)',
                        (arquivo.filename, descricao, categoria))
            conn.commit()
            conn.close()
            mensagem = 'Modelo enviado com sucesso!'
        else:
            mensagem = 'Envie um arquivo .docx válido.'

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, nome, descricao, categoria FROM modelos ORDER BY descricao')
    modelos = cur.fetchall()
    conn.close()

    return render_template('modelos.html', modelos=modelos, mensagem=mensagem)

@app.route('/excluir_modelo/<int:modelo_id>')
def excluir_modelo(modelo_id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT nome FROM modelos WHERE id = ?', (modelo_id,))
    resultado = cur.fetchone()

    if resultado:
        nome_arquivo = resultado[0]
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        cur.execute('DELETE FROM modelos WHERE id = ?', (modelo_id,))
        conn.commit()

    conn.close()
    return redirect('/modelos')

@app.route('/cursos', methods=['GET', 'POST'])
def gerenciar_cursos():
    if 'usuario' not in session:
        return redirect('/login')

    mensagem = ''
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == 'POST':
        novo = request.form.get('novo_curso', '').strip()
        if novo:
            try:
                cur.execute('INSERT INTO cursos (nome) VALUES (?)', (novo,))
                conn.commit()
                mensagem = 'Curso cadastrado com sucesso!'
            except sqlite3.IntegrityError:
                mensagem = 'Este curso já está cadastrado.'

    cur.execute('SELECT id, nome FROM cursos ORDER BY nome')
    cursos = cur.fetchall()
    conn.close()
    return render_template('cursos.html', cursos=cursos, mensagem=mensagem)

@app.route('/excluir_curso/<int:curso_id>')
def excluir_curso(curso_id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM cursos WHERE id = ?', (curso_id,))
    conn.commit()
    conn.close()
    return redirect('/cursos')

@app.route('/alunos')
def listar_alunos():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT nome, cpf, email, tel_aluno, endereco, curso FROM alunos ORDER BY nome')
    alunos = cur.fetchall()
    conn.close()
    return render_template('alunos.html', alunos=alunos)

@app.route('/historico')
def historico():
    if 'usuario' not in session:
        return redirect('/login')

    filtro = request.args.get('filtro', '').lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if filtro:
        cur.execute('''
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            WHERE lower(nome_aluno) LIKE ? OR lower(curso) LIKE ? OR lower(modelo_utilizado) LIKE ?
            ORDER BY data_criacao DESC
        ''', (f'%{filtro}%', f'%{filtro}%', f'%{filtro}%'))
    else:
        cur.execute('''
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            ORDER BY data_criacao DESC
        ''')
    contratos = cur.fetchall()
    conn.close()
    return render_template('historico.html', contratos=contratos)

@app.route('/exportar_historico')
def exportar_historico():
    if 'usuario' not in session:
        return redirect('/login')

    filtro = request.args.get('filtro', '').lower().strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if filtro:
        cur.execute('''
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            WHERE lower(nome_aluno) LIKE ? OR lower(curso) LIKE ? OR lower(modelo_utilizado) LIKE ?
            ORDER BY data_criacao DESC
        ''', (f'%{filtro}%', f'%{filtro}%', f'%{filtro}%'))
    else:
        cur.execute('''
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            ORDER BY data_criacao DESC
        ''')
    contratos = cur.fetchall()
    conn.close()

    df = pd.DataFrame(contratos, columns=["Aluno", "Curso", "Forma de Pagamento", "Data", "Modelo"])
    caminho = os.path.join("temp", "historico_exportado.csv")
    df.to_csv(caminho, index=False, encoding="utf-8-sig")

    return send_file(caminho, as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = ''
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, senha))
        usuario = cur.fetchone()
        conn.close()

        if usuario:
            session['usuario'] = username
            return redirect('/')
        else:
            erro = 'Usuário ou senha inválidos.'

    return render_template('login.html', erro=erro)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')

if __name__ == '__main__':
    from utils.db import init_db
    init_db()
    app.run(host='0.0.0.0', port=10000)
