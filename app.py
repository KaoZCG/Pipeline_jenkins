from flask import Flask, request, render_template_string, session, redirect, url_for
import sqlite3
import os
import hashlib
import html # Para mitigar XSS nativamente

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_secreta_desarrollo')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Helper para validación de MFA (Control de Acceso)
def validar_sesion_mfa(session_dict):
    if 'user_id' not in session_dict or not session_dict.get('mfa_verified', False):
        return False
    return True

@app.route('/')
def index():
    return 'Welcome to the Task Manager Application! <a href="/login">Login here</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        # 1. MITIGACIÓN SQLi: Uso estricto de consultas parametrizadas (?)
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        hashed_password = hash_password(password)
        user = conn.execute(query, (username, hashed_password)).fetchone()
        conn.close()

        if user:
            # 2. MITIGACIÓN AUTENTICACIÓN DÉBIL: Pre-autenticación para MFA
            session['pre_auth_user_id'] = user['id']
            session['role'] = user['role']
            session['mfa_verified'] = False 
            return redirect(url_for('mfa_verify'))
        else:
            return 'Invalid credentials!'
            
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/mfa_verify', methods=['GET', 'POST'])
def mfa_verify():
    if 'pre_auth_user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        token = request.form['mfa_token'].strip()
        # Validación de MFA estático para la prueba
        if token == "123456":
            session['user_id'] = session['pre_auth_user_id']
            session['mfa_verified'] = True
            session.pop('pre_auth_user_id', None)
            return redirect(url_for('dashboard'))
        else:
            return 'Código MFA inválido.'

    return '''
        <form method="post">
            MFA Token (123456): <input type="text" name="mfa_token"><br>
            <input type="submit" value="Verificar">
        </form>
    '''

@app.route('/dashboard')
def dashboard():
    # 3. CONTROL DE ACCESO: Validación de MFA en endpoints críticos
    if not validar_sesion_mfa(session):
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    return render_template_string('''
        <h1>Welcome, user {{ user_id }}!</h1>
        <form action="/add_task" method="post">
            <input type="text" name="task" placeholder="New task"><br>
            <input type="submit" value="Add Task">
        </form>
        <h2>Your Tasks</h2>
        <ul>
        {% for task in tasks %}
            <li>
                {{ task['task'] }}
                <!-- 4. MITIGACIÓN CSRF: Cambio de enlace GET a formulario POST -->
                <form action="/delete_task" method="post" style="display:inline;">
                    <input type="hidden" name="task_id" value="{{ task['id'] }}">
                    <input type="submit" value="Delete">
                </form>
            </li>
        {% endfor %}
        </ul>
    ''', user_id=user_id, tasks=tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    if not validar_sesion_mfa(session):
        return redirect(url_for('login'))

    task_cruda = request.form['task'].strip()
    # 5. MITIGACIÓN XSS: HTML Encoding
    task_sanitizada = html.escape(task_cruda)
    
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task_sanitizada))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    if not validar_sesion_mfa(session):
        return redirect(url_for('login'))

    task_id = request.form['task_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin():
    # Validación combinada: MFA + RBAC
    if not validar_sesion_mfa(session) or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return 'Welcome to the admin panel!'

if __name__ == '__main__':
    # Usar host 0.0.0.0 es OBLIGATORIO para que funcione dentro de un contenedor Docker en Jenkins
    app.run(host='0.0.0.0', port=5000, debug=False)
