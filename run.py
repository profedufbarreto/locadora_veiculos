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

# --- 1. ROTA DE ENTRADA (PORTAL) ---

@app.route('/')
def index():
    # Esta é a PRIMEIRA página que o usuário verá
    return render_template('auth/portal.html')

# --- 2. ÁREA DO CLIENTE (CATÁLOGO E RESERVAS) ---

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
        flash("Faça login como cliente para reservar!")
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
        flash("Reserva confirmada!")
    
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
            session['usuario_id'] = user['id']
            session['nome'] = user['nome']
            session['perfil'] = 'cliente'
            return redirect(url_for('catalogo'))
        
        flash("Login de cliente inválido!")
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
            session['usuario_id'] = user['id']
            session['nome'] = user['nome']
            session['perfil'] = user['perfil']
            return redirect(url_for('dashboard_admin'))
        
        flash("Acesso negado para equipe!")
    return render_template('auth/login_equipe.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, email, senha, perfil) VALUES (%s, %s, %s, 'cliente')", (nome, email, senha))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Cadastro realizado! Faça login agora.")
        return redirect(url_for('login_cliente'))
    return render_template('auth/cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- 4. ÁREA ADMINISTRATIVA (EQUIPE) ---

@app.route('/admin/dashboard')
def dashboard_admin():
    if session.get('perfil') not in ['admin', 'funcionario']:
        flash("Acesso Negado! Identifique-se na área da equipe.")
        return redirect(url_for('login_equipe'))
    return render_template('admin/painel.html')

@app.route('/admin/equipe/novo', methods=['GET', 'POST'])
def cadastrar_equipe():
    if session.get('perfil') != 'admin':
        flash("Acesso restrito apenas ao Administrador.")
        return redirect(url_for('dashboard_admin'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        perfil = request.form['perfil'] 

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, email, senha, perfil) VALUES (%s, %s, %s, %s)", 
                       (nome, email, senha, perfil))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Novo colaborador cadastrado com sucesso!")
        return redirect(url_for('dashboard_admin'))
    
    return render_template('admin/cadastro_funcionario.html')

@app.route('/admin/devolver/<int:id_veiculo>')
def devolver_veiculo(id_veiculo):
    if session.get('perfil') not in ['admin', 'funcionario']:
        return "Acesso Negado!", 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE veiculos SET status = 'disponivel' WHERE id = %s", (id_veiculo,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Veículo liberado com sucesso!")
    return redirect(url_for('dashboard_admin'))

# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    app.run(debug=True)