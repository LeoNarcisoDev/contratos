from flask import Flask, render_template, request, redirect, send_file
from docx import Document
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'modelos')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_PATH = os.path.join(app.root_path, 'data', 'contratos.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')
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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_modelo(nome, descricao, categoria):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO modelos (nome, descricao, categoria) VALUES (?, ?, ?)", (nome, descricao, categoria))
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

def salvar_contrato(data):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO contratos (nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['nome_aluno'],
        data['curso'],
        data['forma_de_pagamento'],
        datetime.now().strftime('%Y-%m-%d %H:%M'),
        data['modelo']
    ))
    conn.commit()
    conn.close()

def fill_contract(data, modelo_nome):
    caminho_modelo = os.path.join(app.config['UPLOAD_FOLDER'], modelo_nome)
    doc = Document(caminho_modelo)

    for para in doc.paragraphs:
        for key, value in data.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in para.text:
                para.text = para.text.replace(placeholder, str(value))

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for key, value in data.items():
                        placeholder = f'{{{{{key}}}}}'
                        if placeholder in para.text:
                            para.text = para.text.replace(placeholder, str(value))

    output_path = os.path.join(app.root_path, 'temp_filled_contract.docx')
    doc.save(output_path)
    return output_path

@app.route('/')
def form():
    cursos = get_cursos()
    modelos = get_modelos()
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

    salvar_contrato(data)
    docx_path = fill_contract(data, modelo)
    return send_file(docx_path, as_attachment=True)

@app.route('/modelos', methods=['GET', 'POST'])
def upload_modelos():
    mensagem = ''
    if request.method == 'POST':
        arquivo = request.files.get('arquivo')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria')

        if arquivo and arquivo.filename.endswith('.docx'):
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.filename)
            arquivo.save(caminho)
            salvar_modelo(arquivo.filename, descricao, categoria)
            mensagem = 'Modelo enviado com sucesso!'
        else:
            mensagem = 'Apenas arquivos .docx são permitidos.'

    modelos = get_modelos()
    return render_template('modelos.html', modelos=modelos, mensagem=mensagem)

@app.route('/excluir_modelo/<int:id>')
def excluir_modelo(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT nome FROM modelos WHERE id = ?", (id,))
    modelo = cur.fetchone()
    if modelo:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], modelo[0])
        if os.path.exists(caminho):
            os.remove(caminho)
        cur.execute("DELETE FROM modelos WHERE id = ?", (id,))
        conn.commit()
    conn.close()
    return redirect('/modelos')

@app.route('/cursos', methods=['GET', 'POST'])
def cadastrar_curso():
    msg = ''
    if request.method == 'POST':
        nome = request.form.get('nome')
        if nome:
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("INSERT INTO cursos (nome) VALUES (?)", (nome,))
                conn.commit()
                msg = 'Curso cadastrado com sucesso!'
            except sqlite3.IntegrityError:
                msg = 'Este curso já está cadastrado.'
            finally:
                conn.close()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
    lista_cursos = cur.fetchall()
    conn.close()

    return render_template('cursos.html', mensagem=msg, cursos=lista_cursos)

@app.route('/excluir_curso/<int:id>')
def excluir_curso(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM cursos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/cursos')

@app.route('/historico')
def historico():
    filtro = request.args.get('filtro', '').strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if filtro:
        like = f'%{filtro}%'
        cur.execute("""
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            WHERE nome_aluno LIKE ? OR curso LIKE ? OR modelo_utilizado LIKE ?
            ORDER BY id DESC
        """, (like, like, like))
    else:
        cur.execute("""
            SELECT nome_aluno, curso, forma_pagamento, data_criacao, modelo_utilizado
            FROM contratos
            ORDER BY id DESC
        """)

    registros = cur.fetchall()
    conn.close()
    return render_template('historico.html', contratos=registros)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
