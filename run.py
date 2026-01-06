from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_sessoes'

# Configuração da conexão com o MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'locadora_veiculos'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- 1. ROTA DE ENTRADA ---
@app.route('/')
def index():
    return render_template('auth/portal.html')

# --- 2. ÁREA DO CLIENTE ---
@app.route('/catalogo')
def catalogo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM veiculos WHERE status = 'disponivel'")
    veiculos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('client/catalogo.html', veiculos=veiculos)

@app.route('/alugar/<int:id_veiculo>')
def alugar_veiculo(id_veiculo):
    if 'usuario_id' not in session:
        flash("Faça login como cliente para reservar!", "danger")
        return redirect(url_for('login_portal'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT valor_diaria FROM veiculos WHERE id = %s", (id_veiculo,))
    veiculo = cursor.fetchone()

    if veiculo:
        cursor.execute("INSERT INTO alugueis (id_usuario, id_veiculo, valor_total) VALUES (%s, %s, %s)", 
                       (session['usuario_id'], id_veiculo, veiculo['valor_diaria']))
        cursor.execute("UPDATE veiculos SET status = 'alugado' WHERE id = %s", (id_veiculo,))
        conn.commit()
        flash("Reserva confirmada com sucesso!", "success")
    
    cursor.close()
    conn.close()
    return redirect(url_for('catalogo'))

# --- 3. AUTENTICAÇÃO E CADASTRO ---
@app.route('/login-portal')
def login_portal():
    return render_template('auth/portal.html')

@app.route('/login/cliente', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s AND perfil = 'cliente'", (email, senha))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session.update({'usuario_id': user['id'], 'nome': user['nome'], 'perfil': 'cliente'})
            return redirect(url_for('catalogo'))
        flash("Login de cliente inválido!", "danger")
    return render_template('auth/login_cliente.html')

@app.route('/login/equipe', methods=['GET', 'POST'])
def login_equipe():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s AND perfil IN ('admin', 'funcionario')", (email, senha))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session.update({'usuario_id': user['id'], 'nome': user['nome'], 'perfil': user['perfil']})
            return redirect(url_for('dashboard_admin'))
        flash("Acesso negado para equipe!", "danger")
    return render_template('auth/login_equipe.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        f = request.form
        # Organizando dados para o banco
        dados = (
            f.get('nome'), f.get('email'), f.get('senha'), f.get('cpf'), 
            f.get('data_nascimento'), f.get('cep'), f.get('rua'), 
            f.get('uf'), f.get('cidade'), f.get('numero'), 
            f.get('complemento', ''), f.get('pagamento_pref', 'pendente'),
            f.get('cartao_numero') if f.get('cartao_numero') else None
        )
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """INSERT INTO usuarios 
                       (nome, email, senha, cpf, data_nascimento, cep, rua, uf, cidade, numero, complemento, pagamento_pref, cartao_numero, perfil) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'cliente')"""
            cursor.execute(query, dados)
            conn.commit()
            flash("Cadastrado com sucesso! Agora você pode entrar.", "success")
            return redirect(url_for('login_cliente'))
        except mysql.connector.Error as err:
            flash(f"Erro ao cadastrar: {err}", "danger")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
            
    return render_template('auth/cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- 4. ÁREA ADMINISTRATIVA ---
@app.route('/admin/dashboard')
def dashboard_admin():
    if session.get('perfil') not in ['admin', 'funcionario']:
        flash("Acesso Negado!", "danger")
        return redirect(url_for('login_equipe'))
    return render_template('admin/painel.html')

if __name__ == '__main__':
    app.run(debug=True)