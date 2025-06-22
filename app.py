# Flask com autenticação e controle de acesso
from flask import request, render_template
from flask import Flask, render_template, request, redirect, send_file, flash, session, url_for, render_template_string, jsonify
import sqlite3
import csv
import io
from datetime import datetime
from collections import defaultdict
from flask import render_template
import pandas as pd
from flask import Flask, render_template_string
from collections import Counter
import json


app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura'
DATABASE = 'base.db'


COLUNAS = [
    'Nome', 'Telefone', 'Email', 'Base', 'Base_disponibilizada',
    'Consultor', 'Status_aluno', 'Primeiro_contato', 'Segundo_contato', 'Finalizado'
]

CONSULTOR_LIST = [
    "Andreza Pinheiro de Lima", "Beatriz Alves Santos", "Dominik Ferreira Josue Silva",
    "Fernanda Souza Ferreira", "Pedro Henrique Gonzaga de Souza", "Raissa da Silva Bueno",
    "Igor Delmondes", "Vanessa Aparecida da Silva de Faria", "Erica Ravene Andrade Almeida",
    "Rafaela Lacerda Alves", "Ana Luisa Fonseca de Campos de Oliveira", "Andre Luiz Reis Rezende Filho",
    "Diogecson Soares Bispo dos Santos", "Evelyn Rainha dos Santos", "Isabela de araujo evangelista",
    "Vanessa Alves", "Juliana Pereira de Moraes Santos", "Lidya Leonice Silva Gonçalves",
    "Raffaela Alves da Silva", "BOT", "Emilly de Oliveira Zanelato"
]


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabela_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def popular_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Admin
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                   ("admin", "123", "admin"))

    # Consultores
    for nome in CONSULTOR_LIST:
        cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha, tipo) VALUES (?, ?, ?)",
                       (nome, "123", "consultor"))

    conn.commit()
    conn.close()

# ROTA DE LOGIN


@app.route('/login', methods=['GET', 'POST'])
def login():
    usuarios = sorted(CONSULTOR_LIST + ["admin"])  # Lista fixa

    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha)).fetchone()
        conn.close()

        if user:
            session['usuario'] = usuario
            session['tipo'] = user['tipo']
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')

    return render_template('login.html', usuarios=usuarios)


# ROTA PRINCIPAL (index.html)
@app.route('/', methods=['GET'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    pagina = request.args.get('pagina', 1, type=int)
    itens_por_pagina = 10
    offset = (pagina - 1) * itens_por_pagina

    filtros = {col: request.args.get(
        col.lower(), '').strip() for col in COLUNAS}

    query_base = "FROM contatos WHERE 1=1"
    params = []
    for col in COLUNAS:
        val = filtros[col]
        if val:
            query_base += f" AND {col} LIKE ?"
            params.append(f"%{val}%")

    if session.get('tipo') == 'consultor':
        query_base += " AND Consultor = ?"
        params.append(session.get('usuario'))

    cursor.execute(f"SELECT COUNT(*) {query_base}", params)
    total_contatos = cursor.fetchone()[0]

    query = f"SELECT * {query_base} LIMIT ? OFFSET ?"
    params_pag = params + [itens_por_pagina, offset]
    cursor.execute(query, params_pag)
    contatos = cursor.fetchall()

    # Telefones, emails, nomes filtrados
    query_telefones = f"{query_base} AND Telefone IS NOT NULL AND Telefone != ''"
    cursor.execute(f"SELECT Telefone {query_telefones}", params)
    telefones_filtrados = [row[0] for row in cursor.fetchall()]

    query_emails = f"{query_base} AND Email IS NOT NULL AND Email != ''"
    cursor.execute(f"SELECT Email {query_emails}", params)
    emails_filtrados = [row[0] for row in cursor.fetchall()]

    query_nomes = f"{query_base} AND Nome IS NOT NULL AND Nome != ''"
    cursor.execute(f"SELECT Nome {query_nomes}", params)
    nomes_filtrados = [row[0] for row in cursor.fetchall()]

    # Valores distintos por coluna
    valores_distintos = {}
    for col in COLUNAS:
        if col == "Primeiro_contato" and session.get('tipo') == 'consultor':
            cursor.execute(f"""
                SELECT DISTINCT {col} FROM contatos 
                WHERE {col} IS NOT NULL AND {col} != '' AND Consultor = ?
            """, (session.get('usuario'),))
        else:
            cursor.execute(f"""
                SELECT DISTINCT {col} FROM contatos 
                WHERE {col} IS NOT NULL AND {col} != ''
            """)
        rows = cursor.fetchall()
        valores_distintos[col] = [r[0] for r in rows if r[0] is not None]

    cursor.execute(
        "SELECT DISTINCT Base FROM contatos WHERE Base IS NOT NULL AND Base != ''")
    bases_distintas = [row[0] for row in cursor.fetchall()]

    consultores_distintos = sorted(set(CONSULTOR_LIST + [
        row[0] for row in cursor.execute("SELECT DISTINCT Consultor FROM contatos WHERE Consultor IS NOT NULL AND Consultor != ''")
    ]))

    todosDados = {
        "consultores": {nome: {} for nome in consultores_distintos}
    }

    total_paginas = (total_contatos + itens_por_pagina - 1) // itens_por_pagina

    return render_template(
        'index.html',
        contatos=contatos,
        filtros=filtros,
        colunas=COLUNAS,
        consultors=sorted(CONSULTOR_LIST),
        pagina=pagina,
        total_paginas=total_paginas,
        valores_distintos=valores_distintos,
        bases_distintas=bases_distintas,
        telefones_filtrados=telefones_filtrados,
        tipo_usuario=session.get('tipo', ''),
        emails_filtrados=emails_filtrados,
        nomes_filtrados=nomes_filtrados,
        todosDados=todosDados
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


@app.context_processor
def inject_user():
    return dict(tipo_usuario=session.get('tipo', ''), usuario_logado=session.get('usuario', ''))


@app.route('/alterar_massa', methods=['POST'])
def alterar_massa():
    base_filtro = request.form.get('base_filtro', '').strip()
    valor_filtro = request.form.get('valor_filtro', '').strip()
    coluna = request.form.get('coluna', '').strip()
    quantidade = request.form.get('quantidade', type=int)
    consultor_novo = request.form.get('consultor_novo', '').strip()

    if not base_filtro or not valor_filtro or not coluna or not quantidade or not consultor_novo:
        flash('Por favor, preencha todos os campos corretamente.', 'danger')
        return redirect('/')

    if coluna not in COLUNAS:
        flash('Coluna para alteração inválida.', 'danger')
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()

    sql_ids = f"SELECT id FROM contatos WHERE Base = ? AND {coluna} = ? LIMIT ?"
    cursor.execute(sql_ids, (base_filtro, valor_filtro, quantidade))
    ids = [row[0] for row in cursor.fetchall()]

    if not ids:
        flash('Nenhum registro encontrado com os filtros selecionados.', 'warning')
        conn.close()
        return redirect('/')

    placeholders = ','.join('?' for _ in ids)
    hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql_update = f"""
        UPDATE contatos
        SET Consultor = ?, Primeiro_contato = ?
        WHERE id IN ({placeholders})
    """

    try:
        cursor.execute(sql_update, (consultor_novo, hoje, *ids))
        conn.commit()
        flash(f'{len(ids)} registros atualizados com o novo consultor "{consultor_novo}" e primeiro contato marcado como {hoje}.', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar registros: {e}', 'danger')
    finally:
        conn.close()

    return redirect('/')


@app.route('/importar', methods=['POST'])
def importar():
    if 'arquivo_csv' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect('/')

    arquivo = request.files['arquivo_csv']
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect('/')

    try:
        conteudo = arquivo.stream.read().decode('utf-8')

        stream = io.StringIO(conteudo)
        leitor = csv.DictReader(stream)

        cabeçalhos_csv = leitor.fieldnames
        if not cabeçalhos_csv:
            flash('Arquivo CSV vazio ou inválido.', 'danger')
            return redirect('/')

        faltantes = [col for col in COLUNAS if col not in cabeçalhos_csv]
        if faltantes:
            flash(
                f'Colunas obrigatórias não encontradas no CSV: {", ".join(faltantes)}', 'danger')
            return redirect('/')

        conn = get_db_connection()
        cursor = conn.cursor()

        linha_num = 1
        for linha in leitor:
            vals = tuple(linha.get(c, '') for c in COLUNAS)
            placeholders = ','.join('?' for _ in COLUNAS)
            cursor.execute(
                f"INSERT INTO contatos ({', '.join(COLUNAS)}) VALUES ({placeholders})", vals)
            linha_num += 1

        conn.commit()
        flash(
            f'Importação realizada com sucesso! {linha_num - 1} registros inseridos.', 'success')
    except Exception as e:
        flash(f'Erro na importação na linha {linha_num}: {str(e)}', 'danger')
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    return redirect('/')


@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    cursor = conn.cursor()

    filtros = {col: request.args.get(
        col.lower(), '').strip() for col in COLUNAS}

    query = "SELECT * FROM contatos WHERE 1=1"
    params = []
    for col in COLUNAS:
        val = filtros[col]
        if val:
            query += f" AND {col} LIKE ?"
            params.append(f"%{val}%")

    cursor.execute(query, params)
    contatos = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(COLUNAS)
    for c in contatos:
        writer.writerow([c[col] for col in COLUNAS])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        download_name='contatos_export.csv',
        as_attachment=True
    )


def limpar_tabela_contatos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contatos")
    conn.commit()
    conn.close()


@app.route('/limpar_testes')
def limpar_testes():
    if session.get('tipo') != 'admin':
        flash("Acesso negado. Esta função é exclusiva para administradores.", "danger")
        return redirect("/")

    limpar_tabela_contatos()
    return "Testes removidos!"


@app.route("/excluir_base", methods=["POST"])
def excluir_base():
    if session.get('tipo') != 'admin':
        flash("Acesso negado. Esta função é exclusiva para administradores.", "danger")
        return redirect("/")

    base_excluir = request.form.get("base_excluir", "").strip()
    if not base_excluir:
        flash("Nenhuma base selecionada para exclusão.", "danger")
        return redirect("/")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM contatos WHERE Base = ?", (base_excluir,))
        conn.commit()
        flash(
            f"Todos os contatos da base '{base_excluir}' foram excluídos com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir a base: {e}", "danger")
    finally:
        conn.close()

    return redirect("/")


@app.route('/alterar_status_massa', methods=['POST'])
def alterar_status_massa():
    tipo_usuario = session.get('tipo')

    # Campos de atualização
    status_novo = request.form.get('status_novo')
    primeiro_novo = request.form.get('primeiro_contato_novo')
    segundo_novo = request.form.get('segundo_contato_novo')
    finalizado_novo = request.form.get('finalizado_novo')
    novo_consultor = request.form.get('consultor_novo')

    # Filtros aplicados
    filtros = {}
    for col in COLUNAS:
        valor = request.form.get(f'filtro_{col}', '').strip()
        if valor:
            filtros[col] = valor

    # ⚠️ Proteção contra alteração em massa por consultores
    if tipo_usuario != 'admin' and not filtros:
        flash("Você precisa aplicar ao menos um filtro para realizar essa alteração.", "danger")
        return redirect('/')

    # ⚠️ Nenhum campo de atualização foi preenchido
    if not any([status_novo, primeiro_novo, segundo_novo, finalizado_novo, novo_consultor]):
        flash("Nenhum campo de atualização foi preenchido.", "warning")
        return redirect('/')

    # Construir UPDATE dinâmico
    updates = []
    params_update = []

    if status_novo:
        updates.append("Status_aluno = ?")
        params_update.append(status_novo)
    if primeiro_novo:
        updates.append("Primeiro_contato = ?")
        params_update.append(primeiro_novo)
    if segundo_novo:
        updates.append("Segundo_contato = ?")
        params_update.append(segundo_novo)
    if finalizado_novo:
        updates.append("Finalizado = ?")
        params_update.append(finalizado_novo)
    if novo_consultor:
        updates.append("Consultor = ?")
        params_update.append(novo_consultor)

    # WHERE dinâmico com igualdade
    where_clauses = []
    params_where = []

    for col, val in filtros.items():
        where_clauses.append(f"{col} = ?")
        params_where.append(val)

    # Montar SQL completo
    sql = f"""
        UPDATE contatos
        SET {', '.join(updates)}
        WHERE {' AND '.join(where_clauses) if where_clauses else '1=1'}
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params_update + params_where)
        conn.commit()
        flash(f"{cursor.rowcount} contatos atualizados com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao atualizar contatos: {e}", "danger")
    finally:
        conn.close()

    return redirect('/')


@app.route('/resetar-base', methods=['POST'])
def resetar_base():
    if session.get('tipo') != 'admin':
        flash("Acesso negado. Essa função é só para administradores.", "danger")
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contatos")
    conn.commit()
    conn.close()

    flash("🚨 A base de contatos foi resetada com sucesso!", "warning")
    return redirect('/dashboard-completo')


@app.route('/dashboard')
def dashboard():
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Totais gerais
    cursor.execute("SELECT COUNT(*) FROM contatos")
    total_geral = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM contatos WHERE Primeiro_contato IS NOT NULL AND Primeiro_contato != ''")
    primeiro_contato = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM contatos WHERE Segundo_contato IS NOT NULL AND Segundo_contato != ''")
    segundo_contato = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM contatos WHERE Finalizado IS NOT NULL AND Finalizado != ''")
    finalizados = cursor.fetchone()[0]

    # Contagem de matriculados com ou sem filtro de data
    # Converta as strings do filtro HTML (yyyy-mm-dd) para datetime com hora zero
    # Filtros de data
    if data_inicio and data_fim:
        # Converte as strings do input date (yyyy-mm-dd) em datetime com hora mínima e máxima
        dt_inicio = datetime.strptime(data_inicio, '%Y-%d-%m')
        dt_fim = datetime.strptime(
            data_fim, '%Y-%d-%m') + timedelta(days=1) - timedelta(seconds=1)

        # Certifique-se que a coluna está convertida corretamente (você já fez isso antes)
        df = df[df['Primeiro_contato'].between(dt_inicio, dt_fim)]

    else:
        cursor.execute(
            "SELECT COUNT(*) FROM contatos WHERE Status_aluno = 'Matriculados'")
        total_matriculados = cursor.fetchone()[0]

    # Contatos de hoje
    cursor.execute("""
        SELECT COUNT(*) FROM contatos
        WHERE datetime(Primeiro_contato) >= datetime('now', 'start of day', 'localtime')
          AND datetime(Primeiro_contato) < datetime('now', 'start of day', '+1 day', 'localtime')
    """)
    contatos_hoje = cursor.fetchone()[0]

    # Telefones únicos
    cursor.execute("""
        SELECT COUNT(DISTINCT Telefone) FROM contatos
        WHERE Telefone IS NOT NULL AND Telefone != ''
    """)
    total_telefones = cursor.fetchone()[0]

    # Contagem por status
    status_labels = [
        "Em Negociação", "Já é Aluno", "Localização",
        "Preço", "Visualizou e Não Respondeu", "Dados Incorreto", "Matriculado"
    ]
    status_contagem = {label: 0 for label in status_labels}
    cursor.execute(
        "SELECT Status_aluno, COUNT(*) as total FROM contatos GROUP BY Status_aluno")
    for row in cursor.fetchall():
        status = row["Status_aluno"].strip()
        if status in status_contagem:
            status_contagem[status] = row["total"]

    # Bases únicas
    cursor.execute(
        "SELECT DISTINCT Base FROM contatos WHERE Base IS NOT NULL AND Base != ''")
    bases_unicas = [row["Base"] for row in cursor.fetchall()]

    # Consultores e ranking
    cursor.execute(
        "SELECT DISTINCT Consultor FROM contatos WHERE Consultor IS NOT NULL AND Consultor != ''")
    consultores = [row["Consultor"] for row in cursor.fetchall()]

    ranking_consultores = []
    for consultor in consultores:
        cursor.execute(
            "SELECT COUNT(*) FROM contatos WHERE Consultor = ?", (consultor,))
        total_consultor = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM contatos WHERE Consultor = ? AND Base = 'Volte'", (consultor,))
        volte = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM contatos WHERE Consultor = ? AND Status_aluno = 'Em Negociação'", (consultor,))
        negociacao = cursor.fetchone()[0]

        bases_dict = defaultdict(int)
        for base in bases_unicas:
            cursor.execute(
                "SELECT COUNT(*) FROM contatos WHERE Consultor = ? AND Base = ?", (consultor, base))
            bases_dict[base] = cursor.fetchone()[0]

        ranking_consultores.append({
            "consultor": consultor,
            "total": total_consultor,
            "volte": volte,
            "negociacao": negociacao,
            "bases": dict(bases_dict)
        })

    # Placeholder para futura lógica de atingimento
    atingimento_bases = []  # Lista vazia por enquanto

    conn.close()

    return render_template(
        'dashboard.html',
        total=total_geral,
        primeiro_contato=primeiro_contato,
        segundo_contato=segundo_contato,
        finalizados=finalizados,
        total_matriculados=total_matriculados,
        contatos_hoje=contatos_hoje,
        total_telefones=total_telefones,
        status_contagem=status_contagem,
        bases_unicas=bases_unicas,
        ranking_consultores=ranking_consultores,
        atingimento_bases=atingimento_bases,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


@app.route('/dashboard-relatorio', methods=['GET'])
def dashboard_relatorio():
    # Parâmetros do filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    consultor = request.args.get('consultor')
    page = int(request.args.get('page', 1))
    per_page = 50
    status_aluno = request.args.get('status_aluno')
    consultor_click = request.args.get('consultor_click')

    # Carrega os dados do banco
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM contatos", conn)
    conn.close()

    # Converte colunas de data
    df['Primeiro_contato'] = pd.to_datetime(
        df['Primeiro_contato'], errors='coerce')
    df['Segundo_contato'] = pd.to_datetime(
        df['Segundo_contato'], errors='coerce')

    # Filtro por intervalo de datas (input tipo date retorna yyyy-mm-dd)
    if data_inicio and data_fim:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        dt_fim = datetime.strptime(
            data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        df = df[df['Primeiro_contato'].between(dt_inicio, dt_fim)]

    # Filtros adicionais
    if consultor:
        df = df[df['Consultor'].str.contains(consultor, case=False, na=False)]
    if status_aluno:
        df = df[df['Status_aluno'] == status_aluno]
    if consultor_click:
        df = df[df['Consultor'] == consultor_click]

    # Paginação
    total_registros = len(df)
    total_paginas = (total_registros + per_page - 1) // per_page
    dados_pagina = df.iloc[(page - 1) * per_page: page * per_page].copy()

    # Formatação das datas para exibição no template
    dados_pagina['Primeiro_contato'] = dados_pagina['Primeiro_contato'].dt.strftime(
        '%d/%m/%Y').fillna('-')
    dados_pagina['Segundo_contato'] = dados_pagina['Segundo_contato'].dt.strftime(
        '%d/%m/%Y').fillna('-')
    dados_pagina = dados_pagina.to_dict(orient='records')

    # Dados para os gráficos
    status_opcoes = [
        "Em Negociação", "Já é Aluno", "Localização", "Preço",
        "Matriculado", "Visualizou e Não Respondeu", "Dados Incorreto", "Retirar da Base"
    ]
    contagem_status = df['Status_aluno'].value_counts().to_dict()
    grafico_status = {status: contagem_status.get(
        status, 0) for status in status_opcoes}
    grafico_consultor = df['Consultor'].value_counts().to_dict()

    # Renderização final
    return render_template(
        'relatorio.html',
        dados=dados_pagina,
        grafico_status=grafico_status,
        grafico_consultor=grafico_consultor,
        page=page,
        total_paginas=total_paginas,
        data_inicio=data_inicio,
        data_fim=data_fim,
        consultor=consultor,
        status_aluno=status_aluno,
        consultor_click=consultor_click
    )


@app.route("/dashboard-completo", endpoint='dashboard_completo')
def interativo():
    conn = sqlite3.connect("base.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Nome, Telefone, Email, Base, Base_disponibilizada,
               Consultor, Status_aluno, Primeiro_contato, Segundo_contato, Finalizado
        FROM contatos
    """)
    rows = cursor.fetchall()
    conn.close()

    def parse_data(d):
        if not d:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(d.strip(), fmt)
            except ValueError:
                continue
        return None

    def normaliza_status(valor):
        valor = (valor or "Base Disponível").strip().lower()
        if valor == "já é aluno":
            return "Já é Aluno"
        elif valor == "em negociação":
            return "Em Negociação"
        elif valor == "base disponível":
            return "Base Disponível"
        elif valor == "matriculado":
            return "Matriculado"
        elif valor == "finalizado":
            return "Finalizado"
        else:
            return valor.title()

    consultores = {}
    for r in rows:
        consultor = r[5] or "Sem nome"
        consultores.setdefault(consultor, []).append(r)

    dados = {
        "totais": {
            "indicadores": {
                "Total Telefones": len(rows),
                "Total Contatados": sum(1 for r in rows if r[7] and r[7].strip()),
                "Total Não Contatados": sum(1 for r in rows if not r[7] or not r[7].strip()),
                "Finalizados": sum(1 for r in rows if normaliza_status(r[6]) not in ["", "Matriculado", "Em Negociação"]),
                "Em Negociação": sum(1 for r in rows if normaliza_status(r[6]) == "Em Negociação"),
                "Matriculados": sum(1 for r in rows if normaliza_status(r[6]) == "Matriculado"),
                "Já é Aluno": sum(1 for r in rows if normaliza_status(r[6]) == "Já é Aluno"),
                "Contatados Hoje": sum(
                    1 for r in rows
                    if (dt := parse_data(r[7])) and dt.date() == datetime.today().date()
                )
            },
            "negociacoes": {},
            "matriculados": {},
            "status_aluno": {},
            "contatos": []
        },
        "consultores": {}
    }

    for consultor, registros in consultores.items():
        bloc = {
            "indicadores": {
                "Total Telefones": len(registros),
                "Total Contatados": 0,
                "Total Não Contatados": 0,
                "Finalizados": 0,
                "Em Negociação": 0,
                "Matriculados": 0,
                "Contatados Hoje": 0
            },
            "negociacoes": {},
            "matriculados": {},
            "status_aluno": {},
            "contatos": []
        }

        for r in registros:
            contato_dt = parse_data(r[7])
            status = normaliza_status(r[6])

            contato_formatado = {
                "Nome": r[0],
                "Telefone": r[1],
                "Email": r[2],
                "Base": r[3],
                "Base_disponibilizada": r[4],
                "Consultor": r[5],
                "Status_aluno": status,
                "Primeiro_contato": r[7],
                "Segundo_contato": r[8],
                "Finalizado": r[9],
                "Data": contato_dt.strftime("%Y-%m-%d") if contato_dt else "",
                "Data": contato_dt.strftime("%d/%m/%Y") if contato_dt else ""

            }

            if r[7] and r[7].strip():
                bloc["indicadores"]["Total Contatados"] += 1
                if contato_dt and contato_dt.date() == datetime.today().date():
                    bloc["indicadores"]["Contatados Hoje"] += 1
            else:
                bloc["indicadores"]["Total Não Contatados"] += 1

            if status == "Finalizado":
                bloc["indicadores"]["Finalizados"] += 1
            if status == "Em Negociação":
                bloc["indicadores"]["Em Negociação"] += 1
                mes = contato_dt.strftime(
                    "%m/%Y") if contato_dt else "Desconhecido"
                bloc["negociacoes"][mes] = bloc["negociacoes"].get(mes, 0) + 1
            if status == "Matriculado":
                bloc["indicadores"]["Matriculados"] += 1
                mes = contato_dt.strftime(
                    "%m/%Y") if contato_dt else "Desconhecido"
                bloc["matriculados"][mes] = bloc["matriculados"].get(
                    mes, 0) + 1

            bloc["status_aluno"][status] = bloc["status_aluno"].get(
                status, 0) + 1
            bloc["contatos"].append(contato_formatado)
            dados["totais"]["contatos"].append(contato_formatado)

        dados["consultores"][consultor] = bloc

        for k, v in bloc["status_aluno"].items():
            dados["totais"]["status_aluno"][k] = dados["totais"]["status_aluno"].get(
                k, 0) + v
        for k, v in bloc["negociacoes"].items():
            dados["totais"]["negociacoes"][k] = dados["totais"]["negociacoes"].get(
                k, 0) + v
        for k, v in bloc["matriculados"].items():
            dados["totais"]["matriculados"][k] = dados["totais"]["matriculados"].get(
                k, 0) + v

    return render_template("index_dashboard_completo_interativo.html", todosDados=dados)


@app.route('/dashboard-tabela')
def dashboard_tabela():
    conn = sqlite3.connect('base.db')
    df = pd.read_sql_query("SELECT * FROM contatos", conn)
    conn.close()

    df.fillna('', inplace=True)
    dados = df.to_dict(orient='records')
    return render_template('dashboard_tabela.html', todosDados=dados)


@app.context_processor
def inject_user_type():
    return dict(session=session)


@app.route("/")
def home():
    return "App está rodando. Acesse /dashboard-completo"


@app.route("/remover_duplicados", methods=["POST"])
def remover_duplicados():
    if session.get("tipo") != "admin":
        flash("Acesso negado. Apenas administradores podem remover duplicados.")
        # use o nome correto da sua view
        return redirect(url_for("dashboard_completo"))

    import sqlite3
    from datetime import datetime

    def parse_data(d):
        if not d:
            return datetime.max
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(d.strip(), fmt)
            except ValueError:
                continue
        return datetime.max

    conn = sqlite3.connect("base.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, Telefone, Primeiro_contato FROM contatos WHERE Telefone IS NOT NULL AND Telefone != ''")
    registros = cursor.fetchall()

    contatos_por_telefone = {}
    for id_, telefone, primeiro_contato in registros:
        data = parse_data(primeiro_contato)
        if telefone not in contatos_por_telefone or data < contatos_por_telefone[telefone][1]:
            contatos_por_telefone[telefone] = (id_, data)

    ids_para_manter = {info[0] for info in contatos_por_telefone.values()}
    todos_ids = {r[0] for r in registros}
    ids_para_deletar = todos_ids - ids_para_manter

    if ids_para_deletar:
        cursor.executemany("DELETE FROM contatos WHERE id = ?", [
                           (i,) for i in ids_para_deletar])
        conn.commit()
        mensagem = f"{len(ids_para_deletar)} duplicados removidos com sucesso!"
    else:
        mensagem = "Nenhum duplicado encontrado."

    conn.close()
    flash(mensagem)
    return redirect(url_for("index"))  # ajuste se necessário


@app.route('/adicionar-contato', methods=['GET', 'POST'])
def adicionar_contato():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        base = request.form.get('base')
        base_disponibilizada = request.form.get('base_disponibilizada')
        consultor = request.form.get('consultor')
        status_aluno = request.form.get('status_aluno')
        primeiro_contato = request.form.get('primeiro_contato')
        segundo_contato = request.form.get('segundo_contato')
        finalizado = request.form.get('finalizado')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contatos 
            (Nome, Telefone, Email, Base, Base_disponibilizada, Consultor, Status_aluno, Primeiro_contato, Segundo_contato, Finalizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome, telefone, email, base, base_disponibilizada, consultor,
            status_aluno, primeiro_contato, segundo_contato, finalizado
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    # GET request – carregar selects com dados do banco
    conn = get_db_connection()
    cursor = conn.cursor()

    valores_distintos = {}
    for col in COLUNAS:
        cursor.execute(f"SELECT DISTINCT {col} FROM contatos WHERE {col} IS NOT NULL AND {col} != ''")
        valores_distintos[col] = [r[0] for r in cursor.fetchall()]

    bases = valores_distintos.get("Base", [])
    bases_disponiveis = valores_distintos.get("Base_disponibilizada", [])
    status_aluno = valores_distintos.get("Status_aluno", [])
    finalizado = valores_distintos.get("Finalizado", [])
    consultores = CONSULTOR_LIST

    conn.close()

    return render_template(
        "adicionar_contato.html",
        bases=bases,
        bases_disponiveis=bases_disponiveis,
        status_aluno=status_aluno,
        finalizado=finalizado,
        consultores=consultores,
        contato=None  # <- isso evita o erro
    )

@app.route('/editar-contato/<int:id>', methods=['GET', 'POST'])
def editar_contato(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']
        base = request.form['base']
        base_disponibilizada = request.form['base_disponibilizada']
        consultor = request.form['consultor']
        status_aluno = request.form['status_aluno']
        primeiro_contato = request.form['primeiro_contato']
        segundo_contato = request.form['segundo_contato']
        finalizado = request.form['finalizado']

        cursor.execute('''
            UPDATE contatos
            SET nome = ?, telefone = ?, email = ?, base = ?, base_disponibilizada = ?,
                consultor = ?, status_aluno = ?, primeiro_contato = ?, segundo_contato = ?, finalizado = ?
            WHERE id = ?
        ''', (
            nome, telefone, email, base, base_disponibilizada, consultor, status_aluno,
            primeiro_contato, segundo_contato, finalizado, id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # GET: buscar dados do contato
    cursor.execute("SELECT * FROM contatos WHERE id = ?", (id,))
    contato = cursor.fetchone()

    bases = ["Instagram", "Facebook", "Google", "Indicação", "Feira", "WhatsApp"]
    bases_disponiveis = ["Base VOLTE", "Base B", "Base C", "Base D"]
    consultores = CONSULTOR_LIST
    status_aluno = ["Em Negociação", "Já é Aluno", "Matriculado", "Visualizou E Não Respondeu", "Retirar da Base"]
    finalizado = ["sim", "não"]

    conn.close()
    return render_template(
        'editar_contato.html',
        contato=contato,
        bases=bases,
        bases_disponiveis=bases_disponiveis,
        consultores=consultores,
        status_aluno=status_aluno,
        finalizado=finalizado
    )


if __name__ == '__main__':
    criar_tabela_usuarios()
    popular_usuarios()
    app.run(debug=True)
