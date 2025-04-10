from flask import Flask, render_template, request, send_file
from docx import Document
from datetime import datetime
import os

app = Flask(__name__)

def fill_contract(data):
    doc = Document(os.path.join(app.root_path, 'contrato_padrao.docx'))

    # Substituir em parágrafos
    for para in doc.paragraphs:
        for key, value in data.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in para.text:
                para.text = para.text.replace(placeholder, str(value))

    # Substituir em tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for key, value in data.items():
                        placeholder = f'{{{{{key}}}}}'
                        if placeholder in para.text:
                            para.text = para.text.replace(placeholder, str(value))

    # Salvar arquivo preenchido
    output_path = os.path.join(app.root_path, 'temp_filled_contract.docx')
    doc.save(output_path)
    return output_path

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit_contract', methods=['POST'])
def submit_contract():
    # Data atual no formato "Belo Horizonte, 09 de abril de 2025"
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

    # Coletar dados do formulário
    data = {
        'nome_aluno': request.form.get('nome_aluno', ''),
        'cpf_aluno': request.form.get('cpf_aluno', ''),
        'end_aluno': request.form.get('end_aluno', ''),
        'bairro_aluno': request.form.get('bairro_aluno', ''),
        'cep_aluno': request.form.get('cep_aluno', ''),
        'cidade_aluno': request.form.get('cidade_aluno', ''),
        'tel_aluno': request.form.get('tel_aluno', ''),
        'email_aluno': request.form.get('email_aluno', ''),
        'forma_de_pagamento': request.form.get('forma_de_pagamento', ''),
        'parcela_cartao': request.form.get('parcela_cartao', ''),
        'total_contrato': request.form.get('total_contrato', ''),
        'curso': request.form.get('curso', ''),
        'carga_horaria': request.form.get('carga_horaria', ''),
        'dia_inicio': request.form.get('dia_inicio', ''),
        'mes_inicio': request.form.get('mes_inicio', ''),
        'ano_inicio': request.form.get('ano_inicio', ''),
        'dia_termino': request.form.get('dia_termino', ''),
        'mes_termino': request.form.get('mes_termino', ''),
        'ano_termino': request.form.get('ano_termino', ''),
        'dia_semana': request.form.get('dia_semana', ''),
        'contratante': request.form.get('nome_aluno', ''),
        'data_contrato': data_contrato_formatada
    }

    # Preencher e salvar o contrato
    docx_path = fill_contract(data)
    return send_file(docx_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
