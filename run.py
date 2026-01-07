from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_sessoes'

# Configuração da conexão com o MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',       # Seu usuário do MySQL
    'password': 'root',       # Sua senha do MySQL
    'database': 'locadora_veiculos'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Rota da Página Inicial (Catálogo)
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM veiculos WHERE status = 'disponivel'")
    veiculos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('client/catalogo.html', veiculos=veiculos)

# Rota para Login Simplificada
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Aqui depois faremos a lógica de conferir email e senha
        session['usuario'] = 'Admin'
        session['perfil'] = 'admin'
        return redirect(url_for('index'))
    return render_template('auth/login.html')

if __name__ == '__main__':
    app.run(debug=True)
    
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # Clientes sempre são criados com perfil 'cliente' por padrão
        cursor.execute("INSERT INTO usuarios (nome, email, senha, perfil) VALUES (%s, %s, %s, 'cliente')", 
                       (nome, email, senha))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('auth/cadastro.html') # Você precisará criar este HTML similar ao login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
        user = cursor.fetchone()
        
        if user:
            session['usuario_id'] = user['id']
            session['nome'] = user['nome']
            session['perfil'] = user['perfil'] # Aqui guardamos se é 'cliente' ou 'admin'
            
            if user['perfil'] == 'admin':
                return redirect(url_for('dashboard_admin'))
            return redirect(url_for('index'))
        else:
            return "Login inválido!"
            
    return render_template('auth/login.html')

@app.route('/admin/dashboard')
def dashboard_admin():
    # Proteção: Só entra se for admin
    if session.get('perfil') != 'admin':
        return "Acesso Negado! Apenas administradores podem ver esta página.", 403
    return "Bem-vindo ao Painel do Administrador! Aqui você poderá criar funcionários."

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))